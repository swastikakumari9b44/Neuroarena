"use client";

// Provide a local ambient declaration so TypeScript can find the api types
// when the module resolution for "@/api/game" isn't available.
declare module "@/api/game" {
  export type GameState = {
    health: number;
    gems_collected: number;
    time_left: number;
    gem_x: number;
    gem_y: number;
    enemy_x: number;
    enemy_y: number;
    player_x: number;
    player_y: number;
  };

  export function startGame(playerId: string, difficulty: string): Promise<{
    game_id: string;
    state: GameState;
  }>;

  export function sendAction(gameId: string, action: string): Promise<{
    state: GameState;
    reward: number;
    done: boolean;
  }>;
}

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { startGame, sendAction, GameState } from "@/api/game";

const WIDTH = 800;
const HEIGHT = 600;

const WALLS = [
  { x: 200, y: 100, w: 40, h: 250 },
  { x: 450, y: 200, w: 40, h: 250 },
  { x: 600, y: 50, w: 40, h: 200 },
  { x: 100, y: 420, w: 250, h: 40 },
  { x: 350, y: 500, w: 250, h: 40 },
];

// One action sent per tick while a movement key is held down.
const TICK_MS = 100;

const KEY_ACTION: Record<string, string> = {
  w: "move_up",
  a: "move_left",
  s: "move_down",
  d: "move_right",
};

export default function GamePage() {
  const [gameId, setGameId] = useState<string | null>(null);
  const [state, setState] = useState<GameState | null>(null);
  const [reward, setReward] = useState(0);
  const [done, setDone] = useState(false);
  const [status, setStatus] = useState<string>("Press Start to play");

  const pressedKeys = useRef<Set<string>>(new Set());

  async function handleStart() {
    try {
      setStatus("Starting game...");
      const res = await startGame("player1", "Medium");
      setGameId(res.game_id);
      setState(res.state);
      setReward(0);
      setDone(false);
      setStatus("Playing — use W A S D to move");
    } catch (err) {
      console.error(err);
      setStatus("Failed to start game");
    }
  }

  // Track which movement keys are currently held down.
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      const key = e.key.toLowerCase();
      if (key in KEY_ACTION) {
        pressedKeys.current.add(key);
      }
      // Space is reserved for a future action; currently a no-op.
    }

    function onKeyUp(e: KeyboardEvent) {
      const key = e.key.toLowerCase();
      pressedKeys.current.delete(key);
    }

    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);

    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("keyup", onKeyUp);
    };
  }, []);

  // Every tick, if a movement key is held, send that action to the
  // backend and render whatever state comes back. Nothing moves
  // locally -- the backend is the source of truth.
  useEffect(() => {
    if (!gameId || done) return;

    const interval = setInterval(async () => {
      const held = Array.from(pressedKeys.current);
      if (held.length === 0) return;

      // Only one direction at a time; last-pressed wins if multiple are held.
      const action = KEY_ACTION[held[held.length - 1]];

      try {
        const res = await sendAction(gameId, action);
        setState(res.state);
        setReward(res.reward);
        if (res.done) {
          setDone(true);
          setStatus(
            res.state.health <= 0 ? "Game Over" : "Time's up"
          );
        }
      } catch (err) {
        console.error(err);
      }
    }, TICK_MS);

    return () => clearInterval(interval);
  }, [gameId, done]);

  return (
    <main className="min-h-dvh bg-background">
      <div className="mx-auto max-w-4xl px-4 py-6">
        <header className="flex items-center justify-between border-b border-border pb-4">
          <div>
            <h1 className="text-lg font-semibold tracking-tight">NeuroArena</h1>
            <p className="text-xs text-muted-foreground">{status}</p>
          </div>
          <Button onClick={handleStart}>
            {gameId ? "Restart" : "Start Game"}
          </Button>
        </header>

        {state && (
          <div className="mt-4 flex gap-6 font-mono text-xs text-muted-foreground">
            <span>Health: {state.health}</span>
            <span>Gems: {state.gems_collected}/20</span>
            <span>Time: {state.time_left}s</span>
            <span>Reward: {reward.toFixed(1)}</span>
          </div>
        )}

        <div
          className="relative mt-4 overflow-hidden rounded-lg border border-border bg-black"
          style={{ width: WIDTH, height: HEIGHT, maxWidth: "100%", aspectRatio: `${WIDTH} / ${HEIGHT}` }}
        >
          {WALLS.map((w, i) => (
            <div
              key={i}
              className="absolute bg-gray-500"
              style={{ left: w.x, top: w.y, width: w.w, height: w.h }}
            />
          ))}

          {state && (
            <>
              <div
                className="absolute rounded-sm bg-yellow-400"
                style={{ left: state.gem_x, top: state.gem_y, width: 30, height: 30 }}
              />
              <div
                className="absolute rounded-sm bg-red-500"
                style={{ left: state.enemy_x, top: state.enemy_y, width: 40, height: 40 }}
              />
              <div
                className="absolute rounded-sm bg-green-500"
                style={{ left: state.player_x, top: state.player_y, width: 40, height: 40 }}
              />
            </>
          )}
        </div>
      </div>
    </main>
  );
}