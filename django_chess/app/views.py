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


def get_buttonlike_div(
    *,
    board: chess.Board,
    rank: int,
    file_: int,
    game_display_number: int,
    highlight_class: str | None,
) -> SafeString:
    # see what's on the board at this spot.
    # - empty
    # - piece of active player
    # - piece of other player
    piece = board.piece_map().get(chess.square(file_, rank), None)
    background_color_class = "light" if (rank - file_) % 2 else "dark"

    svg_piece = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 45 45"></svg>"""

    target = reverse(
        "game",
        query=dict(game_display_number=game_display_number, rank=rank, file=file_),
    )

    if piece is not None:
        svg_piece = chess.svg.piece(piece)

    return render_to_string(
        "app/buttonlike-div.html",
        context={
            "background_color_class": background_color_class,
            "content": SafeString(svg_piece),
            "highlight": highlight_class,
            "target": target,
        },
    )


def get_squares(
    *, board: chess.Board, game_display_number: int, selected_square: int | None
) -> Iterator[dict[str, SafeString]]:
    legal_moves = list(board.legal_moves) if board.outcome() is None else []
    selected_squares_moves = [m for m in legal_moves if selected_square == m.from_square]
    for rank in range(7, -1, -1):
        for file_ in range(8):
            this_square = chess.square(file_, rank)
            highlight_class = None
            if (
                selected_square is not None
                and rank == chess.square_rank(selected_square)
                and file_ == chess.square_file(selected_square)
            ):
                highlight_class = "highlighted"
            else:
                if any(m.to_square == this_square for m in selected_squares_moves):
                    highlight_class = "potential-target"
            yield {
                "button": get_buttonlike_div(
                    board=board,
                    rank=rank,
                    file_=file_,
                    game_display_number=game_display_number,
                    highlight_class=highlight_class,
                )
            }


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

    selected_square = None
    if (rank := request.GET.get("rank")) is not None and (
        file_ := request.GET.get("file")
    ) is not None:
        selected_square = chess.square(int(file_), int(rank))

    return TemplateResponse(
        request,
        "app/game.html",
        context={
            "outcome": str(board.outcome()),
            "squares": get_squares(
                board=board, game_display_number=g.pk, selected_square=selected_square
            ),
        },
    )
