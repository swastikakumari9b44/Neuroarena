from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import GameStartRequest, GameStartResponse, GameActionRequest, GameActionResponse, GameStateResponse
import sys
import os
import uuid
import gymnasium as gym

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from neuroarena_env import NeuroArenaEnv

router = APIRouter()

# Store active games in memory (in production, use Redis or database)
active_games = {}

@router.post("/start", response_model=GameStartResponse)
def start_game(request: GameStartRequest, db: Session = Depends(get_db)):
    """Start a new game session"""
    game_id = str(uuid.uuid4())
    try:
        env = NeuroArenaEnv()
        observation, info = env.reset()
        
        active_games[game_id] = {
            "env": env,
            "observation": observation.tolist(),
            "episode_reward": 0,
            "steps": 0
        }
        
        return {
            "game_id": game_id,
            "state": {"observation": observation.tolist(), "episode_reward": 0}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/action", response_model=GameActionResponse)
def game_action(request: GameActionRequest, db: Session = Depends(get_db)):
    """Process player action and return new state"""
    if request.game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    try:
        game_data = active_games[request.game_id]
        env = game_data["env"]
        
        observation, reward, terminated, truncated, info = env.step(request.action)
        done = terminated or truncated
        
        game_data["observation"] = observation.tolist()
        game_data["episode_reward"] += float(reward)
        game_data["steps"] += 1
        
        return {
            "state": observation.tolist(),
            "reward": float(reward),
            "done": done
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/state/{game_id}", response_model=GameStateResponse)
def get_game_state(game_id: str, db: Session = Depends(get_db)):
    """Get current game state"""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game_data = active_games[game_id]
    return {
        "observation": game_data["observation"],
        "reward": game_data["episode_reward"],
        "done": False
    }