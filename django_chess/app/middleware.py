"""Custom middleware for the chess application."""
from django.http import HttpRequest, HttpResponse
from typing import Callable

from django_chess.app.version import API_VERSION


class APIVersionMiddleware:
    """
    Middleware that adds X-Chess-API-Version header to all responses.

    This allows clients to check API compatibility by comparing the server
    version (integer) against their minimum required version.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        # Add version header to all responses as integer
        response["X-Chess-API-Version"] = str(API_VERSION)

        return response
