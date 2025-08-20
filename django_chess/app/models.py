import uuid

import chess

from django.db import models


class Game(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    in_progress = models.BooleanField(default=True)
    moves = models.CharField(null=True)
    computer_think_time_ms = models.PositiveSmallIntegerField(default=1)

    def promoting_push(self, board: chess.Board, move: chess.Move) -> None:
        # unfortunately this is effectively a copy of some code in Board.is_pseudo_legal
        piece = board.piece_type_at(move.from_square)

        if piece == chess.PAWN and (
            (board.turn == chess.WHITE and chess.square_rank(move.to_square) == 7)
            or (board.turn == chess.BLACK and chess.square_rank(move.to_square) == 0)
        ):
            move.promotion = chess.QUEEN
        board.push(move)

        if board.outcome() is not None:
            self.in_progress = False
            self.save()
