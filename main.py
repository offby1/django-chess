import random

import chess
import chess.engine


def main() -> None:
    GNUCHESS_PATH = "gnuchess"

    board = chess.Board()

    with chess.engine.SimpleEngine.popen_uci([GNUCHESS_PATH, "--uci"]) as engine:
        while not board.is_game_over():
            print(board)
            print("FEN:", board.fen())

            # Get engine move
            result = engine.play(board, chess.engine.Limit(time=1.0))
            print("Engine plays:", result.move)

            # Apply engine move
            if result.move is not None:
                board.push(result.move)

            if board.is_game_over():
                break

        print("Game over:", board.result())


if __name__ == "__main__":
    main()
