// lib/api.ts

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface GameStartResponse {
  game_id: string;
  state: {
    observation: number[];
    episode_reward: number;
  };
}

interface GameActionResponse {
  state: number[];
  reward: number;
  done: boolean;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
}

// Auth APIs
export const registerUser = async (username: string, email: string, password: string): Promise<AuthResponse> => {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  });
  if (!res.ok) throw new Error("Registration failed");
  return res.json();
};

export const loginUser = async (username: string, password: string): Promise<AuthResponse> => {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error("Login failed");
  return res.json();
};

// Game APIs
export const startGame = async (playerId: string, difficulty: string = "Medium"): Promise<GameStartResponse> => {
  const res = await fetch(`${API_BASE}/game/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ player_id: playerId, difficulty }),
  });
  if (!res.ok) throw new Error("Failed to start game");
  return res.json();
};

export const sendGameAction = async (gameId: string, action: number): Promise<GameActionResponse> => {
  const res = await fetch(`${API_BASE}/game/action`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ game_id: gameId, action }),
  });
  if (!res.ok) throw new Error("Action failed");
  return res.json();
};

export const getGameState = async (gameId: string) => {
  const res = await fetch(`${API_BASE}/game/state/${gameId}`);
  if (!res.ok) throw new Error("Failed to get game state");
  return res.json();
};

// AI APIs
export const getAIMove = async (state: number[], modelName?: string) => {
  const res = await fetch(`${API_BASE}/ai/move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ state, model_name: modelName }),
  });
  if (!res.ok) throw new Error("AI move failed");
  return res.json();
};

// Training APIs
export const startTraining = async (modelName: string, totalSteps: number = 10000) => {
  const res = await fetch(`${API_BASE}/train/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model_name: modelName, total_steps: totalSteps }),
  });
  if (!res.ok) throw new Error("Training start failed");
  return res.json();
};

export const getTrainingStatus = async (sessionId: string) => {
  const res = await fetch(`${API_BASE}/train/status/${sessionId}`);
  if (!res.ok) throw new Error("Failed to get training status");
  return res.json();
};

export const pauseTraining = async (sessionId: string) => {
  const res = await fetch(`${API_BASE}/train/pause/${sessionId}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to pause training");
  return res.json();
};

export const resumeTraining = async (sessionId: string) => {
  const res = await fetch(`${API_BASE}/train/resume/${sessionId}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to resume training");
  return res.json();
};

export const stopTraining = async (sessionId: string) => {
  const res = await fetch(`${API_BASE}/train/stop/${sessionId}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to stop training");
  return res.json();
};

// Leaderboard APIs
export const getLeaderboard = async () => {
  const res = await fetch(`${API_BASE}/leaderboard/`);
  if (!res.ok) throw new Error("Failed to get leaderboard");
  return res.json();
};

export const getUserStats = async (username: string) => {
  const res = await fetch(`${API_BASE}/leaderboard/${username}`);
  if (!res.ok) throw new Error("Failed to get user stats");
  return res.json();
};

// Health check
export const healthCheck = async (): Promise<boolean> => {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return res.ok;
  } catch {
    return false;
  }
};