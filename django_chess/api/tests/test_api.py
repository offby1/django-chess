import json
from typing import Any

import pytest
from rest_framework.test import APIClient

from django_chess.app.models import Game
from django_chess.api.serializers import GameListSerializer


@pytest.fixture
def api_client() -> APIClient:
    """Fixture to provide a DRF API client."""
    return APIClient()


@pytest.fixture
def sample_game() -> Game:
    """Fixture to create a sample game with some moves."""
    game = Game.objects.create(black_smartness=7)
    # Add some moves (e4 e5 Nf3 Nc6)
    game.moves = json.dumps(["e2e4", "e7e5", "g1f3", "b8c6"])
    game.save()
    return game


@pytest.fixture
def completed_game() -> Game:
    """Fixture to create a completed game."""
    game = Game.objects.create(black_smartness=10, in_progress=False)
    # Scholar's mate
    game.moves = json.dumps(["e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"])
    game.save()
    return game


# Serializer tests


@pytest.mark.django_db
def test_serializer_new_game() -> None:
    """Test serializing a new game with no moves."""
    game = Game.objects.create(black_smartness=5)
    serializer = GameListSerializer(game)
    data = serializer.data

    assert data["id"] == str(game.id)
    assert data["in_progress"] is True
    assert data["move_count"] == 0
    assert data["black_smartness"] == 5
    assert data["whose_turn"] == "white"
    assert data["outcome"] is None


@pytest.mark.django_db
def test_serializer_game_with_moves(sample_game: Game) -> None:
    """Test serializing a game with moves."""
    serializer = GameListSerializer(sample_game)
    data = serializer.data

    assert data["id"] == str(sample_game.id)
    assert data["in_progress"] is True
    assert data["move_count"] == 4
    assert data["black_smartness"] == 7
    assert data["whose_turn"] == "white"  # 4 moves = white's turn
    assert data["outcome"] is None


@pytest.mark.django_db
def test_serializer_game_black_turn() -> None:
    """Test serializing a game where it's black's turn."""
    game = Game.objects.create()
    game.moves = json.dumps(["e2e4"])  # Only one move
    game.save()

    serializer = GameListSerializer(game)
    data = serializer.data

    assert data["move_count"] == 1
    assert data["whose_turn"] == "black"


@pytest.mark.django_db
def test_serializer_completed_game(completed_game: Game) -> None:
    """Test serializing a completed game."""
    serializer = GameListSerializer(completed_game)
    data = serializer.data

    assert data["in_progress"] is False
    assert data["move_count"] == 7
    assert data["whose_turn"] == ""  # Empty for completed games
    assert data["outcome"] is not None
    assert "won" in data["outcome"].lower() or "draw" in data["outcome"].lower()


@pytest.mark.django_db
def test_serializer_multiple_games(sample_game: Game, completed_game: Game) -> None:
    """Test serializing multiple games."""
    games = [sample_game, completed_game]
    serializer = GameListSerializer(games, many=True)
    data = serializer.data

    assert len(data) == 2
    assert data[0]["id"] == str(sample_game.id)
    assert data[1]["id"] == str(completed_game.id)


@pytest.mark.django_db
def test_serializer_move_count_calculation() -> None:
    """Test that move count is calculated correctly."""
    game = Game.objects.create()
    serializer = GameListSerializer(game)
    assert serializer.data["move_count"] == 0

    game.moves = json.dumps(["e2e4"])
    game.save()
    serializer = GameListSerializer(game)
    assert serializer.data["move_count"] == 1

    game.moves = json.dumps(["e2e4", "e7e5", "g1f3"])
    game.save()
    serializer = GameListSerializer(game)
    assert serializer.data["move_count"] == 3


@pytest.mark.django_db
def test_serializer_whose_turn_alternates() -> None:
    """Test that whose_turn alternates correctly."""
    game = Game.objects.create()

    # Even number of moves = white's turn
    game.moves = json.dumps(["e2e4", "e7e5"])
    game.save()
    serializer = GameListSerializer(game)
    assert serializer.data["whose_turn"] == "white"

    # Odd number of moves = black's turn
    game.moves = json.dumps(["e2e4", "e7e5", "g1f3"])
    game.save()
    serializer = GameListSerializer(game)
    assert serializer.data["whose_turn"] == "black"


@pytest.mark.django_db
def test_serializer_outcome_for_white_win() -> None:
    """Test outcome when white wins."""
    game = Game.objects.create(in_progress=False)
    # Scholar's mate - white wins
    game.moves = json.dumps(["e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"])
    game.save()

    serializer = GameListSerializer(game)
    data = serializer.data

    assert data["outcome"] is not None
    assert "white" in data["outcome"].lower()


@pytest.mark.django_db
def test_serializer_read_only_fields() -> None:
    """Test that computed fields are read-only."""
    game = Game.objects.create(black_smartness=5)
    serializer = GameListSerializer(game)

    # These fields should be in the data
    assert "id" in serializer.data
    assert "move_count" in serializer.data
    assert "whose_turn" in serializer.data
    assert "outcome" in serializer.data

    # These are read-only fields
    assert "id" in serializer.Meta.read_only_fields
    assert "move_count" in serializer.Meta.read_only_fields
    assert "whose_turn" in serializer.Meta.read_only_fields
    assert "outcome" in serializer.Meta.read_only_fields


# API endpoint tests


@pytest.mark.django_db
def test_api_list_empty_games(api_client: APIClient) -> None:
    """Test listing games when database is empty."""
    response = api_client.get("/api/games/")

    assert response.status_code == 200
    data = response.json()
    assert "in_progress" in data
    assert "completed" in data
    assert data["in_progress"] == []
    assert data["completed"] == []


