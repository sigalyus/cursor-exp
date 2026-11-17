"""
Bubbles! - a simple, colorful bubble-popping arcade game.

Bubbles float up from the bottom of the screen. Click them to pop them and
score points. Smaller/faster bubbles are worth more. Let too many escape off
the top and you lose lives. Pop combos quickly for bonus points.

Run:
    python bubbles_game.py

Controls:
    Mouse click  - pop a bubble
    P            - pause / resume
    R            - restart after game over
    Esc / Q      - quit
"""

import math
import random
import sys

import pygame

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
WIDTH, HEIGHT = 800, 600
FPS = 60

MAX_LIVES = 5
SPAWN_INTERVAL_START = 0.9   # seconds between spawns at the start
SPAWN_INTERVAL_MIN = 0.28    # fastest spawn rate
DIFFICULTY_RAMP = 0.985      # spawn interval multiplier applied each spawn

COMBO_WINDOW = 1.2           # seconds to keep a combo alive

BG_TOP = (12, 18, 46)
BG_BOTTOM = (30, 12, 58)
WHITE = (245, 245, 255)
DIM = (150, 155, 190)

BUBBLE_PALETTE = [
    (255, 99, 132),
    (255, 159, 64),
    (255, 205, 86),
    (75, 192, 192),
    (54, 162, 235),
    (153, 102, 255),
    (99, 255, 176),
]


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def lerp_color(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def make_background(width, height):
    surf = pygame.Surface((width, height))
    for y in range(height):
        surf.fill(lerp_color(BG_TOP, BG_BOTTOM, y / height), (0, y, width, 1))
    return surf


class Particle:
    """A tiny fragment from a popped bubble."""

    def __init__(self, x, y, color):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(60, 260)
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color
        self.life = random.uniform(0.3, 0.7)
        self.age = 0.0
        self.radius = random.uniform(2, 5)

    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 400 * dt  # gravity

    @property
    def dead(self):
        return self.age >= self.life

    def draw(self, surf):
        t = max(0.0, 1 - self.age / self.life)
        r = max(1, int(self.radius * t))
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), r)


