import pygame
import random
import os
import sys

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 500, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Superman Flight Game")
clock = pygame.time.Clock()
FPS = 60

ASSETS = os.path.join(os.path.dirname(__file__), "assets")
font_path = os.path.join(ASSETS, "comic.ttf")
highscore_file = "highscore.txt"

background = pygame.transform.scale(pygame.image.load(os.path.join(ASSETS, "background.png")), (WIDTH, HEIGHT))
city_bg = background.copy()
superman_frames = [
    pygame.transform.scale(pygame.image.load(os.path.join(ASSETS, f"superman{i}.png")).convert_alpha(), (60, 60))
    for i in (1, 2, 3)
]
shield_img = pygame.transform.scale(pygame.image.load(os.path.join(ASSETS, "shield.png")).convert_alpha(), (40, 40))
hit_sound = pygame.mixer.Sound(os.path.join(ASSETS, "hit.wav"))
whoosh_sound = pygame.mixer.Sound(os.path.join(ASSETS, "whoosh.wav"))
pygame.mixer.music.load(os.path.join(ASSETS, "superman_theme.wav"))

font = pygame.font.Font(font_path, 36)
big_font = pygame.font.Font(font_path, 72)
game_over_font = pygame.font.Font(font_path, 54)

gravity = 0.5
jump_strength = -10
gap_height = 200
obstacle_speed = 4
sound_on = True
hit_sound_on = True

score = 0
obstacles = []
shield_active = False
shield_timer = 0
paused = False
city_scroll_x = 0
first_run = True

button_font = pygame.font.Font(font_path, 32)

