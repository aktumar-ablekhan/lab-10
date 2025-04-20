import pygame
import random
import time
import psycopg2

# DB CONNECT
def connect():
    return psycopg2.connect(
        host="localhost",
        dbname="snake_game",
        user="postgres",
        password="Lovelovelove3."
    )

# CREATE TABLES
def create_tables():
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_scores (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    level INTEGER NOT NULL,
                    score INTEGER NOT NULL,
                    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    print("Tables are ready.")

# GET OR CREATE USER
def get_or_create_user(username):
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            row = cur.fetchone() #SQL сұранысының нәтижесінен бір ғана жолды (record) алу әдісі
            if row:
                user_id = row[0]
                cur.execute(
                    "SELECT level, score FROM user_scores WHERE user_id = %s ORDER BY saved_at DESC LIMIT 1",
                    (user_id,)
                )
                progress = cur.fetchone()
                if progress:
                    return user_id, progress[0], progress[1]
                return user_id, 1, 0
            cur.execute("INSERT INTO users (username) VALUES (%s) RETURNING id", (username,))
            user_id = cur.fetchone()[0]
            cur.execute("INSERT INTO user_scores (user_id, level, score) VALUES (%s, %s, %s)", (user_id, 1, 0))
            return user_id, 1, 0

# SAVE PROGRESS 
def save_progress(user_id, level, score):
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO user_scores (user_id, level, score) VALUES (%s, %s, %s)",
                (user_id, level, score)
            )
    print("Game saved.")

