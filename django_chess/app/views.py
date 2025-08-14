from typing import Iterator

import chess
import chess.svg

from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils.safestring import SafeString
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django_chess.app.models import Game


def get_buttonlike_div(board: chess.Board, rank: int, file_: int, game_display_number: int) -> SafeString:
    # see what's on the board at this spot.
    # - empty
    # - piece of active player
    # - piece of other player
    piece = board.piece_map().get(chess.square(file_, rank), None)
    background_color_class = "light" if (rank - file_) % 2 else "dark"

    svg_piece = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 45 45"></svg>"""

    target = reverse(
        "game",
        query=dict(
            game_display_number=game_display_number,
            rank=rank,
            file=file_
        ),
    )

    if piece is not None:
        svg_piece = chess.svg.piece(piece)

    return render_to_string(
        "app/buttonlike-div.html",
        context={
            "background_color_class": background_color_class,
            "content": SafeString(svg_piece),
            "target": target,
        },
    )


def get_squares(board: chess.Board, game_display_number: int) -> Iterator[dict[str, SafeString]]:
    for rank in range(7, -1, -1):
        for file_ in range(8):
            yield {"button": get_buttonlike_div(board, rank, file_, game_display_number)}


@require_http_methods(["GET", "POST"])
def game(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        new_game = Game.objects.create(board_fen=chess.Board().board_fen())
        return HttpResponseRedirect(reverse("game", query=dict(game_display_number=new_game.pk)))

    if (game_display_number := request.GET.get("game_display_number")) is None:
        return TemplateResponse(request, "app/game.html", context={})

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
            "squares": get_squares(board, g.pk),
        },
    )
