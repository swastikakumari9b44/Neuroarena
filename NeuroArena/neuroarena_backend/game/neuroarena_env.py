"""
NeuroArena Gym environment.

This module exposes NeuroArenaEnv, a gymnasium.Env subclass that
implements the NeuroArena game rules (player vs. AI opponent, gem
collection, walls, health, timer) so it can be driven step-by-step by
the FastAPI backend (see routes/game.py):

    env = NeuroArenaEnv()
    observation, info = env.reset()
    observation, reward, terminated, truncated, info = env.step(action)

IMPORTANT: importing this module does NOT open a window or start any
game loop. All game state lives on the NeuroArenaEnv instance and only
advances when .step() is called. This is what makes it safe to import
from a web server.

Optional human rendering (a pygame window) is available by passing
render_mode="human" to the constructor, and is only initialized lazily,
the first time render() actually needs it.
"""

import math
import random

import numpy as np
import gymnasium as gym
from gymnasium import spaces


# -----------------------------
# Constants (unchanged from the original game)
# -----------------------------
WIDTH = 800
HEIGHT = 600

PLAYER_SIZE = 40
ENEMY_SIZE = 40
GEM_SIZE = 30
WALL_SIZE = 40

TARGET_GEMS = 20
TIME_LIMIT = 60          # seconds
DAMAGE_COOLDOWN_MS = 500  # overridden per-difficulty below

# Walls as plain (x, y, w, h) tuples -- no pygame.Rect needed, so the
# env has no hard dependency on a display/video driver being available.
WALLS = [
    (200, 100, 40, 250),
    (450, 200, 40, 250),
    (600, 50, 40, 200),
    (100, 420, 250, 40),
    (350, 500, 250, 40),
]

DIFFICULTIES = {
    "Easy": {"speed": 4, "chase_chance": 0.0, "prediction": 0, "cooldown_ms": 500},
    "Medium": {"speed": 5, "chase_chance": 0.5, "prediction": 5, "cooldown_ms": 400},
    "Hard": {"speed": 6, "chase_chance": 0.85, "prediction": 15, "cooldown_ms": 300},
    "Impossible": {"speed": 7, "chase_chance": 1.0, "prediction": 25, "cooldown_ms": 150},
}


def _rects_overlap(x1, y1, w1, h1, x2, y2, w2, h2):
    """Simple AABB collision test, replacement for pygame.Rect.colliderect."""
    return x1 < x2 + w2 and x1 + w1 > x2 and y1 < y2 + h2 and y1 + h1 > y2


