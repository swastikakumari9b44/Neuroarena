const API_URL = "http://127.0.0.1:8000";

export type GameState = {
  player_x: number;
  player_y: number;
  enemy_x: number;
  enemy_y: number;
  gem_x: number;
  gem_y: number;
  health: number;
  gems_collected: number;
  time_left: number;
  player_vx: number;
  player_vy: number;
};

export async function startGame(playerId: string, difficulty: string = "Medium") {
  const response = await fetch(`${API_URL}/game/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ player_id: playerId, difficulty }),
  });

  if (!response.ok) {
    throw new Error("Failed to start game");
  }

  return await response.json() as { game_id: string; state: GameState };
}

export async function sendAction(gameId: string, action: string) {
  const response = await fetch(`${API_URL}/game/action`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ game_id: gameId, action }),
  });

  if (!response.ok) {
    throw new Error("Failed to send action");
  }

  return await response.json() as { state: GameState; reward: number; done: boolean };
}