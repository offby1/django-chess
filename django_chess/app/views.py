import os
import pathlib
import random

from uuid import UUID

import chess
import chess.engine
import chess.svg

from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseNotFound,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from django_chess.app.models import Game
from django_chess.app.utils import (
    get_squares_none_selected,
    get_squares_with_selection,
    load_board,
    save_board,
    sort_upper_left_first,
)


def _first_existing_executable(candidates: list[str]) -> pathlib.Path | None:
    for c in candidates:
        p = pathlib.Path(c)
        if p.exists() and p.is_file() and os.access(p, os.X_OK):
            return p

    return None


GNUCHESS_EXECUTABLE = _first_existing_executable(
    [
        # This works on Debian 12 ("bookworm")
        "/usr/games/gnuchess",
        # This works on MacOS with homebrew
        "/opt/homebrew/bin/gnuchess",
    ]
)


# If no square is selected:
# - give each square that has a moveable piece a link that will select that piece.
# Otherwise:
# (assume that the selected piece is indeed moveable.)
# - the selected piece is highlighted.
# - the selected piece has a link to this view with nothing selected -- i.e., clicking a selected piece clears the selection.
# - moveable pieces other than the selected one have the same link they'd have in the "not selected" case.
# - each legal destination of the selected piece gets a button that does a POST that actually makes the piece move to that destination.  This might overwrite the links from the previous step, in case of a capture.


@require_http_methods(["GET"])
def home(request: HttpRequest) -> HttpResponse:
    completed_games = Game.objects.filter(in_progress=False)
    return TemplateResponse(
        request,
        "app/home.html",
        context={
            "completed_games": completed_games,
            "num_games": Game.objects.count(),
        },
    )


@require_http_methods(["POST"])
def new_game(request: HttpRequest) -> HttpResponse:
    new_game = Game.objects.create()
    return HttpResponseRedirect(reverse("game", kwargs=dict(game_id=new_game.pk)))


@require_http_methods(["GET"])
def game(request: HttpRequest, game_id: UUID | str) -> HttpResponse:
    game = Game.objects.filter(pk=game_id).first()
    if game is None:
        return HttpResponseNotFound()

    board = load_board(game=game)

    selected_square = None
    if (rank := request.GET.get("rank")) is not None and (
        file_ := request.GET.get("file")
    ) is not None:
        selected_square = chess.square(int(file_), int(rank))

    if selected_square is None:
        square_items = get_squares_none_selected(board=board, game_id=game.pk)
    else:
        square_items = get_squares_with_selection(
            board=board, game_id=game.pk, selected_square=selected_square
        )

    context = {
        "board": board,
        "event_log": getattr(board, "sans", []),
        "game": game,
        "squares": [t[1] for t in sort_upper_left_first(square_items)],
        "whose_turn": "white" if board.turn else "black",
    }

    if (outcome := board.outcome()) is not None:
        context["outcome"] = str(outcome)

    return TemplateResponse(
        request,
        "app/game.html",
        context=context,
    )


def num_black_moves(board: chess.Board) -> int:
    # Remember, len(board.move_stack) == the number of "half-moves".
    total_moves, _ = divmod(len(board.move_stack), 2)

    return total_moves


@require_http_methods(["POST"])
def move(request: HttpRequest, game_id: UUID | str) -> HttpResponse:
    game: Game | None = Game.objects.filter(pk=game_id).first()
    if game is None:
        return HttpResponseNotFound()

    board = load_board(game=game)

    # TODO -- error handling.  What if "move" isn't present?
    move = chess.Move.from_uci(request.POST["move"])

    # TODO -- check that the move is legal
    game.promoting_push(board, move)

    if board.outcome() is not None:
        game.in_progress = False

    save_board(board=board, game=game)

    if num_black_moves(board) % 10 < game.black_smartness and GNUCHESS_EXECUTABLE is not None:
        with chess.engine.SimpleEngine.popen_uci([str(GNUCHESS_EXECUTABLE), "--uci"]) as engine:
            result = engine.play(board, chess.engine.Limit(time=0))

            if result.move is not None:
                game.promoting_push(board, result.move)
                save_board(board=board, game=game)
    else:
        legal_moves = list(board.legal_moves)
        if legal_moves:
            random.shuffle(legal_moves)
            game.promoting_push(board, legal_moves[0])
            save_board(board=board, game=game)

    return HttpResponseRedirect(reverse("game", kwargs=dict(game_id=game_id)))


# Meant for HTMX, which is why it returns just the slider, not a whole page.
@require_http_methods(["POST"])
def set_black_smartness(request: HttpRequest, game_id: UUID) -> TemplateResponse:
    game = get_object_or_404(Game, pk=game_id)

    game.black_smartness = request.POST["smartness_tenths"]
    game.save()

    return TemplateResponse(request, "app/smartness-slider.html", context={"game": game})
