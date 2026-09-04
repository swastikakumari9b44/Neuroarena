// lib/websocket.ts
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export class GameWebSocket {
  private ws: WebSocket | null = null;
  private gameId: string;
  private onMessage: (data: any) => void;
  private onClose: () => void;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  constructor(gameId: string, onMessage: (data: any) => void, onClose: () => void) {
    this.gameId = gameId;
    this.onMessage = onMessage;
    this.onClose = onClose;
  }

  connect() {
    const wsUrl = `${WS_BASE}/ws/game/${this.gameId}`;
    console.log(`Connecting to game WebSocket: ${wsUrl}`);
    
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log("Game WebSocket connected");
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.onMessage(data);
    };

    this.ws.onerror = (error) => {
      console.error("Game WebSocket error:", error);
    };

    this.ws.onclose = () => {
      console.log("Game WebSocket disconnected");
      this.onClose();
      this.reconnect();
    };
  }

  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn("WebSocket not connected");
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  private reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.pow(2, this.reconnectAttempts) * 1000;
      console.log(`Reconnecting in ${delay}ms...`);
      setTimeout(() => this.connect(), delay);
    }
  }
}

export class TrainingWebSocket {
  private ws: WebSocket | null = null;
  private sessionId: string;
  private onProgress: (data: any) => void;
  private onMetrics: (data: any) => void;

  constructor(sessionId: string, onProgress: (data: any) => void, onMetrics: (data: any) => void) {
    this.sessionId = sessionId;
    this.onProgress = onProgress;
    this.onMetrics = onMetrics;
  }

  connect() {
    const wsUrl = `${WS_BASE}/ws/training/${this.sessionId}`;
    console.log(`Connecting to training WebSocket: ${wsUrl}`);
    
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log("Training WebSocket connected");
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === "training_progress") {
        this.onProgress(data.progress);
      } else if (data.type === "training_metrics") {
        this.onMetrics(data.metrics);
      }
    };

    this.ws.onerror = (error) => {
      console.error("Training WebSocket error:", error);
    };

    this.ws.onclose = () => {
      console.log("Training WebSocket disconnected");
    };
  }

  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export class LeaderboardWebSocket {
  private ws: WebSocket | null = null;
  private onUpdate: (data: any) => void;

  constructor(onUpdate: (data: any) => void) {
    this.onUpdate = onUpdate;
  }

  connect() {
    const wsUrl = `${WS_BASE}/ws/leaderboard`;
    console.log(`Connecting to leaderboard WebSocket: ${wsUrl}`);
    
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log("Leaderboard WebSocket connected");
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.onUpdate(data);
    };

    this.ws.onerror = (error) => {
      console.error("Leaderboard WebSocket error:", error);
    };

    this.ws.onclose = () => {
      console.log("Leaderboard WebSocket disconnected");
    };
  }

  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}