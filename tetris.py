import pygame
import random
import numpy as np
from scipy import signal
import os
import time

# Initialize Pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
GRID_OFFSET_X = (SCREEN_WIDTH - GRID_WIDTH * GRID_SIZE) // 2
GRID_OFFSET_Y = (SCREEN_HEIGHT - GRID_HEIGHT * GRID_SIZE) // 2

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
CYAN = (0, 255, 255)    # I piece
BLUE = (0, 0, 255)      # J piece
ORANGE = (255, 165, 0)  # L piece
YELLOW = (255, 255, 0)  # O piece
GREEN = (0, 255, 0)     # S piece
PURPLE = (128, 0, 128)  # T piece
RED = (255, 0, 0)       # Z piece

# Tetromino shapes
SHAPES = [
    [[1, 1, 1, 1]],                         # I
    [[1, 0, 0], [1, 1, 1]],                 # J
    [[0, 0, 1], [1, 1, 1]],                 # L
    [[1, 1], [1, 1]],                       # O
    [[0, 1, 1], [1, 1, 0]],                 # S
    [[0, 1, 0], [1, 1, 1]],                 # T
    [[1, 1, 0], [0, 1, 1]]                  # Z
]

# Tetromino colors
COLORS = [CYAN, BLUE, ORANGE, YELLOW, GREEN, PURPLE, RED]

# Game variables
score = 0
level = 1
lines_cleared = 0

# Create the game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tetris")
clock = pygame.time.Clock()

# Sound effects directory
SOUNDS_DIR = "sounds"
if not os.path.exists(SOUNDS_DIR):
    os.makedirs(SOUNDS_DIR)

# Sound effects
def generate_sound_effects():
    # Function to generate and save a sound effect
    def create_sound(filename, freq, duration, volume=0.5, fade=0.1, sample_rate=44100):
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Generate the waveform
        if filename == "rotate.wav":
            # Quick upward sweep
            freq_sweep = np.linspace(freq, freq * 1.5, len(t))
            note = 0.5 * np.sin(2 * np.pi * freq_sweep * t)
        elif filename == "drop.wav":
            # Downward sweep
            freq_sweep = np.linspace(freq * 1.5, freq * 0.8, len(t))
            note = 0.7 * np.sin(2 * np.pi * freq_sweep * t)
        elif filename == "clear.wav":
            # Chord with harmonics
            note = 0.3 * np.sin(2 * np.pi * freq * t)
            note += 0.2 * np.sin(2 * np.pi * freq * 1.5 * t)
            note += 0.1 * np.sin(2 * np.pi * freq * 2 * t)
        elif filename == "gameover.wav":
            # Descending notes
            note = np.zeros_like(t)
            segments = 8
            segment_duration = len(t) // segments
            for i in range(segments):
                segment_freq = freq * (1 - i * 0.1)
                start = i * segment_duration
                end = (i + 1) * segment_duration
                note[start:end] = 0.5 * np.sin(2 * np.pi * segment_freq * t[start:end])
        elif filename == "levelup.wav":
            # Ascending arpeggio
            note = np.zeros_like(t)
            segments = 5
            segment_duration = len(t) // segments
            for i in range(segments):
                segment_freq = freq * (1 + i * 0.2)
                start = i * segment_duration
                end = (i + 1) * segment_duration
                note[start:end] = 0.5 * np.sin(2 * np.pi * segment_freq * t[start:end])
        else:  # move.wav or default
            # Simple tone
            note = 0.5 * np.sin(2 * np.pi * freq * t)
        
        # Apply fade in/out
        fade_samples = int(fade * sample_rate)
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)
        
        if len(note) > 2 * fade_samples:
            note[:fade_samples] *= fade_in
            note[-fade_samples:] *= fade_out
        
        # Apply volume
        note = (note * volume * 32767).astype(np.int16)
        
        # Save as WAV file
        from scipy.io import wavfile
        wavfile.write(os.path.join(SOUNDS_DIR, filename), sample_rate, note)
    
    # Generate different sound effects
    create_sound("move.wav", 220, 0.1, 0.4)
    create_sound("rotate.wav", 330, 0.15, 0.4)
    create_sound("drop.wav", 440, 0.2, 0.5)
    create_sound("clear.wav", 523, 0.3, 0.6)
    create_sound("levelup.wav", 660, 0.5, 0.6)
    create_sound("gameover.wav", 220, 1.0, 0.7)

# Generate sound effects if they don't exist
sound_files = ["move.wav", "rotate.wav", "drop.wav", "clear.wav", "levelup.wav", "gameover.wav"]
missing_sounds = any(not os.path.exists(os.path.join(SOUNDS_DIR, f)) for f in sound_files)

if missing_sounds:
    generate_sound_effects()

# Load sound effects
move_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "move.wav"))
rotate_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "rotate.wav"))
drop_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "drop.wav"))
clear_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "clear.wav"))
levelup_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "levelup.wav"))
gameover_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "gameover.wav"))

