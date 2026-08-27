"""
watch_duel.py

Loads two saved self-play checkpoints and renders them playing
against each other - one as runner, one as chaser. Great for putting
model_001 up against model_500 to see the generational gap.

Usage:
    python watch_duel.py model_001 model_500
    (first argument plays runner, second plays chaser)

    python watch_duel.py self_play_best self_play_best
    (watch the current best model play against itself)
"""

import sys

from stable_baselines3 import PPO

from duel_env import NeuroArenaDuelEnv, ROLE_RUNNER, ROLE_CHASER


def main():
    if len(sys.argv) < 3:
        print("Usage: python watch_duel.py <runner_model> <chaser_model>")
        print("Example: python watch_duel.py model_001 model_500")
        sys.exit(1)

    runner_path, chaser_path = sys.argv[1], sys.argv[2]

    chaser_model = PPO.load(chaser_path)

    # The env is single-agent from the "runner" perspective; the
    # chaser model is passed in as the frozen opponent.
    env = NeuroArenaDuelEnv(opponent_model=chaser_model, render_mode="human")
    runner_model = PPO.load(runner_path, env=env)

    episodes = 5

    for ep in range(1, episodes + 1):
        obs, info = env.reset(options={"role": ROLE_RUNNER})
        terminated = truncated = False

        while not (terminated or truncated):
            action, _ = runner_model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            env.render()

        print(f"Episode {ep}: winner={info['winner']} gems={info['gems_collected']} health={info['health']}")

    env.close()


if __name__ == "__main__":
    main()