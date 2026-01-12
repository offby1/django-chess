import json

from rest_framework import serializers

from django_chess.app.models import Game
from django_chess.app.utils import load_board


class GameListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing games."""

    move_count = serializers.SerializerMethodField()
    whose_turn = serializers.SerializerMethodField()
    outcome = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = ['id', 'in_progress', 'move_count', 'black_smartness', 'whose_turn', 'outcome']
        read_only_fields = ['id', 'move_count', 'whose_turn', 'outcome']

    def get_move_count(self, obj: Game) -> int:
        """Return the number of moves made in the game."""
        if obj.moves is None:
            return 0
        return len(json.loads(obj.moves))

    def get_whose_turn(self, obj: Game) -> str:
        """Return whose turn it is ('white' or 'black')."""
        if not obj.in_progress:
            return ""

        board = load_board(game=obj)
        return "white" if board.turn else "black"

    def get_outcome(self, obj: Game) -> str | None:
        """Return the game outcome if the game is finished."""
        if obj.in_progress:
            return None

        board = load_board(game=obj)
        outcome = board.outcome()

        if outcome is None:
            return None

        if outcome.winner is None:
            return "Draw"
        elif outcome.winner:
            return "White won"
        else:
            return "Black won"
