import pygame
import sys
import random
import copy

# ==================== ОБЩИЕ НАСТРОЙКИ ====================
SIZE = 10
WIN_LINE = SIZE // 2
CELL_SIZE = 50
INFO_PANEL_HEIGHT = 60
WINDOW_WIDTH = SIZE * CELL_SIZE
WINDOW_HEIGHT = SIZE * CELL_SIZE + INFO_PANEL_HEIGHT

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
PLAYER_SYMBOL = {PLAYER_X: 'X', PLAYER_O: 'O'}

# ========== КОНСТАНТЫ ДЛЯ КОНКРЕТНЫХ ВЕРСИЙ =============
V1_ANIMATION_DURATION = 300
V4_ANIMATION_DURATION = 500
V4_ROTATION_FALL_DURATION = 600
V4_PRE_FALL_DELAY = 1000
# =========================================================

# ---------------------------------------------------------
# Базовый класс для бота (минимакс с альфа-бета отсечением)
# ---------------------------------------------------------
class Bot:
    def __init__(self, game, max_depth=3):
        self.game = game
        self.max_depth = max_depth

    def get_best_move(self):
        # Получаем все возможные ходы
        moves = self.game.get_possible_moves(PLAYER_O)
        if not moves:
            return None

        # Быстрая эвристическая оценка каждого хода
        scored_moves = []
        for move in moves:
            game_copy = self.game.copy()
            game_copy.make_move(move)
            # Оцениваем позицию с точки зрения текущего игрока (O)
            score = self._evaluate(game_copy, PLAYER_O)
            scored_moves.append((score, move))

        # Сортируем по убыванию оценки
        scored_moves.sort(reverse=True, key=lambda x: x[0])

        # Ограничиваем количество рассматриваемых ходов (для скорости)
        if len(scored_moves) > 20:
            scored_moves = scored_moves[:20]

        # Теперь перебираем в этом порядке
        best_score = -float('inf')
        best_move = None
        alpha = -float('inf')
        beta = float('inf')
        for _, move in scored_moves:
            game_copy = self.game.copy()
            game_copy.make_move(move)
            score = self._alphabeta(game_copy, self.max_depth - 1, alpha, beta, False)
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)
        return best_move

    def _alphabeta(self, game, depth, alpha, beta, is_maximizing):
        if depth == 0 or game.game_over:
            return self._evaluate(game, PLAYER_O)

        if is_maximizing:
            value = -float('inf')
            # Получаем ходы и сортируем их (для улучшения отсечения)
            moves = game.get_possible_moves(PLAYER_O)
            # Можно также применить эвристику, но для глубины >0 это дорого
            for move in moves:
                game_copy = game.copy()
                game_copy.make_move(move)
                value = max(value, self._alphabeta(game_copy, depth - 1, alpha, beta, False))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            moves = game.get_possible_moves(PLAYER_X)
            for move in moves:
                game_copy = game.copy()
                game_copy.make_move(move)
                value = min(value, self._alphabeta(game_copy, depth - 1, alpha, beta, True))
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    def _evaluate(self, game, player):
        opponent = PLAYER_X if player == PLAYER_O else PLAYER_O
        size = game.size
        win_line = game.win_line
        # Веса для линий разной длины (эмпирические)
        weight = {1: 1, 2: 10, 3: 100, 4: 1000, 5: 10000}
        score = 0

        # Горизонтали
        for r in range(size):
            for c in range(size - win_line + 1):
                line = [game.board[r][c + i] for i in range(win_line)]
                score += self._line_score(line, player, opponent, weight)
        # Вертикали
        for c in range(size):
            for r in range(size - win_line + 1):
                line = [game.board[r + i][c] for i in range(win_line)]
                score += self._line_score(line, player, opponent, weight)
        # Главные диагонали
        for r in range(size - win_line + 1):
            for c in range(size - win_line + 1):
                line = [game.board[r + i][c + i] for i in range(win_line)]
                score += self._line_score(line, player, opponent, weight)
        # Побочные диагонали
        for r in range(size - win_line + 1):
            for c in range(win_line - 1, size):
                line = [game.board[r + i][c - i] for i in range(win_line)]
                score += self._line_score(line, player, opponent, weight)

        return score

    def _line_score(self, line, player, opponent, weight):
        cnt_player = line.count(player)
        cnt_opp = line.count(opponent)
        if cnt_opp == 0:
            return weight.get(cnt_player, 0)
        elif cnt_player == 0:
            return -weight.get(cnt_opp, 0)
        else:
            return 0

