"""Graphical interface (pygame).

    python gui.py

Two modes, chosen at the top of the side panel:

* Human vs Agent - pick your opponent, your colour and the difficulty,
  then click a piece and click where it should go.
* Agent vs Agent - pick an agent and difficulty for each colour, press
  Start and watch. Pause and Step control the game.

Every agent in the registry appears as a choice automatically.
"""

import io
import threading

import chess
import chess.svg
import pygame

import engine
from agents import AGENTS

SQ = 80                                   # size of one square in pixels
BOARD = 8 * SQ
PANEL = 320                               # width of the side panel
WIDTH, HEIGHT = BOARD + PANEL, BOARD
PANEL_X = BOARD + 16                      # left edge of the panel's contents
PANEL_W = PANEL - 32                      # width of the panel's contents

LIGHT, DARK = (240, 217, 181), (181, 136, 99)
LAST_MOVE = (205, 210, 106)
SELECTED = (130, 151, 105)
CHECK = (220, 80, 70)
PANEL_BG, TEXT, MUTED = (40, 42, 48), (235, 235, 235), (160, 164, 172)
BUTTON, BUTTON_HOVER, BUTTON_ON = (70, 74, 84), (92, 97, 110), (76, 140, 96)

HUMAN = "You"
HUMAN_MODE, AGENT_MODE = "Human vs Agent", "Agent vs Agent"
DEPTHS = (1, 2, 3, 4)
MOVE_DELAY_MS = 500                       # pause between agent moves so games are watchable
SIDE = {chess.WHITE: "White", chess.BLACK: "Black"}


class Search(threading.Thread):
    """Runs one agent's search in the background so the window stays responsive."""

    def __init__(self, board, player, depth):
        super().__init__(daemon=True)
        self.board = board.copy()         # the agent works on its own copy
        self.position = board.fen()
        self.player, self.depth = player, depth
        self.move, self.nodes = None, 0

    def run(self):
        self.move = engine.choose_move(self.board, self.depth, AGENTS[self.player])
        self.nodes = engine.nodes_searched


class Game:
    """The state of the current game: mode, players, depths, board, selection."""

    def __init__(self):
        names = list(AGENTS)
        self.mode = HUMAN_MODE
        self.human_color = chess.WHITE
        self.agent = {chess.WHITE: names[0], chess.BLACK: names[-1]}
        self.depth = {chess.WHITE: 3, chess.BLACK: 3}
        self.new_game()

    # ----- settings chosen in the side panel -----

    def new_game(self):
        """Reset to the starting position, keeping the chosen settings."""
        self.board = chess.Board()
        self.outcome = None               # set once the game has ended
        self.selected = None              # square the human has clicked on
        self.san_moves = []               # moves played, in normal chess notation
        self.search = None                # the agent search in progress, if any
        self.paused = self.mode == AGENT_MODE   # agent games wait for Start
        self.step = False                 # play exactly one agent move while paused
        self.last_move_time = 0
        self.info = ""                    # what the last agent search did

    def set_mode(self, mode):
        if mode != self.mode:
            self.mode = mode
            self.new_game()

    def set_side(self, color):
        """Choose which colour the human plays; the opponent moves across."""
        if color != self.human_color:
            old_opponent = not self.human_color
            self.agent[not color] = self.agent[old_opponent]
            self.depth[not color] = self.depth[old_opponent]
            self.human_color = color
            self.new_game()

    def set_agent(self, color, name):
        self.agent[color] = name

    def set_depth(self, color, depth):
        self.depth[color] = depth

    def toggle_pause(self):
        self.paused = not self.paused

    def step_once(self):
        self.paused, self.step = True, True

    # ----- playing -----

    def player(self, color):
        """Who plays this colour: HUMAN or an agent's name."""
        if self.mode == HUMAN_MODE and color == self.human_color:
            return HUMAN
        return self.agent[color]

    def flipped(self):
        """Show the board from Black's side when the human plays Black."""
        return self.mode == HUMAN_MODE and self.human_color == chess.BLACK

    def human_to_move(self):
        return self.outcome is None and self.player(self.board.turn) == HUMAN

    def play(self, move):
        """Make a move on the board and record it."""
        self.san_moves.append(self.board.san(move))
        self.board.push(move)
        self.outcome = self.board.outcome(claim_draw=True)
        self.selected = None
        self.last_move_time = pygame.time.get_ticks()

    def find_move(self, from_square, to_square):
        """The legal move between two squares, if any (pawns promote to a queen)."""
        for move in self.board.legal_moves:
            if (move.from_square == from_square and move.to_square == to_square
                    and move.promotion in (None, chess.QUEEN)):
                return move
        return None

    def click_square(self, square):
        """Handle a human click on the board: select a piece, or move it."""
        if not self.human_to_move():
            return
        if self.selected is not None:
            move = self.find_move(self.selected, square)
            if move:
                self.play(move)
                return
        piece = self.board.piece_at(square)
        own_piece = piece is not None and piece.color == self.board.turn
        self.selected = square if own_piece else None

    def update(self):
        """Start the agent's search when it is its turn, and play the result.

        Called once per frame.
        """
        if self.search:
            if self.search.is_alive():
                return
            search, self.search = self.search, None
            # Ignore the result if the game or the players changed meanwhile.
            still_valid = (search.position == self.board.fen()
                           and search.player == self.player(self.board.turn))
            if still_valid and search.move:
                self.info = f"{search.player} looked at {search.nodes:,} positions"
                self.play(search.move)
            return

        player = self.player(self.board.turn)
        if self.outcome is not None or player == HUMAN:
            return
        if self.mode == AGENT_MODE and self.paused and not self.step:
            return
        if pygame.time.get_ticks() - self.last_move_time < MOVE_DELAY_MS:
            return
        self.step = False
        self.search = Search(self.board, player, self.depth[self.board.turn])
        self.search.start()

    # ----- text shown in the panel -----

    def status(self):
        """One line describing whose turn it is or how the game ended."""
        if self.outcome is not None:
            if self.outcome.winner is None:
                reason = self.outcome.termination.name.replace("_", " ").lower()
                return f"Draw - {reason}"
            winner = self.player(self.outcome.winner)
            if winner == HUMAN:
                return "Checkmate - you win!"
            return f"Checkmate - {winner} ({SIDE[self.outcome.winner]}) wins"
        turn = self.board.turn
        player = self.player(turn)
        if self.search:
            return f"{player} ({SIDE[turn]}) is thinking..."
        if player == HUMAN:
            return f"Your move ({SIDE[turn]})" + (" - check!" if self.board.is_check() else "")
        if self.mode == AGENT_MODE and self.paused:
            return "Paused" if self.board.move_stack else "Press Start to begin"
        return f"{player} ({SIDE[turn]}) to move"

    def hint(self):
        """A smaller second line: what to do next, or what the agent just did."""
        if self.outcome is not None:
            return "Press New game to play again"
        if self.human_to_move():
            if self.selected is None:
                return "Click one of your pieces"
            return "Click a marked square to move it"
        return self.info


