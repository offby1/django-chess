import chess

from django.test import TestCase


# Create your tests here.
def test_pawns_always_get_promoted() -> None:
    board = chess.Board.empty()

    for p, q in (["p", "q"], ["P", "Q"]):
        board.set_piece_at(chess.Square(chess.parse_square("a7")), chess.Piece.from_symbol(p))
        board.push(
            chess.Move(
                from_square=chess.parse_square("a7"),
                to_square=chess.parse_square("a8"),
                promotion=chess.QUEEN,
            )
        )
        assert board.piece_at(chess.parse_square("a8")) == chess.Piece.from_symbol(q)
