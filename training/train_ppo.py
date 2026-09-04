"""
train_ppo.py

Weeks 5-6: Train Your First AI

Runs the PPO training curriculum in three stages, saving a checkpoint
after each so you can watch how the agent's behavior changes as it
trains longer:

    Stage 1 :   10,000 steps  -> watch it fail
    Stage 2 :  100,000 steps  -> watch improvement
    Stage 3 : 1,000,000 steps -> should begin to play intelligently

Usage:
    pip install -r requirements.txt
    python train_ppo.py
"""

from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.monitor import Monitor

from neuroarena_env import NeuroArenaEnv
from metrics_callback import WinRateCallback

TENSORBOARD_LOG_DIR = "./tensorboard_logs/"


def main():
    raw_env = NeuroArenaEnv()

    # Optional but recommended: sanity-checks the env against the
    # Gymnasium API before you spend time training on it.
    check_env(raw_env, warn=True)

    # Monitor wraps the env so SB3 tracks per-episode reward/length,
    # which is what feeds the "Reward" graph in TensorBoard.
    env = Monitor(raw_env)

    # Phase 5: Visualize Learning - tracks win/loss per episode and
    # logs a rolling win rate under the "custom/win_rate" tag.
    win_rate_callback = WinRateCallback(window=50)

    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        tensorboard_log=TENSORBOARD_LOG_DIR,
    )

    # -----------------------------
    # Stage 1: 10,000 steps
    # -----------------------------
    print("\n=== Stage 1: training to 10,000 steps ===")
    model.learn(
        total_timesteps=10_000,
        callback=win_rate_callback,
        tb_log_name="stage1_10k",
    )
    model.save("ppo_neuroarena_10k")
    print("Saved ppo_neuroarena_10k.zip -> run watch_agent.py ppo_neuroarena_10k to watch it fail")

    # -----------------------------
    # Stage 2: 100,000 steps total
    # -----------------------------
    print("\n=== Stage 2: training to 100,000 steps ===")
    model.learn(
        total_timesteps=90_000,
        reset_num_timesteps=False,
        callback=win_rate_callback,
        tb_log_name="stage2_100k",
    )
    model.save("ppo_neuroarena_100k")
    print("Saved ppo_neuroarena_100k.zip -> run watch_agent.py ppo_neuroarena_100k to watch improvement")

    # -----------------------------
    # Stage 3: 1,000,000 steps total
    # -----------------------------
    print("\n=== Stage 3: training to 1,000,000 steps ===")
    model.learn(
        total_timesteps=900_000,
        reset_num_timesteps=False,
        callback=win_rate_callback,
        tb_log_name="stage3_1m",
    )
    model.save("ppo_neuroarena_1m")
    print("Saved ppo_neuroarena_1m.zip -> run watch_agent.py ppo_neuroarena_1m to see intelligent play")

    print(f"\nTensorBoard logs written to {TENSORBOARD_LOG_DIR}")
    print(f"View them with: tensorboard --logdir {TENSORBOARD_LOG_DIR}")


if __name__ == "__main__":
    main()