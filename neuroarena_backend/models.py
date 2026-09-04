from .database import Base
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid


# ===========================
# USERS
# ===========================

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    matches = relationship("Match", back_populates="player")
    leaderboard = relationship(
        "Leaderboard",
        back_populates="user",
        uselist=False
    )


# ===========================
# SAVED AI MODELS
# ===========================

class SavedModel(Base):
    __tablename__ = "saved_models"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    accuracy = Column(Float, default=0.0)
    filepath = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ===========================
# TRAINING SESSION
# ===========================

class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    model_name = Column(String, default="PPO")

    episode = Column(Integer, default=0)

    reward = Column(Float, default=0.0)

    loss = Column(Float, default=0.0)

    win_rate = Column(Float, default=0.0)

    duration = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)


# ===========================
# TRAINING METRIC HISTORY (one row per episode, for charting)
# ===========================

class TrainingMetric(Base):
    __tablename__ = "training_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    session_id = Column(String, ForeignKey("training_sessions.id"), nullable=False, index=True)

    episode = Column(Integer, nullable=False)

    reward = Column(Float, default=0.0)

    loss = Column(Float, default=0.0)

    win_rate = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)


# ===========================
# GAME MATCHES
# ===========================

class Match(Base):
    __tablename__ = "matches"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    player_id = Column(
        String,
        ForeignKey("users.id"),
        nullable=False
    )

    opponent = Column(String, default="AI")

    winner = Column(String, nullable=False)

    score = Column(Integer, default=0)

    duration = Column(Integer, default=0)

    timestamp = Column(DateTime, default=datetime.utcnow)

    player = relationship("User", back_populates="matches")


# ===========================
# MATCH REPLAY
# ===========================

class MatchReplay(Base):
    __tablename__ = "match_replays"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    match_id = Column(
        String,
        ForeignKey("matches.id"),
        nullable=False
    )

    actions = Column(JSON, default=[])

    positions = Column(JSON, default=[])

    winner = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)


# ===========================
# LEADERBOARD
# ===========================

class Leaderboard(Base):
    __tablename__ = "leaderboard"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    user_id = Column(
        String,
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    elo = Column(Float, default=1200.0)

    wins = Column(Integer, default=0)

    losses = Column(Integer, default=0)

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    user = relationship("User", back_populates="leaderboard")