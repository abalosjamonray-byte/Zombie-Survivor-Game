from settings import *
from player import Player
from sprites import *
from wavemanager import *
from pytmx.util_pygame import load_pygame
from random import randint, choice
from groups import AllSprites

class Game:
    def __init__(self):
        #setup
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
        pygame.display.set_caption('Survivor')
        self.clock = pygame.time.Clock()
        self.running = True

        #groups
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.ammo_refill_sprites = pygame.sprite.Group()

        #gun timer
        self.can_shoot = True
        self.shoot_time = 0
        self.gun_cooldown = 100
        self.is_reloading = False
        self.reload_time = 2000
        self.reload_start_time = 0

        #gun shooting animation
        self.shooting_frames = []
        self.shooting_frame_index = 0
        self.shooting_animation_speed = 15

        #magazine and ammo
        self.magazine = 30
        self.magazine_capacity = 30
        self.ammo_reserve = 90

        #ammo refill cooldown
        self.last_refill_time = 0
        self.refill_cooldown = 2000

        #sound effects
        self.reload_sound = pygame.mixer.Sound(join('sounds', 'ak47_reload.mp3'))
        self.shoot_sound = pygame.mixer.Sound(join('sounds', 'AK47', 'ak4704.wav'))
        self.zombie_hit_sound = pygame.mixer.Sound(join('sounds', 'impact', 'hit zombie.mp3'))

        #enemy timer
        self.wave_manager = WaveManager()
        self.wave_manager.start_next_wave()
        self.spawn_position = []

        #waves
        self.wave_text = pygame.font.SysFont('Arial', 8)
        self.wave_finished_text = pygame.font.SysFont('Trebuchet MS', 25)

        #player score
        self.score = 0

        #game state
        self.state = 'MENU'
        self.play_music('mm02')
        self.title = 'Zombie Survivor'
        self.death_text = 'YOU DIED'
        self.title_font = pygame.font.SysFont('Comic Sans MS', 20)
        self.menu_font = pygame.font.SysFont('Comic Sans MS', 10)
        self.death_font = pygame.font.SysFont('Comic Sans MS', 30)
        self.how_to_play_action_font = pygame.font.SysFont('Comic Sans MS', 9)
        self.how_to_play_text_font = pygame.font.SysFont('Comic Sans MS', 8)

        #button sounds
        self.button_sound = pygame.mixer.Sound(join('sounds', 'button sounds', 'bs02.wav'))

        self.load_images()
        self.setup()

    def play_music(self, music_name):
        pygame.mixer.music.load(join('sounds', 'music', f'{music_name}.mp3'))
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(loops=-1)

    def load_images(self):
        self.shooting_frames = []
        for folder_path, _, file_names in walk(join('images', 'weapon', 'gun')):
            # Sorting is CRITICAL so frame 1 comes before frame 2
            for image_name in sorted(file_names):
                full_path = join(folder_path, image_name)
                image_surf = pygame.image.load(full_path).convert_alpha()
                self.shooting_frames.append(image_surf)

        self.btn_idle_surf = pygame.image.load(join('images', 'buttons', 'idle.png')).convert_alpha()
        self.btn_hover_surf = pygame.image.load(join('images', 'buttons', 'hover.png')).convert_alpha()

        self.bullet_surf = pygame.image.load(join('images', 'weapon', 'bullet', 'b01.png')).convert_alpha()

        folders = list(walk(join('images', 'enemies')))[0][1]
        self.enemy_frames = {}
        for folder in folders:
            for folder_path, _, file_names in walk(join('images', 'enemies', folder)):
                self.enemy_frames[folder] = []
                for file_name in file_names:
                    full_path = join(folder_path, file_name)
                    surf = pygame.image.load(full_path).convert_alpha()
                    self.enemy_frames[folder].append(surf)

    def input(self):
        keys = pygame.key.get_pressed()
            
        #switch to Gun
        if keys[pygame.K_1]:
            self.active_weapon = self.gun
            self.all_sprites.add(self.gun)
            self.all_sprites.remove(self.bat) 
                
        #switch to Bat
        if keys[pygame.K_2]:
            self.active_weapon = self.bat
            self.all_sprites.add(self.bat) 
            self.all_sprites.remove(self.gun) 

        if pygame.mouse.get_pressed()[0] and self.can_shoot and not self.is_reloading and self.magazine > 0:
            if isinstance(self.active_weapon, Gun):
                pos = self.gun.rect.center + self.gun.player_direction * 20
                Bullet(self.bullet_surf, pos, self.gun.player_direction, (self.all_sprites, self.bullet_sprites), self.collision_sprites, self.enemy_sprites)
                self.shoot_sound.play()

                self.can_shoot = False
                self.magazine -= 1
                self.shoot_time = pygame.time.get_ticks()

                if self.magazine <= 0 and self.ammo_reserve > 0:
                    self.is_reloading = True
                    self.reload_start_time = pygame.time.get_ticks()
                    self.reload_sound.play()

        if keys[pygame.K_r]:
            if not self.is_reloading and self.magazine < self.magazine_capacity and self.ammo_reserve > 0:
                if isinstance(self.active_weapon, Gun):
                    self.is_reloading = True
                    self.reload_start_time = pygame.time.get_ticks()
                    self.reload_sound.play()
            elif isinstance(self.active_weapon, Bat):
                # Implement melee attack logic here
                pass

    def gun_timer(self):
        if not isinstance(self.active_weapon, Gun): return
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_time >= self.gun_cooldown:
                self.can_shoot = True

    def gun_reload(self):
        if not isinstance(self.active_weapon, Gun): return
        if self.is_reloading:
            current_time = pygame.time.get_ticks()
            if current_time - self.reload_start_time >= self.reload_time:
            
            # Check if we have enough in the reserve
                if self.ammo_reserve >= (self.magazine_capacity - self.magazine):
                    self.ammo_reserve -= (self.magazine_capacity - self.magazine)
                    self.magazine += (self.magazine_capacity - self.magazine)
                else:
                    # If we don't have enough, just take what's left
                    self.magazine += self.ammo_reserve 
                    self.ammo_reserve = 0
            
                self.is_reloading = False

    def check_ammo_refill(self):
        keys = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks()

        if pygame.sprite.spritecollide(self.player, self.ammo_refill_sprites, False) and keys[pygame.K_e]:
            if current_time - self.last_refill_time >= self.refill_cooldown and self.ammo_reserve < 150:
                self.ammo_reserve += 30
                self.last_refill_time = current_time

    def setup(self):
        map = load_pygame(join('data', 'map', 'pygame map.tmx'))

        #for loop for the ground(grass, pavement, etc.)
        for layer in map.visible_layers:
            if hasattr(layer, 'data'):
                is_ground = layer.name in ['dirt', 'pavement', 'road', 'grass', 'floor', 'buildings', 'walls', 'windows', 'roof']
                for x, y, surf in layer.tiles():
                    Sprite((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites, is_ground = is_ground)

        #objects that have collisions but have no surf
        for obj in map.get_layer_by_name('collision'):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), (self.collision_sprites))

        #objects that have a surf but no collision
        for obj in map.get_layer_by_name('game objects'):
            Sprite((obj.x, obj.y), obj.image, (self.all_sprites))

        #where I spawn entities
        for marker in map.get_layer_by_name('entities'):
            if marker.name == 'spawnpoint': #the player
                self.player = Player((marker.x, marker.y), self.all_sprites, self.collision_sprites)
        
                self.gun = Gun(self.player, self.all_sprites)
                self.bat = Bat(self.player, self.all_sprites, self.collision_sprites, self.enemy_sprites)
                
                # This is the "Switch" that controls your methods
                self.active_weapon = self.bat
                self.all_sprites.remove(self.gun)
            elif marker.name == 'ammo refill': #for the ammo refill
                refill_zone = pygame.sprite.Sprite(self.ammo_refill_sprites)
                refill_zone.rect = pygame.Rect(marker.x, marker.y, marker.width, marker.height)
            elif marker.name == 'enemy': #the enemies
                self.spawn_position.append((marker.x, marker.y))

    def spawn_enemy(self):
        pos = choice(self.spawn_position)
        if randint(0, 10) > 8:
            zombie = BigZombie(pos, self.enemy_frames['bigZombie'], self.enemy_frames['bz attack'], 
                      (self.all_sprites, self.enemy_sprites), self.player, self.collision_sprites)
        else:
            zombie = SmallZombie(pos, self.enemy_frames['smallZombie'], self.enemy_frames['sz attack'], 
                        (self.all_sprites, self.enemy_sprites), self.player, self.collision_sprites)
        zombie.game = self

    def wave_logic(self):
        current_time = pygame.time.get_ticks()

        # 1. Spawning phase
        if self.wave_manager.spawned_this_wave < self.wave_manager.enemies_to_spawn:
            if current_time - self.wave_manager.last_spawn_time >= self.wave_manager.spawn_speed:
                self.spawn_enemy()
                self.wave_manager.spawned_this_wave += 1
                self.wave_manager.last_spawn_time = current_time

        # 2. Check if wave is cleared
        elif not self.enemy_sprites and not self.wave_manager.is_intermission:
            self.wave_manager.is_intermission = True
            self.wave_manager.intermission_start_time = current_time
            print("Wave Cleared! Intermission...")

        # 3. Intermission timer
        if self.wave_manager.is_intermission:
            if current_time - self.wave_manager.intermission_start_time >= self.wave_manager.intermission_duration:
                self.wave_manager.start_next_wave()

    def display_stats(self):
        #displaying current wave number
        wave_str = f'Wave: {self.wave_manager.current_wave}'
        wave_surf = self.wave_text.render(wave_str, False, (0, 0, 0))

        self.display_surface.blit(wave_surf, (10, 10))

        #enemies left
        enemies_still_to_spawn = self.wave_manager.enemies_to_spawn - self.wave_manager.spawned_this_wave
        enemies_alive = len(self.enemy_sprites)
        total_remaining = enemies_still_to_spawn + enemies_alive

        rem_surf = self.wave_text.render(f'Zombies Left: {total_remaining}', False, 'orange')
        rem_rect = rem_surf.get_rect(center = (WINDOW_WIDTH / 2, 10))
        
        self.display_surface.blit(rem_surf, rem_rect)

        #displaying current ammo and ammo reserve
        ammo_color = 'red' if self.magazine <= 5 else 'black'
        ammo_surf = self.wave_text.render(f'Ammo: {self.magazine} / {self.ammo_reserve}', False, ammo_color)
        self.display_surface.blit(ammo_surf, (10, 30))

        #displaying score
        score_surf = self.wave_text.render(f'Score: {self.score}', False, 'black')
        score_rect = score_surf.get_rect(topright = (WINDOW_WIDTH - 20, 20))
        self.display_surface.blit(score_surf, score_rect)

        #when the playerr completes a wave
        if self.wave_manager.is_intermission:
            complete_surf = self.wave_finished_text.render('WAVE COMPLETED', False, (0, 0, 0))
            complete_rect = complete_surf.get_rect(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))

            self.display_surface.blit(complete_surf, complete_rect)

    def create_button(self, text, y_pos, event_list):
        width = self.btn_idle_surf.get_width()
        height = self.btn_idle_surf.get_height()

        x_pos = (WINDOW_WIDTH / 2) - (width / 2)
        button_rect = pygame.Rect(x_pos, y_pos, width, height)
        
        mouse_pos = pygame.mouse.get_pos()
        
        current_surf = self.btn_idle_surf
        if button_rect.collidepoint(mouse_pos):
            current_surf = self.btn_hover_surf 
            for event in event_list:
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    return True

        self.display_surface.blit(current_surf, button_rect)
        
        x_offset, y_offset = 0, -2

        text_surf = self.menu_font.render(text, False, 'white')
        text_center = (button_rect.centerx + x_offset, button_rect.centery + y_offset)
        text_rect = text_surf.get_rect(center = text_center)
        self.display_surface.blit(text_surf, text_rect)
        
        return False

    def reset_game(self):
        #clear all groups
        self.all_sprites.empty()
        self.enemy_sprites.empty()
        self.bullet_sprites.empty()
        
        #re-run setup to place player and map objects
        self.setup()
        
        #reset stats
        self.magazine = 30
        self.ammo_reserve = 90
        self.score = 0
        self.wave_manager.current_wave = 0
        self.wave_manager.start_next_wave()

    def display_how_to_play(self, event_list):
        self.all_sprites.draw(self.player.rect.center)
        
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(190) 
        overlay.fill('black')
        self.display_surface.blit(overlay, (0,0))

        #title of the screen
        title_surf = self.title_font.render('How to Play', False, 'white')
        title_rect = title_surf.get_frect(center = (WINDOW_WIDTH / 2, (WINDOW_HEIGHT / 2) - 75))
        self.display_surface.blit(title_surf, title_rect)

        #the action 
        text_surf = self.how_to_play_action_font.render('Switching Weapons', False, 'white')
        text_rect = text_surf.get_frect(center = ((WINDOW_WIDTH / 2) - 95, (WINDOW_HEIGHT / 2) - 50))
        self.display_surface.blit(text_surf, text_rect)

        text_surf = self.how_to_play_action_font.render('Reloading', False, 'white')
        text_rect = text_surf.get_frect(center = ((WINDOW_WIDTH / 2) - 112, (WINDOW_HEIGHT / 2) - 25))
        self.display_surface.blit(text_surf, text_rect)

        text_surf = self.how_to_play_action_font.render('Refilling Ammo', False, 'white')
        text_rect = text_surf.get_frect(center = ((WINDOW_WIDTH / 2) - 102, (WINDOW_HEIGHT / 2) + 0))
        self.display_surface.blit(text_surf, text_rect)

        text_surf = self.how_to_play_action_font.render('Aiming with the Gun', False, 'white')
        text_rect = text_surf.get_frect(center = ((WINDOW_WIDTH / 2) - 95, (WINDOW_HEIGHT / 2) + 25))
        self.display_surface.blit(text_surf, text_rect)

        text_surf = self.how_to_play_action_font.render('Hiting with the bat', False, 'white')
        text_rect = text_surf.get_frect(center = ((WINDOW_WIDTH / 2) - 95, (WINDOW_HEIGHT / 2) + 50))
        self.display_surface.blit(text_surf, text_rect)

        #description
        text_surf = self.how_to_play_text_font.render('to switch, click either one for the gun, or two for the bat.', False, 'white')
        text_rect = text_surf.get_frect(topleft = ((WINDOW_WIDTH / 2) - 120, (WINDOW_HEIGHT / 2) - 45))
        self.display_surface.blit(text_surf, text_rect)

        text_surf = self.how_to_play_text_font.render('to reload, simply press r.', False, 'white')
        text_rect = text_surf.get_frect(topleft = ((WINDOW_WIDTH / 2) - 120, (WINDOW_HEIGHT / 2) - 20))
        self.display_surface.blit(text_surf, text_rect)

        text_surf = self.how_to_play_text_font.render('to refil, look for a green ammo refill box then press e.', False, 'white')
        text_rect = text_surf.get_frect(topleft = ((WINDOW_WIDTH / 2) - 120, (WINDOW_HEIGHT / 2) + 5))
        self.display_surface.blit(text_surf, text_rect)

        text_surf = self.how_to_play_text_font.render('your gun direction follows the mouse cursor, so aim with the cursor.', False, 'white')
        text_rect = text_surf.get_frect(topleft = ((WINDOW_WIDTH / 2) - 120, (WINDOW_HEIGHT / 2) + 30))
        self.display_surface.blit(text_surf, text_rect)

        text_surf = self.how_to_play_text_font.render('swing with the mouse cursor as the bat follows the mouse cursor as well.', False, 'white')
        text_rect = text_surf.get_frect(topleft = ((WINDOW_WIDTH / 2) - 120, (WINDOW_HEIGHT / 2) + 55))
        self.display_surface.blit(text_surf, text_rect)
        
        if self.create_button('BACK', (WINDOW_HEIGHT / 2) + 70, event_list):
            self.button_sound.play()
            self.state = 'MENU'

    def display_menu(self, event_list):
        self.all_sprites.draw(self.player.rect.center)
        
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(190) 
        overlay.fill('black')
        self.display_surface.blit(overlay, (0,0))

        title_surf = self.title_font.render(self.title, False, 'white')
        title_rect = title_surf.get_frect(center = (WINDOW_WIDTH / 2, (WINDOW_HEIGHT / 2) - 70))
        self.display_surface.blit(title_surf, title_rect)

        if self.create_button('START GAME', (WINDOW_HEIGHT / 2) - 40, event_list):
            self.reset_game()
            self.button_sound.play()
            self.play_music('mm03')
            self.state = 'GAME'

        if self.create_button('HOW TO PLAY', (WINDOW_HEIGHT / 2) + 5, event_list):
            self.button_sound.play()
            self.state = 'TUTORIAL'

        if self.create_button('QUIT', (WINDOW_HEIGHT / 2) + 50, event_list):
            self.button_sound.play()
            self.running = False

    def display_pause_screen(self, event_list):
        self.all_sprites.draw(self.player.rect.center)
        
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill('black')
        self.display_surface.blit(overlay, (0,0))

        if self.create_button('RESUME', (WINDOW_HEIGHT / 2) - 40, event_list):
            self.button_sound.play()
            pygame.mixer.music.unpause()
            self.state = 'GAME'

        if self.create_button('RESTART', (WINDOW_HEIGHT / 2) + 5, event_list):
            self.reset_game()
            self.button_sound.play()
            self.play_music('mm03')
            self.state = 'GAME'

        if self.create_button('MAIN MENU', (WINDOW_HEIGHT / 2) + 50, event_list):
            self.reset_game()
            self.button_sound.play()
            self.play_music('mm02')
            self.state = 'MENU'

    def display_death_screen(self, event_list):
        self.all_sprites.draw(self.player.rect.center)

        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill('black')
        self.display_surface.blit(overlay, (0,0))

        death_surf = self.death_font.render(self.death_text, False, 'white')
        death_rect = death_surf.get_frect(center = (WINDOW_WIDTH / 2, (WINDOW_HEIGHT / 2) - 40))
        self.display_surface.blit(death_surf, death_rect)

        if self.create_button('RESTART', (WINDOW_HEIGHT / 2) + 0, event_list):
            self.button_sound.play()
            self.reset_game()
            self.play_music('mm03')
            self.state = 'GAME'

        if self.create_button('MAIN MENU', (WINDOW_HEIGHT / 2) + 40, event_list):
            self.reset_game()
            self.button_sound.play()
            self.play_music('mm02')
            self.state = 'MENU'

    def run(self):
        while self.running:
            #dt
            dt = self.clock.tick() / 1000

            event_list = pygame.event.get()

            #event loop
            for event in event_list:
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == 'GAME': 
                            self.state = 'PAUSE'
                            pygame.mixer.music.pause()
                        elif self.state == 'PAUSE': 
                            self.state = 'GAME'
                            pygame.mixer.music.unpause()
                
            if self.state == 'MENU':
                self.display_menu(event_list)

            elif self.state == 'TUTORIAL':
                self.display_how_to_play(event_list)

            elif self.state == 'PAUSE':
                self.display_pause_screen(event_list)

            elif self.state == 'DEATH':
                pygame.mixer.music.stop()
                self.display_death_screen(event_list)

            elif self.state == 'GAME':
                #update
                self.input()
                self.gun_timer()
                self.gun_reload()
                self.wave_logic()
                self.check_ammo_refill()
                self.all_sprites.update(dt)

                if self.player.hp <= 0:
                    self.state = 'DEATH'

                #draw
                self.display_surface.fill('black')
                self.all_sprites.draw(self.player.rect.center)

                self.display_stats()

            pygame.display.flip()
        
        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()