from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods


# Create your views here.

@require_http_methods(["POST"])
def new_game(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Hello, world.  Hint: I did not create a new game.")


@require_http_methods(["GET"])
def game(request: HttpRequest, game_display_number: int) -> HttpResponse:
    return HttpResponse(f"Pretend this is game {game_display_number}.")
