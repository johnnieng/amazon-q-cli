import os
import numpy as np
from scipy.io import wavfile

def create_sound_effects():
    print("Creating sound effects...")
    
    sound_dir = os.path.join(os.path.dirname(__file__), 'sounds')
    if not os.path.exists(sound_dir):
        os.makedirs(sound_dir)
    
    # Player shoot sound
    sample_rate = 44100
    duration = 0.2
    t = np.linspace(0, duration, int(sample_rate * duration))
    shoot_sound = np.sin(2 * np.pi * 440 * t) * np.exp(-5 * t)
    shoot_sound = np.int16(shoot_sound / np.max(np.abs(shoot_sound)) * 32767)
    wavfile.write(os.path.join(sound_dir, 'player_shoot.wav'), sample_rate, shoot_sound)
    
    # Explosion sound
    duration = 0.5
    t = np.linspace(0, duration, int(sample_rate * duration))
    explosion_sound = np.random.uniform(-1, 1, int(sample_rate * duration)) * np.exp(-3 * t)
    explosion_sound = np.int16(explosion_sound / np.max(np.abs(explosion_sound)) * 32767)
    wavfile.write(os.path.join(sound_dir, 'explosion.wav'), sample_rate, explosion_sound)
    
    # Enemy shoot sound
    duration = 0.15
    t = np.linspace(0, duration, int(sample_rate * duration))
    enemy_shoot = np.sin(2 * np.pi * 220 * t) * np.exp(-10 * t)
    enemy_shoot = np.int16(enemy_shoot / np.max(np.abs(enemy_shoot)) * 32767)
    wavfile.write(os.path.join(sound_dir, 'enemy_shoot.wav'), sample_rate, enemy_shoot)
    
    # Game over sound
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    game_over = np.sin(2 * np.pi * np.linspace(440, 110, int(sample_rate * duration)))
    game_over = np.int16(game_over / np.max(np.abs(game_over)) * 32767)
    wavfile.write(os.path.join(sound_dir, 'game_over.wav'), sample_rate, game_over)
    
    # Level complete sound
    duration = 0.7
    t = np.linspace(0, duration, int(sample_rate * duration))
    level_complete = np.sin(2 * np.pi * np.linspace(220, 880, int(sample_rate * duration)))
    level_complete = np.int16(level_complete / np.max(np.abs(level_complete)) * 32767)
    wavfile.write(os.path.join(sound_dir, 'level_complete.wav'), sample_rate, level_complete)
    
    print("Sound effects created successfully!")

if __name__ == "__main__":
    create_sound_effects()