class Tetromino:
    def __init__(self):
        self.shape_idx = random.randint(0, len(SHAPES) - 1)
        self.shape = [row[:] for row in SHAPES[self.shape_idx]]
        self.color = COLORS[self.shape_idx]
        self.x = GRID_WIDTH // 2 - len(self.shape[0]) // 2
        self.y = 0
    
    def rotate(self):
        # Transpose the shape matrix and reverse each row to rotate 90 degrees clockwise
        rotated = [[self.shape[y][x] for y in range(len(self.shape) - 1, -1, -1)] 
                  for x in range(len(self.shape[0]))]
        
        # Check if rotation is valid
        old_shape = self.shape
        self.shape = rotated
        if not self.is_valid_position(board):
            self.shape = old_shape
            return False
        
        rotate_sound.play()
        return True
    
    def move_left(self):
        self.x -= 1
        if not self.is_valid_position(board):
            self.x += 1
            return False
        move_sound.play()
        return True
    
    def move_right(self):
        self.x += 1
        if not self.is_valid_position(board):
            self.x -= 1
            return False
        move_sound.play()
        return True
    
    def move_down(self):
        self.y += 1
        if not self.is_valid_position(board):
            self.y -= 1
            return False
        return True
    
    def hard_drop(self):
        while self.move_down():
            pass
        drop_sound.play()
    
    def is_valid_position(self, board):
        for y, row in enumerate(self.shape):
            for x, cell in enumerate(row):
                if cell:
                    # Check if out of bounds
                    if (self.x + x < 0 or self.x + x >= GRID_WIDTH or 
                        self.y + y >= GRID_HEIGHT):
                        return False
                    # Check if collides with existing blocks
                    if self.y + y >= 0 and board[self.y + y][self.x + x]:
                        return False
        return True

