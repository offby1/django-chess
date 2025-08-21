import logging

import chess
import chess.engine
import pytest

from django_chess.app.models import Game
from django_chess.app.views import GNUCHESS_EXECUTABLE
from django_chess.app.tests import repro_moves


@pytest.mark.django_db
def test_kaboom() -> None:
    chess.engine.LOGGER.setLevel(logging.DEBUG)
    board = chess.Board()
    game = Game.objects.create()

    repro_moves.play_back_prep(game, board)

    # I guess we've checkmated Black.
    print(board)

    with chess.engine.SimpleEngine.popen_uci([str(GNUCHESS_EXECUTABLE), "--uci"]) as engine:
        engine.play(board, chess.engine.Limit(time=0))

    # No assertion; we're just checking that the above call to "engine.play" doesn't raise an exception.
