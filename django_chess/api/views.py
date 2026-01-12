from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django_chess.app.models import Game
from django_chess.api.serializers import GameListSerializer


class GameViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for game operations.

    Currently supports:
    - list: GET /api/games/ - List all games grouped by status
    """

    queryset = Game.objects.all().order_by('-id')
    serializer_class = GameListSerializer

    def list(self, request, *args, **kwargs):
        """
        Return games grouped by status: in_progress and completed.
        """
        # Get all games
        in_progress_games = Game.objects.filter(in_progress=True).order_by('-id')
        completed_games = Game.objects.filter(in_progress=False).order_by('-id')

        # Serialize the games
        in_progress_serializer = self.get_serializer(in_progress_games, many=True)
        completed_serializer = self.get_serializer(completed_games, many=True)

        return Response({
            'in_progress': in_progress_serializer.data,
            'completed': completed_serializer.data
        })
