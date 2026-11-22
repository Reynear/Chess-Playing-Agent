"""Darren's agent: aggressive and attacking.

Built by Darren.

Strategy: My strategy is to be as aggressive as is reasonable ant=d to attack the enemy king. 
This agent is rewarded by the activity of its pieces, particularly those aimed at the enemy king.I got
the idea of offense is the best defence from watching Mr Robot
"""

import chess

PIECE_VALUES = {
    chess.PAWN: 100, chess.KNIGHT: 300, chess.BISHOP: 300,

    chess.ROOK: 500, chess.QUEEN: 900,
      chess.KING: 0,

}

# The pieces that do the attacking 
ATTACKERS = (chess.KNIGHT , chess.BISHOP, chess.ROOK, chess.QUEEN)

# giving a weight to a specific piece attacking the enemy king. Pawns are not very dangeros, but a queen is a real threat.
ATTACK_WEIGHT = {chess.PAWN: 10, chess.KNIGHT: 25, chess.BISHOP: 25,
                 chess.ROOK: 40, chess.QUEEN: 80}

# An attack needs numbers: one piece near the king is a nuisance, three or
# four together are a mating attack. Percentage of the summed weight that
# counts, indexed by how many pieces are attacking.
ATTACK_SCALE = (0, 30, 65, 90, 100, 110, 115, 120)

# Value of one extra square to move to, and of one step closer to the king.
MOBILITY = {chess.KNIGHT: 4, chess.BISHOP: 4, chess.ROOK: 2, chess.QUEEN: 1}
CLOSENESS = {chess.KNIGHT: 4, chess.BISHOP: 2, chess.ROOK: 3, chess.QUEEN: 5}

CHECK_BONUS = 35        # the enemy king is in check right now so we add a bonus to the score

THREAT_BONUS = 15       # an enemy piece is under real threat
CAPTURE_SHARE = 75      # % of a threatened piece's value counted when it is our move


def material(board, color):
    """Total value of one side's pieces."""
    return sum(value * len(board.pieces(piece, color))
               
               for piece, value in PIECE_VALUES.items())


def king_zone(board, color):
    """The squares to aim at: `color`'s king, the squares touching it, and
    the row just beyond those on the side the attack comes from."""
    king = board.king(color)
    zone = chess.SquareSet(chess.BB_KING_ATTACKS[king] | chess.BB_SQUARES[king])
    kfile, krank = chess.square_file(king), chess.square_rank(king)
    rank = krank + (2 if color == chess.WHITE else -2)
    if 0 <= rank <= 7:
        for f in (kfile - 1, kfile, kfile + 1):
            if 0 <= f <= 7:
                zone.add(chess.square(f, rank))
    return zone


def piece_activity(board, color):
    """King attack, mobility and closeness, worked out in one pass.

    For every attacking piece: how many squares can it go to, how close is
    it to the enemy king, and does it hit the enemy king's zone? Zone hits
    are added up and then scaled by how many pieces take part.
    """
    enemy_king = board.king(not color)
    zone = king_zone(board, not color)
    own = board.occupied_co[color]

    score = attackers = attack_weight = 0
    for piece in ATTACKERS:
        for sq in board.pieces(piece, color):
            reach = board.attacks(sq)
            score += MOBILITY[piece] * len(reach & ~own)
            score += CLOSENESS[piece] * (7 - chess.square_distance(sq, enemy_king))
            hits = len(reach & zone)
            if hits:
                attackers += 1
                attack_weight += ATTACK_WEIGHT[piece] + 5 * hits

    for sq in board.pieces(chess.PAWN, color):            # pawns join in too
        if board.attacks(sq) & zone:
            attackers += 1
            attack_weight += ATTACK_WEIGHT[chess.PAWN]

    if not board.pieces(chess.QUEEN, color):              # no queen, far less bite
        attack_weight //= 2
    return score + attack_weight * ATTACK_SCALE[min(attackers, 7)] // 100


def pawn_storm(board, color):
    """Pawns earn more the further they advance, and double that on the
    three files in front of the enemy king, where they pry it open."""
    kfile = chess.square_file(board.king(not color))
    score = 0
    for sq in board.pieces(chess.PAWN, color):
        rank = chess.square_rank(sq)
        steps = rank - 1 if color == chess.WHITE else 6 - rank   # 0 at home, 5 one from queening
        near_king = abs(chess.square_file(sq) - kfile) <= 1
        score += steps * steps * (2 if near_king else 1)
    return score


def open_lines(board, color):
    """Rooks and queens want files with none of their own pawns in the way,
    most of all files that lead to the enemy king."""
    kfile = chess.square_file(board.king(not color))
    own_pawn_files = {chess.square_file(sq) for sq in board.pieces(chess.PAWN, color)}
    score = 0
    for sq in board.pieces(chess.ROOK, color) | board.pieces(chess.QUEEN, color):
        f = chess.square_file(sq)
        if f not in own_pawn_files:
            score += 25 if abs(f - kfile) <= 1 else 10
    return score


def threats(board, color):
    """Enemy pieces that are attacked by something cheaper than themselves,
    or attacked and not defended at all.

    Each one earns a small bonus for the pressure it creates. If it is also
    `color`'s turn, the most valuable of them can simply be taken next move,
    so most of that gain is counted now. This stops the agent from leaving
    its own pieces hanging at the end of a line it thinks is an attack.
    """
    enemy = not color
    count = best_gain = 0
    for sq in chess.SquareSet(board.occupied_co[enemy] & ~board.kings):
        attackers = board.attackers(color, sq)
        if not attackers:
            continue
        value = PIECE_VALUES[board.piece_type_at(sq)]
        cheapest = min(PIECE_VALUES[board.piece_type_at(a)] for a in attackers)
        if not board.attackers(enemy, sq):
            gain = value                       # free piece
        elif cheapest < value:
            gain = value - cheapest            # winning trade
        else:
            continue
        count += 1
        best_gain = max(best_gain, gain)
    score = count * THREAT_BONUS
    if board.turn == color:
        score += best_gain * CAPTURE_SHARE // 100
    return score


def side_score(board, color):
    """Everything this agent values, for one side."""
    score = (material(board, color) + piece_activity(board, color)
             + pawn_storm(board, color) + open_lines(board, color)
             + threats(board, color))
    if board.turn != color and board.is_check():          # we are giving check
        score += CHECK_BONUS
    return score


def darren_eval(board):
    """Positive = White is better. Aggressive: activity and king attack first."""
    return side_score(board, chess.WHITE) - side_score(board, chess.BLACK)
