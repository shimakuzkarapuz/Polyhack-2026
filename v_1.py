import pygame
import sys

# ===== НАСТРОЙКИ =====
SIZE = 10                # размер поля (N x N)
WIN_LINE = SIZE // 2     # для победы нужно собрать линию длиной N/2 (можно изменить)
CELL_SIZE = 50           # размер клетки в пикселях
ANIMATION_DURATION = 300 # длительность анимации падения в миллисекундах
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
YELLOW = (255, 255, 0)

# Константы игроков
EMPTY = 0
PLAYER_X = 1
PLAYER_O = 2

# Символы для отображения
PLAYER_SYMBOL = {PLAYER_X: 'X', PLAYER_O: 'O'}


class GravityTicTacToe:
    """Крестики-нолики с гравитацией (фишки падают вниз) и анимацией падения."""
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

        # Переменные для анимации
        self.anim_active = False
        self.anim_col = 0
        self.anim_target_row = 0
        self.anim_player = PLAYER_X
        self.anim_start_time = 0
        self.anim_start_y = 0.0      # верхняя граница поля (в пикселях)
        self.anim_end_y = 0.0        # координата Y целевой клетки
        self.anim_current_y = 0.0     # текущая Y координата фишки во время анимации

    def _find_target_row(self, col):
        """Возвращает индекс самой нижней свободной строки в колонке или None, если колонка заполнена."""
        for row in range(self.size - 1, -1, -1):
            if self.board[row][col] == EMPTY:
                return row
        return None

    def start_animation(self, col):
        """
        Запускает анимацию падения фишки в указанную колонку.
        Возвращает True, если анимация успешно запущена.
        """
        if self.game_over or self.anim_active:
            return False

        target_row = self._find_target_row(col)
        if target_row is None:
            return False  # колонка заполнена

        # Запоминаем параметры анимации
        self.anim_active = True
        self.anim_col = col
        self.anim_target_row = target_row
        self.anim_player = self.current_player
        self.anim_start_time = pygame.time.get_ticks()
        # Начальная позиция — сразу над верхней границей поля
        self.anim_start_y = -CELL_SIZE   # фишка начинает падать сверху
        # Конечная позиция — центр целевой клетки (для отрисовки)
        self.anim_end_y = target_row * CELL_SIZE + CELL_SIZE // 2
        self.anim_current_y = self.anim_start_y

        return True

    def update_animation(self, current_time):
        """
        Обновляет состояние анимации: вычисляет текущую позицию падающей фишки
        и завершает анимацию, если время истекло.
        """
        if not self.anim_active:
            return

        elapsed = current_time - self.anim_start_time
        if elapsed >= ANIMATION_DURATION:
            # Анимация завершена — фиксируем фишку на доске
            self._finish_move()
        else:
            # Линейная интерполяция между start_y и end_y
            t = elapsed / ANIMATION_DURATION
            self.anim_current_y = self.anim_start_y + t * (self.anim_end_y - self.anim_start_y)

    def _finish_move(self):
        """Завершает анимацию: устанавливает фишку на доску, проверяет победу, переключает игрока."""
        # Устанавливаем фишку в целевую клетку
        self.board[self.anim_target_row][self.anim_col] = self.anim_player
        self.moves_count += 1

        # Проверка победы
        if self._check_win(self.anim_target_row, self.anim_col):
            self.game_over = True
            self.winner = self.anim_player
        elif self.moves_count == self.size * self.size:
            self.game_over = True  # ничья
        else:
            # Смена игрока
            self.current_player = PLAYER_O if self.anim_player == PLAYER_X else PLAYER_X

        # Сбрасываем флаг анимации
        self.anim_active = False

    def _check_win(self, row, col):
        """
        Проверяет, есть ли линия из win_line фишек текущего игрока,
        проходящая через клетку (row, col).
        """
        player = self.board[row][col]
        # Направления: горизонталь, вертикаль, главная диагональ, побочная диагональ
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

    def get_col_from_pos(self, pos):
        """Преобразует координаты мыши в индекс колонки или возвращает None, если анимация активна."""
        if self.anim_active:   # во время анимации клики игнорируются
            return None
        x, y = pos
        # Клик в информационной панели не учитываем
        if y >= WINDOW_HEIGHT - INFO_PANEL_HEIGHT:
            return None
        col = x // CELL_SIZE
        if 0 <= col < self.size:
            return col
        return None


def draw_board(screen, game):
    """Отрисовывает игровое поле, фишки и анимированную падающую фишку."""
    screen.fill(WHITE)

    # Рисуем сетку
    for i in range(game.size + 1):
        pygame.draw.line(screen, BLACK, (0, i * CELL_SIZE), (game.size * CELL_SIZE, i * CELL_SIZE), 2)
        pygame.draw.line(screen, BLACK, (i * CELL_SIZE, 0), (i * CELL_SIZE, game.size * CELL_SIZE), 2)

    # Рисуем фишки, уже стоящие на доске
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

    # Если идёт анимация, рисуем падающую фишку
    if game.anim_active:
        col = game.anim_col
        # Центр фишки по X (центр колонки)
        center_x = col * CELL_SIZE + CELL_SIZE // 2
        # Текущая Y координата центра фишки (anim_current_y уже хранит центр)
        center_y = game.anim_current_y

        if game.anim_player == PLAYER_X:
            # Крестик
            margin = 10
            start_pos = (center_x - CELL_SIZE//2 + margin, center_y - CELL_SIZE//2 + margin)
            end_pos = (center_x + CELL_SIZE//2 - margin, center_y + CELL_SIZE//2 - margin)
            pygame.draw.line(screen, RED, start_pos, end_pos, 3)
            pygame.draw.line(screen, RED, (end_pos[0], start_pos[1]), (start_pos[0], end_pos[1]), 3)
        else:
            # Нолик
            radius = CELL_SIZE // 2 - 10
            pygame.draw.circle(screen, BLUE, (int(center_x), int(center_y)), radius, 3)

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
        if game.anim_active:
            text = f"Ходит {PLAYER_SYMBOL[game.current_player]}"
        else:
            text = f"Ходит {PLAYER_SYMBOL[game.current_player]} (кликните в колонку)"

    text_surface = font.render(text, True, BLACK)
    text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, game.size * CELL_SIZE + INFO_PANEL_HEIGHT // 2))
    screen.blit(text_surface, text_rect)

    pygame.display.flip()


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(f"Гравитационные крестики-нолики {SIZE}x{SIZE} (победа - {WIN_LINE} в ряд)")
    clock = pygame.time.Clock()

    game = GravityTicTacToe(SIZE, WIN_LINE)
    running = True

    while running:
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Левая кнопка мыши
                pos = pygame.mouse.get_pos()
                col = game.get_col_from_pos(pos)
                if col is not None:
                    # Пытаемся запустить анимацию вместо мгновенного хода
                    game.start_animation(col)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Клавиша R для перезапуска
                    game.reset()

        # Обновляем анимацию
        game.update_animation(current_time)

        draw_board(screen, game)
        clock.tick(60)  # 60 FPS для плавной анимации


if __name__ == "__main__":
    main()
