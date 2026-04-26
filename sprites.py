from settings import *
from math import atan2, degrees

class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups, is_ground = False):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(topleft = pos)
        self.ground = is_ground

class CollisionSprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(topleft = pos)

class Bat(pygame.sprite.Sprite):
    def __init__(self, player, groups, collision_sprites, enemy_sprites):
        super().__init__(groups)
        #player connection
        self.player = player
        self.enemy_sprites = enemy_sprites
        self.distance = 5
        self.player_direction = pygame.Vector2(0, -1)

        #sprite setup
        self.bat_surf = pygame.image.load(join('images', 'weapon', 'melee', 'bat00.png')).convert_alpha()
        self.image = self.bat_surf
        self.rect = self.image.get_frect(center = self.player.rect.center + self.player_direction * self.distance)

        #bat stats
        self.damage = 25

        #checks if it swings
        self.old_pos_center = pygame.Vector2(self.rect.center)
        self.swing_threshold = 5

        #hit list
        self.entities_hit = []

        #knockback 
        self.knockback_strength = 2

        #collision
        self.collision_sprites = collision_sprites

    def get_direction(self):
        mouse_pos = pygame.mouse.get_pos()
        player_screen_pos = pygame.Vector2(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)

        self.player_direction = (mouse_pos - player_screen_pos)
        
        if self.player_direction.magnitude() > 0:
            self.player_direction = self.player_direction.normalize()

    def rotate_bat(self):
        angle = degrees(atan2(self.player_direction.x, self.player_direction.y)) - 90
        if self.player_direction.x > 0:
            self.image = pygame.transform.rotozoom(self.bat_surf, angle, 1)
        else:
            self.image = pygame.transform.rotozoom(self.bat_surf, abs(angle), 1)
            self.image = pygame.transform.flip(self.image, False, True)
    
    def check_velocity_hit(self):
        current_pos = pygame.Vector2(self.rect.center)
        distance_moved = current_pos.distance_to(self.old_pos_center)
        self.old_pos_center = current_pos

        #checks if the bat has swung fast enough to count as an attack
        if distance_moved > self.swing_threshold:
            collided_enemies = pygame.sprite.spritecollide(self, self.enemy_sprites, False)

            #puts enemy in hit list if it has not been hit already
            for enemy in collided_enemies:
                if enemy not in self.entities_hit:
                    if hasattr(enemy, 'health'):
                        #dealiong the damage
                        enemy.health -= self.damage
                        self.entities_hit.append(enemy)

                        player_pos = pygame.Vector2(self.player.rect.center)
                        enemy_pos = pygame.Vector2(enemy.rect.center)

                        #dealing knockback
                        if (enemy_pos - player_pos).magnitude() > 0:
                            knockback_direction = (enemy_pos - player_pos).normalize()
                                
                            enemy.knockback_vector = knockback_direction * self.knockback_strength

                            self.can_apply_knockback = False

                        if enemy.health <= 0:
                                enemy.kill
                    print(f"Enemy HP: {enemy.health}")

        #removes the enemies inside the hit list if the bat stopped swinging
        else:
            self.entities_hit.clear()

    def update(self, _):
        self.get_direction()
        self.rotate_bat()
        self.check_velocity_hit()
        self.rect = self.image.get_frect(center = self.player.rect.center + self.player_direction * self.distance)

class Gun(pygame.sprite.Sprite):
    def __init__(self, player, groups):
        super().__init__(groups)
        #player connection
        self.player = player
        self.distance = 10
        self.player_direction = pygame.Vector2(0, -1)


        #sprite setup
        super().__init__(groups)
        self.gun_surf = pygame.image.load(join('images', 'weapon', 'gun', 'ar00.png')).convert_alpha()
        self.image = self.gun_surf
        self.rect = self.image.get_frect(center = self.player.rect.center + self.player_direction * self.distance)

    def get_direction(self):
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        player_pos = pygame.Vector2(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)

        if (mouse_pos - player_pos).magnitude() > 0:
            self.player_direction = (mouse_pos - player_pos).normalize()
        else:
            self.player_direction = pygame.Vector2(0, -1)

    def rotate_gun(self):
        angle = degrees(atan2(self.player_direction.x, self.player_direction.y)) - 90
        if self.player_direction.x > 0:
            self.image = pygame.transform.rotozoom(self.gun_surf, angle, 1)
        else:
            self.image = pygame.transform.rotozoom(self.gun_surf, abs(angle), 1)
            self.image = pygame.transform.flip(self.image, False, True)


    def update(self, _):
        self.get_direction()
        self.rotate_gun()
        self.rect.center = self.player.rect.center + self.player_direction * self.distance

