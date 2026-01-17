import os
import pathlib
import random
from typing import Any

import chess
import chess.engine
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from django_chess.app.models import Game
from django_chess.app.utils import load_board, save_board
from django_chess.api.serializers import (
    CreateGameSerializer,
    GameDetailSerializer,
    GameListSerializer,
    MoveSerializer,
    UpdateGameSerializer,
)


def _first_existing_executable(candidates: list[str]) -> pathlib.Path | None:
    """Find first existing executable from a list of candidates."""
    for c in candidates:
        p = pathlib.Path(c)
        if p.exists() and p.is_file() and os.access(p, os.X_OK):
            return p
    return None


GNUCHESS_EXECUTABLE = _first_existing_executable(
    [
        "/usr/games/gnuchess",  # Debian/Ubuntu
        "/opt/homebrew/bin/gnuchess",  # macOS Homebrew
    ]
)


def num_black_moves(board: chess.Board) -> int:
    """Calculate number of black moves made."""
    total_moves, _ = divmod(len(board.move_stack), 2)
    return total_moves


def get_black_move(board: chess.Board, smartness: int) -> chess.Move | None:
    """Get black's move based on AI smartness level (0-10)."""
    if not board.turn:  # It's black's turn
        # Use GNU Chess engine if smartness threshold met and executable available
        if num_black_moves(board) % 10 < smartness and GNUCHESS_EXECUTABLE is not None:
            try:
                with chess.engine.SimpleEngine.popen_uci([str(GNUCHESS_EXECUTABLE), "--uci"]) as engine:
                    result = engine.play(board, chess.engine.Limit(time=0))
                    if result.move is not None and result.move != chess.Move.null():
                        return result.move
            except Exception:
                # Fall through to random move if engine fails
                pass

        # Otherwise make a random legal move
        legal_moves = list(board.legal_moves)
        if legal_moves:
            return random.choice(legal_moves)

    return None


class GameViewSet(viewsets.ModelViewSet[Game]):
    """
    ViewSet for game operations.

    Endpoints:
    - list: GET /api/games/ - List completed games
    - create: POST /api/games/ - Create a new game
    - retrieve: GET /api/games/<uuid>/ - Get game detail with board state
    - partial_update: PATCH /api/games/<uuid>/ - Update game settings
    - destroy: DELETE /api/games/<uuid>/ - Delete a game
    - moves: POST /api/games/<uuid>/moves/ - Make a move
    """

    queryset = Game.objects.ordered_queryset()
    serializer_class = GameListSerializer

    def get_queryset(self) -> Any:
        """Return queryset, filtering for completed games only in list action."""
        queryset = super().get_queryset()
        if self.action == 'list':
            return queryset.filter(in_progress=False)
        return queryset

    def get_serializer_class(self) -> type[GameListSerializer] | type[GameDetailSerializer] | type[CreateGameSerializer] | type[UpdateGameSerializer]:
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return GameDetailSerializer
        elif self.action == 'create':
            return CreateGameSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateGameSerializer
        return GameListSerializer

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Return completed games only.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a new game.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        game = serializer.save()

        # Return detailed game state
        detail_serializer = GameDetailSerializer(game)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Get detailed game state including board position and legal moves.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Update game settings (currently only black_smartness).
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Delete a game.
        """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def moves(self, request: Request, pk: str | None = None) -> Response:
        """
        Make a move in the game.

        Request body: {"move": "e2e4"}
        Returns updated game state including AI response if applicable.
        """
        game = self.get_object()

        if not game.in_progress:
            return Response(
                {"error": "Game is already finished"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate the move
        move_serializer = MoveSerializer(data=request.data)
        move_serializer.is_valid(raise_exception=True)
        move_uci = move_serializer.validated_data['move']

        # Load board and validate move is legal
        board = load_board(game=game)

        try:
            move = chess.Move.from_uci(move_uci)
        except ValueError:
            return Response(
                {"error": "Invalid move format"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if move not in board.legal_moves:
            return Response(
                {"error": "Illegal move"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Make the move
        game.promoting_push(board, move)
        save_board(board=board, game=game)

        ai_response = None

        # If game is still in progress and it's black's turn, make AI move
        if game.in_progress and not board.turn:  # black's turn
            black_move = get_black_move(board, game.black_smartness)
            if black_move:
                ai_response = black_move.uci()
                game.promoting_push(board, black_move)
                save_board(board=board, game=game)

        # Return updated game state
        detail_serializer = GameDetailSerializer(game)
        response_data = {
            "move_made": move_uci,
            "ai_response": ai_response,
            "game_state": detail_serializer.data
        }

        return Response(response_data)
