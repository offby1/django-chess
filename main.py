import chess
import chess.engine


def main() -> None:
    GNUCHESS_PATH = "gnuchess"

    with chess.engine.SimpleEngine.popen_uci([GNUCHESS_PATH, "--uci"]) as engine:
        board = chess.Board()

        while True:
            whose_turn = chess.COLOR_NAMES[board.turn]
            print()
            print(f"{len(board.piece_map())} pieces; {whose_turn}'s turn")
            print(board)

            # Get engine move
            result = engine.play(board, chess.engine.Limit(time=0 if board.turn else 0))
            print(f"{whose_turn} plays:", result.move)

            # Apply engine move
            if result.move is not None:
                if result.move.to_square == result.move.from_square:
                    board.push(
                        chess.Move.from_uci("0000")
                    )  # I think this can happen in a stalemate
                else:
                    board.push(result.move)

            if board.is_game_over():
                print(board)
                print("Game over:", board.result(), board.outcome())
                break


if __name__ == "__main__":
    main()