class Button:
    def __init__(self, text, y):
        self.text = text
        self.y = y
        self.rect = None

    def draw(self, selected=False):
        color = (255, 255, 0) if selected else (200, 200, 200)
        label = button_font.render(self.text, True, color)
        self.rect = label.get_rect(center=(WIDTH // 2, self.y))
        if selected:
            pygame.draw.rect(screen, (50, 50, 50), self.rect.inflate(20, 10), border_radius=8)
        screen.blit(label, self.rect)

    def is_hovered(self, pos):
        return self.rect and self.rect.collidepoint(pos)

def draw_3d_block(rect, color):
    pygame.draw.rect(screen, (color[0] - 20, color[1] - 20, color[2] - 20), rect.inflate(10, 10))
    pygame.draw.rect(screen, color, rect, border_radius=10)
    shadow = pygame.Surface((rect.width, rect.height))
    shadow.set_alpha(60)
    shadow.fill((0, 0, 0))
    screen.blit(shadow, (rect.x + 5, rect.y + 5))

def draw_text_center(text, y, font_obj, color=(255, 255, 0), shadow=True):
    if shadow:
        shadow_label = font_obj.render(text, True, (0, 0, 0))
        screen.blit(shadow_label, (WIDTH // 2 - shadow_label.get_width() // 2 + 3, y + 3))
    label = font_obj.render(text, True, color)
    screen.blit(label, (WIDTH // 2 - label.get_width() // 2, y))

def load_high_score():
    if os.path.exists(highscore_file):
        with open(highscore_file, 'r') as file:
            return int(file.read())
    return 0

def save_high_score(new_score):
    with open(highscore_file, 'w') as file:
        file.write(str(new_score))

def create_obstacle_pair():
    top_height = random.randint(100, HEIGHT - gap_height - 100)
    bottom_y = top_height + gap_height
    return {
        "top": pygame.Rect(WIDTH, 0, 80, top_height),
        "bottom": pygame.Rect(WIDTH, bottom_y, 80, HEIGHT - bottom_y),
        "scored": False
    }

def show_game_over(score):
    high = load_high_score()
    if score > high:
        save_high_score(score)
        high = score

    while True:
        screen.blit(background, (0, 0))
        draw_text_center("GAME OVER", 160, game_over_font, (255, 0, 0))
        draw_text_center(f"Your Score: {score}", 240, font, (255, 255, 255))
        draw_text_center(f"High Score: {high}", 290, font, (0, 255, 0))
        draw_text_center("Click to Retry", 380, font, (255, 200, 100))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                return

def run_game():
    global score, shield_active, shield_timer, paused, city_scroll_x
    superman_x = 100
    superman_y = HEIGHT // 2
    velocity = 0
    frame_index = 0
    frame_count = 0
    obstacles.clear()
    score = 0
    shield_active = False
    shield_timer = 0
    shield_rect = None

    if sound_on:
        pygame.mixer.music.play(-1)

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or event.type == pygame.MOUSEBUTTONDOWN:
                if not paused:
                    velocity = jump_strength
                    if sound_on:
                        whoosh_sound.play()

        velocity += gravity
        superman_y += velocity

        city_scroll_x = (city_scroll_x - 1) % WIDTH
        screen.blit(city_bg, (-city_scroll_x, 0))
        screen.blit(city_bg, (-city_scroll_x + WIDTH, 0))

        frame_count += 1
        if frame_count % 5 == 0:
            frame_index = (frame_index + 1) % len(superman_frames)

        superman_rect = pygame.Rect(superman_x, superman_y, 60, 60)
        screen.blit(superman_frames[frame_index], (superman_x, superman_y))

        if len(obstacles) == 0 or obstacles[-1]["top"].x < WIDTH - 200:
            obstacles.append(create_obstacle_pair())

        for o in obstacles:
            o["top"].x -= obstacle_speed
            o["bottom"].x -= obstacle_speed
            draw_3d_block(o["top"], (255, 50, 50))
            draw_3d_block(o["bottom"], (255, 50, 50))

            if not o["scored"] and o["top"].x + 80 < superman_x:
                o["scored"] = True
                score += 1
                if score % 2 == 0:
                    shield_rect = pygame.Rect(WIDTH + 200, random.randint(200, HEIGHT - 100), 40, 40)

            if superman_rect.colliderect(o["top"]) or superman_rect.colliderect(o["bottom"]):
                if not shield_active:
                    if sound_on and hit_sound_on:
                        hit_sound.play()
                    return show_game_over(score)

        if shield_rect:
            shield_rect.x -= obstacle_speed
            screen.blit(shield_img, shield_rect)
            if superman_rect.colliderect(shield_rect):
                shield_active = True
                shield_timer = pygame.time.get_ticks()
                shield_rect = None

        if shield_active:
            if pygame.time.get_ticks() - shield_timer > 10000:
                shield_active = False
            pygame.draw.circle(screen, (0, 255, 255), (superman_x + 30, int(superman_y + 30)), 35, 2)

        if superman_y < 0 or superman_y > HEIGHT:
            if not shield_active:
                if sound_on and hit_sound_on:
                    hit_sound.play()
                return show_game_over(score)

        draw_text_center(f"Score: {score}", 20, font, (255, 255, 255))
        pygame.display.flip()

def main_menu():
    buttons = [Button("Start Game", 250), Button("Settings", 320), Button("High Score", 390)]
    while True:
        screen.blit(background, (0, 0))
        draw_text_center("SUPERMAN FLIGHT", 100, big_font, (0, 255, 255))
        mouse_pos = pygame.mouse.get_pos()
        for btn in buttons:
            btn.draw(btn.is_hovered(mouse_pos))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for idx, btn in enumerate(buttons):
                    if btn.is_hovered(mouse_pos):
                        if idx == 0:
                            return
                        elif idx == 1:
                            toggle_settings()
                        elif idx == 2:
                            show_high_score()

def toggle_settings():
    global sound_on, hit_sound_on
    while True:
        screen.blit(background, (0, 0))
        draw_text_center("SETTINGS", 100, big_font, (255, 255, 255))
        draw_text_center(f"Sound: {'ON' if sound_on else 'OFF'}", 240, font)
        draw_text_center(f"Hit Sound: {'ON' if hit_sound_on else 'OFF'}", 300, font)
        draw_text_center("Press S to toggle Sound", 400, font, (255, 200, 100))
        draw_text_center("Press H to toggle Hit Sound", 440, font, (255, 200, 100))
        draw_text_center("Press ESC to go Back", 500, font, (255, 100, 100))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    sound_on = not sound_on
                elif event.key == pygame.K_h:
                    hit_sound_on = not hit_sound_on
                elif event.key == pygame.K_ESCAPE:
                    return

def show_high_score():
    high = load_high_score()
    while True:
        screen.blit(background, (0, 0))
        draw_text_center("HIGH SCORE", 180, big_font, (0, 255, 0))
        draw_text_center(str(high), 260, game_over_font, (255, 255, 255))
        draw_text_center("Press ESC to go Back", 460, font, (255, 100, 100))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

if first_run:
    main_menu()
    first_run = False

while True:
    run_game()
