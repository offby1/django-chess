from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse

from debug_toolbar.toolbar import debug_toolbar_urls  # type: ignore [import-untyped]
from django_chess.app import views

urlpatterns = [
    path("", lambda request: HttpResponseRedirect(reverse("game"))),
    path("admin/", admin.site.urls),
    path("game/", views.game, name="game"),
] + debug_toolbar_urls()
