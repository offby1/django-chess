import chess

from django.shortcuts import get_object_or_404, render
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
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


@require_http_methods(["GET"])
def game(request: HttpRequest, game_display_number: int) -> HttpResponse:
    g = Game.objects.filter(pk=game_display_number).first()
    board = chess.Board()
    board.set_board_fen(g.board_fen)
    return TemplateResponse(request, "app/game.html", context={"board": str(board)})
