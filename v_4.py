import pygame
import sys

# ===== НАСТРОЙКИ =====
SIZE = 10
WIN_LINE = SIZE // 2
CELL_SIZE = 50
ANIMATION_DURATION = 500
ROTATION_FALL_DURATION = 600
PRE_FALL_DELAY = 1000
# =====================

WINDOW_WIDTH = SIZE * CELL_SIZE
WINDOW_HEIGHT = SIZE * CELL_SIZE + 60
INFO_PANEL_HEIGHT = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

EMPTY = 0
PLAYER_X = 1
PLAYER_O = 2
PLAYER_SYMBOL = {PLAYER_X: 'X', PLAYER_O: 'O'}


class FallingPiece:
    def __init__(self, player, start_row, start_col, end_row, end_col):
        self.player = player
        self.start_row = start_row
        self.start_col = start_col
        self.end_row = end_row
        self.end_col = end_col
        self.start_x = start_col * CELL_SIZE + CELL_SIZE // 2
        self.start_y = start_row * CELL_SIZE + CELL_SIZE // 2
        self.end_x = end_col * CELL_SIZE + CELL_SIZE // 2
        self.end_y = end_row * CELL_SIZE + CELL_SIZE // 2
        self.progress = 0.0

    def update(self, progress):
        self.progress = max(0.0, min(1.0, progress))

    def get_current_position(self):
        x = self.start_x + (self.end_x - self.start_x) * self.progress
        y = self.start_y + (self.end_y - self.start_y) * self.progress
        return x, y


