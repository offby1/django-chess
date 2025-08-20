import enum
import json
from typing import Any, Iterable, Iterator
from uuid import UUID

import chess

from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import SafeString

from django_chess.app.models import Game


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


def move_button(*, game_display_number: UUID | str, from_: chess.Square, to: chess.Square) -> Any:
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
    game_display_number: UUID | str,
    flavor: SquareFlavor,
) -> SafeString:
    piece = board.piece_map().get(square, None)
    css_class = "light" if (chess.square_rank(square) - chess.square_file(square)) % 2 else "dark"

    svg_piece = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 45 45"></svg>"""

    if piece is not None:
        svg_piece = chess.svg.piece(piece)

    link_target = button_magic = None
    match flavor:
        case SquareFlavor.BLANK:
            pass
        case SquareFlavor.NON_MOVEABLE_PIECE:
            pass
        case SquareFlavor.SELECTABLE:
            link_target = reverse(
                "game",
                kwargs=dict(game_display_number=game_display_number),
                query=dict(
                    rank=chess.square_rank(square),
                    file=chess.square_file(square),
                ),
            )
        case SquareFlavor.SELECTED:
            css_class = "highlighted"
            link_target = reverse(
                "game",
                kwargs=dict(game_display_number=game_display_number),
            )
        case SquareFlavor.MOVE_HERE | SquareFlavor.CAPTURABLE_PIECE:
            assert selected_square is not None
            button_magic = move_button(
                game_display_number=game_display_number, from_=selected_square, to=square
            )
        case _:
            assert False, f"I don't know what to do with {flavor=}"

    if piece is not None and board.move_stack:
        most_recent_move = board.move_stack[-1].to_square

        if square == most_recent_move:
            css_class += " glow"

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
            "content": SafeString(content),
            "css_class": css_class,
            "square_flavor": flavor,
        },
    )


def get_squares_none_selected(
    *, board: chess.Board, game_display_number: UUID | str
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
    *, board: chess.Board, game_display_number: UUID | str, selected_square: chess.Square
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
