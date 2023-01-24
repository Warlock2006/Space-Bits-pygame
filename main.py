import collections
from typing import Callable, Any

import pygame
from pygame.sprite import AbstractGroup


class Game:
    def __init__(self, width: int, height: int, screen, fps: int = 0):
        self.height = height
        self.width = width
        self.fps = fps

        self.running = False

        self.screen = screen

        self.event_handlers: dict[int, list[Callable[[pygame.event.Event], None]]] = collections.defaultdict(list)

    def setup(self):
        pass

    def register_event(self, event_type: int, action: Callable[[pygame.event.Event], None]):
        self.event_handlers[event_type].append(action)

    def start(self):

        timer = pygame.time.Clock()

        self.running = True
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if callbacks := self.event_handlers[event.type]:
                    for callback in callbacks:
                        callback(event)
            delta_t = timer.tick(self.fps) / 1000
            self.screen.fill(pygame.Color('black'))
            self.draw(self.screen)
            self.update(delta_t)
            pygame.display.flip()

    def update(self, delta_t: float):
        pass

    def draw(self, screen: pygame.Surface):
        pass


width, height = 1920, 1080
screen = pygame.display.set_mode((width, height))
pygame.init()
pygame.font.init()
font = pygame.font.Font("MinimalPixel v2.ttf", 20)
score_image = pygame.image.load('score_text.png')
laser_sound1 = pygame.mixer.Sound('Laser_shoot 66.wav')
laser_sound2 = pygame.mixer.Sound('Laser_shoot 70 (1).wav')
laser_sound3 = pygame.mixer.Sound('Laser_shoot 85 (1).wav')
hit_sound = pygame.mixer.Sound('Hit_hurt 64.wav')
explosion_sound = pygame.mixer.Sound('Explosion 20.wav')
clicksound = pygame.mixer.Sound('click.wav')
win_sound = pygame.mixer.Sound('You Win (Street Fighter) - Sound Effect (256  kbps).mp3')
pygame.mixer.music.load('Lost In The Neon Light - Fei Theme 8 bit (Space Rangers cover).mp3')
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play()


class Space(pygame.sprite.Sprite):
    def __init__(self, loc, *groups: AbstractGroup):
        super().__init__(*groups)
        self.image = pygame.image.load('space.png')
        self.image = pygame.transform.scale(self.image, (1920, 1080))
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.bottom = loc

    def update(self, *args: Any, **kwargs: Any):
        self.rect.bottom += 2
        if self.rect.top >= height:
            self.rect.bottom = 0


class Explosion(pygame.sprite.Sprite):
    def __init__(self, pos, scale, *groups):
        super().__init__(*groups)
        self.images = []
        for i in range(1, 9):
            image = pygame.image.load(f'{i}.png')
            image = pygame.transform.scale(image, scale)
            self.images.append(image)
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = pos
        self.counter = 0

    def update(self, *args: Any, **kwargs: Any) -> None:
        exp_speed = 7
        self.counter += 1
        if self.counter >= exp_speed and self.index < len(self.images) - 1:
            self.counter = 0
            self.index += 1
            self.image = self.images[self.index]
        if self.index >= len(self.images) - 1 and self.index >= exp_speed:
            self.kill()


class Bullet(pygame.sprite.Sprite):
    y_speed = 10

    def __init__(self, pos, *groups: AbstractGroup):
        super().__init__(*groups)
        self.image = pygame.image.load('playerbullet.png')
        self.image = pygame.transform.scale(self.image, (30, 30))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = pos

    def update(self, *args: Any, **kwargs: Any) -> None:
        if self.rect.y < 0:
            self.kill()
        self.move()

    def move(self):
        dy = 0
        dy -= Bullet.y_speed
        self.rect.y += dy


class PlayerBullet(Bullet):
    def __init__(self, pos, *groups: AbstractGroup):
        super(PlayerBullet, self).__init__(pos, *groups)
        self.image = pygame.image.load('playerbullet.png')
        self.image = pygame.transform.scale(self.image, (30, 30))


