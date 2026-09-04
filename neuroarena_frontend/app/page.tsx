"use client";

import { useEffect, useRef, useState } from "react";
import {
  Activity,
  Award,
  Cpu,
  Gauge,
  Pause,
  Play,
  Percent,
  PlayCircle,
  RotateCcw,
  Target,
  Trophy,
  Zap,
} from "lucide-react";

import {
  pauseTraining,
  resumeTraining,
  stopTraining,
} from "@/lib/api";

import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/dashboard/stat-card";
import { LineChart } from "@/components/dashboard/line-chart";
import { ReplayDialog } from "@/components/dashboard/replay-dialog";
import { useTrainingSim } from "@/lib/use-training-sim";

// Minimal client-side API helpers
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function startTraining(modelName: string) {
  const res = await fetch(`${API_BASE}/train/start`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model_name: modelName,
    }),
  });

  if (!res.ok) {
    const errorText = await res.text();
    console.error("Training API error:", errorText);
    throw new Error("Failed to start training");
  }

  return res.json();
}

  

async function getTrainingStatus(sessionId: string) {
  const res = await fetch(`${API_BASE}/train/status/${sessionId}`);

  if (!res.ok) {
    throw new Error("Failed to fetch status");
  }

  return res.json();
}

async function getTrainingHistory(sessionId: string) {
  const res = await fetch(`${API_BASE}/train/history/${sessionId}`);

  if (!res.ok) {
    throw new Error("Failed to fetch history");
  }

  return res.json();
}

async function getBestModel(algorithm: string) {
  const res = await fetch(
    `${API_BASE}/train/best-model?model_name=${encodeURIComponent(algorithm)}`
  );

  if (!res.ok) {
    throw new Error("Failed to fetch best model");
  }

  return res.json();
}

const SPEEDS = [1, 2, 4];

type MetricPoint = {
  episode: number;
  reward: number;
  loss: number;
  win_rate: number;
};

type BestModel = {
  version: string;
  accuracy: number;
};

