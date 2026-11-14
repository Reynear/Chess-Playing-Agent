"""Shared search engine: minimax with alpha-beta pruning.

Every agent uses this same look-ahead. Agents differ only in the
evaluation function they pass in, which must have the form

    evaluate(board) -> number   (positive = good for White)
"""

import math

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
    """Plain minimax: best score reachable looking `depth` moves ahead.

    Kept without pruning so it can be compared against `alphabeta`.
    """
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


def alphabeta(board, depth, alpha, beta, evaluate):
    """Minimax with alpha-beta pruning. Same answer as `minimax`, less work.

    alpha = best score White can already guarantee elsewhere.
    beta  = best score Black can already guarantee elsewhere.
    Once alpha >= beta this branch cannot change the result, so stop.
    """
    score = finished_score(board, depth)
    if score is not None:
        return score
    if depth == 0:
        return evaluate(board)

    if board.turn == chess.WHITE:
        best = -math.inf
        for move in list(board.legal_moves):
            board.push(move)
            best = max(best, alphabeta(board, depth - 1, alpha, beta, evaluate))
            board.pop()
            alpha = max(alpha, best)
            if alpha >= beta:        # Black would never allow this line
                break
        return best
    else:
        best = math.inf
        for move in list(board.legal_moves):
            board.push(move)
            best = min(best, alphabeta(board, depth - 1, alpha, beta, evaluate))
            board.pop()
            beta = min(beta, best)
            if alpha >= beta:        # White would never allow this line
                break
        return best
