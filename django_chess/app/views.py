import enum
from typing import Any, Iterator

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


class SquareFlavor(enum.Enum):
    # no piece on it, no "move here" button.  All we display is the underlying square's background color.
    BLANK = enum.auto()

    # no link.  The piece could be either white or black.
    NON_MOVEABLE_PIECE = enum.auto()

    # has a link that clears the highlight
    HIGHLIGHTED_PIECE = enum.auto()

    # has no piece on it, but has a button
    MOVE_HERE = enum.auto()

    # has a piece and a "capture me" button
    CAPTURABLE_PIECE = enum.auto()


def post_for_move(*args: Any, **kwargs: Any) -> Any:
    return "TODO"


def html_for_square(
    *,
    board: chess.Board,
    square: chess.Square,
    game_display_number: int,
    flavor: SquareFlavor,
) -> SafeString:
    piece = board.piece_map().get(square, None)
    background_color_class = (
        "light" if (chess.square_rank(square) - chess.square_file(square)) % 2 else "dark"
    )

    svg_piece = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 45 45"></svg>"""

    if piece is not None:
        svg_piece = chess.svg.piece(piece)

    highlight_class = link_target = button_magic = None
    match flavor:
        case SquareFlavor.BLANK:
            pass
        case SquareFlavor.NON_MOVEABLE_PIECE:
            pass
        case SquareFlavor.HIGHLIGHTED_PIECE:
            highlight_class = "highlighted"
            link_target = reverse("game", query=dict(game_display_number=game_display_number))
        case SquareFlavor.MOVE_HERE:
            # TODO -- looks like we need to be passed the currently-selected square, so that we can construct the URL to make the move.
            button_magic = post_for_move(...)
        case SquareFlavor.CAPTURABLE_PIECE:
            button_magic = post_for_move(...)

    return render_to_string(
        "app/buttonlike-div.html",
        context={
            "background_color_class": background_color_class,
            "button_magic": button_magic,
            "content": SafeString(svg_piece),
            "highlight": highlight_class,
            "target": link_target,
        },
    )


# If no square is selected:
# - give each square that has a moveable piece a link that will select that piece.
# Otherwise:
# (assume that the selected piece is indeed moveable.)
# - the selected piece is highlighted.
# - the selected piece has a link to this view with nothing selected -- i.e., clicking a selected piece clears the selection.
# - moveable pieces other than the selected one have the same link they'd have in the "not selected" case.
# - each legal destination of the selected piece gets a button that does a POST that actually makes the piece move to that destination.  This might overwrite the links from the previous step, in case of a capture.


def get_squares_none_selected(
    *, board: chess.Board, game_display_number: int
) -> Iterator[tuple[chess.Square, str]]:
    legal_moves = list(board.legal_moves) if board.outcome() is None else []
    movable_pieces = {board.piece_at(m.from_square) for m in legal_moves}

    for rank in range(7, -1, -1):
        for file_ in range(8):
            this_square = chess.square(file_, rank)
            selectable = board.piece_at(this_square) in movable_pieces

            if board.piece_at(this_square) is None:
                flavor = SquareFlavor.BLANK
            elif selectable:
                flavor = SquareFlavor.HIGHLIGHTED_PIECE
            else:
                flavor = SquareFlavor.NON_MOVEABLE_PIECE

            yield (
                this_square,
                html_for_square(
                    board=board,
                    square=this_square,
                    game_display_number=game_display_number,
                    flavor=flavor,
                ),
            )


def get_squares_with_selection(
    *, board: chess.Board, game_display_number: int, selected_square: chess.Square
) -> Iterator[tuple[chess.Square, str]]:
    yield_me = dict(get_squares_none_selected(board=board, game_display_number=game_display_number))

    legal_moves = list(board.legal_moves) if board.outcome() is None else []

    def holds_movable_piece(sq: chess.Square) -> bool:
        return sq in {m.from_square for m in legal_moves}

    selected_squares_moves = [m for m in legal_moves if selected_square == m.from_square]
    selected_squares_destinations = {m.to_square for m in selected_squares_moves}

    for rank in range(7, -1, -1):
        for file_ in range(8):
            this_square = chess.square(file_, rank)

            if this_square == selected_square:
                yield_me[this_square] = html_for_square(
                    board=board,
                    game_display_number=game_display_number,
                    square=this_square,
                    flavor=SquareFlavor.HIGHLIGHTED_PIECE,
                )

            elif holds_movable_piece(this_square):
                pass  # what's in yield_me is fine
            elif this_square in selected_squares_destinations:
                if board.piece_at(this_square) is None:
                    flavor = SquareFlavor.MOVE_HERE
                else:
                    flavor = SquareFlavor.CAPTURABLE_PIECE

                yield_me[this_square] = html_for_square(
                    board=board,
                    game_display_number=game_display_number,
                    square=this_square,
                    flavor=flavor,
                )

    yield from yield_me.items()


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

    if selected_square is None:
        square_items = get_squares_none_selected(board=board, game_display_number=g.pk)
    else:
        square_items = get_squares_with_selection(
            board=board, game_display_number=g.pk, selected_square=selected_square
        )

    return TemplateResponse(
        request,
        "app/game.html",
        context={
            "outcome": str(board.outcome()),
            "squares": dict(square_items),
        },
    )
