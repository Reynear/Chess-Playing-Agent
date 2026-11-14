"""Graphical interface (pygame).

    python gui.py

Each side can be a human or any agent in the registry, so the same window
covers human-vs-agent and agent-vs-agent. Click a piece, then click where
it should go. The side panel sets who plays each colour and how deep each
agent searches (the difficulty level).
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
PANEL = 280                               # width of the side panel
WIDTH, HEIGHT = BOARD + PANEL, BOARD

LIGHT, DARK = (240, 217, 181), (181, 136, 99)
LAST_MOVE = (205, 210, 106)
SELECTED = (130, 151, 105)
CHECK = (220, 80, 70)
PANEL_BG, BUTTON_BG, TEXT = (40, 42, 48), (70, 74, 84), (235, 235, 235)

HUMAN = "Human"
PLAYERS = [HUMAN] + list(AGENTS)          # choices for each colour
MAX_DEPTH = 4
MOVE_DELAY_MS = 500                       # pause between agent moves so games are watchable


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
    """The state of the current game: board, players, depths, selection."""

    def __init__(self):
        self.players = {chess.WHITE: HUMAN, chess.BLACK: PLAYERS[-1]}
        self.depth = {chess.WHITE: 3, chess.BLACK: 3}
        self.new_game()

    def new_game(self):
        """Reset to the starting position, keeping the chosen players and depths."""
        self.board = chess.Board()
        self.outcome = None               # set once the game has ended
        self.selected = None              # square the human has clicked on
        self.san_moves = []               # moves played, in normal chess notation
        self.search = None                # the agent search in progress, if any
        self.paused = False
        self.step = False                 # play exactly one agent move while paused
        self.last_move_time = 0
        self.info = ""                    # what the last agent search did

    def flipped(self):
        """Show the board from Black's side when only Black is human."""
        return self.players[chess.WHITE] != HUMAN and self.players[chess.BLACK] == HUMAN

    def human_to_move(self):
        return self.outcome is None and self.players[self.board.turn] == HUMAN

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
                           and search.player == self.players[self.board.turn])
            if still_valid and search.move:
                self.info = f"{search.player} looked at {search.nodes:,} positions"
                self.play(search.move)
            return

        player = self.players[self.board.turn]
        if self.outcome is not None or player == HUMAN:
            return
        if self.paused and not self.step:
            return
        if pygame.time.get_ticks() - self.last_move_time < MOVE_DELAY_MS:
            return
        self.step = False
        self.search = Search(self.board, player, self.depth[self.board.turn])
        self.search.start()

    def status(self):
        """One line describing whose turn it is or how the game ended."""
        if self.outcome is not None:
            if self.outcome.winner is None:
                reason = self.outcome.termination.name.replace("_", " ").lower()
                return f"Draw: {reason}"
            winner = "White" if self.outcome.winner == chess.WHITE else "Black"
            return f"{winner} wins by checkmate"
        side = "White" if self.board.turn == chess.WHITE else "Black"
        player = self.players[self.board.turn]
        if self.search:
            return f"{side} ({player}) is thinking..."
        if player != HUMAN and self.paused:
            return "Paused"
        return f"{side} to move" + (" - check" if self.board.is_check() else "")


class Button:
    """A clickable rectangle whose label can change with the game state."""

    def __init__(self, y, label, action):
        self.rect = pygame.Rect(BOARD + 20, y, PANEL - 40, 34)
        self.label, self.action = label, action


def make_buttons(game):
    """Build the side-panel buttons. Labels are functions so they stay current."""
    def next_player(color):
        choices = PLAYERS
        game.players[color] = choices[(choices.index(game.players[color]) + 1) % len(choices)]
        game.selected = None

    def next_depth(color):
        game.depth[color] = game.depth[color] % MAX_DEPTH + 1

    def toggle_pause():
        game.paused = not game.paused

    def step():
        game.paused, game.step = True, True

    white, black = chess.WHITE, chess.BLACK
    return [
        Button(44, lambda: game.players[white], lambda: next_player(white)),
        Button(84, lambda: f"Depth {game.depth[white]}", lambda: next_depth(white)),
        Button(154, lambda: game.players[black], lambda: next_player(black)),
        Button(194, lambda: f"Depth {game.depth[black]}", lambda: next_depth(black)),
        Button(254, lambda: "New game", game.new_game),
        Button(294, lambda: "Resume" if game.paused else "Pause", toggle_pause),
        Button(334, lambda: "Step one move", step),
    ]


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


def handle_click(game, buttons, pos):
    """Send a mouse click to the board or to whichever button it hit."""
    square = square_at(pos, game.flipped())
    if square is not None:
        game.click_square(square)
        return
    for button in buttons:
        if button.rect.collidepoint(pos):
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
            pygame.draw.circle(screen, SELECTED, (x + SQ // 2, y + SQ // 2), SQ // 7)

    for i in range(8):                              # file letters and rank numbers
        file = 7 - i if flipped else i
        rank = i if flipped else 7 - i
        # Along the bottom and left edges the squares alternate, starting dark
        # at the bottom-left corner; use the opposite shade so labels show up.
        file_color = LIGHT if i % 2 == 0 else DARK
        rank_color = DARK if i % 2 == 0 else LIGHT
        screen.blit(small_font.render(chess.FILE_NAMES[file], True, file_color), (i * SQ + 4, BOARD - 18))
        screen.blit(small_font.render(chess.RANK_NAMES[rank], True, rank_color), (4, i * SQ + 2))


def draw_panel(screen, game, buttons, font, small_font):
    """Draw the side panel: player and depth buttons, status and move list."""
    pygame.draw.rect(screen, PANEL_BG, (BOARD, 0, PANEL, HEIGHT))
    x = BOARD + 20
    screen.blit(font.render("White", True, TEXT), (x, 16))
    screen.blit(font.render("Black", True, TEXT), (x, 126))

    for button in buttons:
        pygame.draw.rect(screen, BUTTON_BG, button.rect, border_radius=6)
        label = font.render(button.label(), True, TEXT)
        screen.blit(label, label.get_rect(center=button.rect.center))

    screen.blit(font.render(game.status(), True, TEXT), (x, 386))
    screen.blit(small_font.render(game.info, True, TEXT), (x, 412))

    # The most recent moves, two per line: "12. Nf3 Nc6".
    lines = [f"{i // 2 + 1}. " + " ".join(game.san_moves[i:i + 2])
             for i in range(0, len(game.san_moves), 2)]
    for row, line in enumerate(lines[-9:]):
        screen.blit(small_font.render(line, True, TEXT), (x, 446 + row * 20))


def draw(screen, game, buttons, images, font, small_font):
    """Draw one full frame."""
    draw_board(screen, game, images, small_font)
    draw_panel(screen, game, buttons, font, small_font)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess Agents")
    font = pygame.font.Font(None, 26)
    small_font = pygame.font.Font(None, 22)
    images = load_piece_images()
    game = Game()
    buttons = make_buttons(game)
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                handle_click(game, buttons, event.pos)
        game.update()
        draw(screen, game, buttons, images, font, small_font)
        pygame.display.flip()
        clock.tick(30)


if __name__ == "__main__":
    main()