def create_board():
    return [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

def draw_board(board):
    # Draw background
    screen.fill(BLACK)
    
    # Draw grid border
    pygame.draw.rect(screen, WHITE, 
                    (GRID_OFFSET_X - 2, GRID_OFFSET_Y - 2, 
                     GRID_WIDTH * GRID_SIZE + 4, GRID_HEIGHT * GRID_SIZE + 4), 2)
    
    # Draw grid cells
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if board[y][x]:
                color = board[y][x]
                pygame.draw.rect(screen, color, 
                                (GRID_OFFSET_X + x * GRID_SIZE, 
                                 GRID_OFFSET_Y + y * GRID_SIZE, 
                                 GRID_SIZE, GRID_SIZE))
                pygame.draw.rect(screen, WHITE, 
                                (GRID_OFFSET_X + x * GRID_SIZE, 
                                 GRID_OFFSET_Y + y * GRID_SIZE, 
                                 GRID_SIZE, GRID_SIZE), 1)
    
    # Draw current tetromino
    if current_tetromino:
        for y, row in enumerate(current_tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(screen, current_tetromino.color, 
                                    (GRID_OFFSET_X + (current_tetromino.x + x) * GRID_SIZE, 
                                     GRID_OFFSET_Y + (current_tetromino.y + y) * GRID_SIZE, 
                                     GRID_SIZE, GRID_SIZE))
                    pygame.draw.rect(screen, WHITE, 
                                    (GRID_OFFSET_X + (current_tetromino.x + x) * GRID_SIZE, 
                                     GRID_OFFSET_Y + (current_tetromino.y + y) * GRID_SIZE, 
                                     GRID_SIZE, GRID_SIZE), 1)
    
    # Draw next tetromino preview
    if next_tetromino:
        # Draw preview box
        preview_x = GRID_OFFSET_X + GRID_WIDTH * GRID_SIZE + 50
        preview_y = GRID_OFFSET_Y + 50
        preview_size = 4 * GRID_SIZE
        
        pygame.draw.rect(screen, WHITE, (preview_x, preview_y, preview_size, preview_size), 2)
        
        # Draw "NEXT" text
        font = pygame.font.Font(None, 36)
        text = font.render("NEXT", True, WHITE)
        screen.blit(text, (preview_x, preview_y - 40))
        
        # Calculate offset to center the tetromino in the preview box
        shape_width = len(next_tetromino.shape[0]) * GRID_SIZE
        shape_height = len(next_tetromino.shape) * GRID_SIZE
        offset_x = (preview_size - shape_width) // 2
        offset_y = (preview_size - shape_height) // 2
        
        # Draw the next tetromino
        for y, row in enumerate(next_tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(screen, next_tetromino.color, 
                                    (preview_x + offset_x + x * GRID_SIZE, 
                                     preview_y + offset_y + y * GRID_SIZE, 
                                     GRID_SIZE, GRID_SIZE))
                    pygame.draw.rect(screen, WHITE, 
                                    (preview_x + offset_x + x * GRID_SIZE, 
                                     preview_y + offset_y + y * GRID_SIZE, 
                                     GRID_SIZE, GRID_SIZE), 1)
    
    # Draw score, level, and lines
    font = pygame.font.Font(None, 36)
    
    score_text = font.render(f"Score: {score}", True, WHITE)
    level_text = font.render(f"Level: {level}", True, WHITE)
    lines_text = font.render(f"Lines: {lines_cleared}", True, WHITE)
    
    screen.blit(score_text, (50, 50))
    screen.blit(level_text, (50, 100))
    screen.blit(lines_text, (50, 150))
    
    # Draw game instructions
    instructions = [
        "Controls:",
        "← → : Move",
        "↑ : Rotate",
        "↓ : Soft Drop",
        "Space : Hard Drop",
        "P : Pause"
    ]
    
    small_font = pygame.font.Font(None, 24)
    y_pos = 250
    
    for instruction in instructions:
        text = small_font.render(instruction, True, WHITE)
        screen.blit(text, (50, y_pos))
        y_pos += 30

def lock_tetromino(board, tetromino):
    for y, row in enumerate(tetromino.shape):
        for x, cell in enumerate(row):
            if cell:
                board[tetromino.y + y][tetromino.x + x] = tetromino.color
    
    return check_lines(board)

def check_lines(board):
    lines_to_clear = []
    
    for y in range(GRID_HEIGHT):
        if all(board[y]):
            lines_to_clear.append(y)
    
    if lines_to_clear:
        clear_sound.play()
    
    # Clear lines from bottom to top
    for line in sorted(lines_to_clear, reverse=True):
        del board[line]
        board.insert(0, [0 for _ in range(GRID_WIDTH)])
    
    return len(lines_to_clear)

def game_over():
    gameover_sound.play()
    font = pygame.font.Font(None, 72)
    text = font.render("GAME OVER", True, RED)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
    
    restart_font = pygame.font.Font(None, 36)
    restart_text = restart_font.render("Press SPACE to restart", True, WHITE)
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    
    screen.blit(text, text_rect)
    screen.blit(restart_text, restart_rect)
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False
                    return True
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return False
    
    return True

def show_pause_screen():
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))
    screen.blit(overlay, (0, 0))
    
    font = pygame.font.Font(None, 72)
    text = font.render("PAUSED", True, WHITE)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    
    screen.blit(text, text_rect)
    pygame.display.flip()

# Main game loop
def main():
    global board, current_tetromino, next_tetromino, score, level, lines_cleared
    
    board = create_board()
    current_tetromino = Tetromino()
    next_tetromino = Tetromino()
    
    score = 0
    level = 1
    lines_cleared = 0
    
    fall_speed = 0.5  # seconds per grid cell
    last_fall_time = time.time()
    
    game_paused = False
    running = True
    
    while running:
        current_time = time.time()
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if not game_paused:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        current_tetromino.move_left()
                    elif event.key == pygame.K_RIGHT:
                        current_tetromino.move_right()
                    elif event.key == pygame.K_UP:
                        current_tetromino.rotate()
                    elif event.key == pygame.K_DOWN:
                        current_tetromino.move_down()
                    elif event.key == pygame.K_SPACE:
                        current_tetromino.hard_drop()
                        lines = lock_tetromino(board, current_tetromino)
                        if lines > 0:
                            lines_cleared += lines
                            score += lines * lines * 100 * level
                            
                            # Level up every 10 lines
                            new_level = lines_cleared // 10 + 1
                            if new_level > level:
                                level = new_level
                                fall_speed = max(0.05, 0.5 - (level - 1) * 0.05)
                                levelup_sound.play()
                        
                        current_tetromino = next_tetromino
                        next_tetromino = Tetromino()
                        
                        # Check if the new tetromino can be placed
                        if not current_tetromino.is_valid_position(board):
                            draw_board(board)
                            if game_over():
                                # Reset the game
                                board = create_board()
                                current_tetromino = Tetromino()
                                next_tetromino = Tetromino()
                                score = 0
                                level = 1
                                lines_cleared = 0
                                fall_speed = 0.5
                            else:
                                running = False
                    elif event.key == pygame.K_p:
                        game_paused = True
            else:  # Game is paused
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        game_paused = False
        
        if game_paused:
            show_pause_screen()
            continue
        
        # Move tetromino down automatically
        if current_time - last_fall_time > fall_speed:
            if not current_tetromino.move_down():
                lines = lock_tetromino(board, current_tetromino)
                if lines > 0:
                    lines_cleared += lines
                    score += lines * lines * 100 * level
                    
                    # Level up every 10 lines
                    new_level = lines_cleared // 10 + 1
                    if new_level > level:
                        level = new_level
                        fall_speed = max(0.05, 0.5 - (level - 1) * 0.05)
                        levelup_sound.play()
                
                current_tetromino = next_tetromino
                next_tetromino = Tetromino()
                
                # Check if the new tetromino can be placed
                if not current_tetromino.is_valid_position(board):
                    draw_board(board)
                    if game_over():
                        # Reset the game
                        board = create_board()
                        current_tetromino = Tetromino()
                        next_tetromino = Tetromino()
                        score = 0
                        level = 1
                        lines_cleared = 0
                        fall_speed = 0.5
                    else:
                        running = False
            
            last_fall_time = current_time
        
        # Draw everything
        draw_board(board)
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
    pygame.quit()