export default function Page() {
  const {
    state,
    running,
    setRunning,
    speedMultiplier,
    setSpeedMultiplier,
    reset,
  } = useTrainingSim();

  const [sessionId, setSessionId] = useState<string | null>(null);

  const [backendData, setBackendData] = useState({
    episode: 0,
    reward: 0,
    win_rate: 0,
    loss: 0,
    steps_done: 0,
  });

  const [history, setHistory] = useState<MetricPoint[]>([]);
  const [bestModel, setBestModel] = useState<BestModel | null>(null);

  const [replayOpen, setReplayOpen] = useState(false);

  const lastTickRef = useRef<{
    time: number;
    episode: number;
  } | null>(null);

  const [trainingSpeed, setTrainingSpeed] = useState(0);

  useEffect(() => {
    if (!sessionId) return;

    const timer = setInterval(async () => {
      try {
        const [status, hist, best] = await Promise.all([
          getTrainingStatus(sessionId),
          getTrainingHistory(sessionId),
          getBestModel("PPO"),
        ]);

        setBackendData(status);

        const now = Date.now();

        if (lastTickRef.current) {
          const dtSeconds =
            (now - lastTickRef.current.time) / 1000;

          const episodeDelta =
            status.episode - lastTickRef.current.episode;

          if (dtSeconds > 0) {
            setTrainingSpeed(
              Math.max(0, episodeDelta / dtSeconds)
            );
          }
        }

        lastTickRef.current = {
          time: now,
          episode: status.episode,
        };

        setHistory(hist);
        setBestModel(best);
      } catch (err) {
        console.error(err);
      }
    }, 1000);

    return () => clearInterval(timer);
  }, [sessionId]);

  async function handleStartTraining() {
  try {
    const session = await startTraining("PPO");

    setSessionId(session.session_id);
    setRunning(true);

    alert(
      "Training Started\n\nSession ID:\n" +
        session.session_id
    );
  } catch (err) {
    console.error(err);
    alert("Could not start training.");
  }
}

  const rewardChartData = history.map((h) => ({
    value: h.reward,
  }));

  const lossChartData = history.map((h) => ({
    value: h.loss,
  }));

  const rewardTrend =
    history.length > 4
      ? backendData.reward >=
        history[history.length - 5].reward
        ? "up"
        : "down"
      : "flat";

  const lossTrend =
    history.length > 4
      ? backendData.loss <=
        history[history.length - 5].loss
        ? "down"
        : "up"
      : "flat";

  return (
    <main className="min-h-dvh bg-background">
      <div className="mx-auto max-w-6xl px-4 py-6 md:px-6 md:py-8">

        {/* Header */}
        <header className="flex flex-col gap-4 border-b border-border pb-5 md:flex-row md:items-center md:justify-between">

          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-lg bg-primary/10">
              <Cpu className="size-5 text-primary" />
            </div>

            <div>
              <h1 className="text-lg font-semibold tracking-tight">
                RL Training Monitor
              </h1>

              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span
                  className={`inline-block size-2 rounded-full ${
                    running
                      ? "animate-pulse bg-primary"
                      : "bg-muted-foreground"
                  }`}
                />

                {running
                  ? "Training in Progress"
                  : "Paused"}
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">

            {/* Speed Controls */}
            <div className="flex items-center gap-1 rounded-lg border border-border bg-card p-1">
              {SPEEDS.map((s) => (
                <button
                  key={s}
                  onClick={() => setSpeedMultiplier(s)}
                  className={`rounded-md px-2 py-1 text-xs ${
                    speedMultiplier === s
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-muted"
                  }`}
                >
                  {s}x
                </button>
              ))}
            </div>

            {/* Pause / Resume */}
            <Button
              variant="outline"
              onClick={async () => {
                try {
                  if (!sessionId) return;
                  if (running) {
                    await pauseTraining(sessionId);
                    setRunning(false);
                  } else {
                    await resumeTraining(sessionId);
                    setRunning(true);
                  }
                } catch (err) {
                  console.error(err);
                }
              }}
            >
              {running ? <Pause /> : <Play />}
              {running ? "Pause" : "Resume"}
            </Button>

            {/* Stop */}
            <Button
              variant="destructive"
              onClick={async () => {
                try {
                  if (!sessionId) return;
                  await stopTraining(sessionId);
                  setRunning(false);
                } catch (err) {
                  console.error(err);
                }
              }}
            >
              Stop
            </Button>

            {/* Reset */}
            <Button
              variant="outline"
              onClick={reset}
            >
              <RotateCcw />
              Reset
            </Button>

            {/* Start Training */}
            <Button onClick={handleStartTraining}>
              <PlayCircle />
              Start Training
            </Button>

            {/* Replay */}
            <Button
              onClick={() => setReplayOpen(true)}
            >
              Replay Best
            </Button>
          </div>
        </header>

        {/* Metric Cards */}
        <section className="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4">

          <StatCard
            label="Current Episode"
            value={backendData.episode.toLocaleString()}
            sub="episodes elapsed"
            icon={Activity}
            accent="chart-2"
          />

          <StatCard
            label="Current Reward"
            value={backendData.reward.toFixed(1)}
            sub="per-episode reward"
            icon={Target}
            accent="primary"
            trend={rewardTrend}
          />

          <StatCard
            label="Win Rate"
            value={`${backendData.win_rate.toFixed(1)}%`}
            sub="training win rate"
            icon={Percent}
            accent="chart-4"
            trend="up"
          />

          <StatCard
            label="Training Speed"
            value={trainingSpeed.toFixed(1)}
            sub="episodes/sec"
            icon={Zap}
            accent="chart-2"
          />

        </section>

        {/* Charts */}
        <section
          className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2"
          aria-label="Training curves"
        >

          <ChartCard
            title="Learning Curve"
            subtitle="Reward trajectory"
            icon={Gauge}
            value={backendData.reward.toFixed(1)}
            valueClass="text-primary"
          >
            <LineChart
              data={rewardChartData}
              color="var(--chart-1)"
              valueFormat={(v) => v.toFixed(0)}
            />
          </ChartCard>

          <ChartCard
            title="Loss Curve"
            subtitle="Policy loss (lower is better)"
            icon={Activity}
            value={backendData.loss.toFixed(3)}
            valueClass="text-[var(--chart-3)]"
          >
            <LineChart
              data={lossChartData}
              color="var(--chart-3)"
              fixedMin={0}
              valueFormat={(v) => v.toFixed(2)}
            />
          </ChartCard>

        </section>

        {/* AI Version + Best Model */}
        <section
          className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2"
          aria-label="Model status"
        >

          {/* AI Version */}
          <div className="rounded-lg border border-border bg-card p-5">

            <div className="flex items-center gap-2">
              <Cpu
                className="size-4 text-[var(--chart-2)]"
                aria-hidden="true"
              />

              <h2 className="text-sm font-semibold">
                AI Version
              </h2>
            </div>

            <div className="mt-4 flex items-baseline gap-3">

              <span className="font-mono text-3xl font-semibold">
                {bestModel?.version ?? "v0"}
              </span>

              <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">
                live
              </span>

            </div>

            <dl className="mt-4 grid grid-cols-2 gap-3 text-xs font-mono">

              <Meta
                label="Algorithm"
                value="PPO"
              />

              <Meta
                label="Framework"
                value="PyTorch"
              />

              <Meta
                label="Loss"
                value={backendData.loss.toFixed(3)}
              />

              <Meta
                label="Checkpoints"
                value={Math.floor(
                  backendData.episode / 50
                ).toString()}
              />

            </dl>
          </div>

          {/* Best Model */}
          <div className="rounded-lg border border-border bg-card p-5">

            <div className="flex items-center justify-between">

              <div className="flex items-center gap-2">
                <Trophy
                  className="size-4 text-[var(--chart-4)]"
                />

                <h2 className="text-sm font-semibold">
                  Best Model
                </h2>
              </div>

              <Button
                size="sm"
                variant="secondary"
                onClick={() => setReplayOpen(true)}
              >
                <PlayCircle />
                Replay
              </Button>

            </div>

            {bestModel && bestModel.accuracy > 0 ? (
              <>
                <div className="mt-4 flex items-baseline gap-3">

                  <span className="font-mono text-3xl font-semibold">
                    {bestModel.version}
                  </span>

                </div>

                <dl className="mt-4 grid grid-cols-2 gap-3 text-xs font-mono">

                  <Meta
                    label="Win Rate"
                    value={`${bestModel.accuracy.toFixed(1)}%`}
                    accent
                  />

                  <Meta
                    label="Saved"
                    value="auto-checkpoint"
                  />

                  <Meta
                    label="Status"
                    value="deployed"
                  />

                </dl>
              </>
            ) : (
              <p className="mt-6 flex items-center gap-2 text-xs text-muted-foreground">
                <Award className="size-4" />
                Training to first checkpoint...
              </p>
            )}

          </div>

        </section>
      </div>

      {/* Replay Dialog */}
      <ReplayDialog
        open={replayOpen}
        onClose={() => setReplayOpen(false)}
        best={state.best}
      />

    </main>
  );
}

function ChartCard({
  title,
  subtitle,
  icon: Icon,
  value,
  valueClass,
  children,
}: {
  title: string;
  subtitle: string;
  icon: typeof Activity;
  value: string;
  valueClass: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">

      <div className="flex items-start justify-between">

        <div className="flex items-center gap-2">

          <Icon
            className="size-4 text-muted-foreground"
            aria-hidden="true"
          />

          <div>
            <h2 className="text-sm font-semibold text-card-foreground">
              {title}
            </h2>

            <p className="text-xs text-muted-foreground">
              {subtitle}
            </p>
          </div>

        </div>

        <span
          className={`font-mono text-lg font-semibold tabular-nums ${valueClass}`}
        >
          {value}
        </span>

      </div>

      <div className="mt-3">
        {children}
      </div>

    </div>
  );
}

function Meta({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div>
      <dt className="text-muted-foreground">
        {label}
      </dt>

      <dd
        className={
          accent
            ? "text-primary"
            : "text-foreground"
        }
      >
        {value}
      </dd>
    </div>
  );
}