# ---------------------------------------------------------
# Версия 1: гравитация + анимация падения
# ---------------------------------------------------------
class GameV1:
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

        self.anim_active = False
        self.anim_col = 0
        self.anim_target_row = 0
        self.anim_player = PLAYER_X
        self.anim_start_time = 0
        self.anim_start_y = 0.0
        self.anim_end_y = 0.0
        self.anim_current_y = 0.0

    def _find_target_row(self, col):
        for row in range(self.size - 1, -1, -1):
            if self.board[row][col] == EMPTY:
                return row
        return None

    def start_animation(self, col):
        if self.game_over or self.anim_active:
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
        if not self.anim_active:
            return
        elapsed = current_time - self.anim_start_time
        if elapsed >= V1_ANIMATION_DURATION:
            self._finish_move()
        else:
            t = elapsed / V1_ANIMATION_DURATION
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
        self.anim_active = False

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
        if self.anim_active:
            return None
        x, y = pos
        if y >= WINDOW_HEIGHT - INFO_PANEL_HEIGHT:
            return None
        col = x // CELL_SIZE
        if 0 <= col < self.size:
            return col
        return None

    # Методы для бота
    def get_possible_moves(self, player):
        moves = []
        for col in range(self.size):
            if self._find_target_row(col) is not None:
                moves.append(col)
        return moves

    def make_move(self, move):
        col = move
        target_row = self._find_target_row(col)
        if target_row is None:
            return False
        self.board[target_row][col] = self.current_player
        self.moves_count += 1
        if self._check_win(target_row, col):
            self.game_over = True
            self.winner = self.current_player
        elif self.moves_count == self.size * self.size:
            self.game_over = True
        else:
            self.current_player = PLAYER_O if self.current_player == PLAYER_X else PLAYER_X
        return True

    def copy(self):
        new = GameV1(self.size, self.win_line)
        new.board = [row[:] for row in self.board]
        new.current_player = self.current_player
        new.game_over = self.game_over
        new.winner = self.winner
        new.moves_count = self.moves_count
        return new

def draw_board_v1(screen, game):
    screen.fill(WHITE)
    for i in range(game.size + 1):
        pygame.draw.line(screen, BLACK, (0, i * CELL_SIZE), (game.size * CELL_SIZE, i * CELL_SIZE), 2)
        pygame.draw.line(screen, BLACK, (i * CELL_SIZE, 0), (i * CELL_SIZE, game.size * CELL_SIZE), 2)

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

def run_v1():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(f"[V1] Гравитация {SIZE}x{SIZE} (победа - {WIN_LINE} в ряд)")
    clock = pygame.time.Clock()
    game = GameV1(SIZE, WIN_LINE)
    bot = Bot(game, max_depth=3)  # глубина 3 допустима, так как ходов мало
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

        # Ход бота (нолики)
        if not game.game_over and game.current_player == PLAYER_O and not game.anim_active:
            move = bot.get_best_move()
            if move is not None:
                game.start_animation(move)

        game.update_animation(current_time)
        draw_board_v1(screen, game)
        clock.tick(60)

