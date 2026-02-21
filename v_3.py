import pygame
import sys

# ===== НАСТРОЙКИ =====
SIZE = 10                # размер поля (N x N)
WIN_LINE = SIZE // 2     # для победы нужно собрать линию длиной N/2
CELL_SIZE = 50           # размер клетки в пикселях
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
        self.shift_direction = 1          # 1 = вправо, -1 = влево
        self.shift_parity = 0              # 0 = нечётные строки, 1 = чётные

    def make_move(self, row, col):
        """
        Совершает ход текущим игроком в клетку (row, col).
        После хода (если игра не завершена) выполняет сдвиг строк с текущей чётностью
        в текущем направлении, затем оба параметра переключаются.
        """
        if self.game_over:
            return False
        if not (0 <= row < self.size and 0 <= col < self.size):
            return False
        if self.board[row][col] != EMPTY:
            return False

        # 1. Ставим фишку
        self.board[row][col] = self.current_player
        self.moves_count += 1

        # 2. Проверяем победу после хода
        if self.check_win(row, col):
            self.game_over = True
            self.winner = self.current_player
            return True

        # 3. Проверяем ничью (заполнено всё поле)
        if self.moves_count == self.size * self.size:
            self.game_over = True
            self.winner = None
            return True

        # 4. Меняем игрока (ход переходит к противнику)
        self.current_player = PLAYER_O if self.current_player == PLAYER_X else PLAYER_X

        # 5. Выполняем сдвиг строк с текущей чётностью и направлением
        self._shift_rows(self.shift_parity, self.shift_direction)

        # 6. Переключаем параметры для следующего сдвига
        self.shift_direction *= -1
        self.shift_parity = 1 - self.shift_parity   # чередуем 0 и 1

        # 7. После сдвига проверяем, не возникла ли победная ситуация или ничья
        self._check_game_over_after_shift()

        return True

    def _shift_rows(self, parity, direction):
        """
        Циклический сдвиг строк с заданной чётностью.
        parity = 0 : нечётные индексы (1,3,5,...)
        parity = 1 : чётные индексы (0,2,4,...)
        direction = 1 : сдвиг вправо
        direction = -1: сдвиг влево
        """
        if parity == 0:
            rows_to_shift = range(1, self.size, 2)   # нечётные
        else:
            rows_to_shift = range(0, self.size, 2)   # чётные

        if direction == 1:  # сдвиг вправо
            for row in rows_to_shift:
                last = self.board[row][self.size - 1]
                for col in range(self.size - 1, 0, -1):
                    self.board[row][col] = self.board[row][col - 1]
                self.board[row][0] = last
        else:  # сдвиг влево
            for row in rows_to_shift:
                first = self.board[row][0]
                for col in range(self.size - 1):
                    self.board[row][col] = self.board[row][col + 1]
                self.board[row][self.size - 1] = first

    def _check_game_over_after_shift(self):
        """Проверяет, есть ли после сдвига победитель или ничья."""
        winner = self._check_winner_on_board()
        if winner is not None:
            self.game_over = True
            self.winner = winner
            return

        if self.moves_count == self.size * self.size:
            self.game_over = True
            self.winner = None

    def _check_winner_on_board(self):
        """Пробегает по всем клеткам и ищет линию из win_line фишек."""
        for r in range(self.size):
            for c in range(self.size):
                player = self.board[r][c]
                if player != EMPTY:
                    if self.check_win(r, c):
                        return player
        return None

    def check_win(self, row, col):
        """
        Проверяет, есть ли линия из win_line фишек текущего игрока,
        проходящая через клетку (row, col).
        """
        player = self.board[row][col]
        if player == EMPTY:
            return False

        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

        for dr, dc in directions:
            count = 1
            # положительное направление
            r, c = row + dr, col + dc
            while 0 <= r < self.size and 0 <= c < self.size and self.board[r][c] == player:
                count += 1
                r += dr
                c += dc
            # отрицательное направление
            r, c = row - dr, col - dc
            while 0 <= r < self.size and 0 <= c < self.size and self.board[r][c] == player:
                count += 1
                r -= dr
                c -= dc

            if count >= self.win_line:
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
                margin = 10
                start_pos = (col * CELL_SIZE + margin, row * CELL_SIZE + margin)
                end_pos = ((col + 1) * CELL_SIZE - margin, (row + 1) * CELL_SIZE - margin)
                pygame.draw.line(screen, RED, start_pos, end_pos, 3)
                pygame.draw.line(screen, RED, (end_pos[0], start_pos[1]), (start_pos[0], end_pos[1]), 3)
            elif game.board[row][col] == PLAYER_O:
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
    pygame.display.set_caption(f"Крестики-нолики {SIZE}x{SIZE} со сдвигом строк (чередование чётности и направления)")
    clock = pygame.time.Clock()

    game = TicTacToe(SIZE, WIN_LINE)
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = pygame.mouse.get_pos()
                cell = game.get_cell_from_pos(pos)
                if cell is not None:
                    row, col = cell
                    game.make_move(row, col)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset()

        draw_board(screen, game)
        clock.tick(30)


if __name__ == "__main__":
    main()
