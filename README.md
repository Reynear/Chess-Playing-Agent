# Chess-Playing-Agent

We created Two chess agents built on a shared minimax search with alpha-beta pruning.The agents have a shared core but individual play styles 
and evaluation functions.
## Who built what

| Part | Owner |
|---|---|
| Reynear agent (`agents/reynear.py`) – defensive: king safety first, positional | Reynear Douglas |
| Darren agent (`agents/darren.py`) – aggressive: piece activity, king attack, threats | Darren Tyme |
| Shared search, opening book, match harness | Reynear Douglas and Darren Tyme|
| GUI | Darren Tyme and Reynear Douglas with the assistance of claude to understand the pygame semantics(claude sonnet 5) |

## Setup
To run the program:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running

Agent-vs-agent match (each opening is played twice with colours swapped;
every move is logged to `match.pgn` it is in standard chess notation, so fun fact you can import the games into chess.com and replay see the matches play out there if you want  ):

```bash
python match.py Darren Reynear --depth 3 --openings 5

```

Graphical interface:

```bash

python gui.py
```

The side panel has two modes:

- **Human vs Agent:** choose your opponent, the colour you play and the
  difficulty. In the GUI it follows standard chess procedures for movement.


- **Agent vs Agent:** choose an agent and a difficulty for each colour and
  press `Start`  . 



The difficulty setting adjusts the search depth meaning how many  moves ahead the agent considers.

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

**Minimax.** The agent tries every  move that would be legal to make, then every reply, and so on
down to a fixed depth. At the bottom it scores the board with an evaluation
function (positive = good for White). White picks the move leading to the
highest score and assumes Black will always pick the reply leading to the
lowest, and vice versa.

**Alpha-beta pruning.** While searching, the agent keeps track of the best
score each side can already guarantee .
As soon as a branch is shown to be worse than an option already found, the
rest of that branch is skipped. The chosen move is identical to plain
minimax; only the amount of work changes. Trying captures first makes the
skipping far more effective.This is because captures lead to a better evaluation because base grading is based on the piece advantage a player may have.

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

### Darren's agent: aggressive and attacking

Its first priority is the enemy king. It wants its pieces aimed at and
close to the squares around that king, its pawns pushed forward, its rooks
on open files and enemy pieces under threat. It never looks at its own
king's shelter or pawn structure, so it will loosen its own position to
keep an attack going.

| Term | What it rewards | Size |
|---|---|---|
| Material | Standard piece values | Pawn 100 to queen 900 |
| King attack | Pieces and pawns hitting the squares around the enemy king | Up to about 300 |
| Activity | Squares each piece can move to, and closeness to the enemy king | 1 to 5 per square or step |
| Pawn storm | Advanced pawns, double on the files in front of the enemy king | Up to 50 per pawn |
| Open lines | Rooks and queens on files free of their own pawns | 10 to 25 each |
| Threats and checks | Enemy pieces hanging or attacked by something cheaper; giving check | 15 to 35 each |

King attack is the largest positional term and grows with numbers: one
attacker counts for 30% of its weight, three or more for 90% to 120%, so the
agent brings pieces over together instead of sending one in alone. Without a
queen it counts half. Threats also count most of a hanging piece's value when
it is this agent's move, since it can take it next move; this stops it from
ending a line with its own pieces left loose.

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