# ---------------------------------------------------------
# Версия 2: сдвиг нечётных столбцов вниз
# ---------------------------------------------------------
class GameV2:
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

    def make_move(self, move):
        row, col = move
        if self.game_over:
            return False
        if not (0 <= row < self.size and 0 <= col < self.size):
            return False
        if self.board[row][col] != EMPTY:
            return False

        self.board[row][col] = self.current_player
        self.moves_count += 1

        if self.check_win(row, col):
            self.game_over = True
            self.winner = self.current_player
            return True

        if self.moves_count == self.size * self.size:
            self.game_over = True
            self.winner = None
            return True

        self.current_player = PLAYER_O if self.current_player == PLAYER_X else PLAYER_X
        self._shift_columns()
        self._check_game_over_after_shift()
        return True

    def _shift_columns(self):
        for col in range(1, self.size, 2):
            bottom = self.board[self.size - 1][col]
            for row in range(self.size - 1, 0, -1):
                self.board[row][col] = self.board[row - 1][col]
            self.board[0][col] = bottom

    def _check_game_over_after_shift(self):
        winner = self._check_winner_on_board()
        if winner is not None:
            self.game_over = True
            self.winner = winner
            return
        if self.moves_count == self.size * self.size:
            self.game_over = True
            self.winner = None

    def _check_winner_on_board(self):
        for r in range(self.size):
            for c in range(self.size):
                player = self.board[r][c]
                if player != EMPTY:
                    if self.check_win(r, c):
                        return player
        return None

    def check_win(self, row, col):
        player = self.board[row][col]
        if player == EMPTY:
            return False
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

    def get_cell_from_pos(self, pos):
        x, y = pos
        if y >= WINDOW_HEIGHT - INFO_PANEL_HEIGHT:
            return None
        col = x // CELL_SIZE
        row = y // CELL_SIZE
        if 0 <= row < self.size and 0 <= col < self.size:
            return row, col
        return None

    # Методы для бота
    def get_possible_moves(self, player):
        moves = []
        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] == EMPTY:
                    moves.append((r, c))
        return moves

    def copy(self):
        new = GameV2(self.size, self.win_line)
        new.board = [row[:] for row in self.board]
        new.current_player = self.current_player
        new.game_over = self.game_over
        new.winner = self.winner
        new.moves_count = self.moves_count
        return new

def draw_board_v2(screen, game):
    screen.fill(WHITE)
    for i in range(game.size + 1):
        pygame.draw.line(screen, BLACK, (0, i * CELL_SIZE), (game.size * CELL_SIZE, i * CELL_SIZE), 2)
        pygame.draw.line(screen, BLACK, (i * CELL_SIZE, 0), (i * CELL_SIZE, game.size * CELL_SIZE), 2)

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

def run_v2():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(f"[V2] Сдвиг столбцов {SIZE}x{SIZE} (победа - {WIN_LINE} в ряд)")
    clock = pygame.time.Clock()
    game = GameV2(SIZE, WIN_LINE)
    bot = Bot(game, max_depth=2)  # глубина 2 для скорости
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
                    game.make_move((row, col))
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                game.reset()

        # Ход бота (нолики)
        if not game.game_over and game.current_player == PLAYER_O:
            move = bot.get_best_move()
            if move is not None:
                game.make_move(move)

        draw_board_v2(screen, game)
        clock.tick(30)

# ---------------------------------------------------------
# Версия 3: сдвиг строк (чередование чётности и направления)
# ---------------------------------------------------------
class GameV3:
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
        self.shift_direction = 1
        self.shift_parity = 0

    def make_move(self, move):
        row, col = move
        if self.game_over:
            return False
        if not (0 <= row < self.size and 0 <= col < self.size):
            return False
        if self.board[row][col] != EMPTY:
            return False

        self.board[row][col] = self.current_player
        self.moves_count += 1

        if self.check_win(row, col):
            self.game_over = True
            self.winner = self.current_player
            return True

        if self.moves_count == self.size * self.size:
            self.game_over = True
            self.winner = None
            return True

        self.current_player = PLAYER_O if self.current_player == PLAYER_X else PLAYER_X
        self._shift_rows(self.shift_parity, self.shift_direction)
        self.shift_direction *= -1
        self.shift_parity = 1 - self.shift_parity
        self._check_game_over_after_shift()
        return True

    def _shift_rows(self, parity, direction):
        if parity == 0:
            rows_to_shift = range(1, self.size, 2)
        else:
            rows_to_shift = range(0, self.size, 2)

        if direction == 1:  # вправо
            for row in rows_to_shift:
                last = self.board[row][self.size - 1]
                for col in range(self.size - 1, 0, -1):
                    self.board[row][col] = self.board[row][col - 1]
                self.board[row][0] = last
        else:  # влево
            for row in rows_to_shift:
                first = self.board[row][0]
                for col in range(self.size - 1):
                    self.board[row][col] = self.board[row][col + 1]
                self.board[row][self.size - 1] = first

    def _check_game_over_after_shift(self):
        winner = self._check_winner_on_board()
        if winner is not None:
            self.game_over = True
            self.winner = winner
            return
        if self.moves_count == self.size * self.size:
            self.game_over = True
            self.winner = None

    def _check_winner_on_board(self):
        for r in range(self.size):
            for c in range(self.size):
                player = self.board[r][c]
                if player != EMPTY:
                    if self.check_win(r, c):
                        return player
        return None

    def check_win(self, row, col):
        player = self.board[row][col]
        if player == EMPTY:
            return False
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

    def get_cell_from_pos(self, pos):
        x, y = pos
        if y >= WINDOW_HEIGHT - INFO_PANEL_HEIGHT:
            return None
        col = x // CELL_SIZE
        row = y // CELL_SIZE
        if 0 <= row < self.size and 0 <= col < self.size:
            return row, col
        return None

    # Методы для бота
    def get_possible_moves(self, player):
        moves = []
        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] == EMPTY:
                    moves.append((r, c))
        return moves

    def copy(self):
        new = GameV3(self.size, self.win_line)
        new.board = [row[:] for row in self.board]
        new.current_player = self.current_player
        new.game_over = self.game_over
        new.winner = self.winner
        new.moves_count = self.moves_count
        new.shift_direction = self.shift_direction
        new.shift_parity = self.shift_parity
        return new

