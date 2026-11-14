"""Shared search engine: minimax.

Every agent uses this same look-ahead. Agents differ only in the
evaluation function they pass in, which must have the form

    evaluate(board) -> number   (positive = good for White)
"""

import chess

# Checkmate must outscore anything an evaluation function can return.
MATE = 100_000


def finished_score(board, depth):
    """Return the score if the game has ended here, otherwise None.

    Adding `depth` makes a quicker checkmate worth more than a slower one.
    """
    if board.is_checkmate():
        # The side to move has been mated.
        return -(MATE + depth) if board.turn == chess.WHITE else MATE + depth
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    return None


def minimax(board, depth, evaluate):
    """Plain minimax: best score reachable looking `depth` moves ahead."""
    score = finished_score(board, depth)
    if score is not None:
        return score
    if depth == 0:
        return evaluate(board)

    scores = []
    for move in list(board.legal_moves):
        board.push(move)                                  # try the move
        scores.append(minimax(board, depth - 1, evaluate))
        board.pop()                                       # take it back
    # White picks the highest score, Black the lowest.
    return max(scores) if board.turn == chess.WHITE else min(scores)
