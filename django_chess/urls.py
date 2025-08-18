from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse

from debug_toolbar.toolbar import debug_toolbar_urls  # type: ignore [import-untyped]
from django_chess.app import views

urlpatterns = [
    path("", views.home, name="home"),
    path("admin/", admin.site.urls),
    path("game/<int:game_display_number>/", views.game, name="game"),
    # POST-only urls
    path("auto-move/<int:game_display_number>/", views.auto_move, name="auto-move"),
    path("move/<int:game_display_number>/", views.move, name="move"),
    path("game/", views.new_game, name="new-game"),
] + debug_toolbar_urls()
