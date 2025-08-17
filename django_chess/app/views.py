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

GNUCHESS_EXECUTABLE = "/home/erichanchrow/.local/bin/gnuchess"


class SquareFlavor(enum.Enum):
    # no piece on it, no "move here" button.  All we display is the underlying square's background color.
    BLANK = enum.auto()

    # no link.  The piece could be either white or black.
    NON_MOVEABLE_PIECE = enum.auto()

    # has a link that clears the highlight
    SELECTED = enum.auto()

    SELECTABLE = enum.auto()

    # has no piece on it, but has a button
    MOVE_HERE = enum.auto()

    # has a piece and a "capture me" button
    CAPTURABLE_PIECE = enum.auto()


def move_button(*, game_display_number: int, from_: chess.Square, to: chess.Square) -> Any:
    the_move = chess.Move(from_square=from_, to_square=to)
    label = the_move.uci()

    return format_html(
        """<button type="submit" form="move" name="move" value="{}">{}</button>""",
        the_move.uci(),
        label,
    )


def html_for_square(
    *,
    board: chess.Board,
    selected_square: chess.Square | None = None,
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
        case SquareFlavor.SELECTABLE:
            link_target = reverse(
                "game",
                query=dict(
                    game_display_number=game_display_number,
                    rank=chess.square_rank(square),
                    file=chess.square_file(square),
                ),
            )
        case SquareFlavor.SELECTED:
            highlight_class = "highlighted"
            link_target = reverse(
                "game",
                query=dict(game_display_number=game_display_number),
            )
        case SquareFlavor.MOVE_HERE | SquareFlavor.CAPTURABLE_PIECE:
            # TODO -- looks like we need to be passed the currently-selected square, so that we can construct the URL to make the move.
            assert selected_square is not None
            button_magic = move_button(
                game_display_number=game_display_number, from_=selected_square, to=square
            )
        case _:
            assert False, f"I don't know what to do with {flavor=}"

    content = svg_piece
    assert link_target is None or button_magic is None

    if link_target is not None:
        content = format_html(
            """<a href="{}">{}</a>""",
            SafeString(link_target),
            SafeString(content),
        )
    elif button_magic is not None:
        content = format_html(
            """<div>{}</div>""",
            button_magic,
        )

    return render_to_string(
        "app/buttonlike-div.html",
        context={
            "background_color_class": background_color_class,
            "content": SafeString(content),
            "highlight": highlight_class,
            "square_flavor": flavor,
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
    legal_moves = list(board.legal_moves) if board.legal_moves else []
    movable_pieces = {board.piece_at(m.from_square) for m in legal_moves}

    for rank in range(7, -1, -1):
        for file_ in range(8):
            this_square = chess.square(file_, rank)
            selectable = board.piece_at(this_square) in movable_pieces

            if board.piece_at(this_square) is None:
                flavor = SquareFlavor.BLANK
            elif selectable:
                flavor = SquareFlavor.SELECTABLE
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

    legal_moves = list(board.legal_moves) if board.legal_moves else []

    def holds_movable_piece(sq: chess.Square) -> bool:
        return sq in {m.from_square for m in legal_moves}

    selected_squares_moves = [m for m in legal_moves if selected_square == m.from_square]
    selected_squares_destinations = {m.to_square for m in selected_squares_moves}

    for rank in range(7, -1, -1):
        for file_ in range(8):
            this_square = chess.square(file_, rank)

            def p(*, flavor: SquareFlavor) -> str:
                return html_for_square(
                    board=board,
                    game_display_number=game_display_number,
                    selected_square=selected_square,
                    square=this_square,
                    flavor=flavor,
                )

            if this_square == selected_square:
                yield_me[this_square] = p(flavor=SquareFlavor.SELECTED)

            elif holds_movable_piece(this_square):
                pass  # what's in yield_me is fine
            elif this_square in selected_squares_destinations:
                yield_me[this_square] = p(
                    flavor=(
                        SquareFlavor.MOVE_HERE
                        if board.piece_at(this_square) is None
                        else SquareFlavor.CAPTURABLE_PIECE
                    )
                )

    yield from yield_me.items()


def sort_upper_left_first(
    square_string_tuples: Iterable[tuple[chess.Square, str]],
) -> Iterable[tuple[chess.Square, str]]:
    def key(toop: tuple[chess.Square, str]) -> tuple[int, int]:
        return (-chess.square_rank(toop[0]), chess.square_file(toop[0]))

    return sorted(square_string_tuples, key=key)


def save_board(*, board: chess.Board, game: Game) -> None:
    game.moves = json.dumps([m.uci() for m in board.move_stack])
    game.save()


def promoting_push(board: chess.Board, move: chess.Move) -> None:
    # unfortunately this is effectively a copy of some code in Board.is_pseudo_legal
    piece = board.piece_type_at(move.from_square)

    if piece == chess.PAWN and (
        (board.turn == chess.WHITE and chess.square_rank(move.to_square) == 7)
        or (board.turn == chess.BLACK and chess.square_rank(move.to_square) == 0)
    ):
        move.promotion = chess.QUEEN
    board.push(move)


def load_board(*, game: Game) -> chess.Board:
    board = chess.Board()
    sans = []

    if game.moves is not None:
        for m_uci_str in json.loads(game.moves):
            move = chess.Move.from_uci(m_uci_str)
            sans.append(board.san(move))
            promoting_push(board, move)

    setattr(board, "sans", sans)
    return board


@require_http_methods(["GET", "POST"])
def game(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        new_game = Game.objects.create()
        return HttpResponseRedirect(reverse("game", query=dict(game_display_number=new_game.pk)))

    if (game_display_number := request.GET.get("game_display_number")) is None:
        return TemplateResponse(request, "app/game.html", context={})

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
        "event_log": board.sans,
        "game_display_number": game_display_number,
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

    with chess.engine.SimpleEngine.popen_uci([GNUCHESS_EXECUTABLE, "--uci"]) as engine:
        result = engine.play(board, chess.engine.Limit(time=0.01))

        if result.move is not None:
            promoting_push(board, result.move)
            save_board(board=board, game=game)

    return HttpResponseRedirect(
        reverse("game", query=dict(game_display_number=game_display_number))
    )


@require_http_methods(["POST"])
def auto_move(request: HttpRequest, game_display_number: int) -> HttpResponse:
    game = Game.objects.filter(pk=game_display_number).first()
    if game is None:
        return HttpResponseNotFound()

    board = load_board(game=game)

    # TODO -- start the engine when the server starts, as opposed to every single time we want it to move
    with chess.engine.SimpleEngine.popen_uci([GNUCHESS_EXECUTABLE, "--uci"]) as engine:
        result = engine.play(board, chess.engine.Limit(time=1.0))

        if result.move is not None:
            promoting_push(board, result.move)
            save_board(board=board, game=game)

    return HttpResponseRedirect(
        reverse("game", query=dict(game_display_number=game_display_number))
    )