class Player(pygame.sprite.Sprite):
    x_speed = 3
    y_speed = 3

    def __init__(self, pos: tuple[int, int], *groups: AbstractGroup):
        super().__init__(*groups)
        self.image = pygame.image.load("main_ship_idle.png")
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = pos
        self.x_speed = 0
        self.y_speed = 0
        self.is_moving_left = None
        self.is_moving_right = None
        self.is_moving_forward = None
        self.is_moving_back = None
        self.is_alive = True
        self.is_shooting = False
        self.score = 0
        self.timer = 0
        self.bullets = pygame.sprite.Group()

    def update(self):
        for group in self.groups():
            for s in group:
                if self.rect.colliderect(s.rect) and type(s) != Player:
                    self.is_alive = False
                    exp = Explosion((self.rect.x, self.rect.y), (50, 50), self.bullets)
                    explosion_sound.play()
                    self.kill()
                    if type(s) != Boss:
                        s.kill()
                if type(s) == ShootingEnemy or type(s) == Boss:
                    s: ShootingEnemy
                    for b in s.bullets:
                        if self.rect.colliderect(b):
                            b.kill()
                            self.is_alive = False
                            exp = Explosion((self.rect.x, self.rect.y), (50, 50), self.bullets)
                            explosion_sound.play()
                            self.kill()

        if self.is_alive:
            if not self.is_shooting:
                self.timer = 0
            else:
                self.timer += 1
                self.shoot(self.timer)
            self.move()

    def set_flags(self, event):
        if event.type == pygame.KEYDOWN:
            is_down = True
        else:
            is_down = False
        if event.key == pygame.K_LEFT:
            self.is_moving_left = is_down
        elif event.key == pygame.K_RIGHT:
            self.is_moving_right = is_down
        elif event.key == pygame.K_UP:
            self.is_moving_forward = is_down
        elif event.key == pygame.K_DOWN:
            self.is_moving_back = is_down
        elif event.key == pygame.K_SPACE:
            self.is_shooting = is_down

    def move(self):
        dx = 0
        dy = 0
        if self.is_alive:
            if self.is_moving_left:
                dx -= Player.x_speed
                self.image = pygame.image.load('main_ship_l.png')
                self.image = pygame.transform.scale(self.image, (51, 51))
            if self.is_moving_right:
                dx += Player.x_speed
                self.image = pygame.image.load('main_ship_r.png')
                self.image = pygame.transform.scale(self.image, (51, 51))
            if (self.is_moving_left and self.is_moving_right) or (not self.is_moving_right and not self.is_moving_left):
                self.image = pygame.image.load("main_ship_idle.png")
                self.image = pygame.transform.scale(self.image, (51, 51))
            if self.is_moving_forward:
                dy -= Player.y_speed
            if self.is_moving_back:
                dy += Player.y_speed
            self.rect.x += dx
            self.rect.y += dy
            if self.rect.left < 0:
                self.rect.left = 0
            if self.rect.right > width:
                self.rect.right = width
            if self.rect.top < 0:
                self.rect.top = 0
            if self.rect.bottom > height:
                self.rect.bottom = height

    def shoot(self, timer):
        if self.is_alive and timer % 18 == 1:
            bullet = PlayerBullet((self.rect.centerx - 15, self.rect.top - 30), self.bullets)
            laser_sound1.set_volume(0.3)
            laser_sound1.play()


class BaseEnemy(pygame.sprite.Sprite):
    def __init__(self, pos, player: Player, *groups: AbstractGroup):
        super().__init__(*groups)
        self.image = pygame.image.load('enemy.png')
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = pos
        self.player = player
        self.is_alive = True
        self.exp = pygame.sprite.Group()

    def update(self, *args: Any, **kwargs: Any) -> None:
        if self.rect.y > height:
            self.kill()
        for b in self.player.bullets:
            if self.rect.colliderect(b.rect):
                self.is_alive = False
                exp = Explosion((self.rect.x, self.rect.y), (50, 50), self.player.bullets)
                explosion_sound.play()
                self.player.score += 10
                self.kill()
                b.kill()
        self.move()

    def move(self):
        dy = 32
        while self.rect.y > 0 and dy > 1:
            dy -= 1
        self.rect.y += dy


class EnemyBullet(Bullet):
    def __init__(self, pos, *groups: AbstractGroup):
        super(EnemyBullet, self).__init__(pos, *groups)
        self.image = pygame.image.load('enemybullet.png')
        self.image = pygame.transform.scale(self.image, (30, 30))
        self.image = pygame.transform.flip(self.image, False, True)

    def update(self, *args: Any, **kwargs: Any) -> None:
        if self.rect.y > height:
            self.kill()
        self.move()

    def move(self):
        dy = 0
        dy += Bullet.y_speed
        self.rect.y += dy