class Button:
    """A clickable rectangle. `active` marks the currently selected option."""

    def __init__(self, rect, label, action, active=False):
        self.rect, self.label, self.action, self.active = rect, label, action, active


def build_panel(game):
    """Lay out the side panel for the current mode.

    Returns (buttons, headings, y) where headings are (text, y) pairs and
    y is where the status text should start. Rebuilt whenever it is needed,
    so the highlighted options always match the game's settings.
    """
    buttons, headings = [], []
    y = 14

    def heading(text):
        nonlocal y
        headings.append((text, y))
        y += 22

    def row(options, per_row):
        """Add a row (or rows) of buttons from (label, active, action) triples."""
        nonlocal y
        gap = 6
        width = (PANEL_W - gap * (per_row - 1)) // per_row
        for i, (label, active, action) in enumerate(options):
            rect = pygame.Rect(PANEL_X + (i % per_row) * (width + gap),
                               y + (i // per_row) * 38, width, 32)
            buttons.append(Button(rect, label, action, active))
        y += 38 * ((len(options) - 1) // per_row + 1) + 8

    def agent_row(color):
        row([(name, game.agent[color] == name, lambda n=name: game.set_agent(color, n))
             for name in AGENTS], 3)

    def depth_row(color):
        row([(str(d), game.depth[color] == d, lambda d=d: game.set_depth(color, d))
             for d in DEPTHS], len(DEPTHS))

    heading("Mode")
    row([(mode, game.mode == mode, lambda m=mode: game.set_mode(m))
         for mode in (HUMAN_MODE, AGENT_MODE)], 2)

    if game.mode == HUMAN_MODE:
        opponent = not game.human_color
        heading("Opponent")
        agent_row(opponent)
        heading("You play")
        row([(SIDE[c], game.human_color == c, lambda c=c: game.set_side(c))
             for c in (chess.WHITE, chess.BLACK)], 2)
        heading("Difficulty (moves the agent looks ahead)")
        depth_row(opponent)
        row([("New game", False, game.new_game)], 1)
    else:
        for color in (chess.WHITE, chess.BLACK):
            heading(f"{SIDE[color]} agent")
            agent_row(color)
            heading(f"{SIDE[color]} difficulty")
            depth_row(color)
        if not game.paused:
            pause_label = "Pause"
        else:
            pause_label = "Resume" if game.board.move_stack else "Start"
        row([(pause_label, False, game.toggle_pause),
             ("Step", False, game.step_once),
             ("New game", False, game.new_game)], 3)
    return buttons, headings, y + 4


def square_at(pos, flipped):
    """The board square under a pixel position, or None if off the board."""
    x, y = pos
    if not (0 <= x < BOARD and 0 <= y < BOARD):
        return None
    file, rank = x // SQ, 7 - y // SQ
    if flipped:
        file, rank = 7 - file, 7 - rank
    return chess.square(file, rank)


def square_corner(square, flipped):
    """Top-left pixel of a square."""
    file, rank = chess.square_file(square), chess.square_rank(square)
    if flipped:
        file, rank = 7 - file, 7 - rank
    return file * SQ, (7 - rank) * SQ


def button_at(game, pos):
    """The panel button under a pixel position, or None."""
    for button in build_panel(game)[0]:
        if button.rect.collidepoint(pos):
            return button
    return None


def handle_click(game, pos):
    """Send a mouse click to the board or to whichever button it hit."""
    square = square_at(pos, game.flipped())
    if square is not None:
        game.click_square(square)
        return
    button = button_at(game, pos)
    if button:
        button.action()


def load_piece_images():
    """Render python-chess's built-in piece drawings to pygame images."""
    images = {}
    for color in chess.COLORS:
        for piece_type in chess.PIECE_TYPES:
            piece = chess.Piece(piece_type, color)
            svg = chess.svg.piece(piece, size=SQ)
            images[piece.symbol()] = pygame.image.load(
                io.BytesIO(svg.encode()), "piece.svg").convert_alpha()
    return images


def draw_board(screen, game, images, small_font):
    """Draw the squares, highlights, pieces and coordinates."""
    board, flipped = game.board, game.flipped()
    last = board.peek() if board.move_stack else None
    targets = ([m.to_square for m in board.legal_moves if m.from_square == game.selected]
               if game.selected is not None else [])
    king_in_check = board.king(board.turn) if board.is_check() else None

    for square in chess.SQUARES:
        x, y = square_corner(square, flipped)
        light = (chess.square_file(square) + chess.square_rank(square)) % 2 == 1
        color = LIGHT if light else DARK
        if last and square in (last.from_square, last.to_square):
            color = LAST_MOVE
        if square == game.selected:
            color = SELECTED
        if square == king_in_check:
            color = CHECK
        pygame.draw.rect(screen, color, (x, y, SQ, SQ))

        piece = board.piece_at(square)
        if piece:
            screen.blit(images[piece.symbol()], (x, y))
        if square in targets:                       # where the selected piece can go
            centre = (x + SQ // 2, y + SQ // 2)
            if piece:                               # a capture: ring around the piece
                pygame.draw.circle(screen, SELECTED, centre, SQ // 2 - 3, 5)
            else:
                pygame.draw.circle(screen, SELECTED, centre, SQ // 7)

    for i in range(8):                              # file letters and rank numbers
        file = 7 - i if flipped else i
        rank = i if flipped else 7 - i
        # Along the bottom and left edges the squares alternate, starting dark
        # at the bottom-left corner; use the opposite shade so labels show up.
        file_color = LIGHT if i % 2 == 0 else DARK
        rank_color = DARK if i % 2 == 0 else LIGHT
        screen.blit(small_font.render(chess.FILE_NAMES[file], True, file_color), (i * SQ + 4, BOARD - 18))
        screen.blit(small_font.render(chess.RANK_NAMES[rank], True, rank_color), (4, i * SQ + 2))


def draw_panel(screen, game, font, small_font, mouse=(-1, -1)):
    """Draw the side panel: settings, status, hint and the recent moves."""
    pygame.draw.rect(screen, PANEL_BG, (BOARD, 0, PANEL, HEIGHT))
    buttons, headings, y = build_panel(game)

    for text, heading_y in headings:
        screen.blit(small_font.render(text, True, MUTED), (PANEL_X, heading_y))
    for button in buttons:
        if button.active:
            color = BUTTON_ON
        elif button.rect.collidepoint(mouse):
            color = BUTTON_HOVER
        else:
            color = BUTTON
        pygame.draw.rect(screen, color, button.rect, border_radius=6)
        label = small_font.render(button.label, True, TEXT)
        screen.blit(label, label.get_rect(center=button.rect.center))

    screen.blit(font.render(game.status(), True, TEXT), (PANEL_X, y))
    screen.blit(small_font.render(game.hint(), True, MUTED), (PANEL_X, y + 26))

    # The most recent moves, two per line: "12. Nf3 Nc6".
    lines = [f"{i // 2 + 1}. " + " ".join(game.san_moves[i:i + 2])
             for i in range(0, len(game.san_moves), 2)]
    first_line = y + 60
    room = (HEIGHT - 8 - first_line) // 20
    for row, line in enumerate(lines[-room:] if room > 0 else []):
        screen.blit(small_font.render(line, True, TEXT), (PANEL_X, first_line + row * 20))


def draw(screen, game, images, font, small_font, mouse=(-1, -1)):
    """Draw one full frame."""
    draw_board(screen, game, images, small_font)
    draw_panel(screen, game, font, small_font, mouse)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess Agents")
    font = pygame.font.Font(None, 26)
    small_font = pygame.font.Font(None, 21)
    images = load_piece_images()
    game = Game()
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                handle_click(game, event.pos)
        game.update()

        mouse = pygame.mouse.get_pos()
        over_button = button_at(game, mouse) is not None
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if over_button
                                else pygame.SYSTEM_CURSOR_ARROW)
        draw(screen, game, images, font, small_font, mouse)
        pygame.display.flip()
        clock.tick(30)


if __name__ == "__main__":
    main()
