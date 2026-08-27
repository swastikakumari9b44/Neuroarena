"""
watch_advanced.py

Phase 8 demo - play the advanced environment yourself with the
keyboard against a scripted AI personality. No trained model or
stable-baselines3 needed here, just pygame, so you can check each
new feature works before investing in training against it.

Examples:
    python watch_advanced.py
    python watch_advanced.py --map cross --obstacles --fog
    python watch_advanced.py --map open --mode deathmatch --items --personality tactical
    python watch_advanced.py --mode survival --items --personality defensive
"""

import argparse

import pygame

from advanced_env import (
    AdvancedNeuroArenaEnv,
    ROLE_RUNNER,
    ACTION_NONE,
    ACTION_LEFT,
    ACTION_RIGHT,
    ACTION_UP,
    ACTION_DOWN,
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", default="classic", choices=["classic", "cross", "open", "random"])
    parser.add_argument("--mode", default="classic", choices=["classic", "survival", "deathmatch"])
    parser.add_argument(
        "--personality", default="aggressive",
        choices=["aggressive", "defensive", "erratic", "tactical"]
    )
    parser.add_argument("--fog", action="store_true", help="enable fog of war")
    parser.add_argument("--items", action="store_true", help="enable weapon/shield/heal pickups")
    parser.add_argument("--obstacles", action="store_true", help="enable random obstacles")
    return parser.parse_args()


def keys_to_action(keys):
    if keys[pygame.K_LEFT]:
        return ACTION_LEFT
    if keys[pygame.K_RIGHT]:
        return ACTION_RIGHT
    if keys[pygame.K_UP]:
        return ACTION_UP
    if keys[pygame.K_DOWN]:
        return ACTION_DOWN
    return ACTION_NONE


def main():
    args = parse_args()

    env = AdvancedNeuroArenaEnv(
        opponent_model=None,   # chaser is scripted, driven by --personality
        map_name=args.map,
        random_obstacles=args.obstacles,
        fog_of_war=args.fog,
        items_enabled=args.items,
        game_mode=args.mode,
        personality=args.personality,
        render_mode="human",
    )

    obs, info = env.reset(options={"role": ROLE_RUNNER})
    env.render()

    print(f"Playing as the RUNNER (arrow keys). Chaser personality: {args.personality}")
    print(f"Map: {args.map}  Mode: {args.mode}  Fog: {args.fog}  Items: {args.items}  Obstacles: {args.obstacles}")
    print("ESC or close the window to quit.")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        if not running:
            break

        keys = pygame.key.get_pressed()
        action = keys_to_action(keys)

        obs, reward, terminated, truncated, info = env.step(action)
        env.render()

        if terminated or truncated:
            print(f"Match over - winner: {info['winner']}  gems: {info['gems_collected']}")
            obs, info = env.reset(options={"role": ROLE_RUNNER})

    env.close()


if __name__ == "__main__":
    main()