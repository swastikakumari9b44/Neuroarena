from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str

class GameStartRequest(BaseModel):
    player_id: str
    difficulty: str = "Medium"

class GameStartResponse(BaseModel):
    game_id: str
    state: Dict[str, Any]

class GameActionRequest(BaseModel):
    game_id: str
    action: int

class GameActionResponse(BaseModel):
    state: Dict[str, Any]
    reward: float
    done: bool

class GameStateResponse(BaseModel):
    observation: List[float]
    reward: float
    done: bool

class AIMoveRequest(BaseModel):
    state: List[float]
    model_name: Optional[str] = None

class AIMoveResponse(BaseModel):
    action: int
    confidence: float

class TrainStartRequest(BaseModel):
    model_name: str
    total_steps: int = 10000

class TrainStatusResponse(BaseModel):
    episode: int
    reward: float
    win_rate: float
    steps_done: int

class ReplayResponse(BaseModel):
    match_id: str
    actions: List[int]
    score: int
    winner: str

class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    elo: float
    wins: int
    losses: int