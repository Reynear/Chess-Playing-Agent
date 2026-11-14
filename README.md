# Chess-Playing-Agent

Two chess agents built on a shared minimax search with alpha-beta pruning
(COMP3220 pair assignment). Each agent has its own evaluation function and
its own playing style.

## Who built what

| Part | Owner |
|---|---|
| Reynear agent (`agents/reynear.py`) – defensive: king safety first, positional | Reynear Douglas |
| Darren agent (`agents/darren.py`) – aggressive: piece activity, king attack, threats | Darren |
| Shared search, opening book, match harness | Reynear Douglas |
| GUI | _to be added_ |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running

Agent-vs-agent match (each opening is played twice with colours swapped;
every move is logged to `match.pgn`):

```bash
python match.py Darren Reynear --depth 3 --openings 5
```

Graphical interface:

```bash
python gui.py
```

The side panel has two modes:

- **Human vs Agent:** choose your opponent, the colour you play and the
  difficulty. Click one of your pieces, then click a marked square.
- **Agent vs Agent:** choose an agent and a difficulty for each colour and
  press `Start`. `Pause` stops the game and `Step` plays a single move.

Difficulty is the search depth (1-4): how many moves ahead the agent looks.
Every agent in the registry appears as a choice automatically.

## Project layout

| File | Purpose |
|---|---|
| `engine.py` | Minimax, alpha-beta pruning, move ordering, move selection |
| `agents/__init__.py` | Registry of agents; add a new agent here |
| `agents/reference.py` | Baseline agent that only counts material |
| `agents/reynear.py` | Reynear's agent: defensive evaluation function |
| `agents/darren.py` | Darren's agent: aggressive evaluation function |
| `openings.py` | Hard-coded opening book used to start match games |
| `match.py` | Agent-vs-agent match harness |
| `gui.py` | Pygame window for human-vs-agent and agent-vs-agent play |

## How the search works

**Minimax.** The agent tries every legal move, then every reply, and so on
down to a fixed depth. At the bottom it scores the board with an evaluation
function (positive = good for White). White picks the move leading to the
highest score and assumes Black will always pick the reply leading to the
lowest, and vice versa.

**Alpha-beta pruning.** While searching, the agent keeps track of the best
score each side can already guarantee (`alpha` for White, `beta` for Black).
As soon as a branch is shown to be worse than an option already found, the
rest of that branch is skipped. The chosen move is identical to plain
minimax; only the amount of work changes. Trying captures first makes the
skipping far more effective.

Positions searched from one middlegame position:

| Depth | Plain minimax | With alpha-beta |
|---|---|---|
| 2 | 1,373 | 72 |
| 3 | 47,347 | 1,227 |

**Depth control.** Every agent takes a search depth; deeper is stronger and
slower. Checkmate is scored higher the sooner it happens, so agents take the
quickest win.

**Draws and variety.** Threefold repetition and the fifty-move rule score as
draws. When several moves score exactly the same, one is picked at random,
and matches start from a small book of standard openings.

## Strategy comparison

_To be written once both agents are finished._

## Match report

_To be written from the final match results._