class ShootingEnemy(BaseEnemy):
    def __init__(self, pos, player: Player, *groups):
        super(ShootingEnemy, self).__init__(pos, player, *groups)
        self.image = pygame.image.load('shootingenemy.png')
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.bullets = pygame.sprite.Group()
        self.is_shooting = True
        self.is_alive = True
        self.timer = 0

    def shoot(self):
        if self.is_alive and self.timer % 100 == 0:
            bullet = EnemyBullet((self.rect.x + 10, self.rect.bottom), self.bullets)
            laser_sound2.set_volume(0.2)
            laser_sound2.play()

    def update(self, *args: Any, **kwargs: Any) -> None:
        if self.is_shooting:
            self.timer += 1
            self.shoot()
        for b in self.player.bullets:
            if self.rect.colliderect(b.rect):
                self.is_alive = False
                b.kill()
                exp = Explosion((self.rect.x, self.rect.y), (50, 50), self.player.bullets)
                explosion_sound.play()
                self.player.score += 20
                self.kill()
        self.move()

    def move(self):
        dy = 5
        while self.rect.y > 15 and dy > 0:
            dy -= 1
        self.rect.y += dy


class BossBullet(EnemyBullet):
    def __init__(self, pos, *groups):
        super().__init__(pos, *groups)
        self.image = pygame.image.load('boss_bullet.png')
        self.image = pygame.transform.scale(self.image, (40, 25))
        self.image = pygame.transform.flip(self.image, False, True)
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = pos


class Boss(pygame.sprite.Sprite):
    def __init__(self, pos, player: Player, *groups):
        super().__init__(*groups)
        self.image = pygame.image.load('boss.png')
        self.image = pygame.transform.scale(self.image, (80, 80))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = pos
        self.player = player
        self.is_alive = True
        self.is_shooting = False
        self.bullets = pygame.sprite.Group()
        self.hp = 30
        self.timer = 0
        self.dx = 3

    def update(self, *args: Any, **kwargs: Any) -> None:
        if self.is_shooting:
            self.timer += 1
            self.shoot()
        for b in self.player.bullets:
            if self.rect.colliderect(b.rect):
                self.hp -= 1
                hit_sound.set_volume(0.3)
                hit_sound.play()
                b.kill()
        if self.hp == 0:
            self.is_alive = False
            explosion = Explosion((self.rect.x, self.rect.y), (100, 100), self.player.bullets)
            explosion_sound.play()
            self.player.score += 100
            self.kill()
        self.move()

    def move(self):
        dy = 5
        while self.rect.y > 15 and dy > 0:
            dy -= 1
        self.rect.y += dy
        if dy == 0:
            self.is_shooting = True
            if self.rect.right >= width:
                self.dx = -3
            if self.rect.left <= 0:
                self.dx = 3
            self.rect.x += self.dx

    def shoot(self):
        if self.is_alive and self.timer % 60 == 0:
            bullet = BossBullet((self.rect.x + 10, self.rect.bottom), self.bullets)
            laser_sound3.set_volume(0.3)
            laser_sound3.play()


class Title(pygame.sprite.Sprite):
    def __init__(self, pos, img: str, scale_x, scale_y, *groups):
        super().__init__(*groups)
        self.image = pygame.image.load(img)
        self.image = pygame.transform.scale(self.image, (scale_x, scale_y))
        self.rect = self.image.get_rect()
        self.rect.centerx, self.rect.centery = pos


class Button(pygame.sprite.Sprite):
    start_text = pygame.transform.scale(pygame.image.load('start_text.png'), (72, 28))
    exit_text = pygame.transform.scale(pygame.image.load('exit_text.png'), (72, 28))
    restart_text = pygame.transform.scale(pygame.image.load('restart_text.png'), (72, 28))

    def __init__(self, pos, text, menu, *groups: AbstractGroup):
        super().__init__(*groups)
        self.text = text
        self.menu = menu
        self.timer = 0
        self.is_clicked = False
        self.image = pygame.image.load('idle_button.png')
        self.image = pygame.transform.scale(self.image, (120, 56))
        if self.text == 'start':
            self.image.blit(Button.start_text, (25, 10))
        elif self.text == 'exit':
            self.image.blit(Button.exit_text, (25, 10))
        elif self.text == 'restart':
            self.image.blit(Button.restart_text, (25, 10))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = pos

    def update(self, *args: Any, **kwargs: Any) -> None:
        mouse_pos = pygame.mouse.get_pos()
        mouse_x = mouse_pos[0]
        mouse_y = mouse_pos[1]
        if self.rect.left <= mouse_x <= self.rect.right and self.rect.top <= mouse_y <= self.rect.bottom:
            self.image = pygame.image.load('selected_button.png')
            self.image = pygame.transform.scale(self.image, (120, 56))
            if self.text == 'start':
                self.image.blit(Button.start_text, (25, 10))
            elif self.text == 'exit':
                self.image.blit(Button.exit_text, (25, 10))
            elif self.text == 'restart':
                self.image.blit(Button.restart_text, (25, 10))
        else:
            self.image = pygame.image.load('idle_button.png')
            self.image = pygame.transform.scale(self.image, (120, 56))
            if self.text == 'start':
                self.image.blit(Button.start_text, (25, 10))
            elif self.text == 'exit':
                self.image.blit(Button.exit_text, (25, 10))
            elif self.text == 'restart':
                self.image.blit(Button.restart_text, (25, 10))

    def click(self, event):
        if event.button == 1 and self.rect.left <= event.pos[0] <= self.rect.right and self.rect.top \
                <= event.pos[1] <= self.rect.bottom:
            self.image = pygame.image.load('clicked_button.png')
            self.image = pygame.transform.scale(self.image, (120, 56))
            self.is_clicked = True
            clicksound.play()
            self.timer = 0
            self.menu.game.setup()
            if self.text == 'start':
                self.image.blit(Button.start_text, (25, 10))
            elif self.text == 'exit':
                self.image.blit(Button.exit_text, (25, 10))
            elif self.text == 'restart':
                self.image.blit(Button.restart_text, (25, 10))


