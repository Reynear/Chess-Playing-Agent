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

### Reynear's agent: defensive and positional

Its first priority is a safe king. It wants to castle, keep the pawns in
front of the king where they are and keep the files next to the king closed.
After that it looks after its pawn structure and puts each piece on a sound
square. It never counts attackers, checks or how many moves it has, so it
does not go looking for an attack; it waits for the opponent to overreach.

| Term | What it rewards | Size |
|---|---|---|
| Material | Standard piece values | Pawn 100 to queen 900 |
| King shelter | Castled king, pawn shield, no open files beside the king | Up to about 130 |
| Pawn structure | Avoiding doubled and isolated pawns | -10 to -15 each |
| Piece placement | Piece-square tables for pawns, knights, bishops and rooks, plus the bishop pair | -50 to +50 per piece |
| Passed pawns | Pawns no enemy pawn can stop, more as they advance | 5 to 70 |
| King activity | King near the centre | Up to 48 |

King shelter is the largest positional term but is always worth less than a
piece, so the agent will not give up material for it. It also fades: it
counts in full while the opponent still has a queen and rook's worth of
pieces, and shrinks to nothing as they are traded off. King activity grows
by the same amount, so in the endgame the king leaves its shelter and helps.

### Darren's agent

_To be written by Darren._

### How the two differ

| | Reynear's agent | Darren's agent |
|---|---|---|
| Style | Defensive, positional | Aggressive, attacking |
| Which king it watches | Its own | The opponent's |
| Main positional term | King shelter: castled, pawn shield, closed files | King attack: pieces aimed at and close to the enemy king |
| Pawns | Kept tidy; doubled and isolated pawns penalised | Pushed forward as a pawn storm |
| Pieces | Good fixed squares (piece-square tables) | Free movement, open lines, threats and checks |
| Does not look at | Attackers, mobility, threats, checks | Its own king's shelter, pawn structure |

The only term the two share is material. One agent measures the *structure*
of its own position and scores the same whether or not anything is being
attacked; the other measures *activity* against the opponent and changes
with every threat on the board.

## Match report

Ten games at search depth 3, started from five book openings, each opening
played twice with colours swapped (`python match.py Reynear Darren --depth 3
--openings 5`, seed 1). Every move is in `match.pgn`.

**Final score: Darren 9 - 1 Reynear** (Darren 8 wins, 2 draws, 0 losses).

| Opening | Reynear as White | Reynear as Black |
|---|---|---|
| Open Game | Draw (58 moves) | Loss (64) |
| Sicilian Defence | Loss (32) | Loss (32) |
| French Defence | Loss (39) | Draw (54) |
| Caro-Kann Defence | Loss (54) | Loss (21) |
| Queen's Pawn Game | Loss (21) | Loss (50) |

All eight decisive games ended in checkmate and both draws were by
threefold repetition.

### What decided the games

The attacking agent won clearly, but mostly not by breaking through a
sheltered king. In six of the ten games Reynear's agent was already at
least two pawns behind by move 7, and in three games it never castled at
all. The games were decided by material lost in the opening, before the
defensive plan had been set up.

The reason is what each evaluation can see when the search runs out. At
depth 3 the search stops and scores the board as it stands, even if a piece
is about to be captured. Reynear's agent scores structure only (shelter,
pawns, piece squares), so a position where one of its pieces is hanging
looks as good as one where it is safe. Darren's agent has a threats term
that counts enemy pieces which are attacked and undefended, or attacked by
something cheaper. That gives it one extra move of tactical sight at the
end of every line: it avoids leaving pieces loose and it notices when the
opponent has.

So the strategic difference showed up in an unexpected place. An evaluation
built on activity and threats is also a tactical evaluation, which matters
a great deal at shallow depth. An evaluation built on structure is sound
positionally but tactically blind, and a safe king is no use once the
pieces defending it have been lost.

### Against the reference agent

For comparison, Reynear's agent beat the material-only reference agent 7 - 3
over ten games at the same depth, so the structural terms do help against
an opponent with no positional or tactical knowledge of its own.
