const API_URL = "http://127.0.0.1:8000";

export async function startTraining(
  modelName: string = "PPO",
  totalSteps: number = 10000
) {
  const response = await fetch(`${API_URL}/train/start`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model_name: modelName,
      total_steps: totalSteps,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to start training");
  }

  return await response.json();
}

export async function getTrainingStatus(sessionId: string) {
  const response = await fetch(
    `${API_URL}/train/status/${sessionId}`
  );

  if (!response.ok) {
    throw new Error("Failed to get training status");
  }

  return await response.json();
}
export async function getTrainingHistory(sessionId: string) {
  const response = await fetch(`${API_URL}/train/history/${sessionId}`);
  if (!response.ok) {
    throw new Error("Failed to get training history");
  }
  return await response.json();
}

export async function getBestModel(modelName: string = "PPO") {
  const response = await fetch(`${API_URL}/train/best-model?model_name=${modelName}`);
  if (!response.ok) {
    throw new Error("Failed to get best model");
  }
  return await response.json();
}