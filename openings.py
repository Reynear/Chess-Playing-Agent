"""Hard-coded opening book.

Each opening is White's first move and Black's standard reply. Matches
start from these so that games differ while still following real theory.
"""

import chess

OPENINGS = {
    "Open Game":         ["e4", "e5"],
    "Sicilian Defence":  ["e4", "c5"],
    "French Defence":    ["e4", "e6"],
    "Caro-Kann Defence": ["e4", "c6"],
    "Queen's Pawn Game": ["d4", "d5"],
    "Indian Defence":    ["d4", "Nf6"],
    "English Opening":   ["c4", "e5"],
    "Reti Opening":      ["Nf3", "d5"],
}


def board_from_opening(name):
    """Return a board with the named opening's moves already played."""
    board = chess.Board()
    for move in OPENINGS[name]:
        board.push_san(move)      # push_san takes normal chess notation
    return board
