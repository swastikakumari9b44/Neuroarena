"""
advanced_env.py

Phase 8: Add Advanced Features (Weeks 11-12)

Extends the Phase 7 duel into one configurable environment. Every
feature below is a constructor flag, so you can mix and match:

  - Different maps              -> map_name: "classic" | "cross" | "open" | "random"
  - Random obstacles             -> random_obstacles=True (scatters extra blocks each episode)
  - Fog of war                   -> fog_of_war=True, vision_radius=... (opponent hidden beyond it)
  - Multiple weapons             -> items_enabled=True adds a stun pickup
  - Shields                      -> part of items_enabled - temporary invulnerability
  - Healing packs                -> part of items_enabled - restores runner health
  - Multiple game modes          -> game_mode: "classic" | "survival" | "deathmatch"
  - Different AI personalities   -> personality: "aggressive" | "defensive" | "erratic" | "tactical"
    (only used for the built-in scripted fallback opponent, i.e. when
    no trained opponent_model is supplied)

Example: train on the "open" map with fog of war and items enabled,
in "survival" mode, against a "tactical" scripted opponent - then
swap any of those flags for the next run.
"""

import random
import math

import numpy as np
import gymnasium as gym
from gymnasium import spaces

import pygame


WIDTH = 800
HEIGHT = 600

AGENT_SIZE = 40
ITEM_SIZE = 28
GEM_SIZE = 30
AGENT_SPEED = 5

TARGET_GEMS = 20
TIME_LIMIT_SECONDS = 60
FPS = 60
MAX_STEPS = TIME_LIMIT_SECONDS * FPS

DAMAGE_COOLDOWN_STEPS = int(0.5 * FPS)

STUN_DURATION_STEPS = int(1.5 * FPS)
SHIELD_DURATION_STEPS = int(4.0 * FPS)
HEAL_AMOUNT = 30
OBSTACLE_COUNT = 4
OBSTACLE_SIZE = 60
VISION_RADIUS_DEFAULT = 220

ROLE_RUNNER = 0
ROLE_CHASER = 1

ACTION_NONE = 0
ACTION_LEFT = 1
ACTION_RIGHT = 2
ACTION_UP = 3
ACTION_DOWN = 4

GAME_MODES = ("classic", "survival", "deathmatch")

# -----------------------------
# Different Maps
# -----------------------------
MAPS = {
    "classic": [
        pygame.Rect(200, 100, 40, 250),
        pygame.Rect(450, 200, 40, 250),
        pygame.Rect(600, 50, 40, 200),
        pygame.Rect(100, 420, 250, 40),
        pygame.Rect(350, 500, 250, 40),
    ],
    "cross": [
        pygame.Rect(380, 0, 40, 240),
        pygame.Rect(380, 360, 40, 240),
        pygame.Rect(0, 280, 240, 40),
        pygame.Rect(560, 280, 240, 40),
    ],
    "open": [
        pygame.Rect(340, 260, 120, 40),
    ],
}

# -----------------------------
# Different AI Personalities (scripted fallback opponent only)
# -----------------------------
PERSONALITIES = {
    "aggressive": {"chase_chance": 1.0, "prediction": 20, "speed": 6, "jitter": 0.0, "guard_gem": False, "cutoff": False},
    "defensive":  {"chase_chance": 0.3, "prediction": 5,  "speed": 4, "jitter": 0.0, "guard_gem": True,  "cutoff": False},
    "erratic":    {"chase_chance": 0.6, "prediction": 0,  "speed": 5, "jitter": 3.0, "guard_gem": False, "cutoff": False},
    "tactical":   {"chase_chance": 0.9, "prediction": 15, "speed": 5, "jitter": 0.0, "guard_gem": False, "cutoff": True},
}


def _spawn_free_point(rng, walls, size, margin=50):
    while True:
        x = rng.integers(margin, WIDTH - size - margin)
        y = rng.integers(margin, HEIGHT - size - margin)
        rect = pygame.Rect(int(x), int(y), size, size)
        if not any(rect.colliderect(w) for w in walls):
            return int(x), int(y)


