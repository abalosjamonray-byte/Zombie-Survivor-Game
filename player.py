from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, collision_sprites):
        super().__init__(groups)
        self.load_images()
        self.state, self.frame_index = 'idle', 0
        self.image =  pygame.image.load(join('images', 'player', 'animation', 'idle', 'idle00.png')).convert_alpha()
        self.rect = self.image.get_frect(center = pos)
        self.hitbox_rect = self.rect.inflate(0, 0)

        #movement'
        self.direction = pygame.Vector2()
        self.collision_sprites = collision_sprites

        #stats
        self.speed = 50
        self.hp = 100

        self.hit_timer = 0
        self.flash_duration = 100

        #attack logic
        self.can_take_damage = True
        self.damage_timer = 0
        self.invulnerable_duration = 500


    def load_images(self):
        self.frames = {'left': [], 'right': [], 'up': [], 'down': [], 'idle': []}

        for state in self.frames.keys():
            for file_path, sub_folders, filenames in walk(join('images', 'player', 'animation', state)):
                if filenames:
                    for filename in filenames:
                        full_path = join(file_path, filename)
                        surf = pygame.image.load(full_path).convert_alpha()
                        self.frames[state].append(surf)

    def input(self):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_d]) - int(keys[pygame.K_a]) 
        self.direction.y = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
        self.direction = self.direction.normalize() if self.direction else self.direction

    def move(self, dt):
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

    def animate(self, dt):
        #get state
        if self.direction.x != 0: 
            self.state = 'left' if self.direction.x < 0 else 'right'
        elif self.direction.y != 0:
            self.state = 'up' if self.direction.y < 0 else 'down'
        else:
            self.state = 'idle'

        #animate
        self.frame_index += 5 * dt
        self.image = self.frames[self.state][int(self.frame_index) % len(self.frames[self.state])]

    def check_vulnerability(self):
        if not self.can_take_damage:
            current_time = pygame.time.get_ticks()
            if current_time - self.damage_timer >= self.invulnerable_duration:
                self.can_take_damage = True

    def check_death(self):
        if self.hp <= 0:
            print("Player has died!")
            pygame.quit()
            exit()

    def trigger_damage(self):
        self.hit_timer = pygame.time.get_ticks()

        mask = pygame.mask.from_surface(self.image)
        self.white_surf = mask.to_surface(setcolor='dark red', unsetcolor=(0,0,0))
        self.white_surf.set_colorkey((0,0,0))

    def update(self, dt):
        self.check_vulnerability()
        self.input()
        self.move(dt)
        self.animate(dt)
        self.check_death()