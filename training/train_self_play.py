"""
train_self_play.py

Phase 7: Self-Play (Weeks 9-10)

Each generation:
  1. Load the current best model as a FROZEN opponent (random moves
     if there isn't one yet - generation 1 has nothing to play against).
  2. Train a challenger against it for GENERATION_STEPS timesteps,
     playing both roles (randomly assigned each episode).
  3. Evaluate the challenger against the frozen best over several
     matches, playing both roles equally.
  4. If the challenger wins more than it loses, IT becomes the new
     best - the next generation trains against it instead.
  5. At milestone generations, save a named snapshot
     (model_001, model_010, model_100, model_500, ...) so you can
     watch how the skill level climbed over the run.

Usage:
    python train_self_play.py
"""

import os

from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor

from duel_env import NeuroArenaDuelEnv, ROLE_RUNNER, ROLE_CHASER

TOTAL_GENERATIONS = 500
GENERATION_STEPS = 20_000
EVAL_EPISODES_PER_ROLE = 10          # evaluated as runner AND as chaser
MILESTONE_GENERATIONS = {1, 10, 100, 500}

BEST_MODEL_PATH = "self_play_best"
TENSORBOARD_LOG_DIR = "./tensorboard_logs/"


def evaluate(challenger, opponent, episodes_per_role):
    """
    Plays `challenger` against `opponent` over a fixed number of
    matches in EACH role, and returns the challenger's win rate.
    Ties (timeout without a capture already count as a runner win in
    the env) are handled inside NeuroArenaDuelEnv's `winner` field.
    """

    wins = 0
    total = 0

    for role in (ROLE_RUNNER, ROLE_CHASER):
        eval_env = NeuroArenaDuelEnv(opponent_model=opponent)

        for _ in range(episodes_per_role):
            obs, info = eval_env.reset(options={"role": role})
            terminated = truncated = False

            while not (terminated or truncated):
                action, _ = challenger.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = eval_env.step(action)

            challenger_role_name = "runner" if role == ROLE_RUNNER else "chaser"
            if info["winner"] == challenger_role_name:
                wins += 1
            total += 1

        eval_env.close()

    return wins / total if total > 0 else 0.0


def main():
    best_model = None  # None until generation 1 produces one

    for generation in range(1, TOTAL_GENERATIONS + 1):
        print(f"\n=== Generation {generation}/{TOTAL_GENERATIONS} ===")

        raw_env = NeuroArenaDuelEnv(opponent_model=best_model)
        env = Monitor(raw_env)

        if generation == 1:
            challenger = PPO(
                "MlpPolicy",
                env,
                verbose=0,
                tensorboard_log=TENSORBOARD_LOG_DIR,
            )
        else:
            challenger = PPO.load(f"{BEST_MODEL_PATH}.zip", env=env)

        challenger.learn(
            total_timesteps=GENERATION_STEPS,
            reset_num_timesteps=False,
            tb_log_name="self_play",
        )

        win_rate = evaluate(challenger, best_model, EVAL_EPISODES_PER_ROLE)
        print(f"Generation {generation}: challenger win rate vs previous best = {win_rate:.2f}")

        promoted = best_model is None or win_rate > 0.5

        if promoted:
            challenger.save(BEST_MODEL_PATH)
            best_model = PPO.load(f"{BEST_MODEL_PATH}.zip")
            print(f"  -> promoted: this is the new best model")
        else:
            print(f"  -> not promoted: previous best model stays in place")

        if generation in MILESTONE_GENERATIONS:
            milestone_name = f"model_{generation:03d}"
            (challenger if promoted else best_model).save(milestone_name)
            print(f"  -> saved milestone checkpoint: {milestone_name}.zip")

    print("\nSelf-play complete.")
    print(f"Final best model saved at {BEST_MODEL_PATH}.zip")


if __name__ == "__main__":
    main()