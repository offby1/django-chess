import random

import chess
import chess.engine


def main() -> None:
    GNUCHESS_PATH = "gnuchess"

    found_promotion = False

    with chess.engine.SimpleEngine.popen_uci([GNUCHESS_PATH, "--uci"]) as engine:
        while not found_promotion:
            board = chess.Board()

            while not board.is_game_over():
                whose_turn = chess.COLOR_NAMES[board.turn]
                print()
                print(f"{len(board.piece_map())} pieces; {whose_turn}'s turn")
                print(board)

                # Get engine move
                result = engine.play(board, chess.engine.Limit(time=0 if board.turn else 0))
                print(f"{whose_turn} plays:", result.move)

                # Apply engine move
                if result.move is not None:
                    board.push(result.move)
                    if result.move.promotion is not None:
                        print("HEY LOOK A PIECE GOT PROMOTED")
                        found_promotion = True
                        break

                if board.is_game_over():
                    break

            print(board)
            print("Game over:", board.result(), board.outcome())


if __name__ == "__main__":
    main()
