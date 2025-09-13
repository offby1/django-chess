import io
import json
import logging
import os
import pathlib
import random

from uuid import UUID

import chess
import chess.engine
import chess.pgn

from django.core.files.uploadedfile import UploadedFile
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

from django_chess.app.forms import ImportPGNForm
from django_chess.app.models import Game
from django_chess.app.utils import (
    get_squares_none_selected,
    get_squares_with_selection,
    load_board,
    save_board,
    sort_upper_left_first,
)


logger = logging.getLogger(__name__)


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
    in_progress_games = Game.objects.filter(in_progress=True)
    return TemplateResponse(
        request,
        "app/home.html",
        context={
            "completed_games": completed_games,
            "in_progress_games": in_progress_games,
            "form": ImportPGNForm(),
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
        "captured_pieces": getattr(board, "captured_pieces"),
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


@require_http_methods(["GET"])
def pgn_game(request: HttpRequest, game_id: UUID | str) -> HttpResponse:
    board = load_board(game=get_object_or_404(Game, pk=game_id))
    game = chess.pgn.Game.from_board(board)
    exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
    pgn_string = game.accept(exporter)

    match request.get_preferred_type(["text/html", "text/plain"]):
        case "text/plain":
            return HttpResponse(pgn_string, content_type="text/plain")
        case "text/html":
            return HttpResponse(
                pgn_string,
                headers={
                    "Content-Type": "text/plain",
                    "Content-Disposition": f'attachment; filename="{game_id}.pgn"',
                })
        case _:
            return HttpResponse("Sorry, we only serve text/plain and text/html here", status=400)


@require_http_methods(["POST"])
def import_pgn(request: HttpRequest) -> HttpResponse:
    form = ImportPGNForm(request.POST, request.FILES)

    if not form.is_valid():
        return HttpResponse("Form isn't valid", status=400)

    uploaded_file = request.FILES['imported_pgn']
    if not isinstance(uploaded_file, UploadedFile):
        return HttpResponse(
            f"Sorry, but I don't know how to deal with {uploaded_file=} since it isn't an Uploaded_File",
            status=400,
        )

    if (uploaded_file.size or 0) > 1_000_000: # semi-arbitrary; meant to prevent denial of service
        return HttpResponse(f"{uploaded_file.size} bytes is too large for a PGN", status=400)

    new_games = []
    stringio = io.StringIO(uploaded_file.read().decode())

    while True:
        read_ = chess.pgn.read_game(stringio)

        if read_ is None:
            break

        new_game = Game.objects.create()
        new_game.moves = json.dumps([m.uci() for m in read_.mainline_moves()])
        if read_.board().outcome() is not None:
            new_game.in_progress = False
        new_game.save()
        new_games.append(new_game)

    logger.info("Read %d games from %s", len(new_games), uploaded_file)

    if len(new_games) == 1:
        return HttpResponseRedirect(reverse("game", kwargs=dict(game_id=new_games[0].pk)))

    return HttpResponseRedirect("/")


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
                if result.move == chess.Move.null():
                    # not sure what this means but I'm gonna assume Black is resigned, or checkmated, or something.
                    game.in_progress = False
                else:
                    game.promoting_push(board, result.move)
                save_board(board=board, game=game)

                # TODO -- check result.resigned; dunno what to do if it's True though
    else:
        legal_moves = list(board.legal_moves)
        if legal_moves:
            random.shuffle(legal_moves)
            game.promoting_push(board, legal_moves[0])
            save_board(board=board, game=game)

    if board.outcome() is not None:
        game.in_progress = False
        save_board(board=board, game=game)

    return HttpResponseRedirect(reverse("game", kwargs=dict(game_id=game_id)))


# Meant for HTMX, which is why it returns just the slider, not a whole page.
@require_http_methods(["POST"])
def set_black_smartness(request: HttpRequest, game_id: UUID) -> TemplateResponse:
    game = get_object_or_404(Game, pk=game_id)

    game.black_smartness = request.POST["smartness_tenths"]
    game.save()

    return TemplateResponse(request, "app/smartness-slider.html", context={"game": game})
