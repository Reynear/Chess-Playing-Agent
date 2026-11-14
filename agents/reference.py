"""Reference agent: counts material and nothing else.

This is the basic baseline both real agents are tested against.
"""

import chess

# Standard piece values in hundredths of a pawn.
PIECE_VALUES = {
    chess.PAWN: 100, chess.KNIGHT: 300, chess.BISHOP: 300,
    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0,
}


def material_eval(board):
    """Positive = White is ahead, negative = Black is ahead."""
    score = 0
    for piece, value in PIECE_VALUES.items():
        score += value * len(board.pieces(piece, chess.WHITE))
        score -= value * len(board.pieces(piece, chess.BLACK))
    return score
