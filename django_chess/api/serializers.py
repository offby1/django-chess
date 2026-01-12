import json
from typing import Any

import chess
from rest_framework import serializers

from django_chess.app.models import Game
from django_chess.app.utils import load_board


class GameListSerializer(serializers.ModelSerializer[Game]):
    """Lightweight serializer for listing games."""

    move_count = serializers.SerializerMethodField()
    whose_turn = serializers.SerializerMethodField()
    outcome = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = ['id', 'in_progress', 'move_count', 'black_smartness', 'whose_turn', 'outcome']
        read_only_fields = ['id', 'move_count', 'whose_turn', 'outcome']

    def get_move_count(self, obj: Game) -> int:
        """Return the number of moves made in the game."""
        if obj.moves is None:
            return 0
        return len(json.loads(obj.moves))

    def get_whose_turn(self, obj: Game) -> str:
        """Return whose turn it is ('white' or 'black')."""
        if not obj.in_progress:
            return ""

        board = load_board(game=obj)
        return "white" if board.turn else "black"

    def get_outcome(self, obj: Game) -> str | None:
        """Return the game outcome if the game is finished."""
        if obj.in_progress:
            return None

        board = load_board(game=obj)
        outcome = board.outcome()

        if outcome is None:
            return None

        if outcome.winner is None:
            return "Draw"
        elif outcome.winner:
            return "White won"
        else:
            return "Black won"


class GameDetailSerializer(serializers.ModelSerializer[Game]):
    """Detailed serializer for individual game with full board state."""

    move_uci = serializers.SerializerMethodField()
    move_san = serializers.SerializerMethodField()
    board_fen = serializers.SerializerMethodField()
    whose_turn = serializers.SerializerMethodField()
    legal_moves = serializers.SerializerMethodField()
    captured_pieces = serializers.SerializerMethodField()
    outcome = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            'id', 'in_progress', 'move_uci', 'move_san', 'black_smartness',
            'board_fen', 'whose_turn', 'legal_moves', 'captured_pieces', 'outcome'
        ]
        read_only_fields = [
            'id', 'move_uci', 'move_san', 'board_fen', 'whose_turn',
            'legal_moves', 'captured_pieces', 'outcome'
        ]

    def get_move_uci(self, obj: Game) -> list[str]:
        """Return moves in UCI format."""
        if obj.moves is None:
            return []
        moves: list[str] = json.loads(obj.moves)
        return moves

    def get_move_san(self, obj: Game) -> list[str]:
        """Return moves in Standard Algebraic Notation."""
        board = load_board(game=obj)
        sans: list[str] = getattr(board, 'sans', [])
        return sans

    def get_board_fen(self, obj: Game) -> str:
        """Return current board position in FEN notation."""
        board = load_board(game=obj)
        return board.fen()

    def get_whose_turn(self, obj: Game) -> str:
        """Return whose turn it is ('white' or 'black')."""
        if not obj.in_progress:
            return ""
        board = load_board(game=obj)
        return "white" if board.turn else "black"

    def get_legal_moves(self, obj: Game) -> list[str]:
        """Return all legal moves in UCI format."""
        if not obj.in_progress:
            return []
        board = load_board(game=obj)
        return [move.uci() for move in board.legal_moves]

    def get_captured_pieces(self, obj: Game) -> dict[str, list[str]]:
        """Return captured pieces for both sides."""
        board = load_board(game=obj)
        captured = getattr(board, 'captured_pieces', [[], []])
        return {
            "white": captured[chess.WHITE],
            "black": captured[chess.BLACK]
        }

    def get_outcome(self, obj: Game) -> str | None:
        """Return the game outcome if the game is finished."""
        if obj.in_progress:
            return None

        board = load_board(game=obj)
        outcome = board.outcome()

        if outcome is None:
            return None

        if outcome.winner is None:
            return "Draw"
        elif outcome.winner:
            return "White won by checkmate" if outcome.termination == chess.Termination.CHECKMATE else "White won"
        else:
            return "Black won by checkmate" if outcome.termination == chess.Termination.CHECKMATE else "Black won"


class CreateGameSerializer(serializers.ModelSerializer[Game]):
    """Serializer for creating a new game."""

    class Meta:
        model = Game
        fields = ['id', 'black_smartness']
        read_only_fields = ['id']

    def validate_black_smartness(self, value: int) -> int:
        """Validate AI difficulty is in valid range."""
        if not 0 <= value <= 10:
            raise serializers.ValidationError("black_smartness must be between 0 and 10")
        return value


class MoveSerializer(serializers.Serializer[Any]):
    """Serializer for making a move."""

    move = serializers.CharField(max_length=10, help_text="Move in UCI format (e.g., 'e2e4')")

    def validate_move(self, value: str) -> str:
        """Validate move is in UCI format."""
        try:
            chess.Move.from_uci(value)
        except ValueError as e:
            raise serializers.ValidationError(f"Invalid UCI move format: {e}")
        return value


class UpdateGameSerializer(serializers.ModelSerializer[Game]):
    """Serializer for updating game settings."""

    class Meta:
        model = Game
        fields = ['black_smartness']

    def validate_black_smartness(self, value: int) -> int:
        """Validate AI difficulty is in valid range."""
        if not 0 <= value <= 10:
            raise serializers.ValidationError("black_smartness must be between 0 and 10")
        return value
