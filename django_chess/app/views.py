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


@require_http_methods(["POST"])
def new_game(request: HttpRequest) -> HttpResponse:
    board = chess.Board()
    new_game = Game.objects.create(board_fen=board.board_fen())
    return HttpResponseRedirect(reverse("game", kwargs=dict(game_display_number=new_game.pk)))


def get_squares(board: chess.Board) -> Iterator[SafeString]:
    for rank in range(7, -1, -1):
        for file_ in range(8):
            background_color_class = "light" if (rank - file_) % 2 else "dark"
            n = chess.square(file_, rank)
            piece = board.piece_map().get(n, None)

            rv = {"class": background_color_class}

            if piece is not None:
                rv["piece"] = SafeString(chess.svg.piece(piece))
            else:
                rv["piece"] = SafeString("")

            yield rv


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