def draw_board_v3(screen, game):
    screen.fill(WHITE)
    for i in range(game.size + 1):
        pygame.draw.line(screen, BLACK, (0, i * CELL_SIZE), (game.size * CELL_SIZE, i * CELL_SIZE), 2)
        pygame.draw.line(screen, BLACK, (i * CELL_SIZE, 0), (i * CELL_SIZE, game.size * CELL_SIZE), 2)

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

def run_v3():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(f"[V3] Сдвиг строк {SIZE}x{SIZE} (победа - {WIN_LINE} в ряд)")
    clock = pygame.time.Clock()
    game = GameV3(SIZE, WIN_LINE)
    bot = Bot(game, max_depth=2)  # глубина 2
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
                    game.make_move((row, col))
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                game.reset()

        # Ход бота (нолики)
        if not game.game_over and game.current_player == PLAYER_O:
            move = bot.get_best_move()
            if move is not None:
                game.make_move(move)

        draw_board_v3(screen, game)
        clock.tick(30)

# ---------------------------------------------------------
# Версия 4: гравитация + поворот доски каждые 3 хода + анимация падения
# ---------------------------------------------------------
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

class GameV4:
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
        self.marker_pos = (self.size - 1, self.size - 1)

        self.anim_active = False
        self.anim_col = 0
        self.anim_target_row = 0
        self.anim_player = PLAYER_X
        self.anim_start_time = 0
        self.anim_start_y = 0.0
        self.anim_end_y = 0.0
        self.anim_current_y = 0.0

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
            if elapsed >= V4_PRE_FALL_DELAY:
                self._start_fall_after_delay()
        elif self.rotation_fall_active:
            elapsed = current_time - self.rotation_fall_start_time
            progress = elapsed / V4_ROTATION_FALL_DURATION
            if progress >= 1.0:
                self._finish_rotation_fall()
            else:
                for piece in self.falling_pieces:
                    piece.update(progress)
        elif self.anim_active:
            elapsed = current_time - self.anim_start_time
            if elapsed >= V4_ANIMATION_DURATION:
                self._finish_move()
            else:
                t = elapsed / V4_ANIMATION_DURATION
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
        rotated_board = [[EMPTY] * self.size for _ in range(self.size)]
        for i in range(self.size):
            for j in range(self.size):
                rotated_board[j][self.size - 1 - i] = self.board[i][j]
        self.board = rotated_board

        r, c = self.marker_pos
        self.marker_pos = (c, self.size - 1 - r)

        self.pre_fall_delay_active = True
        self.pre_fall_delay_start_time = pygame.time.get_ticks()

    def _start_fall_after_delay(self):
        self.pre_fall_delay_active = False
        self.post_rotation_board = self._apply_gravity_to_board(self.board)

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

    # Методы для бота
    def get_possible_moves(self, player):
        moves = []
        for col in range(self.size):
            if self._find_target_row(col) is not None:
                moves.append(col)
        return moves

    def make_move(self, move):
        col = move
        target_row = self._find_target_row(col)
        if target_row is None:
            return False
        self.board[target_row][col] = self.current_player
        self.moves_count += 1
        if self._check_win(target_row, col):
            self.game_over = True
            self.winner = self.current_player
            return True
        if self.moves_count == self.size * self.size:
            self.game_over = True
            return True
        # Поворот и гравитация
        if not self.game_over and self.moves_count % 3 == 0:
            # Поворот
            rotated = [[EMPTY]*self.size for _ in range(self.size)]
            for i in range(self.size):
                for j in range(self.size):
                    rotated[j][self.size-1-i] = self.board[i][j]
            self.board = rotated
            # Гравитация
            self.board = self._apply_gravity_to_board(self.board)
            # Проверка победы после
            winner = self._check_win_any()
            if winner is not None:
                self.game_over = True
                self.winner = winner
                return True
            if self._is_board_full():
                self.game_over = True
                self.winner = None
                return True
        # Смена игрока
        if not self.game_over:
            self.current_player = PLAYER_O if self.current_player == PLAYER_X else PLAYER_X
        return True

    def copy(self):
        new = GameV4(self.size, self.win_line)
        new.board = [row[:] for row in self.board]
        new.current_player = self.current_player
        new.game_over = self.game_over
        new.winner = self.winner
        new.moves_count = self.moves_count
        new.marker_pos = self.marker_pos
        return new

