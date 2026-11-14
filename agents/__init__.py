"""Registry of every agent the GUI and match harness can use.

To plug in a new agent: write its evaluation function in its own file in
this folder, then add one line to AGENTS below.
"""

from engine import choose_move

from agents.darren import darren_eval
from agents.reference import material_eval
from agents.reynear import reynear_eval

# Display name -> evaluation function.
AGENTS = {
    "Reference": material_eval,
    "Reynear": reynear_eval,
    "Darren": darren_eval,
}


def make_agent(name, depth):
    """Return a function that takes a board and returns that agent's move."""
    evaluate = AGENTS[name]
    return lambda board: choose_move(board, depth, evaluate)
