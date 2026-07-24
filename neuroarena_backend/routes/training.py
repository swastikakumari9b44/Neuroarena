from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import TrainStartRequest, TrainStatusResponse
from models import TrainingSession
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/start")
def start_training(request: TrainStartRequest, db: Session = Depends(get_db)):
    """Start PPO training"""
    session = TrainingSession(id=str(uuid.uuid4()), created_at=datetime.utcnow())
    db.add(session)
    db.commit()
    return {"session_id": session.id, "started_at": session.created_at}

@router.get("/status/{session_id}", response_model=TrainStatusResponse)
def get_training_status(session_id: str, db: Session = Depends(get_db)):
    """Get training progress"""
    session = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
    if not session:
        return {"episode": 0, "reward": 0.0, "win_rate": 0.0, "steps_done": 0}
    
    return {
        "episode": session.episode,
        "reward": session.reward,
        "win_rate": session.win_rate,
        "steps_done": 0
    }