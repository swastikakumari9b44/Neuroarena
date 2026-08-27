from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db
from routes import game, ai, training, auth, leaderboard
from websockets import manager
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Neuroarena Backend", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(game.router, prefix="/game", tags=["Game"])
app.include_router(ai.router, prefix="/ai", tags=["AI"])
app.include_router(training.router, prefix="/train", tags=["Training"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(leaderboard.router, prefix="/leaderboard", tags=["Leaderboard"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "neuroarena-backend"}

# ============================================================
# WEBSOCKET: Live Game Updates
# ============================================================
@app.websocket("/ws/game/{game_id}")
async def websocket_game(websocket: WebSocket, game_id: str):
    await manager.connect_game(game_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast_game(game_id, {
                "type": "game_update",
                "data": data,
                "timestamp": str(__import__('datetime').datetime.utcnow().isoformat())
            })
    except WebSocketDisconnect:
        manager.disconnect_game(game_id, websocket)

# ============================================================
# WEBSOCKET: Live Training Progress
# ============================================================
@app.websocket("/ws/training/{session_id}")
async def websocket_training(websocket: WebSocket, session_id: str):
    await manager.connect_training(session_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast_training(session_id, {
                "type": "training_progress",
                "data": data,
                "timestamp": str(__import__('datetime').datetime.utcnow().isoformat())
            })
    except WebSocketDisconnect:
        manager.disconnect_training(session_id, websocket)

# ============================================================
# WEBSOCKET: Live Leaderboard
# ============================================================
@app.websocket("/ws/leaderboard")
async def websocket_leaderboard(websocket: WebSocket):
    await manager.connect_leaderboard(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast_leaderboard({
                "type": "leaderboard_update",
                "data": data,
                "timestamp": str(__import__('datetime').datetime.utcnow().isoformat())
            })
    except WebSocketDisconnect:
        manager.disconnect_leaderboard(websocket)

# ============================================================
# WEBSOCKET: AI vs AI Spectating
# ============================================================
@app.websocket("/ws/ai-match/{match_id}")
async def websocket_ai_match(websocket: WebSocket, match_id: str):
    await manager.connect_game(f"ai_{match_id}", websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast_game(f"ai_{match_id}", {
                "type": "ai_match_update",
                "data": data,
                "timestamp": str(__import__('datetime').datetime.utcnow().isoformat())
            })
    except WebSocketDisconnect:
        manager.disconnect_game(f"ai_{match_id}", websocket)