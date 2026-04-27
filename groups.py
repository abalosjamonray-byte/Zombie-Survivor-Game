from settings import *

class AllSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.Vector2()

    def draw(self, target_pos):

        self.offset.x = -(target_pos[0] - WINDOW_WIDTH / 2)
        self.offset.y = -(target_pos[1] - WINDOW_HEIGHT / 2)

        ground_sprites = [sprite for sprite in self if hasattr(sprite, 'ground') and sprite.ground]
        object_sprites = [sprite for sprite in self if not hasattr(sprite, 'ground') or not sprite.ground]

        for sprite in ground_sprites:
            self.display_surface.blit(sprite.image, sprite.rect.topleft + self.offset)

        for sprite in sorted(object_sprites, key = lambda sprite: sprite.rect.centery):
            self.display_surface.blit(sprite.image, sprite.rect.topleft + self.offset)

            if hasattr(sprite, 'hit_timer') and sprite.hit_timer > 0:
                if pygame.time.get_ticks() - sprite.hit_timer < sprite.flash_duration:
                    self.display_surface.blit(sprite.white_surf, sprite.rect.topleft + self.offset)

