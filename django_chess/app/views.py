from django.shortcuts import get_object_or_404, render
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods
from django_chess.app.models import Game

# Create your views here.

@require_http_methods(["POST"])
def new_game(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Hello, world.  Hint: I did not create a new game.")


@require_http_methods(["GET"])
def game(request: HttpRequest, game_display_number: int) -> HttpResponse:
    g = get_object_or_404(Game, pk=game_display_number)
    return HttpResponse(str(g))
