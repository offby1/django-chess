from typing import Iterator

import chess
import chess.svg

from django.shortcuts import get_object_or_404, render
from django.utils.safestring import SafeString
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django_chess.app.models import Game

# Create your views here.


@require_http_methods(["GET", "POST"])
def new_game(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        new_game = Game.objects.create(board_fen=chess.Board().board_fen())
        return HttpResponseRedirect(reverse("game", kwargs=dict(game_display_number=new_game.pk)))

    return TemplateResponse(request, "app/game.html", context={})


def get_button(board: chess.Board, rank: int, file_: int) -> SafeString:
    # see what's on the board at this spot.
    # - empty
    # - piece of active player
    # - piece of other player
    piece = board.piece_map().get(chess.square(file_, rank), None)

    if piece is None:
        return SafeString("")

    return SafeString(chess.svg.piece(piece))


def get_squares(board: chess.Board) -> Iterator[dict[str, SafeString]]:
    for rank in range(7, -1, -1):
        for file_ in range(8):
            background_color_class = "light" if (rank - file_) % 2 else "dark"

            yield {
                "class": SafeString(background_color_class),
                "button": get_button(board, rank, file_),
            }


@require_http_methods(["GET"])
def game(request: HttpRequest, game_display_number: int) -> HttpResponse:
    g = Game.objects.filter(pk=game_display_number).first()
    if g is None:
        return HttpResponseNotFound()
    board = chess.Board()
    board.set_board_fen(g.board_fen)
    return TemplateResponse(
        request,
        "app/game.html",
        context={
            "outcome": str(board.outcome()),
            "squares": get_squares(board),
        },
    )
