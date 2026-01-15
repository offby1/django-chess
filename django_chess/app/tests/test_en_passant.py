import chess
import pytest

from django_chess.app.models import Game


@pytest.mark.django_db
def test_en_passant_capture() -> None:
    """Test that en passant capturing works correctly.

    En passant is a special pawn capture that can occur when:
    1. A pawn advances two squares from its starting position
    2. It lands beside an opponent's pawn on the same rank
    3. The opponent can capture it "in passing" as if it had only moved one square
    4. This capture must be done immediately or the right is lost
    """
    board = chess.Board()
    game = Game.objects.create()

    # Set up the position for en passant:
    # 1. Move white pawn from e2 to e4
    game.promoting_push(board, chess.Move.from_uci("e2e4"))

    # 2. Move black pawn from d7 to d5 (any move to advance the game)
    game.promoting_push(board, chess.Move.from_uci("d7d5"))

    # 3. Move white pawn from e4 to e5 (now it's on the 5th rank)
    game.promoting_push(board, chess.Move.from_uci("e4e5"))

    # 4. Move black pawn from f7 to f5 (two squares forward, landing beside white's pawn on e5)
    game.promoting_push(board, chess.Move.from_uci("f7f5"))

    # Now white can capture en passant: e5 to f6
    en_passant_move = chess.Move.from_uci("e5f6")

    # Verify this is a legal move
    assert en_passant_move in board.legal_moves, "En passant capture should be a legal move"

    # Verify the black pawn is currently at f5
    assert board.piece_at(chess.parse_square("f5")) == chess.Piece.from_symbol("p")

    # Execute the en passant capture
    game.promoting_push(board, en_passant_move)

    # After en passant:
    # - White pawn should be at f6
    assert board.piece_at(chess.parse_square("f6")) == chess.Piece.from_symbol("P")

    # - Black pawn at f5 should be captured (square should be empty)
    assert board.piece_at(chess.parse_square("f5")) is None

    # - The original white pawn position (e5) should be empty
    assert board.piece_at(chess.parse_square("e5")) is None
