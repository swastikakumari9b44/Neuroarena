from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Leaderboard, User
from schemas import LeaderboardEntry

router = APIRouter()

@router.get("/")
def get_leaderboard(db: Session = Depends(get_db)):
    """Get top 100 players"""
    entries = db.query(Leaderboard, User).join(User).order_by(Leaderboard.elo.desc()).limit(100).all()
    result = [
        LeaderboardEntry(
            rank=idx+1,
            username=user.username,
            elo=entry.elo,
            wins=entry.wins,
            losses=entry.losses
        )
        for idx, (entry, user) in enumerate(entries)
    ]
    return {"entries": result}

@router.get("/{username}")
def get_user_leaderboard(username: str, db: Session = Depends(get_db)):
    """Get user stats"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    entry = db.query(Leaderboard).filter(Leaderboard.user_id == user.id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="User not on leaderboard")
    
    rank = db.query(Leaderboard).filter(Leaderboard.elo > entry.elo).count() + 1
    return {"username": username, "elo": entry.elo, "rank": rank, "wins": entry.wins, "losses": entry.losses}