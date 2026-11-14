"""Reynear's agent: defensive and positional.

Built by Reynear Douglas.

Strategy: keep the king sheltered above all else, keep the pawns tidy,
and put pieces on sound squares. It measures the *structure* around its
king (castled, pawns in front, no open files) and never counts attackers,
mobility or checks.
"""

import chess

PIECE_VALUES = {
    chess.PAWN: 100, chess.KNIGHT: 300, chess.BISHOP: 300,
    chess.ROOK: 500, chess.QUEEN: 900,
}


def material(board, color):
    """Total value of one side's pieces."""
    return sum(value * len(board.pieces(piece, color))
               for piece, value in PIECE_VALUES.items())


def pawn_files(board, color):
    """The file (0-7, a-h) of each of this side's pawns."""
    return [chess.square_file(sq) for sq in board.pieces(chess.PAWN, color)]


def king_shelter(board, color):
    """Up to about 130: king tucked on a wing behind its own pawns."""
    king = board.king(color)
    kfile, krank = chess.square_file(king), chess.square_rank(king)
    home, forward = (0, 1) if color == chess.WHITE else (7, -1)
    files = pawn_files(board, color)
    own_pawn = chess.Piece(chess.PAWN, color)

    score = 0
    if krank == home and kfile in (0, 1, 2, 6, 7):      # where castling puts it
        score += 40
    for f in (kfile - 1, kfile, kfile + 1):             # the three files around the king
        if not 0 <= f <= 7:
            continue
        for step, bonus in ((1, 30), (2, 15)):          # pawn directly ahead, or one further
            r = krank + forward * step
            if 0 <= r <= 7 and board.piece_at(chess.square(f, r)) == own_pawn:
                score += bonus
                break
        if f not in files:                              # no pawn on this file: open line to the king
            score -= 20
    return score


def pawn_structure(board, color):
    """Penalties for doubled and isolated pawns."""
    files = pawn_files(board, color)
    score = 0
    for f in set(files):
        count = files.count(f)
        score -= 15 * (count - 1)                       # doubled pawns
        if f - 1 not in files and f + 1 not in files:
            score -= 10 * count                         # isolated pawns
    return score


def placement(board, color):
    """Knights and bishops near the centre, plus a bishop-pair bonus."""
    score = 0
    for sq in board.pieces(chess.KNIGHT, color) | board.pieces(chess.BISHOP, color):
        f, r = chess.square_file(sq), chess.square_rank(sq)
        score += 3 * (min(f, 7 - f) + min(r, 7 - r))    # closer to the centre is better
    if len(board.pieces(chess.BISHOP, color)) >= 2:
        score += 30
    return score


def side_score(board, color):
    """Everything this agent values, for one side."""
    enemy = not color
    enemy_pieces = material(board, enemy) - 100 * len(board.pieces(chess.PAWN, enemy))
    # Shelter matters less as attackers come off: full weight at 1500+ of
    # enemy pieces, shrinking to zero. Whole-number arithmetic throughout.
    shelter = king_shelter(board, color) * min(1500, enemy_pieces) // 1500
    return (material(board, color) + shelter
            + pawn_structure(board, color) + placement(board, color))


def reynear_eval(board):
    """Positive = White is better. Defensive: king shelter first, then structure."""
    return side_score(board, chess.WHITE) - side_score(board, chess.BLACK)
