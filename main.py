import random

import chess


def main():
    board = chess.Board()
    while True:
        outcome = board.outcome()
        if outcome is not None:
            print()
            print(outcome)
            break

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            break
        random.shuffle(legal_moves)
        board.push(legal_moves[0])
        print(f"{legal_moves[0]}:")
        print(board.board_fen())
        print(board)
        print()


if __name__ == "__main__":
    main()
