"""Management command to unstick games where AI hasn't moved."""

from django.core.management.base import BaseCommand
from django_chess.app.models import Game
from django_chess.app.utils import load_board, save_board
from django_chess.api.views import get_black_move


class Command(BaseCommand):
    help = "Make AI moves for games stuck on black's turn"

    def add_arguments(self, parser):
        parser.add_argument(
            '--game-id',
            type=str,
            help='Specific game ID to unstick (optional)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        # Find games where it's black's turn
        games_query = Game.objects.filter(in_progress=True)

        if options['game_id']:
            games_query = games_query.filter(id=options['game_id'])

        stuck_games = []
        for game in games_query:
            board = load_board(game=game)
            if not board.turn:  # False means black's turn
                stuck_games.append(game)

        if not stuck_games:
            self.stdout.write(self.style.SUCCESS('No stuck games found.'))
            return

        self.stdout.write(f'Found {len(stuck_games)} stuck game(s):')

        for game in stuck_games:
            self.stdout.write(f'  - {game.name} ({game.id})')

            if options['dry_run']:
                continue

            # Load board and make AI move
            board = load_board(game=game)
            black_move = get_black_move(board, game.black_smartness)

            if black_move:
                game.promoting_push(board, black_move)
                save_board(board=board, game=game)
                self.stdout.write(
                    self.style.SUCCESS(f'    Made move: {black_move.uci()}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'    No legal moves available!')
                )

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('Dry run complete - no changes made.')
            )