# GAME SETUP
pygame.init()
WIDTH, HEIGHT = 600, 600
CELL = 30
# Colors
colorWHITE = (255, 255, 255)
colorBLACK = (0, 0, 0)
colorGRAY = (100, 100, 100)
colorRED = (255, 0, 0)
colorGREEN = (0, 255, 0)
colorBLUE = (0, 0, 255)
colorYELLOW = (255, 255, 0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Game")
font = pygame.font.SysFont("Arial", 24)

# GRID 
def draw_grid():
    colors = [(144, 238, 144), (60, 179, 113)]
    for row in range(HEIGHT // CELL):
        for col in range(WIDTH // CELL):
            color = colors[(row + col) % 2]
            pygame.draw.rect(screen, color, (col * CELL, row * CELL, CELL, CELL))

# WALLS FOR LEVELS 
def get_walls(level):
    walls = []
    mid_x = WIDTH // CELL // 2
    mid_y = HEIGHT // CELL // 2
    if level >= 2:
        for x in range(5, WIDTH // CELL - 5):
            walls.append((x, mid_y))
    if level >= 3:
        for y in range(5, HEIGHT // CELL - 5):
            walls.append((mid_x, y))
    return walls

class Snake:
    def __init__(self):
        self.body = [(10, 11), (10, 12), (10, 13)]
        self.dx, self.dy = 1, 0

    def move(self):
        head_x, head_y = self.body[0]
        new_head = (head_x + self.dx, head_y + self.dy)
        self.body = [new_head] + self.body[:-1]

    def draw(self):
        head = self.body[0]
        pygame.draw.rect(screen, (70, 130, 180), (head[0] * CELL, head[1] * CELL, CELL, CELL))
        eye_size = CELL // 8
        eye_offset = CELL // 4
        pygame.draw.circle(screen, colorBLACK, (head[0] * CELL + eye_offset, head[1] * CELL + eye_offset), eye_size)
        pygame.draw.circle(screen, colorBLACK, (head[0] * CELL + CELL - eye_offset, head[1] * CELL + eye_offset), eye_size)
        for segment in self.body[1:]:
            x, y = segment
            pygame.draw.rect(screen, (70, 130, 180), (x * CELL, y * CELL, CELL, CELL))

    def collides_self(self):
        return self.body[0] in self.body[1:]

    def collides_wall(self):
        x, y = self.body[0]
        return x < 0 or x >= WIDTH // CELL or y < 0 or y >= HEIGHT // CELL

    def collides_obstacle(self, walls):
        return self.body[0] in walls

    def eats(self, food_pos):
        if self.body[0] == food_pos:
            self.body.append(self.body[-1])
            return True
        return False

class Food:
    def __init__(self):
        self.pos = (9, 9)
        self.type = random.choice(["red", "blue", "yellow"])
        self.points = {"red": 1, "blue": 2, "yellow": 3}[self.type]
        self.time_created = time.time()

    def draw(self):
        color = {"red": colorRED, "blue": colorBLUE, "yellow": colorYELLOW}[self.type]
        x, y = self.pos
        pygame.draw.rect(screen, color, (x * CELL, y * CELL, CELL, CELL))
        pygame.draw.rect(screen, colorBLACK, (x * CELL, y * CELL, CELL, CELL), 1)

    def generate_random_pos(self, snake_body, walls):
        while True:
            pos = (random.randint(0, WIDTH // CELL - 1), random.randint(0, HEIGHT // CELL - 1))
            if pos not in snake_body and pos not in walls:
                self.pos = pos
                self.type = random.choice(["red", "blue", "yellow"])
                self.points = {"red": 1, "blue": 2, "yellow": 3}[self.type]
                self.time_created = time.time()
                break

    def is_expired(self):
        return time.time() - self.time_created > 5

# DISPLAY USERNAME INPUT
def display_username_input():
    username = ""
    active = True
    while active:
        screen.fill((144, 238, 144))
        prompt = font.render("Enter your username:", True, colorWHITE)
        entry = font.render(username, True, colorWHITE)
        screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT // 2 - 40))
        screen.blit(entry, (WIDTH // 2 - entry.get_width() // 2, HEIGHT // 2))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN and username:
                    active = False
                elif e.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                else:
                    username += e.unicode
    return username

# MAIN GAME LOOP
create_tables()
username = display_username_input()
user_id, level, score = get_or_create_user(username)
walls = get_walls(level)
FPS = 5 + (level // 2)
clock = pygame.time.Clock()
snake = Snake()
food = Food()
needed = 3
running = True
paused = False

while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            save_progress(user_id, level, score)
            running = False
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_p:
                paused = not paused
                if paused:
                    save_progress(user_id, level, score)
            if not paused:
                if e.key == pygame.K_RIGHT and snake.dx == 0:
                    snake.dx, snake.dy = 1, 0
                if e.key == pygame.K_LEFT and snake.dx == 0:
                    snake.dx, snake.dy = -1, 0
                if e.key == pygame.K_DOWN and snake.dy == 0:
                    snake.dx, snake.dy = 0, 1
                if e.key == pygame.K_UP and snake.dy == 0:
                    snake.dx, snake.dy = 0, -1

    screen.fill(colorBLACK)
    draw_grid()
    # draw walls
    for wx, wy in walls:
        pygame.draw.rect(screen, colorGRAY, (wx * CELL, wy * CELL, CELL, CELL))

    if not paused:
        snake.move()
        if (snake.collides_self() or snake.collides_wall() or
                snake.collides_obstacle(walls)):
            print("Game Over!")
            print(f"Final Score: {score}, Level: {level}")
            save_progress(user_id, level, score)
            running = False

        if snake.eats(food.pos):
            food.generate_random_pos(snake.body, walls)
            score += food.points
            needed -= 1
            if needed == 0:
                level += 1
                walls = get_walls(level)
                needed = 3
                if level % 2 == 0:
                    FPS += 1

        if food.is_expired():
            food.generate_random_pos(snake.body, walls)
    else:
        pause_text = font.render("Paused", True, colorYELLOW)
        screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2))

    snake.draw()
    food.draw()
    score_text = font.render(f"Score: {score}", True, colorWHITE)
    level_text = font.render(f"Level: {level}", True, colorWHITE)
    screen.blit(score_text, (10, 10))
    screen.blit(level_text, (10, 40))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()