import chess
import pytest

from django_chess.app.models import Game
from django_chess.app.tests import promotion_moves


@pytest.mark.django_db
def test_white_pawns_always_get_promoted() -> None:
    board = chess.Board()
    game = Game.objects.create()

    promotion_moves.play_back_prep_white(game, board)

    assert board.piece_at(chess.parse_square("a7")) == chess.Piece.from_symbol("P")

    game.promoting_push(board, chess.Move.from_uci("a7a8"))

    assert board.piece_at(chess.parse_square("a8")) == chess.Piece.from_symbol("Q")


@pytest.mark.django_db
def test_black_pawns_always_get_promoted() -> None:
    board = chess.Board()
    game = Game.objects.create()

    promotion_moves.play_back_prep_black(game, board)

    assert board.piece_at(chess.parse_square("h2")) == chess.Piece.from_symbol("p")

    game.promoting_push(board, chess.Move.from_uci("h2h1"))

    assert board.piece_at(chess.parse_square("h1")) == chess.Piece.from_symbol("q")

    # TODO -- promote a *white* pawn.
