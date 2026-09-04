from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        self.active_games: Dict[str, List[WebSocket]] = {}
        self.training_watchers: Dict[str, List[WebSocket]] = {}
        self.leaderboard_watchers: List[WebSocket] = []
    
    # Game connections
    async def connect_game(self, game_id: str, websocket: WebSocket):
        await websocket.accept()
        if game_id not in self.active_games:
            self.active_games[game_id] = []
        self.active_games[game_id].append(websocket)
    
    def disconnect_game(self, game_id: str, websocket: WebSocket):
        if game_id in self.active_games:
            try:
                self.active_games[game_id].remove(websocket)
            except:
                pass
    
    async def broadcast_game(self, game_id: str, message: dict):
        if game_id in self.active_games:
            for conn in list(self.active_games[game_id]):
                try:
                    await conn.send_json(message)
                except:
                    self.disconnect_game(game_id, conn)
    
    # Training connections
    async def connect_training(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.training_watchers:
            self.training_watchers[session_id] = []
        self.training_watchers[session_id].append(websocket)
    
    def disconnect_training(self, session_id: str, websocket: WebSocket):
        if session_id in self.training_watchers:
            try:
                self.training_watchers[session_id].remove(websocket)
            except:
                pass
    
    async def broadcast_training(self, session_id: str, message: dict):
        if session_id in self.training_watchers:
            for conn in list(self.training_watchers[session_id]):
                try:
                    await conn.send_json(message)
                except:
                    self.disconnect_training(session_id, conn)
    
    # Leaderboard connections
    async def connect_leaderboard(self, websocket: WebSocket):
        await websocket.accept()
        self.leaderboard_watchers.append(websocket)
    
    def disconnect_leaderboard(self, websocket: WebSocket):
        try:
            self.leaderboard_watchers.remove(websocket)
        except:
            pass
    
    async def broadcast_leaderboard(self, message: dict):
        for conn in list(self.leaderboard_watchers):
            try:
                await conn.send_json(message)
            except:
                self.disconnect_leaderboard(conn)

manager = ConnectionManager()