def draw_board_v4(screen, game):
    screen.fill(WHITE)
    for i in range(game.size + 1):
        pygame.draw.line(screen, BLACK, (0, i * CELL_SIZE), (game.size * CELL_SIZE, i * CELL_SIZE), 2)
        pygame.draw.line(screen, BLACK, (i * CELL_SIZE, 0), (i * CELL_SIZE, game.size * CELL_SIZE), 2)

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

    if not game.game_over:
        marker_row, marker_col = game.marker_pos
        rect_size = 12
        margin = 2
        if marker_row == 0 and marker_col == 0:
            x = marker_col * CELL_SIZE + margin
            y = marker_row * CELL_SIZE + margin
        elif marker_row == 0 and marker_col == game.size - 1:
            x = marker_col * CELL_SIZE + CELL_SIZE - rect_size - margin
            y = marker_row * CELL_SIZE + margin
        elif marker_row == game.size - 1 and marker_col == 0:
            x = marker_col * CELL_SIZE + margin
            y = marker_row * CELL_SIZE + CELL_SIZE - rect_size - margin
        elif marker_row == game.size - 1 and marker_col == game.size - 1:
            x = marker_col * CELL_SIZE + CELL_SIZE - rect_size - margin
            y = marker_row * CELL_SIZE + CELL_SIZE - rect_size - margin
        else:
            x = marker_col * CELL_SIZE + CELL_SIZE - rect_size - margin
            y = marker_row * CELL_SIZE + CELL_SIZE - rect_size - margin
        pygame.draw.rect(screen, RED, (x, y, rect_size, rect_size))

    pygame.display.flip()

def run_v4():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(f"[V4] Гравитация + поворот {SIZE}x{SIZE} (победа - {WIN_LINE} в ряд)")
    clock = pygame.time.Clock()
    game = GameV4(SIZE, WIN_LINE)
    bot = Bot(game, max_depth=3)  # ходов мало (колонки)
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

        # Ход бота (нолики)
        if not game.game_over and game.current_player == PLAYER_O and not game.anim_active and not game.rotation_fall_active and not game.pre_fall_delay_active:
            move = bot.get_best_move()
            if move is not None:
                game.start_animation(move)

        game.update_animation(current_time)
        draw_board_v4(screen, game)
        clock.tick(60)

