const API = process.env.NEXT_PUBLIC_API_URL!;

export async function healthCheck() {
    const res = await fetch(`${API}/health`);
    return await res.json();
}
const API_URL = "http://127.0.0.1:8000";

export async function pauseTraining(sessionId: string) {
  const response = await fetch(`${API_URL}/train/pause/${sessionId}`, { method: "POST" });
  if (!response.ok) throw new Error("Failed to pause training");
  return await response.json();
}

export async function resumeTraining(sessionId: string) {
  const response = await fetch(`${API_URL}/train/resume/${sessionId}`, { method: "POST" });
  if (!response.ok) throw new Error("Failed to resume training");
  return await response.json();
}

export async function stopTraining(sessionId: string) {
  const response = await fetch(`${API_URL}/train/stop/${sessionId}`, { method: "POST" });
  if (!response.ok) throw new Error("Failed to stop training");
  return await response.json();
}