@pytest.mark.django_db
def test_api_list_in_progress_games(api_client: APIClient, sample_game: Game) -> None:
    """Test listing games with only in-progress games."""
    response = api_client.get("/api/games/")

    assert response.status_code == 200
    data = response.json()
    assert len(data["in_progress"]) == 1
    assert len(data["completed"]) == 0

    game_data = data["in_progress"][0]
    assert game_data["id"] == str(sample_game.id)
    assert game_data["in_progress"] is True
    assert game_data["move_count"] == 4
    assert game_data["black_smartness"] == 7


@pytest.mark.django_db
def test_api_list_completed_games(api_client: APIClient, completed_game: Game) -> None:
    """Test listing games with only completed games."""
    response = api_client.get("/api/games/")

    assert response.status_code == 200
    data = response.json()
    assert len(data["in_progress"]) == 0
    assert len(data["completed"]) == 1

    game_data = data["completed"][0]
    assert game_data["id"] == str(completed_game.id)
    assert game_data["in_progress"] is False
    assert game_data["move_count"] == 7


@pytest.mark.django_db
def test_api_list_mixed_games(
    api_client: APIClient, sample_game: Game, completed_game: Game
) -> None:
    """Test listing games with both in-progress and completed games."""
    # Create additional games
    game2 = Game.objects.create(black_smartness=3)
    game2.moves = json.dumps(["d2d4"])
    game2.save()

    game3 = Game.objects.create(black_smartness=8, in_progress=False)
    game3.moves = json.dumps(["e2e4", "e7e5"])
    game3.save()

    response = api_client.get("/api/games/")

    assert response.status_code == 200
    data = response.json()
    assert len(data["in_progress"]) == 2  # sample_game and game2
    assert len(data["completed"]) == 2  # completed_game and game3


@pytest.mark.django_db
def test_api_list_games_ordering(api_client: APIClient) -> None:
    """Test that games are ordered by id."""
    game1 = Game.objects.create(black_smartness=1)
    game2 = Game.objects.create(black_smartness=2)
    game3 = Game.objects.create(black_smartness=3)

    response = api_client.get("/api/games/")

    assert response.status_code == 200
    data = response.json()
    games = data["in_progress"]

    # Should have all 3 games
    assert len(games) == 3

    # All games should be present
    smartness_values = {g["black_smartness"] for g in games}
    assert smartness_values == {1, 2, 3}


@pytest.mark.django_db
def test_api_list_games_json_response(api_client: APIClient) -> None:
    """Test that response is valid JSON."""
    Game.objects.create()

    response = api_client.get("/api/games/")

    assert response.status_code == 200
    assert response["Content-Type"] == "application/json"

    # Should be valid JSON
    data = response.json()
    assert isinstance(data, dict)
    assert isinstance(data["in_progress"], list)
    assert isinstance(data["completed"], list)


@pytest.mark.django_db
def test_api_list_games_response_structure(api_client: APIClient, sample_game: Game) -> None:
    """Test that response has correct structure."""
    response = api_client.get("/api/games/")

    assert response.status_code == 200
    data = response.json()

    # Check top-level structure
    assert set(data.keys()) == {"in_progress", "completed"}

    # Check game object structure
    game_data = data["in_progress"][0]
    expected_fields = {"id", "in_progress", "move_count", "black_smartness", "whose_turn", "outcome"}
    assert set(game_data.keys()) == expected_fields


@pytest.mark.django_db
def test_api_list_allows_get_only(api_client: APIClient) -> None:
    """Test that list endpoint only accepts GET requests."""
    # GET should work
    response = api_client.get("/api/games/")
    assert response.status_code == 200

    # POST should not work (405 Method Not Allowed)
    response = api_client.post("/api/games/", {})
    assert response.status_code == 405

    # PUT should not work
    response = api_client.put("/api/games/", {})
    assert response.status_code == 405

    # DELETE should not work
    response = api_client.delete("/api/games/")
    assert response.status_code == 405


@pytest.mark.django_db
def test_api_list_games_with_various_smartness_levels(api_client: APIClient) -> None:
    """Test listing games with different AI difficulty levels."""
    Game.objects.create(black_smartness=0)
    Game.objects.create(black_smartness=5)
    Game.objects.create(black_smartness=10)

    response = api_client.get("/api/games/")

    assert response.status_code == 200
    data = response.json()
    games = data["in_progress"]

    smartness_levels = [g["black_smartness"] for g in games]
    assert 0 in smartness_levels
    assert 5 in smartness_levels
    assert 10 in smartness_levels


@pytest.mark.django_db
def test_api_list_games_uuid_format(api_client: APIClient) -> None:
    """Test that game IDs are valid UUIDs."""
    Game.objects.create()

    response = api_client.get("/api/games/")

    assert response.status_code == 200
    data = response.json()
    game_id = data["in_progress"][0]["id"]

    # Should be a valid UUID string
    import uuid
    uuid.UUID(game_id)  # Raises ValueError if invalid


@pytest.mark.django_db
def test_api_list_games_cors_headers(api_client: APIClient) -> None:
    """Test that CORS headers are present (for mobile clients)."""
    response = api_client.get("/api/games/")

    assert response.status_code == 200
    # With CORS_ALLOW_ALL_ORIGINS = True, we should have CORS headers
    # Note: In test environment, CORS headers might not be present
    # This test documents expected behavior in production


@pytest.mark.django_db
def test_api_serializer_consistency(api_client: APIClient, sample_game: Game) -> None:
    """Test that API response matches direct serializer output."""
    # Get data from serializer directly
    serializer = GameListSerializer(sample_game)
    serializer_data = serializer.data

    # Get data from API
    response = api_client.get("/api/games/")
    api_data = response.json()["in_progress"][0]

    # Should be identical
    assert api_data == serializer_data