# ---------------------------------------------------------
# Версия 5: случайное превращение X <-> O каждый 3-й ход
# ---------------------------------------------------------
class GameV5:
    def __init__(self, size, win_line, deterministic=False):
        self.size = size
        self.win_line = win_line
        self.deterministic = deterministic
        self.reset()

    def reset(self):
        self.board = [[EMPTY for _ in range(self.size)] for _ in range(self.size)]
        self.current_player = PLAYER_X
        self.game_over = False
        self.winner = None
        self.moves_count = 0

    def make_move(self, move):
        row, col = move
        if self.game_over:
            return False
        if not (0 <= row < self.size and 0 <= col < self.size):
            return False
        if self.board[row][col] != EMPTY:
            return False

        self.board[row][col] = self.current_player
        self.moves_count += 1

        if self.check_win(row, col):
            self.game_over = True
            self.winner = self.current_player
            return True

        if self.moves_count == self.size * self.size:
            self.game_over = True
            self.winner = None
            return True

        self.current_player = PLAYER_O if self.current_player == PLAYER_X else PLAYER_X

        if not self.game_over and self.moves_count % 3 == 0:
            if self.deterministic:
                self._transform_deterministic()
            else:
                self._transform_random()

        return True

    def _transform_random(self):
        x_positions = []
        o_positions = []
        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] == PLAYER_X:
                    x_positions.append((r, c))
                elif self.board[r][c] == PLAYER_O:
                    o_positions.append((r, c))

        changed = False
        if x_positions:
            rx, cx = random.choice(x_positions)
            self.board[rx][cx] = PLAYER_O
            changed = True
        if o_positions:
            ro, co = random.choice(o_positions)
            self.board[ro][co] = PLAYER_X
            changed = True

        if changed:
            if self.check_win_any(PLAYER_X):
                self.game_over = True
                self.winner = PLAYER_X
            elif self.check_win_any(PLAYER_O):
                self.game_over = True
                self.winner = PLAYER_O

    def _transform_deterministic(self):
        # Превращаем первые найденные X и O (по порядку обхода)
        x_pos = None
        o_pos = None
        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] == PLAYER_X and x_pos is None:
                    x_pos = (r, c)
                elif self.board[r][c] == PLAYER_O and o_pos is None:
                    o_pos = (r, c)
        changed = False
        if x_pos:
            r, c = x_pos
            self.board[r][c] = PLAYER_O
            changed = True
        if o_pos:
            r, c = o_pos
            self.board[r][c] = PLAYER_X
            changed = True
        if changed:
            if self.check_win_any(PLAYER_X):
                self.game_over = True
                self.winner = PLAYER_X
            elif self.check_win_any(PLAYER_O):
                self.game_over = True
                self.winner = PLAYER_O

    def check_win(self, row, col):
        player = self.board[row][col]
        if player == EMPTY:
            return False
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

    def check_win_any(self, player):
        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] == player:
                    if self.check_win(r, c):
                        return True
        return False

    def get_cell_from_pos(self, pos):
        x, y = pos
        if y >= WINDOW_HEIGHT - INFO_PANEL_HEIGHT:
            return None
        col = x // CELL_SIZE
        row = y // CELL_SIZE
        if 0 <= row < self.size and 0 <= col < self.size:
            return row, col
        return None

    # Методы для бота
    def get_possible_moves(self, player):
        moves = []
        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] == EMPTY:
                    moves.append((r, c))
        return moves

    def copy(self):
        new = GameV5(self.size, self.win_line, self.deterministic)
        new.board = [row[:] for row in self.board]
        new.current_player = self.current_player
        new.game_over = self.game_over
        new.winner = self.winner
        new.moves_count = self.moves_count
        return new

def draw_board_v5(screen, game):
    screen.fill(WHITE)
    for i in range(game.size + 1):
        pygame.draw.line(screen, BLACK, (0, i * CELL_SIZE), (game.size * CELL_SIZE, i * CELL_SIZE), 2)
        pygame.draw.line(screen, BLACK, (i * CELL_SIZE, 0), (i * CELL_SIZE, game.size * CELL_SIZE), 2)

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

def run_v5():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(f"[V5] Превращение {SIZE}x{SIZE} (победа - {WIN_LINE} в ряд)")
    clock = pygame.time.Clock()
    # Для игры с человеком превращения случайны, для бота детерминированы
    game = GameV5(SIZE, WIN_LINE, deterministic=False)
    bot = Bot(GameV5(SIZE, WIN_LINE, deterministic=True), max_depth=2)  # глубина 2
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
                    game.make_move((row, col))
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                game.reset()

        # Ход бота (нолики)
        if not game.game_over and game.current_player == PLAYER_O:
            # Для бота используем копию игры с детерминированными превращениями
            temp_game = game.copy()
            temp_game.deterministic = True
            bot.game = temp_game
            move = bot.get_best_move()
            if move is not None:
                game.make_move(move)

        draw_board_v5(screen, game)
        clock.tick(30)

# ==================== ЕДИНСТВЕННАЯ ФУНКЦИЯ ДЛЯ ЗАПУСКА ====================
def cross_zero(version=None):
    """
    Запускает одну из пяти версий игры.
    Если version не указана (или None), выбирается случайная версия от 1 до 5.
    """
    if version is None:
        version = random.randint(1, 5)
    #print(f"Запускается версия {version}")
    if version == 1:
        run_v1()
    elif version == 2:
        run_v2()
    elif version == 3:
        run_v3()
    elif version == 4:
        run_v4()
    else:
        run_v5()
