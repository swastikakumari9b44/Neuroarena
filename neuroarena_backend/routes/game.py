from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import GameStartRequest, GameStartResponse, GameActionRequest, GameActionResponse, GameStateResponse
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ..game.neuroarena_env import NeuroArenaEnv
router = APIRouter()

# Store active games in memory (in production, use Redis or database)
active_games = {}

# Maps the readable action names the frontend sends to the integer
# actions NeuroArenaEnv.step() expects.
ACTION_MAP = {
    "none": 0,
    "move_left": 1,
    "move_right": 2,
    "move_up": 3,
    "move_down": 4,
}

# Keys of the observation vector returned by NeuroArenaEnv, in order.
# Used to turn the raw float list into a named dict the frontend can
# render without needing to know the backend's internal ordering.
OBS_KEYS = [
    "player_x", "player_y",
    "enemy_x", "enemy_y",
    "gem_x", "gem_y",
    "health", "gems_collected", "time_left",
    "player_vx", "player_vy",
]


def obs_to_state(observation):
    return dict(zip(OBS_KEYS, observation))


@router.post("/start", response_model=GameStartResponse)
def start_game(request: GameStartRequest, db: Session = Depends(get_db)):
    """Start a new game session"""
    game_id = str(uuid.uuid4())
    try:
        env = NeuroArenaEnv(difficulty=request.difficulty)
        observation, info = env.reset()
        state = obs_to_state(observation.tolist())

        active_games[game_id] = {
            "env": env,
            "state": state,
            "episode_reward": 0.0,
            "steps": 0,
        }

        return {
            "game_id": game_id,
            "state": state,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/action", response_model=GameActionResponse)
def game_action(request: GameActionRequest, db: Session = Depends(get_db)):
    """Process a player action (e.g. 'move_left') and return the new state"""
    if request.game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")

    if request.action not in ACTION_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown action '{request.action}'. Valid actions: {list(ACTION_MAP.keys())}",
        )

    try:
        game_data = active_games[request.game_id]
        env = game_data["env"]

        action_int = ACTION_MAP[request.action]
        observation, reward, terminated, truncated, info = env.step(action_int)
        done = terminated or truncated

        state = obs_to_state(observation.tolist())

        game_data["state"] = state
        game_data["episode_reward"] += float(reward)
        game_data["steps"] += 1

        return {
            "state": state,
            "reward": float(reward),
            "done": done,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/state/{game_id}")
def get_game_state(game_id: str, db: Session = Depends(get_db)):
    """Get current game state"""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")

    game_data = active_games[game_id]
    return {
        "state": game_data["state"],
        "reward": game_data["episode_reward"],
        "done": False,
    }