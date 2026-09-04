"""
metrics_callback.py

Phase 5: Visualize Learning

stable-baselines3 already logs Reward, Loss, and Entropy to TensorBoard
automatically once you pass `tensorboard_log=...` to PPO:

    rollout/ep_rew_mean   -> Reward per episode (rolling mean)
    train/loss            -> Training Loss
    train/entropy_loss    -> Entropy (exploration vs exploitation)

Win Rate is specific to this game, so this callback tracks it manually:
each time an episode ends, it checks the `win` flag NeuroArenaEnv puts
in `info`, keeps a rolling window of outcomes, and logs the win
percentage under a `custom/win_rate` tag so it shows up in TensorBoard
alongside everything else.
"""

from collections import deque

from stable_baselines3.common.callbacks import BaseCallback


class WinRateCallback(BaseCallback):
    def __init__(self, window: int = 50, verbose: int = 0):
        super().__init__(verbose)
        self.window = window
        self.outcomes = deque(maxlen=window)

    def _on_step(self) -> bool:
        infos = self.locals.get("infos", [])
        dones = self.locals.get("dones", [])

        for info, done in zip(infos, dones):
            if done and "win" in info:
                self.outcomes.append(1.0 if info["win"] else 0.0)

                win_rate = sum(self.outcomes) / len(self.outcomes)
                self.logger.record("custom/win_rate", win_rate)

        return True