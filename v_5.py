import pygame
import sys
import random

# ===== НАСТРОЙКИ =====
SIZE = 10          # размер поля (N x N)
WIN_LINE = SIZE // 2    # для победы нужно собрать линию длиной N (можно изменить, например, на 5)
CELL_SIZE = 50     # размер клетки в пикселях
# =====================

WINDOW_WIDTH = SIZE * CELL_SIZE
WINDOW_HEIGHT = SIZE * CELL_SIZE + 60  # +60 для панели информации
INFO_PANEL_HEIGHT = 60

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# Константы игроков
EMPTY = 0
PLAYER_X = 1
PLAYER_O = 2

# Символы для отображения
PLAYER_SYMBOL = {PLAYER_X: 'X', PLAYER_O: 'O'}

class TicTacToe:
    def __init__(self, size, win_line):
        self.size = size
        self.win_line = win_line
        self.reset()

    def reset(self):
        """Начинает новую игру."""
        self.board = [[EMPTY for _ in range(self.size)] for _ in range(self.size)]
        self.current_player = PLAYER_X
        self.game_over = False
        self.winner = None
        self.moves_count = 0

    def make_move(self, row, col):
        """Совершает ход текущим игроком в клетку (row, col). Возвращает True, если ход успешен."""
        if self.game_over:
            return False
        if not (0 <= row < self.size and 0 <= col < self.size):
            return False
        if self.board[row][col] != EMPTY:
            return False

        self.board[row][col] = self.current_player
        self.moves_count += 1

        # Проверка победы
        if self.check_win(row, col):
            self.game_over = True
            self.winner = self.current_player
        elif self.moves_count == self.size * self.size:
            self.game_over = True  # ничья
        else:
            # Смена игрока
            self.current_player = PLAYER_O if self.current_player == PLAYER_X else PLAYER_X

        return True

    def check_win(self, row, col):
        """
        Проверяет, есть ли линия из win_line фишек текущего игрока,
        проходящая через клетку (row, col).
        """
        player = self.board[row][col]
        if player == EMPTY:
            return False
        # Направления: горизонталь, вертикаль, главная диагональ, побочная диагональ
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

        for dr, dc in directions:
            count = 1  # текущая клетка уже занята
            # Положительное направление
            r, c = row + dr, col + dc
            while 0 <= r < self.size and 0 <= c < self.size and self.board[r][c] == player:
                count += 1
                r += dr
                c += dc
            # Отрицательное направление
            r, c = row - dr, col - dc
            while 0 <= r < self.size and 0 <= c < self.size and self.board[r][c] == player:
                count += 1
                r -= dr
                c -= dc

            if count >= self.win_line:
                return True
        return False

    def check_win_any(self, player):
        """Проверяет, есть ли победная линия у указанного игрока на всём поле."""
        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] == player:
                    if self.check_win(r, c):
                        return True
        return False

    def get_cell_from_pos(self, pos):
        """Преобразует координаты мыши в индексы клетки или возвращает None."""
        x, y = pos
        if y >= WINDOW_HEIGHT - INFO_PANEL_HEIGHT:  # клик в информационной панели
            return None
        col = x // CELL_SIZE
        row = y // CELL_SIZE
        if 0 <= row < self.size and 0 <= col < self.size:
            return row, col
        return None


def transform_random_pieces(game):
    """
    Меняет один случайный X на O и один случайный O на X.
    Если какого-то типа нет на поле, соответствующее превращение пропускается.
    После превращения проверяет, не возникла ли победная ситуация.
    """
    # Собираем координаты всех X и O
    x_positions = []
    o_positions = []
    for r in range(game.size):
        for c in range(game.size):
            if game.board[r][c] == PLAYER_X:
                x_positions.append((r, c))
            elif game.board[r][c] == PLAYER_O:
                o_positions.append((r, c))

    changed = False

    # Меняем один X на O, если есть X
    if x_positions:
        rx, cx = random.choice(x_positions)
        game.board[rx][cx] = PLAYER_O
        changed = True

    # Меняем один O на X, если есть O
    if o_positions:
        ro, co = random.choice(o_positions)
        game.board[ro][co] = PLAYER_X
        changed = True

    if changed:
        # После превращений проверяем, не появился ли победитель
        if game.check_win_any(PLAYER_X):
            game.game_over = True
            game.winner = PLAYER_X
        elif game.check_win_any(PLAYER_O):
            game.game_over = True
            game.winner = PLAYER_O
        # Если игра уже была закончена (ничья или победа), мы сюда не попадём,
        # потому что вызываем transform только если game_over == False.


def draw_board(screen, game):
    """Отрисовывает игровое поле и фишки."""
    screen.fill(WHITE)

    # Рисуем сетку
    for i in range(game.size + 1):
        pygame.draw.line(screen, BLACK, (0, i * CELL_SIZE), (game.size * CELL_SIZE, i * CELL_SIZE), 2)
        pygame.draw.line(screen, BLACK, (i * CELL_SIZE, 0), (i * CELL_SIZE, game.size * CELL_SIZE), 2)

    # Рисуем фишки
    for row in range(game.size):
        for col in range(game.size):
            if game.board[row][col] == PLAYER_X:
                # Крестик
                margin = 10
                start_pos = (col * CELL_SIZE + margin, row * CELL_SIZE + margin)
                end_pos = ((col + 1) * CELL_SIZE - margin, (row + 1) * CELL_SIZE - margin)
                pygame.draw.line(screen, RED, start_pos, end_pos, 3)
                pygame.draw.line(screen, RED, (end_pos[0], start_pos[1]), (start_pos[0], end_pos[1]), 3)
            elif game.board[row][col] == PLAYER_O:
                # Нолик (кружок)
                center = (col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2)
                radius = CELL_SIZE // 2 - 10
                pygame.draw.circle(screen, BLUE, center, radius, 3)

    # Информационная панель внизу
    panel_rect = pygame.Rect(0, game.size * CELL_SIZE, WINDOW_WIDTH, INFO_PANEL_HEIGHT)
    pygame.draw.rect(screen, GRAY, panel_rect)
    font = pygame.font.Font(None, 36)

    if game.game_over:
        if game.winner is not None:
            text = f"Победил {PLAYER_SYMBOL[game.winner]}! Нажмите R для новой игры"
        else:
            text = "Ничья! Нажмите R для новой игры"
    else:
        text = f"Ходит {PLAYER_SYMBOL[game.current_player]}"

    text_surface = font.render(text, True, BLACK)
    text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, game.size * CELL_SIZE + INFO_PANEL_HEIGHT // 2))
    screen.blit(text_surface, text_rect)

    pygame.display.flip()


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(f"Крестики-нолики {SIZE}x{SIZE} (победа - {WIN_LINE} в ряд)")
    clock = pygame.time.Clock()

    game = TicTacToe(SIZE, WIN_LINE)
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Левая кнопка мыши
                pos = pygame.mouse.get_pos()
                cell = game.get_cell_from_pos(pos)
                if cell is not None:
                    row, col = cell
                    if game.make_move(row, col):
                        # После успешного хода, если игра не окончена и это третий ход (счётчик ходов уже увеличен)
                        if not game.game_over and game.moves_count % 3 == 0:
                            transform_random_pieces(game)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Клавиша R для перезапуска
                    game.reset()

        draw_board(screen, game)
        clock.tick(30)

if __name__ == "__main__":
    main()
