import pygame
import math
import random
import os

# Initialize Pygame
pygame.init()
pygame.mixer.init()  # For sound later

# ==================== CONSTANTS ====================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 40
FPS = 60
MOVE_SPEED = 4  # Pixels per frame (smooth movement)

# Colors (fallback when no sprites)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
DARK_RED = (150, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
GOLD = (255, 215, 0)
PURPLE = (150, 0, 255)
CYAN = (0, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (30, 30, 30)
BROWN = (139, 69, 19)
ORANGE = (255, 165, 0)
PINK = (255, 192, 203)
SECRET_PURPLE = (50, 40, 60)  # For secret passages

# Tile types
FLOOR = 0
WALL = 1
SECRET_PASSAGE = 2  # New! Looks like wall but is walkable

# Entity types
GOLD = 2
MONSTER = 3
STATION = 4
KEY = 5
DOOR = 6

# Game states
EXPLORE = 0
TTT_GAME = 1
MINESWEEP_GAME = 2
SNAKE_GAME = 3
MENU = 4
GAME_OVER = 5
VICTORY = 6

# ==================== MAZE GENERATION FUNCTIONS ====================

def generate_pacman_style_dungeon(width, height, num_rooms=5):
    """Generate dungeon with multiple rooms and secret passages"""
    
    # Initialize with all walls
    dungeon = [[WALL for _ in range(width)] for _ in range(height)]
    
    # Generate rooms (each at least 3x3)
    rooms = []
    for _ in range(num_rooms):
        room_attempts = 0
        while room_attempts < 100:
            room_w = random.randint(4, 8)
            room_h = random.randint(4, 8)
            room_x = random.randint(2, width - room_w - 2)
            room_y = random.randint(2, height - room_h - 2)
            
            # Check if room overlaps with existing rooms
            overlap = False
            for rx, ry, rw, rh in rooms:
                if (room_x - 2 < rx + rw and room_x + room_w + 2 > rx and
                    room_y - 2 < ry + rh and room_y + room_h + 2 > ry):
                    overlap = True
                    break
            
            if not overlap:
                # Carve the room
                for y in range(room_y, room_y + room_h):
                    for x in range(room_x, room_x + room_w):
                        dungeon[y][x] = FLOOR
                rooms.append((room_x, room_y, room_w, room_h))
                break
            room_attempts += 1
    
    # Connect rooms with corridors
    for i in range(len(rooms) - 1):
        x1 = rooms[i][0] + rooms[i][2] // 2
        y1 = rooms[i][1] + rooms[i][3] // 2
        x2 = rooms[i+1][0] + rooms[i+1][2] // 2
        y2 = rooms[i+1][1] + rooms[i+1][3] // 2
        
        carve_corridor(dungeon, x1, y1, x2, y2)
    
    # Add secret passages (hidden walkable walls)
    add_secret_passages(dungeon, rooms)
    
    # Ensure all rooms are connected
    ensure_connectivity(dungeon)
    
    return dungeon, rooms

def carve_corridor(dungeon, x1, y1, x2, y2):
    """Carve an L-shaped corridor between points"""
    if random.random() < 0.3:
        # Create a detour (secret passage)
        mid_x = random.randint(min(x1, x2), max(x1, x2))
        mid_y = random.randint(min(y1, y2), max(y1, y2))
        
        x, y = x1, y1
        while x != mid_x:
            dungeon[y][x] = FLOOR
            x += 1 if mid_x > x else -1
        while y != mid_y:
            dungeon[y][x] = FLOOR
            y += 1 if mid_y > y else -1
        
        while x != x2:
            dungeon[y][x] = FLOOR
            x += 1 if x2 > x else -1
        while y != y2:
            dungeon[y][x] = FLOOR
            y += 1 if y2 > y else -1
    else:
        # Normal L-shaped corridor
        x, y = x1, y1
        if random.choice([True, False]):
            while x != x2:
                dungeon[y][x] = FLOOR
                x += 1 if x2 > x else -1
            while y != y2:
                dungeon[y][x] = FLOOR
                y += 1 if y2 > y else -1
        else:
            while y != y2:
                dungeon[y][x] = FLOOR
                y += 1 if y2 > y else -1
            while x != x2:
                dungeon[y][x] = FLOOR
                x += 1 if x2 > x else -1

def add_secret_passages(dungeon, rooms):
    """Add hidden passages that look like walls but are walkable"""
    if len(rooms) < 2:
        return
    
    height = len(dungeon)
    width = len(dungeon[0])
    
    # Add 2-4 secret passages
    num_passages = random.randint(2, 4)
    
    for _ in range(num_passages):
        # Pick two random rooms
        r1, r2 = random.sample(range(len(rooms)), 2)
        
        # Get room centers
        x1 = rooms[r1][0] + rooms[r1][2] // 2
        y1 = rooms[r1][1] + rooms[r1][3] // 2
        x2 = rooms[r2][0] + rooms[r2][2] // 2
        y2 = rooms[r2][1] + rooms[r2][3] // 2
        
        # Carve a secret passage that looks like walls
        x, y = x1, y1
        steps = random.randint(15, 25)
        
        for _ in range(steps):
            # Random walk
            if random.random() < 0.4:
                x += random.choice([-1, 1])
            else:
                y += random.choice([-1, 1])
            
            # Keep in bounds
            x = max(1, min(width-2, x))
            y = max(1, min(height-2, y))
            
            # Mark as SECRET_PASSAGE (looks like wall but walkable)
            if dungeon[y][x] == WALL:
                dungeon[y][x] = SECRET_PASSAGE
    
    # Also add single-tile hideouts in corners of rooms
    for rx, ry, rw, rh in rooms:
        # Add 1-2 hiding spots in each room
        for _ in range(random.randint(1, 2)):
            # Find a corner of the room
            corner_x = rx + random.choice([0, rw-1])
            corner_y = ry + random.choice([0, rh-1])
            
            # Check adjacent walls
            for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
                check_x = corner_x + dx
                check_y = corner_y + dy
                
                if (0 <= check_x < width and 0 <= check_y < height and
                    dungeon[check_y][check_x] == WALL):
                    # Turn this wall into a secret hideout
                    dungeon[check_y][check_x] = SECRET_PASSAGE
                    break

def ensure_connectivity(dungeon):
    """Make sure all floor tiles are connected"""
    height = len(dungeon)
    width = len(dungeon[0])
    
    # Find first floor tile
    start = None
    for y in range(height):
        for x in range(width):
            if dungeon[y][x] == FLOOR:
                start = (x, y)
                break
        if start:
            break
    
    if not start:
        return
    
    # Flood fill to find all connected floor tiles
    visited = [[False for _ in range(width)] for _ in range(height)]
    queue = [start]
    visited[start[1]][start[0]] = True
    
    while queue:
        x, y = queue.pop(0)
        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < width and 0 <= ny < height and 
                dungeon[ny][nx] == FLOOR and not visited[ny][nx]):
                visited[ny][nx] = True
                queue.append((nx, ny))
    
    # Connect any disconnected floor tiles
    for y in range(height):
        for x in range(width):
            if dungeon[y][x] == FLOOR and not visited[y][x]:
                min_dist = float('inf')
                target = None
                for ty in range(height):
                    for tx in range(width):
                        if visited[ty][tx]:
                            dist = abs(tx - x) + abs(ty - y)
                            if dist < min_dist:
                                min_dist = dist
                                target = (tx, ty)
                
                if target:
                    carve_corridor(dungeon, x, y, target[0], target[1])

# ==================== SPRITE LOADER ====================
BASE_PATH = os.path.dirname(__file__)
SPRITE_PATH = os.path.join(BASE_PATH, 'sprites')

class SpriteLoader:
    def __init__(self):
        self.sprites = {}
        self.load_sprites()
    
    def load_sprites(self):
        """Load all sprites from the sprites folder"""
        sprite_files = {
            'player': 'Player (2).png',
            'monster': 'zero_monstr.png',
            'gold': 'gold.png',
            'station': 'gate_o_r.png',
            'key': 'key.png',
            'door': 'door.png',
            'wall': 'wall.png',
            'floor': 'floor.png',
            'heart': 'heart.png'
        }
        
        for name, filename in sprite_files.items():
            try:
                path = os.path.join(SPRITE_PATH, filename)
                
                if os.path.exists(path):
                    image = pygame.image.load(path).convert_alpha()
                    image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
                    self.sprites[name] = image
                    print(f"✓ Loaded {name} sprite")
                else:
                    print(f"✗ {filename} not found, will use fallback")
                    self.sprites[name] = None
                    
            except Exception as e:
                print(f"Error loading {name}: {e}")
                self.sprites[name] = None
    
    def get(self, name):
        """Get a sprite by name"""
        return self.sprites.get(name)

def create_fallback_sprites():
    """Create simple colored sprites if image files don't exist"""
    sprites = {}
    
    # Player (Pac-Man style)
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    pygame.draw.circle(surf, (255, 255, 0), (20, 20), 15)
    pygame.draw.polygon(surf, BLACK, [(20, 20), (35, 10), (35, 30)])
    sprites['player'] = surf
    
    # Monster
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    color = random.choice([RED, PINK, CYAN, ORANGE])
    pygame.draw.ellipse(surf, color, (5, 5, TILE_SIZE-10, TILE_SIZE-10))
    pygame.draw.circle(surf, WHITE, (12, 15), 4)
    pygame.draw.circle(surf, WHITE, (28, 15), 4)
    pygame.draw.circle(surf, BLACK, (13, 16), 2)
    pygame.draw.circle(surf, BLACK, (29, 16), 2)
    sprites['monster'] = surf
    
    # Gold
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    pygame.draw.circle(surf, GOLD, (20, 20), 5)
    sprites['gold'] = surf
    
    # Station
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill((150, 150, 150))
    pygame.draw.rect(surf, (100, 100, 100), (5, 5, TILE_SIZE-10, TILE_SIZE-10))
    pygame.draw.rect(surf, CYAN, (10, 8, TILE_SIZE-20, TILE_SIZE-16))
    sprites['station'] = surf
    
    # Key
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    pygame.draw.circle(surf, GOLD, (25, 20), 6)
    pygame.draw.rect(surf, GOLD, (12, 17, 15, 6))
    sprites['key'] = surf
    
    # Door
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(BROWN)
    pygame.draw.circle(surf, GOLD, (30, 20), 3)
    sprites['door'] = surf
    
    # Wall
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill((100, 100, 100))
    for i in range(0, TILE_SIZE, 10):
        pygame.draw.line(surf, (120, 120, 120), (0, i), (TILE_SIZE, i), 1)
    sprites['wall'] = surf
    
    # Floor
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill((30, 30, 30))
    sprites['floor'] = surf
    
    # Heart
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    pygame.draw.polygon(surf, RED, [(20, 10), (10, 20), (20, 30), (30, 20)])
    sprites['heart'] = surf
    
    return sprites

# ==================== ENTITY CLASSES ====================
class Entity:
    def __init__(self, x, y, entity_type):
        self.x = x
        self.y = y
        self.pixel_x = x * TILE_SIZE
        self.pixel_y = y * TILE_SIZE
        self.type = entity_type
        self.collected = False
        self.defeated = False
        
    def draw(self, screen, offset_x, offset_y, visible, sprites):
        if not visible or self.collected or self.defeated:
            return
            
        screen_x = self.pixel_x + offset_x
        screen_y = self.pixel_y + offset_y
        
        sprite_map = {
            GOLD: 'gold',
            MONSTER: 'monster',
            STATION: 'station',
            KEY: 'key',
            DOOR: 'door'
        }
        
        sprite_name = sprite_map.get(self.type)
        
        if sprite_name and sprites and sprites.get(sprite_name):
            screen.blit(sprites.get(sprite_name), (screen_x, screen_y))
        else:
            self.draw_fallback(screen, screen_x, screen_y)
    
    def draw_fallback(self, screen, x, y):
        rect = pygame.Rect(x + 5, y + 5, TILE_SIZE - 10, TILE_SIZE - 10)
        
        if self.type == GOLD:
            pygame.draw.circle(screen, GOLD, rect.center, 5)
        elif self.type == MONSTER:
            pygame.draw.ellipse(screen, RED, rect)
            eye1 = (rect.x + 8, rect.y + 8)
            eye2 = (rect.x + rect.width - 8, rect.y + 8)
            pygame.draw.circle(screen, WHITE, eye1, 4)
            pygame.draw.circle(screen, WHITE, eye2, 4)
            pygame.draw.circle(screen, BLACK, (eye1[0] + 1, eye1[1] + 1), 2)
            pygame.draw.circle(screen, BLACK, (eye2[0] + 1, eye2[1] + 1), 2)
        elif self.type == STATION:
            pygame.draw.rect(screen, (150, 150, 150), rect)
            pygame.draw.rect(screen, (100, 100, 100), 
                           (rect.x + 5, rect.y + 5, rect.width - 10, rect.height - 10))
            pygame.draw.rect(screen, CYAN, 
                           (rect.x + 10, rect.y + 8, rect.width - 20, rect.height - 16))
        elif self.type == KEY:
            pygame.draw.rect(screen, GOLD, (rect.x, rect.y + rect.height//2, 15, 5))
            pygame.draw.circle(screen, GOLD, (rect.x + 18, rect.y + rect.height//2), 8)
        elif self.type == DOOR:
            pygame.draw.rect(screen, BROWN, rect)
            pygame.draw.circle(screen, GOLD, (rect.x + rect.width - 8, rect.y + rect.height//2), 4)

class Monster(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, MONSTER)
        # Smooth movement variables
        self.target_x = self.pixel_x
        self.target_y = self.pixel_y
        self.is_moving = False
        self.move_x = 0
        self.move_y = 0
        
        # AI
        self.move_pattern = random.choice(['patrol', 'random', 'chase'])
        self.direction = random.choice([(0,1), (1,0), (0,-1), (-1,0)])
        self.move_timer = 0
        self.move_delay = random.randint(20, 30)
        self.detection_range = 4
        self.chase_range = 6
        self.color = random.choice([RED, PINK, CYAN, ORANGE])
        self.stuck_counter = 0
        self.last_direction = None
        
    def update(self, dungeon, player_x, player_y):
        if self.defeated:
            return
        
        # Handle smooth movement
        if self.is_moving:
            if abs(self.pixel_x - self.target_x) > MOVE_SPEED:
                self.pixel_x += self.move_x
            else:
                self.pixel_x = self.target_x
                
            if abs(self.pixel_y - self.target_y) > MOVE_SPEED:
                self.pixel_y += self.move_y
            else:
                self.pixel_y = self.target_y
            
            if self.pixel_x == self.target_x and self.pixel_y == self.target_y:
                self.is_moving = False
                self.move_x = 0
                self.move_y = 0
        
        # Decide next move
        if not self.is_moving and self.move_timer <= 0:
            distance = math.sqrt((self.x - player_x)**2 + (self.y - player_y)**2)
            
            should_move = False
            target_dx = 0
            target_dy = 0
            
            if distance < self.detection_range:
                if random.random() < 0.6:
                    dx = 1 if player_x > self.x else -1 if player_x < self.x else 0
                    dy = 1 if player_y > self.y else -1 if player_y < self.y else 0
                    
                    if dx != 0 or dy != 0:
                        should_move = True
                        target_dx = dx
                        target_dy = dy
            
            elif distance < self.chase_range and self.move_pattern == 'chase':
                if random.random() < 0.3:
                    dx = 1 if player_x > self.x else -1 if player_x < self.x else 0
                    dy = 1 if player_y > self.y else -1 if player_y < self.y else 0
                    
                    if dx != 0 or dy != 0:
                        should_move = True
                        target_dx = dx
                        target_dy = dy
            
            if not should_move:
                if self.move_pattern == 'patrol':
                    if random.random() < 0.7:
                        target_dx, target_dy = self.direction
                        if self.can_move_to(self.x + target_dx, self.y + target_dy, dungeon):
                            should_move = True
                        else:
                            self.direction = random.choice([(0,1), (1,0), (0,-1), (-1,0)])
                else:
                    target_dx, target_dy = random.choice([(0,1), (1,0), (0,-1), (-1,0), (0,0)])
                    if target_dx != 0 or target_dy != 0:
                        if self.can_move_to(self.x + target_dx, self.y + target_dy, dungeon):
                            should_move = True
            
            if should_move and (target_dx != 0 or target_dy != 0):
                new_x = self.x + target_dx
                new_y = self.y + target_dy
                
                if self.can_move_to(new_x, new_y, dungeon):
                    self.target_x = new_x * TILE_SIZE
                    self.target_y = new_y * TILE_SIZE
                    self.move_x = target_dx * MOVE_SPEED
                    self.move_y = target_dy * MOVE_SPEED
                    self.is_moving = True
                    
                    self.x = new_x
                    self.y = new_y
                    self.last_direction = (target_dx, target_dy)
                    self.stuck_counter = 0
            
            self.move_timer = random.randint(self.move_delay - 5, self.move_delay + 5)
        else:
            self.move_timer -= 1
        
        if random.random() < 0.005:
            self.move_pattern = random.choice(['patrol', 'random', 'chase'])
    
    def can_move_to(self, x, y, dungeon):
        if 0 <= x < dungeon.width and 0 <= y < dungeon.height:
            # Monsters can use secret passages too!
            if dungeon.layout[y][x] == FLOOR or dungeon.layout[y][x] == SECRET_PASSAGE:
                # Check for other monsters
                for entity in dungeon.entities:
                    if isinstance(entity, Monster) and not entity.defeated:
                        if entity.x == x and entity.y == y:
                            return False
                return True
        return False
    
    def draw(self, screen, offset_x, offset_y, visible, sprites):
        if not visible or self.defeated:
            return
        
        screen_x = self.pixel_x + offset_x
        screen_y = self.pixel_y + offset_y
        
        if sprites and sprites.get('monster'):
            screen.blit(sprites.get('monster'), (screen_x, screen_y))
        else:
            rect = pygame.Rect(screen_x + 5, screen_y + 5, TILE_SIZE - 10, TILE_SIZE - 10)
            pygame.draw.ellipse(screen, self.color, rect)
            
            eye1 = (rect.x + 8, rect.y + 8)
            eye2 = (rect.x + rect.width - 8, rect.y + 8)
            pygame.draw.circle(screen, WHITE, eye1, 4)
            pygame.draw.circle(screen, WHITE, eye2, 4)
            
            if self.is_moving and self.move_x != 0:
                dx = 1 if self.move_x > 0 else -1
                pygame.draw.circle(screen, BLACK, (eye1[0] + dx*2, eye1[1]), 2)
                pygame.draw.circle(screen, BLACK, (eye2[0] + dx*2, eye2[1]), 2)
            elif self.is_moving and self.move_y != 0:
                dy = 1 if self.move_y > 0 else -1
                pygame.draw.circle(screen, BLACK, (eye1[0], eye1[1] + dy*2), 2)
                pygame.draw.circle(screen, BLACK, (eye2[0], eye2[1] + dy*2), 2)
            else:
                pygame.draw.circle(screen, BLACK, (eye1[0] + 1, eye1[1] + 1), 2)
                pygame.draw.circle(screen, BLACK, (eye2[0] + 1, eye2[1] + 1), 2)

# ==================== DUNGEON CLASS ====================
class Dungeon:
    def __init__(self, layout):
        self.layout = layout
        self.height = len(layout)
        self.width = len(layout[0])
        self.visible = [[False for _ in range(self.width)] for _ in range(self.height)]
        self.discovered = [[False for _ in range(self.width)] for _ in range(self.height)]
        self.entities = []
        self.rooms = []
        
    def add_entity(self, entity):
        self.entities.append(entity)
        
    def remove_entity(self, entity):
        if entity in self.entities:
            self.entities.remove(entity)
    
    def get_entity_at(self, x, y):
        for entity in self.entities:
            if entity.x == x and entity.y == y:
                if entity.type == GOLD and not entity.collected:
                    return entity
                elif entity.type == MONSTER and not entity.defeated:
                    return entity
                elif entity.type == STATION:
                    return entity
                elif entity.type == KEY and not entity.collected:
                    return entity
                elif entity.type == DOOR:
                    return entity
        return None
    
    def count_remaining_gold(self):
        count = 0
        for entity in self.entities:
            if entity.type == GOLD and not entity.collected:
                count += 1
        return count
    
    def find_safe_start(self):
        floors = []
        for y in range(self.height):
            for x in range(self.width):
                if self.layout[y][x] == FLOOR:
                    floors.append((x, y))
        return random.choice(floors) if floors else (5, 5)
    
    def update_vision(self, player_pixel_x, player_pixel_y, vision_radius=6):
        player_grid_x = player_pixel_x // TILE_SIZE
        player_grid_y = player_pixel_y // TILE_SIZE
        
        for y in range(self.height):
            for x in range(self.width):
                self.visible[y][x] = False
        
        for dy in range(-vision_radius, vision_radius + 1):
            for dx in range(-vision_radius, vision_radius + 1):
                check_x = player_grid_x + dx
                check_y = player_grid_y + dy
                
                if 0 <= check_x < self.width and 0 <= check_y < self.height:
                    distance = math.sqrt(dx**2 + dy**2)
                    if distance <= vision_radius:
                        if self.has_line_of_sight(player_grid_x, player_grid_y, check_x, check_y):
                            self.visible[check_y][check_x] = True
                            self.discovered[check_y][check_x] = True
    
    def has_line_of_sight(self, x1, y1, x2, y2):
        """Secret passages block vision (they look like walls)"""
        points = self.get_line(x1, y1, x2, y2)
        for i in range(1, len(points) - 1):
            x, y = points[i]
            if self.layout[y][x] == WALL or self.layout[y][x] == SECRET_PASSAGE:
                return False
        return True
    
    def get_line(self, x1, y1, x2, y2):
        points = []
        dx = abs(x2 - x1)
        dy = -abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx + dy
        
        while True:
            points.append((x1, y1))
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x1 += sx
            if e2 <= dx:
                err += dx
                y1 += sy
        return points
    
    def draw(self, screen, player, offset_x=0, offset_y=0, sprites=None):
        # Draw tiles
        for y in range(self.height):
            for x in range(self.width):
                tile_rect = pygame.Rect(
                    x * TILE_SIZE + offset_x,
                    y * TILE_SIZE + offset_y,
                    TILE_SIZE, TILE_SIZE
                )
                
                if self.visible[y][x]:
                    if self.layout[y][x] == WALL:
                        if sprites and sprites.get('wall'):
                            screen.blit(sprites.get('wall'), (tile_rect.x, tile_rect.y))
                        else:
                            pygame.draw.rect(screen, GRAY, tile_rect)
                    
                    elif self.layout[y][x] == SECRET_PASSAGE:
                        # Secret passage - looks like wall but with a hint
                        if sprites and sprites.get('wall'):
                            # Draw wall sprite but slightly purple
                            wall_sprite = sprites.get('wall').copy()
                            # Add purple tint
                            wall_sprite.fill((50, 0, 50, 50), special_flags=pygame.BLEND_RGBA_ADD)
                            screen.blit(wall_sprite, (tile_rect.x, tile_rect.y))
                        else:
                            # Draw slightly different color
                            pygame.draw.rect(screen, SECRET_PURPLE, tile_rect)
                            # Occasional sparkle
                            if random.random() < 0.01:
                                pygame.draw.circle(screen, (255, 255, 255, 100), 
                                                 tile_rect.center, 2)
                    
                    else:  # FLOOR
                        if sprites and sprites.get('floor'):
                            screen.blit(sprites.get('floor'), (tile_rect.x, tile_rect.y))
                        else:
                            pygame.draw.rect(screen, DARK_GRAY, tile_rect)
                    
                    pygame.draw.rect(screen, (70, 70, 70), tile_rect, 1)
                    
                elif self.discovered[y][x]:
                    # Fog of war
                    if self.layout[y][x] == WALL:
                        color = (40, 40, 40)
                    elif self.layout[y][x] == SECRET_PASSAGE:
                        color = (35, 30, 40)  # Slightly purple in fog
                    else:
                        color = (20, 20, 20)
                    
                    pygame.draw.rect(screen, color, tile_rect)
                    pygame.draw.rect(screen, (30, 30, 30), tile_rect, 1)
                else:
                    pygame.draw.rect(screen, BLACK, tile_rect)
        
        # Draw entities
        for entity in self.entities:
            if self.discovered[entity.y][entity.x]:
                entity.draw(screen, offset_x, offset_y, self.visible[entity.y][entity.x], sprites)
        
        # Draw player
        player.draw(screen, sprites, offset_x, offset_y)

# ==================== PLAYER CLASS (SMOOTH) ====================
class Player:
    def __init__(self, start_x, start_y):
        self.grid_x = start_x
        self.grid_y = start_y
        self.pixel_x = start_x * TILE_SIZE
        self.pixel_y = start_y * TILE_SIZE
        
        self.move_x = 0
        self.move_y = 0
        self.target_x = self.pixel_x
        self.target_y = self.pixel_y
        self.is_moving = False
        
        self.gold = 0
        self.keys = 0
        self.health = 3
        self.max_health = 3
        
        self.message = ""
        self.message_timer = 0
        self.invincible_timer = 0
        self.hit_flash_timer = 0
        
    def try_move(self, dx, dy, dungeon):
        if self.is_moving:
            return False
            
        new_grid_x = self.grid_x + dx
        new_grid_y = self.grid_y + dy
        
        if 0 <= new_grid_x < dungeon.width and 0 <= new_grid_y < dungeon.height:
            # Check if tile is walkable (FLOOR or SECRET_PASSAGE)
            tile = dungeon.layout[new_grid_y][new_grid_x]
            if tile == WALL:
                return False
            
            # Secret passages are walkable! No wall collision.
            
            entity = dungeon.get_entity_at(new_grid_x, new_grid_y)
            
            if entity:
                if entity.type == GOLD:
                    self.gold += 1
                    entity.collected = True
                    dungeon.remove_entity(entity)
                    
                elif entity.type == KEY:
                    self.keys += 1
                    entity.collected = True
                    self.set_message(f"Key collected! Keys: {self.keys}")
                    dungeon.remove_entity(entity)
                    
                elif entity.type == DOOR:
                    if self.keys > 0:
                        self.keys -= 1
                        self.set_message("Door unlocked!")
                        dungeon.remove_entity(entity)
                    else:
                        self.set_message("Need a key!")
                        return False
                    
                elif entity.type == STATION:
                    self.set_message("Press E to play game at station")
                    return False
                    
                elif entity.type == MONSTER:
                    # Can't move into monster
                    return False
            
            # Start smooth movement
            self.target_x = new_grid_x * TILE_SIZE
            self.target_y = new_grid_y * TILE_SIZE
            self.move_x = dx * MOVE_SPEED
            self.move_y = dy * MOVE_SPEED
            self.is_moving = True
            
            self.grid_x = new_grid_x
            self.grid_y = new_grid_y
            
            # Special message for secret passages
            if tile == SECRET_PASSAGE:
                self.set_message("Found a secret passage!")
                
            return True
        return False
    
    def update(self, dungeon):
        if self.is_moving:
            if abs(self.pixel_x - self.target_x) > MOVE_SPEED:
                self.pixel_x += self.move_x
            else:
                self.pixel_x = self.target_x
                
            if abs(self.pixel_y - self.target_y) > MOVE_SPEED:
                self.pixel_y += self.move_y
            else:
                self.pixel_y = self.target_y
            
            if self.pixel_x == self.target_x and self.pixel_y == self.target_y:
                self.is_moving = False
                self.move_x = 0
                self.move_y = 0
        
        if self.message_timer > 0:
            self.message_timer -= 1
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1
    
    def set_message(self, msg):
        self.message = msg
        self.message_timer = 120
    
    def take_damage(self):
        if self.invincible_timer <= 0:
            self.health -= 1
            self.invincible_timer = 60
            self.hit_flash_timer = 20
            self.set_message(f"Ouch! Health: {self.health}")
            return True
        return False
    
    def draw(self, screen, sprites, offset_x=0, offset_y=0):
        player_rect = pygame.Rect(
            self.pixel_x + offset_x,
            self.pixel_y + offset_y,
            TILE_SIZE, TILE_SIZE
        )
        
        if self.hit_flash_timer > 0 and (self.hit_flash_timer // 5) % 2 == 0:
            if sprites and sprites.get('player'):
                tinted = sprites.get('player').copy()
                tinted.fill((255, 0, 0, 128), special_flags=pygame.BLEND_RGBA_MULT)
                screen.blit(tinted, (player_rect.x, player_rect.y))
            else:
                pygame.draw.circle(screen, (255, 100, 100), player_rect.center, 15)
        else:
            if sprites and sprites.get('player'):
                screen.blit(sprites.get('player'), (player_rect.x, player_rect.y))
            else:
                pygame.draw.circle(screen, (255, 255, 0), player_rect.center, 15)
                if self.is_moving:
                    mouth_angle = abs(pygame.time.get_ticks() % 500 - 250) / 250 * 45
                else:
                    pygame.draw.polygon(screen, BLACK, 
                                      [player_rect.center, 
                                       (player_rect.center[0] + 15, player_rect.center[1] - 10),
                                       (player_rect.center[0] + 15, player_rect.center[1] + 10)])

# ==================== ENTITY PLACEMENT FUNCTIONS ====================

def place_entities_pacman_style(dungeon, room_num):
    """Place entities with gold on EVERY floor tile"""
    
    floor_tiles = []
    for y in range(dungeon.height):
        for x in range(dungeon.width):
            if dungeon.layout[y][x] == FLOOR:
                floor_tiles.append((x, y))
    
    random.shuffle(floor_tiles)
    gold_positions = floor_tiles.copy()
    
    # Place station
    if floor_tiles:
        station_x, station_y = floor_tiles.pop()
        dungeon.add_entity(Entity(station_x, station_y, STATION))
        if (station_x, station_y) in gold_positions:
            gold_positions.remove((station_x, station_y))
    
    # Place door
    if room_num < 3 and floor_tiles:
        door_x, door_y = floor_tiles.pop()
        dungeon.add_entity(Entity(door_x, door_y, DOOR))
        if (door_x, door_y) in gold_positions:
            gold_positions.remove((door_x, door_y))
    
    # Place monsters
    if room_num == 1:
        num_monsters = 3
    elif room_num == 2:
        num_monsters = 5
    else:
        num_monsters = 7
    
    for _ in range(min(num_monsters, len(floor_tiles))):
        if floor_tiles:
            monster_x, monster_y = floor_tiles.pop()
            dungeon.add_entity(Monster(monster_x, monster_y))
            if (monster_x, monster_y) in gold_positions:
                gold_positions.remove((monster_x, monster_y))
    
    # Place keys
    num_keys = random.randint(1, 2)
    for _ in range(min(num_keys, len(floor_tiles))):
        if floor_tiles:
            key_x, key_y = floor_tiles.pop()
            dungeon.add_entity(Entity(key_x, key_y, KEY))
            if (key_x, key_y) in gold_positions:
                gold_positions.remove((key_x, key_y))
    
    # Gold on every remaining floor tile
    for x, y in gold_positions:
        dungeon.add_entity(Entity(x, y, GOLD))
    
    print(f"Placed {len(gold_positions)} gold pieces in room {room_num}")

# ==================== MINI-GAMES ====================
class TicTacToeGravity:
    def __init__(self):
        self.board = [[' ' for _ in range(4)] for _ in range(4)]
        self.current_player = 'X'
        self.game_over = False
        self.winner = None
        self.gravity = random.choice(['down', 'up', 'left', 'right'])
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)
        
    def handle_click(self, x, y):
        if self.game_over:
            return False
            
        col = x // (SCREEN_WIDTH // 4)
        
        if self.gravity in ['down', 'up']:
            if self.gravity == 'down':
                for row in range(3, -1, -1):
                    if self.board[row][col] == ' ':
                        self.board[row][col] = self.current_player
                        break
            else:
                for row in range(4):
                    if self.board[row][col] == ' ':
                        self.board[row][col] = self.current_player
                        break
        else:
            row = y // (SCREEN_HEIGHT // 4)
            if self.gravity == 'right':
                for c in range(3, -1, -1):
                    if self.board[row][c] == ' ':
                        self.board[row][c] = self.current_player
                        break
            else:
                for c in range(4):
                    if self.board[row][c] == ' ':
                        self.board[row][c] = self.current_player
                        break
        
        self.check_win()
        if not self.game_over:
            self.current_player = 'O' if self.current_player == 'X' else 'X'
        return True
    
    def check_win(self):
        for row in range(4):
            if self.board[row][0] != ' ' and all(self.board[row][c] == self.board[row][0] for c in range(4)):
                self.game_over = True
                self.winner = self.board[row][0]
                return
        
        for col in range(4):
            if self.board[0][col] != ' ' and all(self.board[r][col] == self.board[0][col] for r in range(4)):
                self.game_over = True
                self.winner = self.board[0][col]
                return
        
        if self.board[0][0] != ' ' and all(self.board[i][i] == self.board[0][0] for i in range(4)):
            self.game_over = True
            self.winner = self.board[0][0]
            return
        
        if self.board[0][3] != ' ' and all(self.board[i][3-i] == self.board[0][3] for i in range(4)):
            self.game_over = True
            self.winner = self.board[0][3]
            return
        
        if all(self.board[r][c] != ' ' for r in range(4) for c in range(4)):
            self.game_over = True
            self.winner = 'tie'
    
    def draw(self, screen):
        screen.fill((30, 30, 50))
        
        cell_w = SCREEN_WIDTH // 4
        cell_h = SCREEN_HEIGHT // 4
        
        for i in range(5):
            pygame.draw.line(screen, WHITE, (i * cell_w, 0), (i * cell_w, SCREEN_HEIGHT), 2)
            pygame.draw.line(screen, WHITE, (0, i * cell_h), (SCREEN_WIDTH, i * cell_h), 2)
        
        for row in range(4):
            for col in range(4):
                if self.board[row][col] != ' ':
                    x = col * cell_w + cell_w // 2
                    y = row * cell_h + cell_h // 2
                    
                    if self.board[row][col] == 'X':
                        pygame.draw.line(screen, RED, (x - 30, y - 30), (x + 30, y + 30), 5)
                        pygame.draw.line(screen, RED, (x + 30, y - 30), (x - 30, y + 30), 5)
                    else:
                        pygame.draw.circle(screen, BLUE, (x, y), 30, 5)
        
        if not self.game_over:
            text = self.font.render(f"Player: {self.current_player}", True, WHITE)
            screen.blit(text, (10, 10))
            grav_text = self.small_font.render(f"Gravity: {self.gravity}", True, CYAN)
            screen.blit(grav_text, (10, 60))
        else:
            if self.winner == 'tie':
                text = self.font.render("It's a tie!", True, WHITE)
            else:
                text = self.font.render(f"Player {self.winner} wins!", True, GOLD)
            screen.blit(text, (250, 250))
            restart = self.small_font.render("Press R to restart, ESC to exit", True, WHITE)
            screen.blit(restart, (200, 350))

class Minesweeper:
    def __init__(self, width=10, height=10, num_mines=15):
        self.width = width
        self.height = height
        self.num_mines = num_mines
        self.cell_size = min(SCREEN_WIDTH // width, SCREEN_HEIGHT // height)
        self.offset_x = (SCREEN_WIDTH - (width * self.cell_size)) // 2
        self.offset_y = (SCREEN_HEIGHT - (height * self.cell_size)) // 2
        
        self.board = [[0 for _ in range(width)] for _ in range(height)]
        self.revealed = [[False for _ in range(width)] for _ in range(height)]
        self.flagged = [[False for _ in range(width)] for _ in range(height)]
        self.mines = [[False for _ in range(width)] for _ in range(height)]
        self.game_over = False
        self.won = False
        self.first_click = True
        
        self.font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 48)
        
        self.number_colors = {
            1: (0, 0, 255), 2: (0, 128, 0), 3: (255, 0, 0),
            4: (0, 0, 128), 5: (128, 0, 0), 6: (0, 128, 128),
            7: (0, 0, 0), 8: (128, 128, 128)
        }
    
    def place_mines(self, safe_x, safe_y):
        mines_placed = 0
        while mines_placed < self.num_mines:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            
            if (x == safe_x and y == safe_y) or self.mines[y][x]:
                continue
                
            self.mines[y][x] = True
            mines_placed += 1
        
        for y in range(self.height):
            for x in range(self.width):
                if not self.mines[y][x]:
                    count = 0
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                if self.mines[ny][nx]:
                                    count += 1
                    self.board[y][x] = count
    
    def handle_click(self, x, y, button):
        if self.game_over or self.won:
            return
        
        grid_x = (x - self.offset_x) // self.cell_size
        grid_y = (y - self.offset_y) // self.cell_size
        
        if not (0 <= grid_x < self.width and 0 <= grid_y < self.height):
            return
        
        if button == 1:
            if self.first_click:
                self.place_mines(grid_x, grid_y)
                self.first_click = False
            
            if self.flagged[grid_y][grid_x]:
                return
            
            if self.mines[grid_y][grid_x]:
                self.game_over = True
                self.reveal_all()
            else:
                self.flood_reveal(grid_x, grid_y)
                
        elif button == 3:
            if not self.revealed[grid_y][grid_x]:
                self.flagged[grid_y][grid_x] = not self.flagged[grid_y][grid_x]
        
        self.check_win()
    
    def flood_reveal(self, x, y):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        if self.revealed[y][x] or self.flagged[y][x]:
            return
        
        self.revealed[y][x] = True
        
        if self.board[y][x] == 0:
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    self.flood_reveal(x + dx, y + dy)
    
    def reveal_all(self):
        for y in range(self.height):
            for x in range(self.width):
                self.revealed[y][x] = True
    
    def check_win(self):
        for y in range(self.height):
            for x in range(self.width):
                if not self.mines[y][x] and not self.revealed[y][x]:
                    return False
        self.won = True
        return True
    
    def draw(self, screen):
        screen.fill((50, 50, 70))
        title = self.big_font.render("MINESWEEPER", True, WHITE)
        screen.blit(title, (250, 20))
        
        for y in range(self.height):
            for x in range(self.width):
                rect = pygame.Rect(
                    self.offset_x + x * self.cell_size,
                    self.offset_y + y * self.cell_size,
                    self.cell_size - 2,
                    self.cell_size - 2
                )
                
                if self.revealed[y][x]:
                    pygame.draw.rect(screen, (200, 200, 200), rect)
                    
                    if self.mines[y][x]:
                        center = rect.center
                        pygame.draw.circle(screen, BLACK, center, self.cell_size // 4)
                    elif self.board[y][x] > 0:
                        text = self.font.render(str(self.board[y][x]), True, 
                                               self.number_colors.get(self.board[y][x], BLACK))
                        text_rect = text.get_rect(center=rect.center)
                        screen.blit(text, text_rect)
                else:
                    pygame.draw.rect(screen, (150, 150, 150), rect)
                    pygame.draw.rect(screen, (100, 100, 100), rect, 2)
                    
                    if self.flagged[y][x]:
                        center = rect.center
                        pygame.draw.rect(screen, RED, 
                                       (center[0] - 5, center[1] - 8, 4, 12))
                        pygame.draw.polygon(screen, RED, 
                                          [(center[0] - 1, center[1] - 12),
                                           (center[0] - 1, center[1] - 4),
                                           (center[0] + 8, center[1] - 8)])
        
        if self.game_over:
            text = self.big_font.render("GAME OVER!", True, RED)
            screen.blit(text, (280, SCREEN_HEIGHT - 80))
        elif self.won:
            text = self.big_font.render("YOU WIN!", True, GOLD)
            screen.blit(text, (300, SCREEN_HEIGHT - 80))
        else:
            remaining = self.num_mines - sum(sum(row) for row in self.flagged)
            text = self.font.render(f"Mines: {remaining}", True, WHITE)
            screen.blit(text, (10, SCREEN_HEIGHT - 60))
        
        inst1 = self.font.render("Left click: Reveal | Right click: Flag", True, WHITE)
        screen.blit(inst1, (200, SCREEN_HEIGHT - 40))

# ==================== MAIN GAME ====================
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dungeon Arcade - Secret Passages!")
        self.clock = pygame.time.Clock()
        self.running = True
        
        try:
            self.sprite_loader = SpriteLoader()
            if not any(self.sprite_loader.sprites.values()):
                print("No sprite files found, creating simple sprites")
                self.sprites = create_fallback_sprites()
            else:
                self.sprites = self.sprite_loader.sprites
        except:
            print("Using simple created sprites")
            self.sprites = create_fallback_sprites()
        
        self.state = MENU
        self.current_room = 1
        self.dungeon = None
        self.player = None
        self.minigame = None
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 74)
    
    def generate_new_room(self, room_num):
        layout, rooms = generate_pacman_style_dungeon(25, 19, num_rooms=random.randint(4, 6))
        self.dungeon = Dungeon(layout=layout)
        self.dungeon.rooms = rooms
        
        place_entities_pacman_style(self.dungeon, room_num)
        
        start_x, start_y = self.dungeon.find_safe_start()
        self.player = Player(start_x, start_y)
        
        self.current_room = room_num
        self.state = EXPLORE
        
        self.dungeon.update_vision(
            self.player.pixel_x + TILE_SIZE//2,
            self.player.pixel_y + TILE_SIZE//2
        )
        
        gold_count = self.dungeon.count_remaining_gold()
        self.player.set_message(f"Room {room_num} - Collect {gold_count} gold! (No sword!)")
    
    def run(self):
        move_timer = 0
        
        while self.running:
            dt = self.clock.tick(FPS)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                elif event.type == pygame.KEYDOWN:
                    if self.state == MENU:
                        if event.key == pygame.K_SPACE:
                            self.generate_new_room(1)
                    
                    elif self.state == EXPLORE:
                        if event.key == pygame.K_e:
                            entity = self.dungeon.get_entity_at(self.player.grid_x, self.player.grid_y)
                            if entity and entity.type == STATION:
                                if self.current_room == 1:
                                    self.state = TTT_GAME
                                    self.minigame = TicTacToeGravity()
                                    self.player.set_message("Tic-Tac-Toe with gravity!")
                                elif self.current_room == 2:
                                    self.state = MINESWEEP_GAME
                                    self.minigame = Minesweeper(10, 10, 15)
                                    self.player.set_message("Minesweeper - 10x10!")
                                elif self.current_room == 3:
                                    self.state = SNAKE_GAME
                                    self.player.set_message("Snake coming soon!")
                        
                        elif event.key == pygame.K_r:
                            self.generate_new_room(self.current_room)
                    
                    elif self.state in [TTT_GAME, MINESWEEP_GAME, SNAKE_GAME]:
                        if event.key == pygame.K_ESCAPE:
                            self.state = EXPLORE
                            self.player.set_message("Back to dungeon")
                        elif self.state == TTT_GAME and event.key == pygame.K_r:
                            self.minigame = TicTacToeGravity()
                    
                    elif self.state in [GAME_OVER, VICTORY]:
                        if event.key == pygame.K_SPACE:
                            self.state = MENU
                        elif event.key == pygame.K_r:
                            self.generate_new_room(1)
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == TTT_GAME and self.minigame:
                        x, y = event.pos
                        self.minigame.handle_click(x, y)
                        
                        if self.minigame.game_over:
                            if self.minigame.winner == 'X':
                                self.player.set_message("You won! +1 key")
                                self.player.keys += 1
                            elif self.minigame.winner == 'O':
                                self.player.set_message("You lost...")
                    
                    elif self.state == MINESWEEP_GAME and self.minigame:
                        x, y = event.pos
                        button = event.button
                        self.minigame.handle_click(x, y, button)
                        
                        if self.minigame.won:
                            self.player.set_message("Minesweeper cleared! +2 keys")
                            self.player.keys += 2
                        elif self.minigame.game_over:
                            self.player.set_message("Boom! You lost...")
            
            if self.state == EXPLORE:
                keys = pygame.key.get_pressed()
                
                if not self.player.is_moving:
                    moved = False
                    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                        moved = self.player.try_move(-1, 0, self.dungeon)
                    elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                        moved = self.player.try_move(1, 0, self.dungeon)
                    elif keys[pygame.K_UP] or keys[pygame.K_w]:
                        moved = self.player.try_move(0, -1, self.dungeon)
                    elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                        moved = self.player.try_move(0, 1, self.dungeon)
                
                # Update monsters and check collisions
                for entity in self.dungeon.entities[:]:
                    if isinstance(entity, Monster):
                        old_pixel_x, old_pixel_y = entity.pixel_x, entity.pixel_y
                        
                        entity.update(self.dungeon, self.player.grid_x, self.player.grid_y)
                        
                        # Check collision using pixel positions
                        if (abs(entity.pixel_x - self.player.pixel_x) < TILE_SIZE//2 and
                            abs(entity.pixel_y - self.player.pixel_y) < TILE_SIZE//2):
                            
                            if self.player.take_damage():
                                # Push player back
                                if entity.pixel_x != old_pixel_x or entity.pixel_y != old_pixel_y:
                                    push_x = self.player.pixel_x - (entity.pixel_x - old_pixel_x)
                                    push_y = self.player.pixel_y - (entity.pixel_y - old_pixel_y)
                                    
                                    push_x = max(0, min(push_x, (self.dungeon.width-1) * TILE_SIZE))
                                    push_y = max(0, min(push_y, (self.dungeon.height-1) * TILE_SIZE))
                                    
                                    self.player.pixel_x = push_x
                                    self.player.pixel_y = push_y
                                    self.player.grid_x = push_x // TILE_SIZE
                                    self.player.grid_y = push_y // TILE_SIZE
                                
                                if self.player.health <= 0:
                                    self.state = GAME_OVER
                
                self.dungeon.update_vision(
                    self.player.pixel_x + TILE_SIZE//2,
                    self.player.pixel_y + TILE_SIZE//2
                )
                
                self.player.update(self.dungeon)
                
                remaining_gold = self.dungeon.count_remaining_gold()
                if remaining_gold == 0 and self.current_room < 3:
                    self.player.set_message("All gold collected! Find the door to next room!")
                
                entity = self.dungeon.get_entity_at(self.player.grid_x, self.player.grid_y)
                if entity and entity.type == DOOR:
                    if self.current_room < 3:
                        if self.dungeon.count_remaining_gold() == 0:
                            self.generate_new_room(self.current_room + 1)
                        else:
                            self.player.set_message("Collect all gold first!")
                    else:
                        if self.dungeon.count_remaining_gold() == 0:
                            self.state = VICTORY
                        else:
                            self.player.set_message("Collect all gold to win!")
                
                if self.player.health <= 0:
                    self.state = GAME_OVER
            
            # Draw everything
            self.screen.fill(BLACK)
            
            if self.state == MENU:
                self.draw_menu()
            elif self.state == EXPLORE:
                self.draw_explore()
            elif self.state == TTT_GAME and self.minigame:
                self.minigame.draw(self.screen)
                self.draw_minigame_ui()
            elif self.state == MINESWEEP_GAME and self.minigame:
                self.minigame.draw(self.screen)
                self.draw_minigame_ui()
            elif self.state == SNAKE_GAME:
                self.draw_snake_placeholder()
            elif self.state == GAME_OVER:
                self.draw_game_over()
            elif self.state == VICTORY:
                self.draw_victory()
            
            pygame.display.flip()
        
        pygame.quit()
    
    def draw_menu(self):
        title = self.big_font.render("DUNGEON ARCADE", True, GOLD)
        self.screen.blit(title, (150, 150))
        
        subtitle = self.font.render("Secret Passages!", True, CYAN)
        self.screen.blit(subtitle, (300, 220))
        
        instr = self.small_font.render("Room 1: Tic-Tac-Toe with Gravity", True, WHITE)
        self.screen.blit(instr, (250, 300))
        instr = self.small_font.render("Room 2: Minesweeper 10x10", True, WHITE)
        self.screen.blit(instr, (280, 330))
        instr = self.small_font.render("Room 3: Snake", True, WHITE)
        self.screen.blit(instr, (310, 360))
        
        instr2 = self.small_font.render("Collect ALL gold in each room!", True, GOLD)
        self.screen.blit(instr2, (250, 400))
        instr3 = self.small_font.render("Hide in secret passages!", True, PURPLE)
        self.screen.blit(instr3, (250, 430))
        
        start = self.font.render("Press SPACE to Start", True, GREEN)
        self.screen.blit(start, (250, 500))
    
    def draw_explore(self):
        offset_x = SCREEN_WIDTH//2 - self.player.pixel_x - TILE_SIZE//2
        offset_y = SCREEN_HEIGHT//2 - self.player.pixel_y - TILE_SIZE//2
        
        self.dungeon.draw(self.screen, self.player, offset_x, offset_y, self.sprites)
        
        # Draw UI
        heart_sprite = self.sprites.get('heart') if self.sprites else None
        for i in range(self.player.health):
            x = 10 + i * 30
            alpha = 255
            if self.player.invincible_timer > 0 and i == 0:
                alpha = 128 if (pygame.time.get_ticks() // 100) % 2 else 255
            
            if heart_sprite:
                heart_sprite.set_alpha(alpha)
                self.screen.blit(heart_sprite, (x, 10))
            else:
                color = RED if alpha == 255 else (128, 0, 0)
                pygame.draw.polygon(self.screen, color, [(x+10, 15), (x, 25), (x+20, 25)])
        
        remaining = self.dungeon.count_remaining_gold()
        gold_text = self.small_font.render(f"Gold: {self.player.gold}  Remaining: {remaining}", True, GOLD)
        self.screen.blit(gold_text, (10, 50))
        
        keys_text = self.small_font.render(f"Keys: {self.player.keys}", True, GOLD)
        self.screen.blit(keys_text, (10, 80))
        
        room_text = self.font.render(f"Room {self.current_room}", True, WHITE)
        self.screen.blit(room_text, (SCREEN_WIDTH - 150, 10))
        
        if self.player.message_timer > 0:
            msg_text = self.small_font.render(self.player.message, True, CYAN)
            msg_rect = msg_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
            self.screen.blit(msg_text, msg_rect)
        
        hint = self.small_font.render("R: New dungeon | E: Use station", True, GRAY)
        self.screen.blit(hint, (SCREEN_WIDTH - 300, SCREEN_HEIGHT - 30))
    
    def draw_minigame_ui(self):
        esc_text = self.small_font.render("ESC: Return to dungeon", True, WHITE)
        self.screen.blit(esc_text, (10, SCREEN_HEIGHT - 30))
    
    def draw_snake_placeholder(self):
        self.screen.fill((70, 50, 50))
        title = self.font.render("SNAKE", True, WHITE)
        self.screen.blit(title, (350, 250))
        subtitle = self.small_font.render("Coming to Room 3!", True, CYAN)
        self.screen.blit(subtitle, (330, 300))
        self.draw_minigame_ui()
    
    def draw_game_over(self):
        self.screen.fill(BLACK)
        title = self.big_font.render("GAME OVER", True, RED)
        self.screen.blit(title, (220, 250))
        
        stats = self.font.render(f"Gold collected: {self.player.gold}", True, GOLD)
        self.screen.blit(stats, (280, 350))
        
        restart = self.small_font.render("Press SPACE for menu, R to restart", True, WHITE)
        self.screen.blit(restart, (200, 450))
    
    def draw_victory(self):
        self.screen.fill(BLACK)
        
        for i in range(20):
            color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
            pygame.draw.circle(self.screen, color, 
                             (random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)), 
                             random.randint(2, 5))
        
        title = self.big_font.render("VICTORY!", True, GOLD)
        self.screen.blit(title, (250, 250))
        
        stats = self.font.render(f"Total gold: {self.player.gold}", True, GOLD)
        self.screen.blit(stats, (300, 350))
        
        thanks = self.small_font.render("You collected ALL the gold!", True, CYAN)
        self.screen.blit(thanks, (280, 400))
        
        restart = self.small_font.render("Press SPACE for menu", True, WHITE)
        self.screen.blit(restart, (280, 500))

# ==================== START THE GAME ====================
if __name__ == "__main__":
    game = Game()
    game.run()