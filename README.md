<div align="center">

# 🧠 NeuroArena

**A reinforcement learning training ground with a live web dashboard**

Start reinforcement-learning training and monitor episode rewards, loss, win rate, and checkpoint progress through a web interface.

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-frontend-000000?logo=next.js&logoColor=white)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-database-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-Educational-lightgrey)](#license)

</div>

---

## Overview

NeuroArena is a reinforcement learning (RL) training and game environment that pairs an interactive game with a web-based dashboard for monitoring training progress. Rather than watching a training script scroll by in a terminal, you get a live view of an agent learning to play.

The project uses a **Python/FastAPI** backend for game and training APIs, and a **Next.js** frontend for the monitoring dashboard.

The dashboard tracks:

- Current episode
- Episode reward
- Win rate
- Training speed
- Reward trajectory
- Loss trajectory
- Best model information
- Checkpoint progress

The project currently uses **PPO (Proximal Policy Optimization)** as its reinforcement learning algorithm.

---

## Features

### 🤖 Reinforcement Learning
- PPO-based training workflow
- Custom game environment using Gymnasium
- Training session management
- Training metrics and history
- Model checkpoint tracking

### 🎮 Game Environment
- Interactive game built with Pygame
- Configurable game environment
- Game state and action APIs
- AI move endpoint for interacting with the trained model

### 📊 Training Dashboard
- Real-time training status updates
- Reward and loss visualization
- Win-rate monitoring
- Training-speed indicator
- Best-model information
- Replay interface
- Training reset functionality

### ⚙️ Backend
- REST APIs built with FastAPI
- PostgreSQL database integration
- Training session persistence
- Authentication endpoints
- Leaderboard endpoints
- WebSocket support for real-time communication

### 🖥️ Frontend
- Next.js + React + TypeScript
- Tailwind CSS
- Reusable UI components
- Dashboard-style interface

---

## Tech Stack

| Layer                  | Technology                 |
| ---------------------- | --------------------------- |
| Frontend               | Next.js, React, TypeScript |
| Styling                | Tailwind CSS                |
| UI Components          | Custom React components     |
| Backend                | FastAPI                     |
| Language               | Python                      |
| Reinforcement Learning | Gymnasium, PPO               |
| Game                   | Pygame                       |
| Database               | PostgreSQL                   |
| API Communication      | REST / WebSockets             |

---

## Getting Started

### Prerequisites

Make sure the following are installed:

- Python 3.11+
- Node.js
- npm
- PostgreSQL

### 1. Clone the repository

```bash
git clone https://github.com/swastikakumari9b44/Neuroarena.git
cd Neuroarena
```

### 2. Backend setup

Create a virtual environment:

```bash
python -m venv neuroarena_env
```

Activate it:

```powershell
# Windows
.\neuroarena_env\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source neuroarena_env/bin/activate
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

### 3. Database setup

Create a PostgreSQL database named `neuroarena`.

Configure the database connection with environment variables, e.g. in a `.env` file:

```env
DATABASE_URL=postgresql://<username>:<password>@localhost:5432/neuroarena
JWT_SECRET_KEY=<your-secret-key>
```

> ⚠️ Do not commit your `.env` file or database credentials to GitHub.

### 4. Start the backend

From the project root:

```bash
uvicorn neuroarena_backend.main:app --reload
```

- API: `http://localhost:8000`
- Interactive docs (Swagger UI): `http://localhost:8000/docs`

### 5. Start the frontend

In a separate terminal:

```bash
cd neuroarena_frontend
npm install
npm run dev
```

- Dashboard: `http://localhost:3000`

Optionally, point the frontend at a non-default backend URL by setting:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

in `neuroarena_frontend/.env.local`.

---

## API Overview

### Training

```text
POST /train/start
POST /train/pause/{session_id}
POST /train/resume/{session_id}
POST /train/stop/{session_id}
GET  /train/status/{session_id}
GET  /train/history/{session_id}
GET  /train/best-model
```

### Game

```text
POST /game/start
POST /game/action
GET  /game/state/{game_id}
```

### AI

```text
POST /ai/move
```

### Authentication

```text
POST /auth/register
POST /auth/login
```

### Leaderboard

```text
GET /leaderboard/
GET /leaderboard/{username}
```

Full interactive documentation is available at `/docs` once the backend is running.

---

## How It Works

```text
User
  │
  ▼
Next.js Dashboard
  │  REST API
  ▼
FastAPI Backend
  │
  ├── Training Session
  │       │
  │       ▼
  │    PPO Agent
  │       │
  │       ▼
  │  Gymnasium Environment
  │       │
  │       ▼
  │    Game State
  │
  └── PostgreSQL
```

The frontend starts a training session through the backend. The backend manages the session and persists training data, while the frontend periodically polls for the latest metrics and renders them on the dashboard.

---

## Training Monitoring

| Metric | Description |
|---|---|
| **Reward** | Reward obtained during training episodes |
| **Loss** | Training loss reported by the training process |
| **Win Rate** | Current win-rate over recent episodes |
| **Training Speed** | Approximate episodes completed per second |
| **Checkpoints** | Progress toward the next saved checkpoint |

---

## Current Scope

NeuroArena is primarily a learning and portfolio project focused on combining:

- Reinforcement learning
- Game environments
- Backend API development
- Database integration
- Real-time training monitoring
- Modern web application development

It is not intended as a production-scale reinforcement learning platform.

---

## Roadmap

- [ ] Additional reinforcement learning algorithms
- [ ] Improved model evaluation
- [ ] More detailed training analytics
- [ ] Better experiment management
- [ ] Expanded game mechanics
- [ ] Automated model evaluation
- [ ] Production deployment
- [ ] More comprehensive testing

---

## Author

**Swastika Kumari**
GitHub: [@swastikakumari9b44](https://github.com/swastikakumari9b44)

---

## License

This project is intended for educational and portfolio purposes.

<img width="1515" height="892" alt="Screenshot 2026-09-04 201734" src="https://github.com/user-attachments/assets/083641de-fa75-4958-9609-4e109ed7002b" />


<img width="755" height="788" alt="Screenshot 2026-09-04 202014" src="https://github.com/user-attachments/assets/e95f0196-b353-426d-90f2-da15111a9df0" />


This project is intended for educational and portfolio purposes.
