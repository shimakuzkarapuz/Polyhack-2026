import pygame
import random
import sys

# Инициализация Pygame
pygame.init()

# Размеры
TILE_SIZE = 40               # каждая клетка 40x40
COLS = 20                    # ширина в клетках
ROWS = 15                    # высота в клетках
WALL_COUNT = 40              # количество стен

SCREEN_WIDTH = COLS * TILE_SIZE    # 800
SCREEN_HEIGHT = ROWS * TILE_SIZE   # 600

# Цвета для заглушек (если нет изображений)
FLOOR_COLOR = (50, 150, 50)   # зелёный
WALL_COLOR = (100, 100, 100)  # серый

def load_image(filename, default_color, size=(TILE_SIZE, TILE_SIZE)):
    """Загружает изображение, масштабирует до size. При ошибке создаёт цветную поверхность."""
    try:
        image = pygame.image.load(filename)
        return pygame.transform.scale(image, size)
    except pygame.error:
        surf = pygame.Surface(size)
        surf.fill(default_color)
        return surf

# Загрузка текстур (замените на свои файлы или оставьте цветные заглушки)
floor_img = load_image('sprites/floor.png', FLOOR_COLOR)
wall_img = load_image('sprites/wall.png', WALL_COLOR)

# Настройка окна
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Карта: пол и стены (40x40)")

def generate_map():
    """Создаёт карту с ровно WALL_COUNT стенами, остальное пол."""
    all_positions = [(r, c) for r in range(ROWS) for c in range(COLS)]
    wall_positions = random.sample(all_positions, WALL_COUNT)
    game_map = [[False] * COLS for _ in range(ROWS)]
    for r, c in wall_positions:
        game_map[r][c] = True
    return game_map

# Первая генерация
game_map = generate_map()

# Основной цикл
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:   # пробел для новой карты
                game_map = generate_map()
            elif event.key == pygame.K_ESCAPE:
                running = False

    # Отрисовка всех клеток
    for r in range(ROWS):
        for c in range(COLS):
            x = c * TILE_SIZE
            y = r * TILE_SIZE
            if game_map[r][c]:
                screen.blit(wall_img, (x, y))
            else:
                screen.blit(floor_img, (x, y))

    pygame.display.flip()
    clock.tick(30)   # 30 FPS

pygame.quit()
sys.exit()
