"""
duel_env.py

Phase 7: Self-Play

Instead of a human controlling the player and a scripted/rule-based
enemy, BOTH sides are now neural nets:

    RUNNER (collects gems, avoids capture)  vs  CHASER (hunts the runner)

Standard single-agent RL libraries like stable-baselines3 only train
one policy at a time, so self-play here works the classic way: the
policy currently being trained ("self") is randomly assigned either
role each episode, and the OTHER role is played by a frozen snapshot
of a past model ("opponent"). After a generation of training, the new
model is evaluated against the previous best; if it wins more than it
loses, it becomes the new best, and the next generation trains against
IT. Repeat, and each generation should get a little stronger than the
last - the same idea behind AlphaZero's self-play loop.
"""

import random

import numpy as np
import gymnasium as gym
from gymnasium import spaces

import pygame


WIDTH = 800
HEIGHT = 600

AGENT_SIZE = 40      # both runner and chaser are the same size
GEM_SIZE = 30
AGENT_SPEED = 5      # equal speed for both sides - no built-in edge,
                     # any advantage has to come from learned skill

TARGET_GEMS = 20
TIME_LIMIT_SECONDS = 60
FPS = 60
MAX_STEPS = TIME_LIMIT_SECONDS * FPS

DAMAGE_COOLDOWN_STEPS = int(0.5 * FPS)

WALLS = [
    pygame.Rect(200, 100, 40, 250),
    pygame.Rect(450, 200, 40, 250),
    pygame.Rect(600, 50, 40, 200),
    pygame.Rect(100, 420, 250, 40),
    pygame.Rect(350, 500, 250, 40),
]

ROLE_RUNNER = 0
ROLE_CHASER = 1

ACTION_NONE = 0
ACTION_LEFT = 1
ACTION_RIGHT = 2
ACTION_UP = 3
ACTION_DOWN = 4


def _spawn_gem(rng):
    while True:
        x = rng.integers(50, WIDTH - GEM_SIZE - 50)
        y = rng.integers(50, HEIGHT - GEM_SIZE - 50)
        gem_rect = pygame.Rect(int(x), int(y), GEM_SIZE, GEM_SIZE)
        if not any(gem_rect.colliderect(w) for w in WALLS):
            return int(x), int(y)


def _resolve_move(x, y, move_x, move_y):
    """Wall-sliding movement resolution shared by both agents."""

    target_x = max(0, min(WIDTH - AGENT_SIZE, x + move_x))
    target_y = max(0, min(HEIGHT - AGENT_SIZE, y + move_y))

    full_rect = pygame.Rect(target_x, target_y, AGENT_SIZE, AGENT_SIZE)
    if not any(full_rect.colliderect(w) for w in WALLS):
        return target_x, target_y

    x_rect = pygame.Rect(target_x, y, AGENT_SIZE, AGENT_SIZE)
    if not any(x_rect.colliderect(w) for w in WALLS):
        return target_x, y

    y_rect = pygame.Rect(x, target_y, AGENT_SIZE, AGENT_SIZE)
    if not any(y_rect.colliderect(w) for w in WALLS):
        return x, target_y

    return x, y


def _action_to_delta(action):
    if action == ACTION_LEFT:
        return -AGENT_SPEED, 0
    if action == ACTION_RIGHT:
        return AGENT_SPEED, 0
    if action == ACTION_UP:
        return 0, -AGENT_SPEED
    if action == ACTION_DOWN:
        return 0, AGENT_SPEED
    return 0, 0


