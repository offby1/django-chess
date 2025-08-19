import enum
import json
import random
from typing import Any, Iterable, Iterator

import chess
import chess.engine
import chess.svg

from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseServerError,
    HttpResponseNotFound,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import SafeString
from django.views.decorators.http import require_http_methods

from django_chess.app.models import Game
from django_chess.app.utils import (
    get_squares_none_selected,
    get_squares_with_selection,
    load_board,
    promoting_push,
    save_board,
    sort_upper_left_first,
)

GNUCHESS_EXECUTABLE = "/home/erichanchrow/.local/bin/gnuchess"


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
    return TemplateResponse(request, "app/home.html", context={})


@require_http_methods(["POST"])
def new_game(request: HttpRequest) -> HttpResponse:
    new_game = Game.objects.create()
    return HttpResponseRedirect(reverse("game", kwargs=dict(game_display_number=new_game.pk)))


@require_http_methods(["GET"])
def game(request: HttpRequest, game_display_number: int) -> HttpResponse:
    game = Game.objects.filter(pk=game_display_number).first()
    if game is None:
        return HttpResponseNotFound()

    board = load_board(game=game)

    selected_square = None
    if (rank := request.GET.get("rank")) is not None and (
        file_ := request.GET.get("file")
    ) is not None:
        selected_square = chess.square(int(file_), int(rank))

    if selected_square is None:
        square_items = get_squares_none_selected(board=board, game_display_number=game.pk)
    else:
        square_items = get_squares_with_selection(
            board=board, game_display_number=game.pk, selected_square=selected_square
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


@require_http_methods(["POST"])
def move(request: HttpRequest, game_display_number: int) -> HttpResponse:
    game = Game.objects.filter(pk=game_display_number).first()
    if game is None:
        return HttpResponseNotFound()

    board = load_board(game=game)

    # TODO -- error handling.  What if "move" isn't present?
    move = chess.Move.from_uci(request.POST["move"])

    # TODO -- check that the move is legal
    promoting_push(board, move)

    save_board(board=board, game=game)

    if game.computer_think_time_ms > 0:
        with chess.engine.SimpleEngine.popen_uci([GNUCHESS_EXECUTABLE, "--uci"]) as engine:
            result = engine.play(
                board, chess.engine.Limit(time=game.computer_think_time_ms / 1_000)
            )

            if result.move is not None:
                promoting_push(board, result.move)
                save_board(board=board, game=game)

    return HttpResponseRedirect(
        reverse("game", kwargs=dict(game_display_number=game_display_number))
    )


@require_http_methods(["POST"])
def set_think_time(request: HttpRequest, game_display_number: int) -> HttpResponse:
    game = get_object_or_404(Game, pk=game_display_number)
    game.computer_think_time_ms = request.POST["gnuchess-timelimit-ms"]
    game.save()

    return HttpResponseRedirect(
        reverse("game", kwargs=dict(game_display_number=game_display_number))
    )