def _resolve_move(x, y, move_x, move_y, walls):
    target_x = max(0, min(WIDTH - AGENT_SIZE, x + move_x))
    target_y = max(0, min(HEIGHT - AGENT_SIZE, y + move_y))

    full_rect = pygame.Rect(target_x, target_y, AGENT_SIZE, AGENT_SIZE)
    if not any(full_rect.colliderect(w) for w in walls):
        return target_x, target_y

    x_rect = pygame.Rect(target_x, y, AGENT_SIZE, AGENT_SIZE)
    if not any(x_rect.colliderect(w) for w in walls):
        return target_x, y

    y_rect = pygame.Rect(x, target_y, AGENT_SIZE, AGENT_SIZE)
    if not any(y_rect.colliderect(w) for w in walls):
        return x, target_y

    return x, y


def _action_to_delta(action, speed):
    if action == ACTION_LEFT:
        return -speed, 0
    if action == ACTION_RIGHT:
        return speed, 0
    if action == ACTION_UP:
        return 0, -speed
    if action == ACTION_DOWN:
        return 0, speed
    return 0, 0


class AdvancedNeuroArenaEnv(gym.Env):
    metadata = {"render_modes": ["human"], "render_fps": FPS}

    def __init__(
        self,
        opponent_model=None,
        map_name="classic",
        random_obstacles=False,
        fog_of_war=False,
        vision_radius=VISION_RADIUS_DEFAULT,
        items_enabled=False,
        game_mode="classic",
        personality="aggressive",
        render_mode=None,
    ):
        super().__init__()

        assert game_mode in GAME_MODES
        assert personality in PERSONALITIES

        self.opponent_model = opponent_model
        self.map_name = map_name
        self.random_obstacles = random_obstacles
        self.fog_of_war = fog_of_war
        self.vision_radius = vision_radius
        self.items_enabled = items_enabled
        self.game_mode = game_mode
        self.personality = PERSONALITIES[personality]

        self.render_mode = render_mode
        self.screen = None
        self.clock = None
        self.font = None

        # 9 core + 1 fog visibility flag + 6 item coords + 2 status flags + 1 mode flag
        self.observation_space = spaces.Box(low=-1.0, high=1.0, shape=(19,), dtype=np.float32)
        self.action_space = spaces.Discrete(5)

        self.rng = np.random.default_rng()

        self._reset_state(forced_role=None)

    def set_opponent(self, opponent_model):
        self.opponent_model = opponent_model

    # ------------------------------------------------------------------

    def _build_walls(self):
        base_name = self.map_name
        if base_name == "random":
            base_name = random.choice(list(MAPS.keys()))

        walls = list(MAPS[base_name])

        if self.random_obstacles:
            for _ in range(OBSTACLE_COUNT):
                x, y = _spawn_free_point(self.rng, walls, OBSTACLE_SIZE, margin=80)
                walls.append(pygame.Rect(x, y, OBSTACLE_SIZE, OBSTACLE_SIZE))

        return walls

    def _reset_state(self, forced_role):
        self.role = forced_role if forced_role is not None else random.choice([ROLE_RUNNER, ROLE_CHASER])

        self.walls = self._build_walls()

        self.runner_x, self.runner_y = 100, 150
        self.chaser_x, self.chaser_y = 300, 250

        self.runner_health = 100
        self.chaser_health = 100  # only relevant in "deathmatch" mode

        self.gems_collected = 0
        self.step_count = 0
        self.last_hit_step = -DAMAGE_COOLDOWN_STEPS

        self.gem_x, self.gem_y = _spawn_free_point(self.rng, self.walls, GEM_SIZE)

        self.weapon_pos = None
        self.shield_pos = None
        self.heal_pos = None
        if self.items_enabled:
            self.weapon_pos = _spawn_free_point(self.rng, self.walls, ITEM_SIZE)
            self.shield_pos = _spawn_free_point(self.rng, self.walls, ITEM_SIZE)
            self.heal_pos = _spawn_free_point(self.rng, self.walls, ITEM_SIZE)

        self.runner_shield_steps = 0
        self.chaser_stun_steps = 0

        self.last_seen_by_runner = (self.chaser_x, self.chaser_y)
        self.last_seen_by_chaser = (self.runner_x, self.runner_y)

        self.scripted_direction = 1  # scripted opponent's patrol state

    def _time_left(self):
        return max(0.0, TIME_LIMIT_SECONDS - self.step_count / FPS)

    def _norm(self, x, y):
        return (x / WIDTH) * 2 - 1, (y / HEIGHT) * 2 - 1

    def _obs_for(self, role):
        if role == ROLE_RUNNER:
            self_x, self_y = self.runner_x, self.runner_y
            opp_x, opp_y = self.chaser_x, self.chaser_y
            last_seen = self.last_seen_by_runner
        else:
            self_x, self_y = self.chaser_x, self.chaser_y
            opp_x, opp_y = self.runner_x, self.runner_y
            last_seen = self.last_seen_by_chaser

        visible = 1.0
        if self.fog_of_war:
            dist = math.hypot(opp_x - self_x, opp_y - self_y)
            if dist <= self.vision_radius:
                visible = 1.0
                last_seen = (opp_x, opp_y)
            else:
                visible = -1.0
                opp_x, opp_y = last_seen

            if role == ROLE_RUNNER:
                self.last_seen_by_runner = last_seen
            else:
                self.last_seen_by_chaser = last_seen

        role_flag = -1.0 if role == ROLE_RUNNER else 1.0
        mode_flag = {"classic": -1.0, "survival": 0.0, "deathmatch": 1.0}[self.game_mode]

        self_nx, self_ny = self._norm(self_x, self_y)
        opp_nx, opp_ny = self._norm(opp_x, opp_y)
        gem_nx, gem_ny = self._norm(self.gem_x, self.gem_y)

        def item_coords(pos):
            if pos is None:
                return -1.0, -1.0
            return self._norm(*pos)

        weapon_nx, weapon_ny = item_coords(self.weapon_pos)
        shield_nx, shield_ny = item_coords(self.shield_pos)
        heal_nx, heal_ny = item_coords(self.heal_pos)

        health_for_role = self.runner_health if role == ROLE_RUNNER else self.chaser_health

        return np.array(
            [
                self_nx, self_ny,
                opp_nx, opp_ny,
                gem_nx, gem_ny,
                (health_for_role / 100) * 2 - 1,
                (self._time_left() / TIME_LIMIT_SECONDS) * 2 - 1,
                role_flag,
                visible,
                weapon_nx, weapon_ny,
                shield_nx, shield_ny,
                heal_nx, heal_ny,
                1.0 if (role == ROLE_RUNNER and self.runner_shield_steps > 0) else -1.0,
                1.0 if (role == ROLE_CHASER and self.chaser_stun_steps > 0) else -1.0,
                mode_flag,
            ],
            dtype=np.float32,
        )

    def _get_info(self, winner=None):
        return {
            "role": "runner" if self.role == ROLE_RUNNER else "chaser",
            "gems_collected": self.gems_collected,
            "runner_health": self.runner_health,
            "chaser_health": self.chaser_health,
            "time_left": self._time_left(),
            "winner": winner,
            "map": self.map_name,
            "game_mode": self.game_mode,
        }

    # ------------------------------------------------------------------
    # Scripted fallback opponent (AI personalities) - used only when no
    # trained opponent_model is supplied
    # ------------------------------------------------------------------

    def _scripted_action(self, opponent_role):
        p = self.personality

        if opponent_role == ROLE_CHASER:
            self_x, self_y = self.chaser_x, self.chaser_y
            target_x, target_y = self.runner_x, self.runner_y
        else:
            # scripted runner just heads for the gem - a weak stand-in
            # opponent, not meant to be strong
            self_x, self_y = self.runner_x, self.runner_y
            target_x, target_y = self.gem_x, self.gem_y

        if opponent_role == ROLE_CHASER and (p["guard_gem"] or p["cutoff"]):
            # Defensive personality loiters near the gem; Tactical aims
            # between the runner and the gem to cut off the path
            target_x = (target_x + self.gem_x) / 2
            target_y = (target_y + self.gem_y) / 2

        if random.random() >= p["chase_chance"]:
            dx = self.scripted_direction * p["speed"]
            dy = 0
            if self_x <= 0:
                self.scripted_direction = 1
            if self_x >= WIDTH - AGENT_SIZE:
                self.scripted_direction = -1
        else:
            dx_raw = target_x - self_x
            dy_raw = target_y - self_y
            dist = math.hypot(dx_raw, dy_raw)
            if dist > 0:
                dx = (dx_raw / dist) * p["speed"]
                dy = (dy_raw / dist) * p["speed"]
            else:
                dx = dy = 0

            if p["jitter"] > 0:
                dx += random.uniform(-p["jitter"], p["jitter"])
                dy += random.uniform(-p["jitter"], p["jitter"])

        # the scripted AI still only gets the same 5 discrete actions
        # the learned agents do, so convert the vector to the closest one
        if abs(dx) > abs(dy):
            return ACTION_RIGHT if dx > 0 else ACTION_LEFT
        elif abs(dy) > 0:
            return ACTION_DOWN if dy > 0 else ACTION_UP
        return ACTION_NONE

    # ------------------------------------------------------------------
    # Gymnasium API
    # ------------------------------------------------------------------

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self.rng = np.random.default_rng(seed)

        forced_role = options.get("role") if options else None
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
            opp_action = self._scripted_action(opponent_role)

        # a stunned chaser can't move at all this step
        if opponent_role == ROLE_CHASER and self.chaser_stun_steps > 0:
            opp_action = ACTION_NONE
        if self.role == ROLE_CHASER and self.chaser_stun_steps > 0:
            action = ACTION_NONE

        self_delta = _action_to_delta(action, AGENT_SPEED)
        opp_delta = _action_to_delta(opp_action, AGENT_SPEED)

        if self.role == ROLE_RUNNER:
            runner_delta, chaser_delta = self_delta, opp_delta
        else:
            runner_delta, chaser_delta = opp_delta, self_delta

        self.runner_x, self.runner_y = _resolve_move(self.runner_x, self.runner_y, *runner_delta, self.walls)
        self.chaser_x, self.chaser_y = _resolve_move(self.chaser_x, self.chaser_y, *chaser_delta, self.walls)

        if self.runner_shield_steps > 0:
            self.runner_shield_steps -= 1
        if self.chaser_stun_steps > 0:
            self.chaser_stun_steps -= 1

        runner_rect = pygame.Rect(self.runner_x, self.runner_y, AGENT_SIZE, AGENT_SIZE)
        chaser_rect = pygame.Rect(self.chaser_x, self.chaser_y, AGENT_SIZE, AGENT_SIZE)
        gem_rect = pygame.Rect(self.gem_x, self.gem_y, GEM_SIZE, GEM_SIZE)

        runner_reward = -0.001
        chaser_reward = -0.001

        # ---- gem collection (bonus reward in every mode; win condition only in "classic") ----
        if runner_rect.colliderect(gem_rect):
            self.gems_collected += 1
            runner_reward += 10.0
            chaser_reward -= 5.0
            self.gem_x, self.gem_y = _spawn_free_point(self.rng, self.walls, GEM_SIZE)

        # ---- items: weapon (stun), shield, heal pack ----
        if self.items_enabled:
            if self.weapon_pos and runner_rect.colliderect(pygame.Rect(*self.weapon_pos, ITEM_SIZE, ITEM_SIZE)):
                self.chaser_stun_steps = STUN_DURATION_STEPS
                runner_reward += 3.0
                self.weapon_pos = _spawn_free_point(self.rng, self.walls, ITEM_SIZE)

            if self.shield_pos and runner_rect.colliderect(pygame.Rect(*self.shield_pos, ITEM_SIZE, ITEM_SIZE)):
                self.runner_shield_steps = SHIELD_DURATION_STEPS
                runner_reward += 2.0
                self.shield_pos = _spawn_free_point(self.rng, self.walls, ITEM_SIZE)

            if self.heal_pos and runner_rect.colliderect(pygame.Rect(*self.heal_pos, ITEM_SIZE, ITEM_SIZE)):
                self.runner_health = min(100, self.runner_health + HEAL_AMOUNT)
                runner_reward += 2.0
                self.heal_pos = _spawn_free_point(self.rng, self.walls, ITEM_SIZE)

        # ---- capture / combat ----
        if runner_rect.colliderect(chaser_rect):
            if self.step_count - self.last_hit_step > DAMAGE_COOLDOWN_STEPS:
                if self.runner_shield_steps <= 0:
                    self.runner_health -= 10
                    runner_reward -= 5.0
                    chaser_reward += 5.0
                if self.game_mode == "deathmatch":
                    self.chaser_health -= 10
                    chaser_reward -= 5.0
                    runner_reward += 5.0
                self.last_hit_step = self.step_count

        terminated = False
        truncated = False
        winner = None

        # ---- game modes ----
        if self.game_mode == "classic":
            if self.gems_collected >= TARGET_GEMS:
                runner_reward += 100.0
                chaser_reward -= 50.0
                terminated = True
                winner = "runner"
            if self.runner_health <= 0:
                runner_reward -= 50.0
                chaser_reward += 100.0
                terminated = True
                winner = "chaser"

        elif self.game_mode == "survival":
            if self.runner_health <= 0:
                chaser_reward += 100.0
                runner_reward -= 50.0
                terminated = True
                winner = "chaser"
            runner_reward += 0.01
            chaser_reward -= 0.01

        elif self.game_mode == "deathmatch":
            if self.runner_health <= 0 and self.chaser_health <= 0:
                terminated = True
                winner = "draw"
            elif self.runner_health <= 0:
                chaser_reward += 100.0
                runner_reward -= 100.0
                terminated = True
                winner = "chaser"
            elif self.chaser_health <= 0:
                runner_reward += 100.0
                chaser_reward -= 100.0
                terminated = True
                winner = "runner"

        if not terminated and (self._time_left() <= 0 or self.step_count >= MAX_STEPS):
            truncated = True
            if winner is None:
                if self.game_mode == "deathmatch":
                    if self.runner_health > self.chaser_health:
                        winner = "runner"
                    elif self.chaser_health > self.runner_health:
                        winner = "chaser"
                    else:
                        winner = "draw"
                else:
                    chaser_reward -= 10.0
                    winner = "runner"

        reward = runner_reward if self.role == ROLE_RUNNER else chaser_reward

        return self._obs_for(self.role), reward, terminated, truncated, self._get_info(winner=winner)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self):
        if self.render_mode != "human":
            return

        if self.screen is None:
            pygame.init()
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
            pygame.display.set_caption("NeuroArena - Advanced")
            self.clock = pygame.time.Clock()
            self.font = pygame.font.SysFont(None, 28)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                return

        self.screen.fill((0, 0, 0))

        for wall in self.walls:
            pygame.draw.rect(self.screen, (100, 100, 100), wall)

        pygame.draw.rect(self.screen, (255, 215, 0), (self.gem_x, self.gem_y, GEM_SIZE, GEM_SIZE))

        if self.items_enabled:
            if self.weapon_pos:
                pygame.draw.rect(self.screen, (255, 120, 0), (*self.weapon_pos, ITEM_SIZE, ITEM_SIZE))
            if self.shield_pos:
                pygame.draw.rect(self.screen, (0, 255, 255), (*self.shield_pos, ITEM_SIZE, ITEM_SIZE))
            if self.heal_pos:
                pygame.draw.rect(self.screen, (255, 0, 255), (*self.heal_pos, ITEM_SIZE, ITEM_SIZE))

        chaser_color = (150, 0, 0) if self.chaser_stun_steps > 0 else (255, 0, 0)
        pygame.draw.rect(self.screen, chaser_color, (self.chaser_x, self.chaser_y, AGENT_SIZE, AGENT_SIZE))

        runner_color = (0, 255, 255) if self.runner_shield_steps > 0 else (0, 200, 255)
        pygame.draw.rect(self.screen, runner_color, (self.runner_x, self.runner_y, AGENT_SIZE, AGENT_SIZE))

        if self.fog_of_war:
            pygame.draw.circle(
                self.screen, (60, 60, 60),
                (int(self.runner_x), int(self.runner_y)),
                self.vision_radius, 1
            )

        hud = (
            f"Mode:{self.game_mode} Map:{self.map_name} "
            f"Gems {self.gems_collected}/{TARGET_GEMS} "
            f"RHP {self.runner_health} CHP {self.chaser_health} "
            f"Time {int(self._time_left())}"
        )
        self.screen.blit(self.font.render(hud, True, (255, 255, 255)), (10, 10))

        pygame.display.update()
        self.clock.tick(FPS)

    def close(self):
        if self.screen is not None:
            pygame.quit()
            self.screen = None