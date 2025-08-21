from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse

from debug_toolbar.toolbar import debug_toolbar_urls  # type: ignore [import-untyped]
from django_chess.app import views

urlpatterns = [
    path("", views.home, name="home"),
    path("admin/", admin.site.urls),
    path("game/<uuid:game_id>/", views.game, name="game"),
    # POST-only urls
    path("move/<uuid:game_id>/", views.move, name="move"),
    path("game/", views.new_game, name="new-game"),
    path(
        "set-black-smartness/<uuid:game_id>/", views.set_black_smartness, name="set-black-smartness"
    ),
] + debug_toolbar_urls()