class GameOver:
    def __init__(self, width, height, game):
        self.width = width
        self.height = height
        self.game = game
        self.game_over_components = pygame.sprite.Group()
        self.title = Title((self.width // 2, self.height // 4), 'game_over.png', 400, 400, self.game_over_components)
        self.restart_button = Button((self.width // 2 - 50, self.height // 4 + 150), 'restart', self,
                                     self.game_over_components)
        self.exit_button = Button((self.width // 2 - 50, self.height // 4 + 225), 'exit', self,
                                  self.game_over_components)

    def draw(self):
        self.game_over_components.draw(screen)

    def update(self):
        self.game_over_components.update()


class Win:
    def __init__(self, width, height, game):
        self.width = width
        self.height = height
        self.game = game
        self.win = pygame.sprite.Group()
        self.title = Title((self.width // 2, self.height // 4), 'win_text.png', 400, 400, self.win)
        self.restart_button = Button((self.width // 2 - 50, self.height // 4 + 200), 'restart', self,
                                     self.win)
        self.exit_button = Button((self.width // 2 - 50, self.height // 4 + 275), 'exit', self,
                                  self.win)

    def draw(self):
        self.win.draw(screen)

    def update(self):
        self.win.update()


class Menu:
    def __init__(self, width, height, game):
        self.width = width
        self.height = height
        self.game = game
        self.menu_components = pygame.sprite.Group()
        self.title = Title((self.width // 2, self.height // 4), 'menu_text.png', 420, 190, self.menu_components)
        self.start_button = Button((self.width // 2 - 50, self.height // 4 + 150), 'start', self, self.menu_components)
        self.exit_button = Button((self.width // 2 - 50, self.height // 4 + 225), 'exit', self, self.menu_components)

    def draw(self):
        self.menu_components.draw(screen)

    def update(self):
        self.menu_components.update()


class Score(pygame.sprite.Sprite):
    def __init__(self, pos, player: Player, *groups):
        super().__init__(*groups)
        self.image = pygame.image.load('score_text.png')
        self.image = pygame.transform.scale(self.image, (110, 35))
        self.rect = self.image.get_rect()
        self.player = player
        self.rect.left, self.rect.bottom = pos

    def update(self, *args: Any, **kwargs: Any) -> None:
        score = font.render(f'{self.player.score}', True, (255, 255, 255))
        score = pygame.transform.scale(score, (score.get_width() * 2, score.get_height() * 2))
        screen.blit(score, (self.rect.right + 10, self.rect.top))


class MyGame(Game):

    def __init__(self, width: int, height: int, screen):
        super().__init__(width, height, screen=screen, fps=120)
        self.all_sprites = pygame.sprite.Group()
        self.bg = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.menu = Menu(width, height, self)
        self.game_over = GameOver(width, height, self)
        self.win = Win(width, height, self)
        self.show_menu = True
        self.show_game_over = False
        self.menu_registered = False
        self.game_over_registered = False
        self.win_registered = False
        self.show_win = False
        self.player_registered = False
        self.space_spawned = False
        self.score = None
        self.wave = 1
        self.timer = 450
        self.all_killed = True
        self.boss_was_spawned = False

    def setup(self):
        if not self.space_spawned:
            self.space = Space((0, height), self.bg)
            self.upper_space = Space((0, 0), self.bg)
            self.space_spawned = True
        if not self.win_registered:
            self.register_event(pygame.MOUSEBUTTONDOWN, self.win.exit_button.click)
            self.register_event(pygame.MOUSEBUTTONDOWN, self.win.restart_button.click)
            self.win_registered = True
        if not self.game_over_registered:
            self.register_event(pygame.MOUSEBUTTONDOWN, self.game_over.exit_button.click)
            self.register_event(pygame.MOUSEBUTTONDOWN, self.game_over.restart_button.click)
            self.game_over_registered = True
        if not self.menu_registered:
            self.register_event(pygame.MOUSEBUTTONDOWN, self.menu.exit_button.click)
            self.register_event(pygame.MOUSEBUTTONDOWN, self.menu.start_button.click)
            self.menu_registered = True
        if self.show_menu:
            if self.menu.start_button.is_clicked:
                self.show_menu = False
                self.setup_game()
            if self.menu.exit_button.is_clicked:
                self.running = False
        if self.show_game_over:
            if self.game_over.restart_button.is_clicked:
                self.show_game_over = False
                self.wave = 1
                self.timer = 450
                if self.score:
                    self.score.kill()
                    self.score = None
                self.setup_game()
            if self.game_over.exit_button.is_clicked:
                self.running = False
        if self.show_win:
            if self.win.restart_button.is_clicked:
                self.show_win = False
                self.wave = 1
                self.timer = 450
                if self.score:
                    self.score.kill()
                    self.score = None
                self.setup_game()
            if self.win.exit_button.is_clicked:
                self.running = False

    def setup_game(self):
        if not self.show_menu and not self.show_game_over and not self.show_win:
            self.player_registered = False
            for component in self.menu.menu_components:
                component.kill()
            self.player = Player((width // 2 - 20, height - 100), self.all_sprites, self.enemies)
            if not self.score:
                self.score = Score((0, height), self.player, self.bg)
            if not self.player_registered:
                self.register_event(pygame.KEYDOWN, self.player.set_flags)
                self.register_event(pygame.KEYUP, self.player.set_flags)
                self.player_registered = True

    def spawn_enemies(self):
        self.timer = 0
        if self.wave == 1:
            for i in range(1, 8):
                self.enemy = BaseEnemy((i * width // 8, -100), self.player, self.all_sprites, self.enemies)
        elif self.wave == 2:
            for i in range(1, 8):
                self.enemy = BaseEnemy((i * width // 8, -100), self.player, self.all_sprites, self.enemies)
            for i in range(1, 6):
                self.shootingenemy = ShootingEnemy((i * width // 6, - 200), self.player, self.all_sprites, self.enemies)
        elif self.wave == 3:
            self.boss = Boss((width // 2, -100), self.player, self.all_sprites, self.enemies)
            self.boss_was_spawned = True
        self.wave += 1

    def draw(self, screen: pygame.Surface):
        self.bg.draw(screen)
        if not self.show_menu and not self.show_game_over and not self.show_win:
            self.all_sprites.draw(screen)
            self.player.bullets.draw(screen)
            for e in self.enemies:
                if type(e) == ShootingEnemy or type(e) == Boss:
                    e: ShootingEnemy
                    e.bullets.draw(screen)
        elif self.show_menu:
            self.menu.draw()
        elif self.show_game_over:
            self.game_over.draw()
        elif self.show_win:
            self.win.draw()

    def update(self, delta_t: float):
        self.bg.update()
        if not self.show_menu and not self.show_game_over and not self.show_win:
            self.all_sprites.update()
            self.player.bullets.update()
            if len(self.enemies) - 1 == 0:
                self.all_killed = True
                if self.timer == 450:
                    self.spawn_enemies()
                self.timer += 1
            if not self.player.is_alive:
                if self.boss_was_spawned:
                    if self.boss.is_alive:
                        self.show_game_over = True
                        for s in self.all_sprites:
                            s.kill()
                    else:
                        self.show_game_over = False
                        for s in self.all_sprites:
                            s.kill()
                else:
                    self.show_game_over = True
                    for s in self.all_sprites:
                        s.kill()

            if self.boss_was_spawned:
                if not self.boss.is_alive:
                    self.show_win = True
                    win_sound.play()
                    self.boss_was_spawned = False
                    for s in self.all_sprites:
                        s.kill()
            for e in self.enemies:
                if type(e) == ShootingEnemy or type(e) == Boss:
                    e: ShootingEnemy
                    e.bullets.update()
        elif self.show_menu:
            self.menu.update()
        elif self.show_game_over:
            self.game_over.update()
        elif self.show_win:
            self.win.update()


if __name__ == '__main__':
    game = MyGame(width, height, screen)
    game.setup()
    game.start()
