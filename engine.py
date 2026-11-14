"""Shared search engine: minimax with alpha-beta pruning.

Every agent uses this same look-ahead. Agents differ only in the
evaluation function they pass in, which must have the form

    evaluate(board) -> number   (positive = good for White)
"""

import math
import random

import chess

# Checkmate must outscore anything an evaluation function can return.
MATE = 100_000

# How many positions the last search looked at (for comparing pruning).
nodes_searched = 0

# Piece values in hundredths of a pawn, used to decide which moves to try first.
PIECE_VALUES = {
    chess.PAWN: 100, chess.KNIGHT: 300, chess.BISHOP: 300,
    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0,
}


def finished_score(board, depth):
    """Return the score if the game has ended here, otherwise None.

    Adding `depth` makes a quicker checkmate worth more than a slower one.
    """
    if board.is_checkmate():
        # The side to move has been mated.
        return -(MATE + depth) if board.turn == chess.WHITE else MATE + depth
    if (board.is_stalemate() or board.is_insufficient_material()
            or board.is_repetition(3) or board.is_fifty_moves()):
        return 0
    return None


def move_priority(board, move):
    """Higher number = try this move earlier.

    Captures come first, best trades at the top (pawn takes queen before
    queen takes pawn), then promotions, then everything else.
    """
    if board.is_capture(move):
        victim = board.piece_type_at(move.to_square) or chess.PAWN  # en passant
        attacker = board.piece_type_at(move.from_square)
        return 10 * PIECE_VALUES[victim] - PIECE_VALUES[attacker]
    if move.promotion:
        return PIECE_VALUES[move.promotion]
    return 0


def ordered_moves(board):
    """Legal moves, most promising first, so pruning can skip more."""
    return sorted(board.legal_moves,
                  key=lambda move: move_priority(board, move), reverse=True)


def minimax(board, depth, evaluate):
    """Plain minimax: best score reachable looking `depth` moves ahead.

    Kept without pruning so it can be compared against `alphabeta`.
    """
    global nodes_searched
    nodes_searched += 1

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
    global nodes_searched
    nodes_searched += 1

    score = finished_score(board, depth)
    if score is not None:
        return score
    if depth == 0:
        return evaluate(board)

    if board.turn == chess.WHITE:
        best = -math.inf
        for move in ordered_moves(board):
            board.push(move)
            best = max(best, alphabeta(board, depth - 1, alpha, beta, evaluate))
            board.pop()
            alpha = max(alpha, best)
            if alpha >= beta:        # Black would never allow this line
                break
        return best
    else:
        best = math.inf
        for move in ordered_moves(board):
            board.push(move)
            best = min(best, alphabeta(board, depth - 1, alpha, beta, evaluate))
            board.pop()
            beta = min(beta, best)
            if alpha >= beta:        # White would never allow this line
                break
        return best


def choose_move(board, depth, evaluate):
    """Return the best move for whoever's turn it is (None if game over).

    Moves are shuffled before sorting, so when several moves score exactly
    the same, which one gets played is random.
    """
    global nodes_searched
    nodes_searched = 0

    white = board.turn == chess.WHITE
    best_move, best = None, (-math.inf if white else math.inf)
    alpha, beta = -math.inf, math.inf

    moves = list(board.legal_moves)
    random.shuffle(moves)
    moves.sort(key=lambda move: move_priority(board, move), reverse=True)

    for move in moves:
        board.push(move)
        score = alphabeta(board, depth - 1, alpha, beta, evaluate)
        board.pop()
        if (white and score > best) or (not white and score < best):
            best, best_move = score, move
        if white:
            alpha = max(alpha, best)
        else:
            beta = min(beta, best)
    return best_move
