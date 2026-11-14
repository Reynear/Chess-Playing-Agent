"""Agent-vs-agent match harness.

Plays each opening twice with colours swapped, logs every move of every
game to a PGN file, and prints the final scoreline.

    python match.py Reynear Reference --depth 3 --openings 5
"""

import argparse
import random

import chess
import chess.pgn

from agents import AGENTS, make_agent
from openings import OPENINGS, board_from_opening


def play_game(white_agent, black_agent, opening, max_moves=150):
    """Play one game from a named opening and return the final board."""
    board = board_from_opening(opening)
    while not board.is_game_over(claim_draw=True) and board.fullmove_number <= max_moves:
        agent = white_agent if board.turn == chess.WHITE else black_agent
        board.push(agent(board))
    return board


def save_pgn(board, path, opening, white, black, result):
    """Append one finished game (all moves and the result) to a PGN file."""
    game = chess.pgn.Game.from_board(board)
    game.headers["Event"] = "Agent vs Agent"
    game.headers["Opening"] = opening
    game.headers["White"] = white
    game.headers["Black"] = black
    game.headers["Result"] = result
    with open(path, "a") as f:
        print(game, file=f, end="\n\n")


def run_match(name_a, name_b, depth, openings, seed=1, pgn_path="match.pgn"):
    """Play every opening twice with colours swapped.

    Returns the two scores in the order (agent a, agent b).
    """
    random.seed(seed)                         # same seed = same match every run
    open(pgn_path, "w").close()               # start a fresh log
    names = (name_a, name_b)
    agents = (make_agent(name_a, depth), make_agent(name_b, depth))
    score = [0.0, 0.0]                        # kept by position, so an agent can play itself

    for opening in openings:
        for white, black in ((0, 1), (1, 0)):
            board = play_game(agents[white], agents[black], opening)
            result = board.result(claim_draw=True)
            if result == "1-0":
                score[white] += 1
            elif result == "0-1":
                score[black] += 1
            else:                             # draw, or move limit reached
                result = "1/2-1/2"
                score[white] += 0.5
                score[black] += 0.5
            save_pgn(board, pgn_path, opening, names[white], names[black], result)
            print(f"{opening:20} {names[white]:>10} (W) vs {names[black]:<10} (B)  "
                  f"{result:8} {board.fullmove_number} moves")
    return score


def main():
    parser = argparse.ArgumentParser(description="Play a match between two agents.")
    parser.add_argument("agent_a", choices=list(AGENTS))
    parser.add_argument("agent_b", choices=list(AGENTS))
    parser.add_argument("--depth", type=int, default=3, help="search depth for both agents")
    parser.add_argument("--openings", type=int, default=5,
                        help="number of openings (two games each)")
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    openings = list(OPENINGS)[:args.openings]
    score = run_match(args.agent_a, args.agent_b, args.depth, openings, args.seed)
    print(f"\nFinal score: {args.agent_a} {score[0]} - {score[1]} {args.agent_b}")


if __name__ == "__main__":
    main()
