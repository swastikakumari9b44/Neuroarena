from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import TrainStartRequest, TrainStatusResponse, TrainingMetricPoint, SavedModelResponse
from ..models import TrainingSession, TrainingMetric, SavedModel
from typing import List
import random
import threading
import time
import uuid
from datetime import datetime

router = APIRouter()

CHECKPOINT_EVERY = 50  # episodes between checkpoint attempts

# In-memory pause/stop flags per session_id. Populated when a training
# thread starts, removed when it ends. This is what /pause, /resume,
# and /stop actually flip.
training_controls = {}


def train_model(session_id: str, model_name: str):
    from ..database import SessionLocal

    db = SessionLocal()

    try:
        session = db.query(TrainingSession).filter(
            TrainingSession.id == session_id
        ).first()

        if not session:
            return

        for episode in range(1, 1001):
            controls = training_controls.get(session_id, {"paused": False, "stopped": False})

            if controls.get("stopped"):
                break

            # Block here while paused, but keep re-checking so a stop
            # request during a pause still ends the loop promptly.
            while controls.get("paused") and not controls.get("stopped"):
                time.sleep(0.2)
                controls = training_controls.get(session_id, {"paused": False, "stopped": False})

            if controls.get("stopped"):
                break

            session.episode = episode
            session.reward = min(episode * 0.3, 300) + random.uniform(-5, 5)
            session.loss = max(2.0 - episode * 0.002, 0.05)
            session.win_rate = min(episode * 0.09, 95)
            db.commit()

            db.add(TrainingMetric(
                id=str(uuid.uuid4()),
                session_id=session_id,
                episode=episode,
                reward=session.reward,
                loss=session.loss,
                win_rate=session.win_rate,
            ))
            db.commit()

            if episode % CHECKPOINT_EVERY == 0 or episode == 1000:
                _maybe_save_checkpoint(db, model_name, session.win_rate)

            time.sleep(0.2)
    finally:
        db.close()
        training_controls.pop(session_id, None)


def _maybe_save_checkpoint(db: Session, model_name: str, win_rate: float):
    """Save a new versioned checkpoint only if this beats the best accuracy
    seen so far for this model_name. This is what powers 'Best Model'."""
    best = (
        db.query(SavedModel)
        .filter(SavedModel.model_name == model_name)
        .order_by(SavedModel.accuracy.desc())
        .first()
    )

    if best and best.accuracy >= win_rate:
        return

    existing_versions = db.query(SavedModel).filter(SavedModel.model_name == model_name).count()
    new_version = f"v{existing_versions + 1}"

    checkpoint = SavedModel(
        id=str(uuid.uuid4()),
        model_name=model_name,
        version=new_version,
        accuracy=win_rate,
        filepath=None,
    )
    db.add(checkpoint)
    db.commit()


@router.post("/start")
def start_training(request: TrainStartRequest, db: Session = Depends(get_db)):
    """Start PPO training"""
    session = TrainingSession(
        id=str(uuid.uuid4()),
        model_name=request.model_name,
        created_at=datetime.utcnow(),
    )

    db.add(session)
    db.commit()

    training_controls[session.id] = {"paused": False, "stopped": False}

    thread = threading.Thread(
        target=train_model,
        args=(session.id, request.model_name),
        daemon=True,
    )

    thread.start()
    return {
        "session_id": session.id,
        "started_at": session.created_at,
    }


@router.post("/pause/{session_id}")
def pause_training(session_id: str):
    """Pause a running training session"""
    if session_id not in training_controls:
        raise HTTPException(status_code=404, detail="Training session not found or already finished")

    training_controls[session_id]["paused"] = True
    return {"session_id": session_id, "status": "paused"}


@router.post("/resume/{session_id}")
def resume_training(session_id: str):
    """Resume a paused training session"""
    if session_id not in training_controls:
        raise HTTPException(status_code=404, detail="Training session not found or already finished")

    training_controls[session_id]["paused"] = False
    return {"session_id": session_id, "status": "resumed"}


@router.post("/stop/{session_id}")
def stop_training(session_id: str):
    """Stop a training session permanently (cannot be resumed)"""
    if session_id not in training_controls:
        raise HTTPException(status_code=404, detail="Training session not found or already finished")

    training_controls[session_id]["stopped"] = True
    return {"session_id": session_id, "status": "stopped"}


@router.get("/status/{session_id}", response_model=TrainStatusResponse)
def get_training_status(session_id: str, db: Session = Depends(get_db)):
    """Get training progress (latest snapshot)"""
    session = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
    if not session:
        return {"episode": 0, "reward": 0.0, "win_rate": 0.0, "steps_done": 0, "loss": 0.0}

    return {
        "episode": session.episode,
        "reward": session.reward,
        "win_rate": session.win_rate,
        "steps_done": 0,
        "loss": session.loss,
    }


@router.get("/history/{session_id}", response_model=List[TrainingMetricPoint])
def get_training_history(session_id: str, db: Session = Depends(get_db)):
    """Full episode-by-episode reward/loss/win_rate history, for charting."""
    metrics = (
        db.query(TrainingMetric)
        .filter(TrainingMetric.session_id == session_id)
        .order_by(TrainingMetric.episode.asc())
        .all()
    )

    return [
        {
            "episode": m.episode,
            "reward": m.reward,
            "loss": m.loss,
            "win_rate": m.win_rate,
        }
        for m in metrics
    ]


@router.get("/best-model", response_model=SavedModelResponse)
def get_best_model(model_name: str = "PPO", db: Session = Depends(get_db)):
    """Highest-accuracy checkpoint saved so far for this model_name."""
    best = (
        db.query(SavedModel)
        .filter(SavedModel.model_name == model_name)
        .order_by(SavedModel.accuracy.desc())
        .first()
    )

    if not best:
        return {
            "id": "",
            "model_name": model_name,
            "version": "v0",
            "accuracy": 0.0,
            "created_at": datetime.utcnow(),
        }

    return {
        "id": best.id,
        "model_name": best.model_name,
        "version": best.version,
        "accuracy": best.accuracy,
        "created_at": best.created_at,
    }