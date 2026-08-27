"""
watch_agent.py

Loads a saved PPO checkpoint and renders it playing NeuroArena so
you can watch how it behaves at each training stage.

Usage:
    python watch_agent.py ppo_neuroarena_10k
    python watch_agent.py ppo_neuroarena_100k
    python watch_agent.py ppo_neuroarena_1m
"""

import sys

from stable_baselines3 import PPO

from neuroarena_env import NeuroArenaEnv


def main():
    if len(sys.argv) < 2:
        print("Usage: python watch_agent.py <model_name_without_.zip>")
        print("Example: python watch_agent.py ppo_neuroarena_10k")
        sys.exit(1)

    model_path = sys.argv[1]

    env = NeuroArenaEnv(render_mode="human")
    model = PPO.load(model_path, env=env)

    episodes = 5

    for ep in range(1, episodes + 1):
        obs, info = env.reset()
        terminated = False
        truncated = False
        total_reward = 0.0

        while not (terminated or truncated):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            env.render()

        print(
            f"Episode {ep}: reward={total_reward:.2f} "
            f"gems={info['gems_collected']} health={info['health']}"
        )

    env.close()


if __name__ == "__main__":
    main()