class GravityTicTacToe:
    def __init__(self, size, win_line):
        self.size = size
        self.win_line = win_line
        self.reset()

    def reset(self):
        self.board = [[EMPTY for _ in range(self.size)] for _ in range(self.size)]
        self.current_player = PLAYER_X
        self.game_over = False
        self.winner = None
        self.moves_count = 0
        self.marker_pos = (self.size - 1, self.size - 1)  # изначально правый нижний угол

        # Анимация одиночного хода
        self.anim_active = False
        self.anim_col = 0
        self.anim_target_row = 0
        self.anim_player = PLAYER_X
        self.anim_start_time = 0
        self.anim_start_y = 0.0
        self.anim_end_y = 0.0
        self.anim_current_y = 0.0

        # Состояния для поворота и падения
        self.pre_fall_delay_active = False
        self.pre_fall_delay_start_time = 0
        self.rotation_fall_active = False
        self.rotation_fall_start_time = 0
        self.falling_pieces = []
        self.post_rotation_board = None

    def _find_target_row(self, col):
        for row in range(self.size - 1, -1, -1):
            if self.board[row][col] == EMPTY:
                return row
        return None

    def start_animation(self, col):
        if self.game_over or self.anim_active or self.rotation_fall_active or self.pre_fall_delay_active:
            return False
        target_row = self._find_target_row(col)
        if target_row is None:
            return False
        self.anim_active = True
        self.anim_col = col
        self.anim_target_row = target_row
        self.anim_player = self.current_player
        self.anim_start_time = pygame.time.get_ticks()
        self.anim_start_y = -CELL_SIZE
        self.anim_end_y = target_row * CELL_SIZE + CELL_SIZE // 2
        self.anim_current_y = self.anim_start_y
        return True

    def update_animation(self, current_time):
        if self.pre_fall_delay_active:
            elapsed = current_time - self.pre_fall_delay_start_time
            if elapsed >= PRE_FALL_DELAY:
                self._start_fall_after_delay()
        elif self.rotation_fall_active:
            elapsed = current_time - self.rotation_fall_start_time
            progress = elapsed / ROTATION_FALL_DURATION
            if progress >= 1.0:
                self._finish_rotation_fall()
            else:
                for piece in self.falling_pieces:
                    piece.update(progress)
        elif self.anim_active:
            elapsed = current_time - self.anim_start_time
            if elapsed >= ANIMATION_DURATION:
                self._finish_move()
            else:
                t = elapsed / ANIMATION_DURATION
                self.anim_current_y = self.anim_start_y + t * (self.anim_end_y - self.anim_start_y)

    def _finish_move(self):
        self.board[self.anim_target_row][self.anim_col] = self.anim_player
        self.moves_count += 1

        if self._check_win(self.anim_target_row, self.anim_col):
            self.game_over = True
            self.winner = self.anim_player
        elif self.moves_count == self.size * self.size:
            self.game_over = True
        else:
            self.current_player = PLAYER_O if self.anim_player == PLAYER_X else PLAYER_X

        if not self.game_over and self.moves_count % 3 == 0:
            self._start_rotation_delay()

        self.anim_active = False

    def _start_rotation_delay(self):
        # Поворот доски на 90° по часовой стрелке
        rotated_board = [[EMPTY] * self.size for _ in range(self.size)]
        for i in range(self.size):
            for j in range(self.size):
                rotated_board[j][self.size - 1 - i] = self.board[i][j]
        self.board = rotated_board

        # Поворот красного маркера
        r, c = self.marker_pos
        self.marker_pos = (c, self.size - 1 - r)

        # Запуск задержки
        self.pre_fall_delay_active = True
        self.pre_fall_delay_start_time = pygame.time.get_ticks()

    def _start_fall_after_delay(self):
        self.pre_fall_delay_active = False

        # Доска после падения
        self.post_rotation_board = self._apply_gravity_to_board(self.board)

        # Создание падающих фишек
        self.falling_pieces = []
        for col in range(self.size):
            pieces_in_col = []
            for row in range(self.size):
                if self.board[row][col] != EMPTY:
                    pieces_in_col.append((row, self.board[row][col]))
            target_rows = [r for r in range(self.size - 1, -1, -1) if self.post_rotation_board[r][col] != EMPTY]
            for idx, (src_row, player) in enumerate(pieces_in_col):
                tgt_row = target_rows[len(target_rows) - 1 - idx]
                self.falling_pieces.append(FallingPiece(player, src_row, col, tgt_row, col))

        self.rotation_fall_active = True
        self.rotation_fall_start_time = pygame.time.get_ticks()

    def _finish_rotation_fall(self):
        self.board = self.post_rotation_board
        self.rotation_fall_active = False
        self.falling_pieces = []

        winner = self._check_win_any()
        if winner is not None:
            self.game_over = True
            self.winner = winner
        elif self._is_board_full():
            self.game_over = True
            self.winner = None

    def _apply_gravity_to_board(self, board):
        new_board = [[EMPTY] * self.size for _ in range(self.size)]
        for col in range(self.size):
            pieces = []
            for row in range(self.size - 1, -1, -1):
                if board[row][col] != EMPTY:
                    pieces.append(board[row][col])
            for row in range(self.size - 1, -1, -1):
                if pieces:
                    new_board[row][col] = pieces.pop(0)
        return new_board

    def _check_win_any(self):
        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] != EMPTY and self._check_win(r, c):
                    return self.board[r][c]
        return None

    def _is_board_full(self):
        for row in self.board:
            if EMPTY in row:
                return False
        return True

    def _check_win(self, row, col):
        player = self.board[row][col]
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            r, c = row + dr, col + dc
            while 0 <= r < self.size and 0 <= c < self.size and self.board[r][c] == player:
                count += 1
                r += dr
                c += dc
            r, c = row - dr, col - dc
            while 0 <= r < self.size and 0 <= c < self.size and self.board[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            if count >= self.win_line:
                return True
        return False

    def get_col_from_pos(self, pos):
        if self.anim_active or self.rotation_fall_active or self.pre_fall_delay_active or self.game_over:
            return None
        x, y = pos
        if y >= WINDOW_HEIGHT - INFO_PANEL_HEIGHT:
            return None
        col = x // CELL_SIZE
        if 0 <= col < self.size:
            return col
        return None


def draw_board(screen, game):
    screen.fill(WHITE)

    # Сетка
    for i in range(game.size + 1):
        pygame.draw.line(screen, BLACK, (0, i * CELL_SIZE), (game.size * CELL_SIZE, i * CELL_SIZE), 2)
        pygame.draw.line(screen, BLACK, (i * CELL_SIZE, 0), (i * CELL_SIZE, game.size * CELL_SIZE), 2)

    # Отрисовка фишек
    if game.rotation_fall_active:
        for piece in game.falling_pieces:
            x, y = piece.get_current_position()
            if piece.player == PLAYER_X:
                margin = 10
                start_pos = (x - CELL_SIZE//2 + margin, y - CELL_SIZE//2 + margin)
                end_pos = (x + CELL_SIZE//2 - margin, y + CELL_SIZE//2 - margin)
                pygame.draw.line(screen, RED, start_pos, end_pos, 3)
                pygame.draw.line(screen, RED, (end_pos[0], start_pos[1]), (start_pos[0], end_pos[1]), 3)
            else:
                radius = CELL_SIZE // 2 - 10
                pygame.draw.circle(screen, BLUE, (int(x), int(y)), radius, 3)
    else:
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

    # Анимация одиночного хода (поверх)
    if game.anim_active:
        col = game.anim_col
        center_x = col * CELL_SIZE + CELL_SIZE // 2
        center_y = game.anim_current_y
        if game.anim_player == PLAYER_X:
            margin = 10
            start_pos = (center_x - CELL_SIZE//2 + margin, center_y - CELL_SIZE//2 + margin)
            end_pos = (center_x + CELL_SIZE//2 - margin, center_y + CELL_SIZE//2 - margin)
            pygame.draw.line(screen, RED, start_pos, end_pos, 3)
            pygame.draw.line(screen, RED, (end_pos[0], start_pos[1]), (start_pos[0], end_pos[1]), 3)
        else:
            radius = CELL_SIZE // 2 - 10
            pygame.draw.circle(screen, BLUE, (int(center_x), int(center_y)), radius, 3)

    # Информационная панель
    panel_rect = pygame.Rect(0, game.size * CELL_SIZE, WINDOW_WIDTH, INFO_PANEL_HEIGHT)
    pygame.draw.rect(screen, GRAY, panel_rect)
    font = pygame.font.Font(None, 36)

    if game.game_over:
        if game.winner is not None:
            text = f"Победил {PLAYER_SYMBOL[game.winner]}! Нажмите R для новой игры"
        else:
            text = "Ничья! Нажмите R для новой игры"
    else:
        if game.pre_fall_delay_active:
            text = "Поворот! Падение через мгновение..."
        elif game.rotation_fall_active:
            text = "Падение..."
        elif game.anim_active:
            text = f"Ходит {PLAYER_SYMBOL[game.current_player]}"
        else:
            text = f"Ходит {PLAYER_SYMBOL[game.current_player]} (кликните в колонку)"

    text_surface = font.render(text, True, BLACK)
    text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, game.size * CELL_SIZE + INFO_PANEL_HEIGHT // 2))
    screen.blit(text_surface, text_rect)

    # --- Красный маркер (всегда рисуется, даже во время падения) ---
    if not game.game_over:
        marker_row, marker_col = game.marker_pos
        rect_size = 12
        margin = 2  # отступ от края клетки

        # Определяем, в каком углу доски находится клетка с маркером
        if marker_row == 0 and marker_col == 0:
            # левый верхний угол доски -> маркер в левом верхнем углу клетки
            x = marker_col * CELL_SIZE + margin
            y = marker_row * CELL_SIZE + margin
        elif marker_row == 0 and marker_col == game.size - 1:
            # правый верхний угол доски -> маркер в правом верхнем углу клетки
            x = marker_col * CELL_SIZE + CELL_SIZE - rect_size - margin
            y = marker_row * CELL_SIZE + margin
        elif marker_row == game.size - 1 and marker_col == 0:
            # левый нижний угол доски -> маркер в левом нижнем углу клетки
            x = marker_col * CELL_SIZE + margin
            y = marker_row * CELL_SIZE + CELL_SIZE - rect_size - margin
        elif marker_row == game.size - 1 and marker_col == game.size - 1:
            # правый нижний угол доски -> маркер в правом нижнем углу клетки
            x = marker_col * CELL_SIZE + CELL_SIZE - rect_size - margin
            y = marker_row * CELL_SIZE + CELL_SIZE - rect_size - margin
        else:
            # На всякий случай, если маркер вдруг не в углу (не должно происходить)
            x = marker_col * CELL_SIZE + CELL_SIZE - rect_size - margin
            y = marker_row * CELL_SIZE + CELL_SIZE - rect_size - margin

        pygame.draw.rect(screen, RED, (x, y, rect_size, rect_size))
    # -------------------------------------------------------------

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

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = pygame.mouse.get_pos()
                col = game.get_col_from_pos(pos)
                if col is not None:
                    game.start_animation(col)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                game.reset()

        game.update_animation(current_time)
        draw_board(screen, game)
        clock.tick(60)


if __name__ == "__main__":
    main()
