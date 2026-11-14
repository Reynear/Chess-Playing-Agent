"""Reynear's agent: defensive and positional.

Built by Reynear Douglas.

Strategy: keep the king sheltered above all else, keep the pawns tidy,
and put pieces on sound squares. It measures the *structure* around its
king (castled, pawns in front, no open files) and never counts attackers,
mobility or checks.

Once most of the enemy's pieces are gone the danger has passed, so the
king stops hiding and walks to the centre, and passed pawns are valued so
that a won endgame actually gets won.
"""

import chess

PIECE_VALUES = {
    chess.PAWN: 100, chess.KNIGHT: 300, chess.BISHOP: 300,
    chess.ROOK: 500, chess.QUEEN: 900,
}
# Bonus for a passed pawn by how many ranks it has advanced (0 to 5).
PASSED_BONUS = (0, 5, 10, 20, 40, 70)

# Piece-square tables: how good each square is for each piece, in hundredths
# of a pawn. Written as the board looks from White's side (rank 8 at the top).
PAWN_TABLE = (
     0,   0,   0,   0,   0,   0,   0,   0,
    50,  50,  50,  50,  50,  50,  50,  50,
    10,  10,  20,  30,  30,  20,  10,  10,
     5,   5,  10,  25,  25,  10,   5,   5,
     0,   0,   0,  20,  20,   0,   0,   0,
     5,  -5, -10,   0,   0, -10,  -5,   5,
     5,  10,  10, -20, -20,  10,  10,   5,
     0,   0,   0,   0,   0,   0,   0,   0,
)
KNIGHT_TABLE = (
   -50, -40, -30, -30, -30, -30, -40, -50,
   -40, -20,   0,   0,   0,   0, -20, -40,
   -30,   0,  10,  15,  15,  10,   0, -30,
   -30,   5,  15,  20,  20,  15,   5, -30,
   -30,   0,  15,  20,  20,  15,   0, -30,
   -30,   5,  10,  15,  15,  10,   5, -30,
   -40, -20,   0,   5,   5,   0, -20, -40,
   -50, -40, -30, -30, -30, -30, -40, -50,
)
BISHOP_TABLE = (
   -20, -10, -10, -10, -10, -10, -10, -20,
   -10,   0,   0,   0,   0,   0,   0, -10,
   -10,   0,   5,  10,  10,   5,   0, -10,
   -10,   5,   5,  10,  10,   5,   5, -10,
   -10,   0,  10,  10,  10,  10,   0, -10,
   -10,  10,  10,  10,  10,  10,  10, -10,
   -10,   5,   0,   0,   0,   0,   5, -10,
   -20, -10, -10, -10, -10, -10, -10, -20,
)
ROOK_TABLE = (
     0,   0,   0,   0,   0,   0,   0,   0,
     5,  10,  10,  10,  10,  10,  10,   5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
     0,   0,   0,   5,   5,   0,   0,   0,
)
TABLES = {
    chess.PAWN: PAWN_TABLE, chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE, chess.ROOK: ROOK_TABLE,
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
    """Each piece on a good square (piece-square tables), plus the bishop pair."""
    score = 0
    for piece, table in TABLES.items():
        for sq in board.pieces(piece, color):
            # The tables are drawn from White's side with rank 8 first, so
            # White's squares are flipped top-to-bottom; Black's already match.
            score += table[sq ^ 56] if color == chess.WHITE else table[sq]
    if len(board.pieces(chess.BISHOP, color)) >= 2:
        score += 30
    return score


def passed_pawns(board, color):
    """Bonus for pawns that no enemy pawn can block or capture on the way up."""
    enemy_pawns = board.pieces(chess.PAWN, not color)
    score = 0
    for sq in board.pieces(chess.PAWN, color):
        f, r = chess.square_file(sq), chess.square_rank(sq)
        stoppers = [e for e in enemy_pawns
                    if abs(chess.square_file(e) - f) <= 1
                    and (chess.square_rank(e) > r if color == chess.WHITE
                         else chess.square_rank(e) < r)]
        if not stoppers:
            steps = r - 1 if color == chess.WHITE else 6 - r
            score += PASSED_BONUS[steps]
    return score


def king_activity(board, color):
    """Up to 48: in the endgame the king should come to the centre and help."""
    king = board.king(color)
    f, r = chess.square_file(king), chess.square_rank(king)
    return 8 * (min(f, 7 - f) + min(r, 7 - r))


def side_score(board, color):
    """Everything this agent values, for one side."""
    enemy = not color
    enemy_pieces = material(board, enemy) - 100 * len(board.pieces(chess.PAWN, enemy))
    # danger runs from 1500 (middlegame: plenty of enemy attackers) down to 0
    # (endgame). While it is high the king hides behind its pawns; as it
    # drops the shelter stops mattering and the king is rewarded for coming
    # out instead. Whole-number arithmetic throughout.
    danger = min(1500, enemy_pieces)
    king = (king_shelter(board, color) * danger
            + king_activity(board, color) * (1500 - danger)) // 1500
    return (material(board, color) + king + pawn_structure(board, color)
            + passed_pawns(board, color) + placement(board, color))


def reynear_eval(board):
    """Positive = White is better. Defensive: king shelter first, then structure."""
    return side_score(board, chess.WHITE) - side_score(board, chess.BLACK)
