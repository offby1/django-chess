# wat
Thinking about another django game, roughly similar to bridge: chess.

Otta be a lot simpler.

## urls

### GET /game/1
display existing game with ID 1.

The response should include
- which pieces are where
- perhaps the SVG for each piece; chess.svc.piece can do this for us
- whose turn is it
- maybe a summary of captured pieces (even though you could deduce that by looking at the board)
- maybe which moves are legal (so that if they click an illegal square, we can yell at them without a round trip to the server)

Clicking a square:

- If no piece or square is selected:
  - if the square is occupied: "selects" the piece
    else: "selects" the square
- else:
  - if they just clicked the same sort of square that's selected: reset the selection
    else:
    - if it's a legal move:
    do it
    - else:
    flash red or something

### POST /game/
create new game; redirect to above

## what we need from the underlying library
- create a fresh game: chess.Board()
- serialize and deserialize a game: I suspect `board_fen` and `set_board_fen` are the way to do this ... however, that "FEN" format doesn't include previous *moves*; it includes only the present state of the board.  The board's `move_stack` holds this information; the individual moves can be serialized with `.uci` and deserialized with `Move.from_uci`.
- fetch all the pieces and their positions from a game: `piece_map`
- fetch all the legal moves from a game: `legal_moves`
- modify a game by making a legal move
