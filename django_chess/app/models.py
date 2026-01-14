import uuid

import chess

from django.db import models
from django_extensions.db.models import TimeStampedModel
from django_chess.name_generator import generate_game_name


class Game(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, blank=True)
    in_progress = models.BooleanField(default=True)
    moves = models.CharField(null=True) # JSON list of UCI strings
    black_smartness = models.PositiveSmallIntegerField(default=10)

    def save(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        # Generate name from UUID on first save if not provided
        if not self.name:
            # Use UUID's integer representation as seed for deterministic names
            self.name = generate_game_name(seed=self.id.int)
        super().save(*args, **kwargs)  # type: ignore[no-untyped-call]

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