class NeuroArenaDuelEnv(gym.Env):
    """
    Single-agent Gym wrapper around a two-agent duel. `self` is
    whichever role the policy being trained is playing this episode;
    `opponent_model` (a loaded stable-baselines3 model, or None for a
    random fallback opponent) controls the other role and never
    receives gradient updates.
    """

    metadata = {"render_modes": ["human"], "render_fps": FPS}

    def __init__(self, opponent_model=None, render_mode=None):
        super().__init__()

        self.opponent_model = opponent_model
        self.render_mode = render_mode
        self.screen = None
        self.clock = None
        self.font = None

        self.observation_space = spaces.Box(
            low=-1.0, high=1.0, shape=(9,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(5)

        self.rng = np.random.default_rng()

        self._reset_state(forced_role=None)

    def set_opponent(self, opponent_model):
        self.opponent_model = opponent_model

    # ------------------------------------------------------------------

    def _reset_state(self, forced_role):
        self.role = forced_role if forced_role is not None else random.choice(
            [ROLE_RUNNER, ROLE_CHASER]
        )

        self.runner_x, self.runner_y = 100, 150
        self.chaser_x, self.chaser_y = 300, 250

        self.health = 100
        self.gems_collected = 0
        self.step_count = 0
        self.last_hit_step = -DAMAGE_COOLDOWN_STEPS

        self.gem_x, self.gem_y = _spawn_gem(self.rng)

    def _time_left(self):
        return max(0.0, TIME_LIMIT_SECONDS - self.step_count / FPS)

    def _obs_for(self, role):
        if role == ROLE_RUNNER:
            self_x, self_y = self.runner_x, self.runner_y
            opp_x, opp_y = self.chaser_x, self.chaser_y
        else:
            self_x, self_y = self.chaser_x, self.chaser_y
            opp_x, opp_y = self.runner_x, self.runner_y

        role_flag = -1.0 if role == ROLE_RUNNER else 1.0

        return np.array(
            [
                (self_x / WIDTH) * 2 - 1,
                (self_y / HEIGHT) * 2 - 1,
                (opp_x / WIDTH) * 2 - 1,
                (opp_y / HEIGHT) * 2 - 1,
                (self.gem_x / WIDTH) * 2 - 1,
                (self.gem_y / HEIGHT) * 2 - 1,
                (self.health / 100) * 2 - 1,
                (self._time_left() / TIME_LIMIT_SECONDS) * 2 - 1,
                role_flag,
            ],
            dtype=np.float32,
        )

    def _get_info(self, winner=None):
        return {
            "role": "runner" if self.role == ROLE_RUNNER else "chaser",
            "gems_collected": self.gems_collected,
            "health": self.health,
            "time_left": self._time_left(),
            "winner": winner,
        }

    # ------------------------------------------------------------------
    # Gymnasium API
    # ------------------------------------------------------------------

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self.rng = np.random.default_rng(seed)

        forced_role = None
        if options and "role" in options:
            forced_role = options["role"]

        self._reset_state(forced_role=forced_role)
        return self._obs_for(self.role), self._get_info()

    def step(self, action):
        self.step_count += 1

        opponent_role = ROLE_CHASER if self.role == ROLE_RUNNER else ROLE_RUNNER

        if self.opponent_model is not None:
            opp_obs = self._obs_for(opponent_role)
            opp_action, _ = self.opponent_model.predict(opp_obs, deterministic=False)
            opp_action = int(opp_action)
        else:
            # No opponent trained yet - fall back to random moves so
            # generation 1 has something to play against.
            opp_action = random.randint(0, 4)

        # Apply moves: `action` drives self.role, opp_action drives the other role.
        self_delta = _action_to_delta(action)
        opp_delta = _action_to_delta(opp_action)

        if self.role == ROLE_RUNNER:
            runner_delta, chaser_delta = self_delta, opp_delta
        else:
            runner_delta, chaser_delta = opp_delta, self_delta

        self.runner_x, self.runner_y = _resolve_move(
            self.runner_x, self.runner_y, *runner_delta
        )
        self.chaser_x, self.chaser_y = _resolve_move(
            self.chaser_x, self.chaser_y, *chaser_delta
        )

        runner_rect = pygame.Rect(self.runner_x, self.runner_y, AGENT_SIZE, AGENT_SIZE)
        chaser_rect = pygame.Rect(self.chaser_x, self.chaser_y, AGENT_SIZE, AGENT_SIZE)
        gem_rect = pygame.Rect(self.gem_x, self.gem_y, GEM_SIZE, GEM_SIZE)

        runner_reward = -0.001
        chaser_reward = -0.001

        # ---- gem collection ----
        if runner_rect.colliderect(gem_rect):
            self.gems_collected += 1
            runner_reward += 10.0
            chaser_reward -= 10.0
            self.gem_x, self.gem_y = _spawn_gem(self.rng)

        # ---- capture ----
        if runner_rect.colliderect(chaser_rect):
            if self.step_count - self.last_hit_step > DAMAGE_COOLDOWN_STEPS:
                self.health -= 10
                runner_reward -= 5.0
                chaser_reward += 5.0
                self.last_hit_step = self.step_count

        terminated = False
        truncated = False
        winner = None

        if self.gems_collected >= TARGET_GEMS:
            runner_reward += 100.0
            chaser_reward -= 50.0
            terminated = True
            winner = "runner"

        if self.health <= 0:
            runner_reward -= 50.0
            chaser_reward += 100.0
            terminated = True
            winner = "chaser"

        if not terminated and (self._time_left() <= 0 or self.step_count >= MAX_STEPS):
            chaser_reward -= 10.0   # failing to catch the runner in time is a loss for the chaser
            truncated = True
            winner = "runner"

        reward = runner_reward if self.role == ROLE_RUNNER else chaser_reward

        return (
            self._obs_for(self.role),
            reward,
            terminated,
            truncated,
            self._get_info(winner=winner),
        )

    # ------------------------------------------------------------------
    # Rendering (simple shapes - used by watch_duel.py)
    # ------------------------------------------------------------------

    def render(self):
        if self.render_mode != "human":
            return

        if self.screen is None:
            pygame.init()
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
            pygame.display.set_caption("NeuroArena - Self-Play")
            self.clock = pygame.time.Clock()
            self.font = pygame.font.SysFont(None, 32)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                return

        self.screen.fill((0, 0, 0))

        for wall in WALLS:
            pygame.draw.rect(self.screen, (100, 100, 100), wall)

        pygame.draw.rect(self.screen, (255, 215, 0), (self.gem_x, self.gem_y, GEM_SIZE, GEM_SIZE))
        pygame.draw.rect(self.screen, (255, 0, 0), (self.chaser_x, self.chaser_y, AGENT_SIZE, AGENT_SIZE))
        pygame.draw.rect(self.screen, (0, 200, 255), (self.runner_x, self.runner_y, AGENT_SIZE, AGENT_SIZE))

        hud = (
            f"Gems {self.gems_collected}/{TARGET_GEMS}  "
            f"Health {self.health}  Time {int(self._time_left())}"
        )
        self.screen.blit(self.font.render(hud, True, (255, 255, 255)), (10, 10))

        pygame.display.update()
        self.clock.tick(FPS)

    def close(self):
        if self.screen is not None:
            pygame.quit()
            self.screen = None