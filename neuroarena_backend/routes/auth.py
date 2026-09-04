from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import UserRegister, UserLogin, TokenResponse
from ..models import User, Leaderboard
from ..utils.auth import hash_password, verify_password, create_access_token
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/register", response_model=TokenResponse)
def register(user: UserRegister, db: Session = Depends(get_db)):
    """Register new user"""
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username exists")
    
    new_user = User(
        id=str(uuid.uuid4()),
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password)
    )
    db.add(new_user)
    
    # Create leaderboard entry
    leaderboard = Leaderboard(
        id=str(uuid.uuid4()),
        user_id=new_user.id
    )
    db.add(leaderboard)
    db.commit()
    
    token = create_access_token(new_user.id)
    return {"access_token": token, "token_type": "bearer", "user_id": new_user.id}

@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(db_user.id)
    return {"access_token": token, "token_type": "bearer", "user_id": db_user.id}