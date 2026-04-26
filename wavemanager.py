from settings import *

class WaveManager:
    def __init__(self):
        self.current_wave = 0
        self.enemies_to_spawn = 0
        self.spawned_this_wave = 0
        self.spawn_speed = 1000  
        self.last_spawn_time = 0
        self.is_intermission = False
        self.intermission_start_time = 0
        self.intermission_duration = 3000

        self.enemy_multiplier = 5

    def start_next_wave(self):
        self.current_wave += 1
        self.spawned_this_wave = 0
        self.is_intermission = False

        self.enemies_to_spawn = self.current_wave * self.enemy_multiplier

        self.spawn_speed = max(300, self.spawn_speed * 0.9)