import chess

def main():
    board = chess.Board()
    for move in ("e4"   ,
                 "e5"   ,
                 "Qh5"  ,
                 "Nc6"  ,
                 "Bc4"  ,
                 "Nf6"  ,
                 "Qxf7" ,
                 ):
        board.push_san(move)
        print(f"{move}:")
        print(board)
        print()

if __name__ == "__main__":
    main()
