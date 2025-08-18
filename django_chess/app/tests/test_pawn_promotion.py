import chess

import pytest

from django_chess.app.tests import promotion_moves
from django_chess.app.views import promoting_push

from django.test import TestCase


def test_white_pawns_always_get_promoted() -> None:
    board = chess.Board()
    promotion_moves.play_back_prep_white(board)

    assert board.piece_at(chess.parse_square("a7")) == chess.Piece.from_symbol("P")

    promoting_push(board, chess.Move.from_uci("a7a8"))

    assert board.piece_at(chess.parse_square("a8")) == chess.Piece.from_symbol("Q")


def test_black_pawns_always_get_promoted() -> None:
    board = chess.Board()
    promotion_moves.play_back_prep_black(board)

    assert board.piece_at(chess.parse_square("h2")) == chess.Piece.from_symbol("p")

    promoting_push(board, chess.Move.from_uci("h2h1"))

    assert board.piece_at(chess.parse_square("h1")) == chess.Piece.from_symbol("q")

    # TODO -- promote a *white* pawn.