class NeuroArenaEnv(gym.Env):
    """Gymnasium environment for the NeuroArena player-vs-AI game."""

    metadata = {"render_modes": ["human"], "render_fps": 60}

    # Discrete action space
    ACTION_NONE = 0
    ACTION_LEFT = 1
    ACTION_RIGHT = 2
    ACTION_UP = 3
    ACTION_DOWN = 4

    def __init__(self, difficulty: str = "Medium", render_mode: str | None = None):
        super().__init__()

        self.difficulty_name = difficulty if difficulty in DIFFICULTIES else "Medium"
        self.render_mode = render_mode

        self.action_space = spaces.Discrete(5)

        # Observation vector:
        # [player_x, player_y, enemy_x, enemy_y, gem_x, gem_y,
        #  health, gems_collected, time_left, player_vx, player_vy]
        low = np.array(
            [0, 0, 0, 0, 0, 0, 0, 0, 0, -10, -10], dtype=np.float32
        )
        high = np.array(
            [WIDTH, HEIGHT, WIDTH, HEIGHT, WIDTH, HEIGHT, 100, TARGET_GEMS, TIME_LIMIT, 10, 10],
            dtype=np.float32,
        )
        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)

        self.player_speed = 5
        self.walls = WALLS

        # Lazy pygame handles for optional human rendering
        self._screen = None
        self._clock = None
        self._font = None

        self.reset()

    # -----------------------------
    # Helpers
    # -----------------------------
    def _spawn_gem(self):
        while True:
            x = random.randint(50, WIDTH - GEM_SIZE - 50)
            y = random.randint(50, HEIGHT - GEM_SIZE - 50)
            if not any(
                _rects_overlap(x, y, GEM_SIZE, GEM_SIZE, *w) for w in self.walls
            ):
                return x, y

    def _resolve_enemy_move(self, ex, ey, move_x, move_y):
        """Slide the AI opponent along walls instead of freezing against them."""
        target_x = max(0, min(WIDTH - ENEMY_SIZE, ex + move_x))
        target_y = max(0, min(HEIGHT - ENEMY_SIZE, ey + move_y))

        if not any(
            _rects_overlap(target_x, target_y, ENEMY_SIZE, ENEMY_SIZE, *w) for w in self.walls
        ):
            return target_x, target_y

        if not any(
            _rects_overlap(target_x, ey, ENEMY_SIZE, ENEMY_SIZE, *w) for w in self.walls
        ):
            return target_x, ey

        if not any(
            _rects_overlap(ex, target_y, ENEMY_SIZE, ENEMY_SIZE, *w) for w in self.walls
        ):
            return ex, target_y

        return ex, ey

    def _get_obs(self):
        return np.array(
            [
                self.player_x,
                self.player_y,
                self.enemy_x,
                self.enemy_y,
                self.gem_x,
                self.gem_y,
                self.health,
                self.gems_collected,
                self.time_left,
                self.player_vx,
                self.player_vy,
            ],
            dtype=np.float32,
        )

    def _get_info(self):
        return {
            "score": self.score,
            "difficulty": self.difficulty_name,
            "steps": self.steps,
        }

    # -----------------------------
    # Gymnasium API
    # -----------------------------
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            random.seed(seed)

        if options and options.get("difficulty") in DIFFICULTIES:
            self.difficulty_name = options["difficulty"]

        self.player_x = 100
        self.player_y = 150
        self.player_vx = 0
        self.player_vy = 0

        self.enemy_x = 300
        self.enemy_y = 250
        self.direction = 1

        self.score = 0
        self.health = 100
        self.gems_collected = 0
        self.steps = 0

        self.gem_x, self.gem_y = self._spawn_gem()

        self.elapsed_ms = 0.0
        self.time_left = TIME_LIMIT
        self.last_hit_ms = -DAMAGE_COOLDOWN_MS

        self.terminated = False
        self.truncated = False

        if self.render_mode == "human":
            self._render_frame()

        return self._get_obs(), self._get_info()

    def step(self, action):
        if self.terminated or self.truncated:
            # Episode already over. Gymnasium leaves behavior undefined here;
            # we return the last state rather than raising, so the backend
            # doesn't 500 if a stale request comes in after game over.
            return self._get_obs(), 0.0, self.terminated, self.truncated, self._get_info()

        reward = 0.0
        self.steps += 1

        # Advance the game clock, assuming one step == one 60fps frame
        self.elapsed_ms += 1000 / 60
        self.time_left = max(0, TIME_LIMIT - int(self.elapsed_ms // 1000))

        # --- player movement ---
        new_x, new_y = self.player_x, self.player_y
        if action == self.ACTION_LEFT:
            new_x -= self.player_speed
        elif action == self.ACTION_RIGHT:
            new_x += self.player_speed
        elif action == self.ACTION_UP:
            new_y -= self.player_speed
        elif action == self.ACTION_DOWN:
            new_y += self.player_speed
        # ACTION_NONE (or anything else): stand still

        new_x = max(0, min(WIDTH - PLAYER_SIZE, new_x))
        new_y = max(0, min(HEIGHT - PLAYER_SIZE, new_y))

        blocked = any(
            _rects_overlap(new_x, new_y, PLAYER_SIZE, PLAYER_SIZE, *w) for w in self.walls
        )

        prev_x, prev_y = self.player_x, self.player_y
        if not blocked:
            self.player_x, self.player_y = new_x, new_y

        self.player_vx = self.player_x - prev_x
        self.player_vy = self.player_y - prev_y

        # --- AI opponent movement ---
        diff = DIFFICULTIES[self.difficulty_name]
        ai_speed = diff["speed"]
        chase_chance = diff["chase_chance"]
        prediction_frames = diff["prediction"]

        if random.random() < chase_chance:
            target_x = self.player_x + self.player_vx * prediction_frames
            target_y = self.player_y + self.player_vy * prediction_frames
            target_x = max(0, min(WIDTH - PLAYER_SIZE, target_x))
            target_y = max(0, min(HEIGHT - PLAYER_SIZE, target_y))

            dx = target_x - self.enemy_x
            dy = target_y - self.enemy_y
            dist = math.hypot(dx, dy)

            if dist > 0:
                move_x = (dx / dist) * ai_speed
                move_y = (dy / dist) * ai_speed
            else:
                move_x = move_y = 0

            self.enemy_x, self.enemy_y = self._resolve_enemy_move(
                self.enemy_x, self.enemy_y, move_x, move_y
            )
            self.direction = 1 if move_x >= 0 else -1
        else:
            self.enemy_x += ai_speed * self.direction
            if self.enemy_x <= 0:
                self.direction = 1
            if self.enemy_x >= WIDTH - ENEMY_SIZE:
                self.direction = -1

        # --- gem collection ---
        if _rects_overlap(
            self.player_x, self.player_y, PLAYER_SIZE, PLAYER_SIZE,
            self.gem_x, self.gem_y, GEM_SIZE, GEM_SIZE,
        ):
            self.score += 10
            self.gems_collected += 1
            reward += 10.0
            self.gem_x, self.gem_y = self._spawn_gem()

        # --- enemy collision (with per-difficulty damage cooldown) ---
        if _rects_overlap(
            self.player_x, self.player_y, PLAYER_SIZE, PLAYER_SIZE,
            self.enemy_x, self.enemy_y, ENEMY_SIZE, ENEMY_SIZE,
        ):
            if self.elapsed_ms - self.last_hit_ms > diff["cooldown_ms"]:
                self.health -= 10
                reward -= 10.0
                self.last_hit_ms = self.elapsed_ms

        # --- win / loss conditions ---
        if self.gems_collected >= TARGET_GEMS:
            reward += 100.0
            self.terminated = True
        elif self.health <= 0:
            reward -= 50.0
            self.terminated = True
        elif self.time_left <= 0:
            self.truncated = True

        if self.render_mode == "human":
            self._render_frame()

        return self._get_obs(), reward, self.terminated, self.truncated, self._get_info()

    def render(self):
        if self.render_mode == "human":
            self._render_frame()

    def _render_frame(self):
        """Lazily open a pygame window and draw the current state.
        Only ever called if render_mode='human' was explicitly requested."""
        import pygame

        if self._screen is None:
            pygame.init()
            self._screen = pygame.display.set_mode((WIDTH, HEIGHT))
            pygame.display.set_caption("NeuroArena")
            self._clock = pygame.time.Clock()
            self._font = pygame.font.SysFont(None, 30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                return

        self._screen.fill((0, 0, 0))

        for (x, y, w, h) in self.walls:
            pygame.draw.rect(self._screen, (130, 130, 130), (x, y, w, h))

        pygame.draw.rect(self._screen, (255, 255, 0), (self.gem_x, self.gem_y, GEM_SIZE, GEM_SIZE))
        pygame.draw.rect(self._screen, (255, 0, 0), (self.enemy_x, self.enemy_y, ENEMY_SIZE, ENEMY_SIZE))
        pygame.draw.rect(self._screen, (0, 255, 0), (self.player_x, self.player_y, PLAYER_SIZE, PLAYER_SIZE))

        hud = (
            f"Score: {self.score}  Health: {self.health}  "
            f"Gems: {self.gems_collected}/{TARGET_GEMS}  Time: {self.time_left}"
        )
        surf = self._font.render(hud, True, (255, 255, 255))
        self._screen.blit(surf, (10, 10))

        pygame.display.update()
        self._clock.tick(self.metadata["render_fps"])

    def close(self):
        if self._screen is not None:
            import pygame
            pygame.quit()
            self._screen = None
            self._clock = None
            self._font = None