class Bullet(pygame.sprite.Sprite):

    def __init__(self, surf, pos, direction, groups, collision_sprites, enemy_sprites):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(center = pos)
        self.spawn_timer = pygame.time.get_ticks()
        self.lifetime = 3000

        self.direction = direction
        self.speed = 500
        self.damage = 25

        self.collision_sprites = collision_sprites
        self.enemy_sprites = enemy_sprites 

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt

        #collision with enemies
        if pygame.sprite.spritecollide(self, self.enemy_sprites, False):
            for enemy in pygame.sprite.spritecollide(self, self.enemy_sprites, False):
                enemy.health -= self.damage
            self.kill()

        #collision with walls
        if pygame.sprite.spritecollide(self, self.collision_sprites, False):
            self.kill()

        #bullet lifetime
        if pygame.time.get_ticks() - self.spawn_timer >= self.lifetime:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, frames, attack_frames, groups, player, collision_sprites):
        super().__init__(groups)
        self.player = player
        
        #walking animation
        self.frames, self.frame_index = frames, 0
        self.image = self.frames[self.frame_index]
        self.animation_speed = 6

        #attack animation
        self.attack_frames, self.attack_frame_index = attack_frames, 0
        self.attack_image = self.attack_frames[self.attack_frame_index]
        self.attack_animation_speed = 10
        
        #rect
        self.rect = self.image.get_frect(center = pos)
        self.hitbox_rect = self.rect.inflate(0, 0)
        self.collision_sprites = collision_sprites
        self.direction = pygame.Vector2()
        
        #knockback
        self.knockback_vector = pygame.Vector2()
        self.knockback_friction = 0.9

        #stats
        self.speed = 50
        self.health = 10
        self.points = 50

    def attack(self, dt):
        if self.rect.colliderect(self.player.rect):
            self.attack_frame_index += self.attack_animation_speed * dt
            self.image = self.attack_frames[int(self.attack_frame_index) % len(self.attack_frames)]
            if self.player.can_take_damage:
                self.player.hp -= self.damage
                self.player.can_take_damage = False
                self.player.damage_timer = pygame.time.get_ticks()
                print(f"Player HP: {self.player.hp}")

    def animate(self, dt):
        self.frame_index += self.animation_speed * dt
        self.image = self.frames[int(self.frame_index) % len(self.frames)]

    def move(self, dt):
        #get direction
        player_pos = pygame.Vector2(self.player.rect.center)
        enemy_pos = pygame.Vector2(self.rect.center)
        
        if (player_pos - enemy_pos).magnitude() > 0:
            self.direction = (player_pos - enemy_pos).normalize()
        else:
            self.direction = pygame.Vector2()

        #update the rect position
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.collision('vertical')
        self.rect.center = self.hitbox_rect.center

    def collision(self, direction):
        for sprites in self.collision_sprites:
            if sprites.rect.colliderect(self.hitbox_rect):
                if direction == 'horizontal':
                    if self.direction.x > 0: self.hitbox_rect.right = sprites.rect.left
                    if self.direction.x < 0: self.hitbox_rect.left = sprites.rect.right
                else:
                    if self.direction.y < 0: self.hitbox_rect.top = sprites.rect.bottom
                    if self.direction.y > 0: self.hitbox_rect.bottom = sprites.rect.top

    def check_death(self):
        if self.health <= 0:
            if hasattr(self, 'game'):
                self.game.score += self.points
            self.kill()

    def update(self, dt):
        self.animate(dt)
        self.move(dt)
        self.check_death()
        self.attack(dt)

        if self.knockback_vector.magnitude() > 0.1:
            self.hitbox_rect.center += self.knockback_vector
            self.knockback_vector *= self.knockback_friction

class BigZombie(Enemy):
    def __init__(self, pos, frames, attack_frames, groups, player, collision_sprites):
        super().__init__(pos, frames, attack_frames, groups, player, collision_sprites)
        self.speed = 30
        self.health = 100
        self.damage = 10
        self.points = 100

class SmallZombie(Enemy):
    def __init__(self, pos, frames, attack_frames, groups, player, collision_sprites):
        super().__init__(pos, frames, attack_frames, groups, player, collision_sprites)
        self.speed = 70
        self.health = 50
        self.animation_speed = 12
        self.damage = 5