class Bubble:
    def __init__(self, width, height):
        self.radius = random.randint(18, 46)
        self.x = random.uniform(self.radius, width - self.radius)
        self.y = height + self.radius
        self.speed = random.uniform(60, 150) + (46 - self.radius) * 2.0
        self.drift = random.uniform(-30, 30)
        self.phase = random.uniform(0, math.tau)
        self.color = random.choice(BUBBLE_PALETTE)
        self.wobble = random.uniform(8, 22)

    @property
    def points(self):
        # Smaller and faster bubbles are worth more.
        size_bonus = int((46 - self.radius) / 4)
        speed_bonus = int(self.speed / 40)
        return 5 + size_bonus + speed_bonus

    def update(self, dt):
        self.y -= self.speed * dt
        self.phase += dt * 2.5
        self.x += (self.drift + math.sin(self.phase) * self.wobble) * dt

    def is_hit(self, pos):
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        return dx * dx + dy * dy <= self.radius * self.radius

    def draw(self, surf):
        cx, cy, r = int(self.x), int(self.y), self.radius
        # Soft translucent body.
        body = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(body, (*self.color, 90), (r, r), r)
        pygame.draw.circle(body, (*self.color, 220), (r, r), r, width=3)
        # Highlight sheen.
        hl = int(r * 0.35)
        pygame.draw.circle(
            body, (255, 255, 255, 150), (int(r * 0.65), int(r * 0.6)), hl
        )
        surf.blit(body, (cx - r, cy - r))


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Bubbles!")
        self.clock = pygame.time.Clock()
        self.bg = make_background(WIDTH, HEIGHT)
        self.font_big = pygame.font.SysFont("arialrounded,arial", 64, bold=True)
        self.font = pygame.font.SysFont("arialrounded,arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("arial", 20)
        self.reset()

    def reset(self):
        self.bubbles = []
        self.particles = []
        self.score = 0
        self.lives = MAX_LIVES
        self.spawn_interval = SPAWN_INTERVAL_START
        self.spawn_timer = 0.0
        self.combo = 0
        self.combo_timer = 0.0
        self.paused = False
        self.game_over = False

    # -- game flow -----------------------------------------------------------
    def spawn_bubble(self):
        self.bubbles.append(Bubble(WIDTH, HEIGHT))
        self.spawn_interval = max(
            SPAWN_INTERVAL_MIN, self.spawn_interval * DIFFICULTY_RAMP
        )

    def pop_bubble(self, bubble):
        self.combo = self.combo + 1 if self.combo_timer > 0 else 1
        self.combo_timer = COMBO_WINDOW
        gained = bubble.points * self.combo
        self.score += gained
        for _ in range(int(bubble.radius / 2)):
            self.particles.append(Particle(bubble.x, bubble.y, bubble.color))

    def handle_click(self, pos):
        # Prefer topmost (last drawn) bubble under the cursor.
        for bubble in reversed(self.bubbles):
            if bubble.is_hit(pos):
                self.pop_bubble(bubble)
                self.bubbles.remove(bubble)
                return

    def update(self, dt):
        if self.paused or self.game_over:
            return

        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0.0
            self.spawn_bubble()

        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 0

        for bubble in self.bubbles:
            bubble.update(dt)

        escaped = [b for b in self.bubbles if b.y + b.radius < 0]
        if escaped:
            self.lives -= len(escaped)
            self.bubbles = [b for b in self.bubbles if b.y + b.radius >= 0]
            self.combo = 0
            self.combo_timer = 0.0
            if self.lives <= 0:
                self.lives = 0
                self.game_over = True

        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if not p.dead]

    # -- rendering -----------------------------------------------------------
    def draw_hud(self):
        score_surf = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_surf, (20, 16))

        # Lives as little hearts/circles.
        for i in range(MAX_LIVES):
            color = (255, 90, 120) if i < self.lives else (70, 70, 90)
            pygame.draw.circle(self.screen, color, (WIDTH - 30 - i * 34, 30), 12)

        if self.combo > 1:
            combo_surf = self.font.render(f"Combo x{self.combo}", True, (255, 220, 120))
            self.screen.blit(combo_surf, (20, 52))

    def draw_center_text(self, title, subtitle):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        title_surf = self.font_big.render(title, True, WHITE)
        self.screen.blit(
            title_surf,
            (WIDTH // 2 - title_surf.get_width() // 2, HEIGHT // 2 - 80),
        )
        sub_surf = self.font.render(subtitle, True, DIM)
        self.screen.blit(
            sub_surf,
            (WIDTH // 2 - sub_surf.get_width() // 2, HEIGHT // 2 + 10),
        )

    def draw(self):
        self.screen.blit(self.bg, (0, 0))
        for bubble in self.bubbles:
            bubble.draw(self.screen)
        for p in self.particles:
            p.draw(self.screen)
        self.draw_hud()

        hint = self.font_small.render(
            "Click bubbles to pop  |  P: pause  |  R: restart  |  Esc: quit",
            True,
            DIM,
        )
        self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 30))

        if self.paused:
            self.draw_center_text("Paused", "Press P to resume")
        elif self.game_over:
            self.draw_center_text(
                f"Game Over  -  {self.score}", "Press R to play again"
            )

        pygame.display.flip()

    # -- main loop -----------------------------------------------------------
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        self.quit()
                    elif event.key == pygame.K_p and not self.game_over:
                        self.paused = not self.paused
                    elif event.key == pygame.K_r and self.game_over:
                        self.reset()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not self.paused and not self.game_over:
                        self.handle_click(event.pos)

            self.update(dt)
            self.draw()

    def quit(self):
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
