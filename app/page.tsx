"use client"

import { useState } from "react"
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
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { useTrainingSim } from "@/lib/use-training-sim"
import { StatCard } from "@/components/dashboard/stat-card"
import { LineChart } from "@/components/dashboard/line-chart"
import { ReplayDialog } from "@/components/dashboard/replay-dialog"

const SPEEDS = [1, 2, 4]

export default function Page() {
  const { state, running, setRunning, speedMultiplier, setSpeedMultiplier, reset } = useTrainingSim()
  const [replayOpen, setReplayOpen] = useState(false)

  const rewardTrend = state.rewardHistory.length > 4
    ? state.reward >= state.rewardHistory[state.rewardHistory.length - 5].value
      ? "up"
      : "down"
    : "flat"

  const lossTrend = state.lossHistory.length > 4
    ? state.loss <= state.lossHistory[state.lossHistory.length - 5].value
      ? "down"
      : "up"
    : "flat"

  return (
    <main className="min-h-dvh bg-background">
      <div className="mx-auto max-w-6xl px-4 py-6 md:px-6 md:py-8">
        {/* Header */}
        <header className="flex flex-col gap-4 border-b border-border pb-5 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-lg bg-primary/10">
              <Cpu className="size-5 text-primary" aria-hidden="true" />
            </div>
            <div>
              <h1 className="text-lg font-semibold tracking-tight text-foreground">RL Training Monitor</h1>
              <div className="flex items-center gap-2 font-mono text-xs text-muted-foreground">
                <span
                  className={`inline-block size-2 rounded-full ${
                    running ? "animate-pulse bg-primary" : "bg-muted-foreground"
                  }`}
                  aria-hidden="true"
                />
                {running ? "Training in progress" : "Paused"} · agent-ppo-cartpole
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1 rounded-lg border border-border bg-card p-1">
              {SPEEDS.map((s) => (
                <button
                  key={s}
                  onClick={() => setSpeedMultiplier(s)}
                  className={`rounded-md px-2 py-1 font-mono text-xs transition-colors ${
                    speedMultiplier === s
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                  aria-pressed={speedMultiplier === s}
                >
                  {s}x
                </button>
              ))}
            </div>
            <Button variant="outline" size="lg" onClick={() => setRunning(!running)}>
              {running ? <Pause /> : <Play />}
              {running ? "Pause" : "Resume"}
            </Button>
            <Button variant="outline" size="lg" onClick={reset}>
              <RotateCcw />
              Reset
            </Button>
            <Button size="lg" onClick={() => setReplayOpen(true)}>
              <PlayCircle />
              Replay Best
            </Button>
          </div>
        </header>

        {/* Metric cards */}
        <section
          className="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4"
          aria-label="Live training metrics"
        >
          <StatCard
            label="Current Episode"
            value={state.episode.toLocaleString()}
            sub="episodes elapsed"
            icon={Activity}
            accent="chart-2"
          />
          <StatCard
            label="Current Reward"
            value={state.reward.toFixed(1)}
            sub="per-episode return"
            icon={Target}
            accent="primary"
            trend={rewardTrend}
          />
          <StatCard
            label="Win Rate"
            value={`${state.winRate.toFixed(1)}%`}
            sub="rolling 100-ep avg"
            icon={Percent}
            accent="chart-4"
            trend="up"
          />
          <StatCard
            label="Training Speed"
            value={state.speed.toFixed(1)}
            sub="episodes / sec"
            icon={Zap}
            accent="chart-2"
          />
        </section>

        {/* Charts */}
        <section className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2" aria-label="Training curves">
          <ChartCard
            title="Learning Curve"
            subtitle="Reward trajectory"
            icon={Gauge}
            value={state.reward.toFixed(1)}
            valueClass="text-primary"
          >
            <LineChart
              data={state.rewardHistory}
              color="var(--chart-1)"
              valueFormat={(v) => v.toFixed(0)}
            />
          </ChartCard>

          <ChartCard
            title="Loss Curve"
            subtitle="Policy loss (lower is better)"
            icon={Activity}
            value={state.loss.toFixed(3)}
            valueClass="text-[var(--chart-3)]"
          >
            <LineChart
              data={state.lossHistory}
              color="var(--chart-3)"
              fixedMin={0}
              valueFormat={(v) => v.toFixed(2)}
            />
          </ChartCard>
        </section>

        {/* AI version + best model */}
        <section className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2" aria-label="Model status">
          <div className="rounded-lg border border-border bg-card p-5">
            <div className="flex items-center gap-2">
              <Cpu className="size-4 text-[var(--chart-2)]" aria-hidden="true" />
              <h2 className="text-sm font-semibold text-card-foreground">AI Version</h2>
            </div>
            <div className="mt-4 flex items-baseline gap-3">
              <span className="font-mono text-3xl font-semibold tabular-nums text-foreground">
                {state.version}
              </span>
              <span className="rounded-full bg-primary/10 px-2 py-0.5 font-mono text-xs text-primary">
                live
              </span>
            </div>
            <dl className="mt-4 grid grid-cols-2 gap-3 font-mono text-xs">
              <Meta label="Algorithm" value="PPO" />
              <Meta label="Framework" value="PyTorch" />
              <Meta label="Loss fn" value={state.loss.toFixed(3)} />
              <Meta label="Checkpoints" value={Math.floor(state.episode / 50).toString()} />
            </dl>
          </div>

          <div className="rounded-lg border border-border bg-card p-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Trophy className="size-4 text-[var(--chart-4)]" aria-hidden="true" />
                <h2 className="text-sm font-semibold text-card-foreground">Best Model</h2>
              </div>
              <Button size="sm" variant="secondary" onClick={() => setReplayOpen(true)}>
                <PlayCircle />
                Replay
              </Button>
            </div>
            {state.best ? (
              <>
                <div className="mt-4 flex items-baseline gap-3">
                  <span className="font-mono text-3xl font-semibold tabular-nums text-foreground">
                    {state.best.version}
                  </span>
                  <span className="font-mono text-xs text-muted-foreground">
                    @ ep {state.best.episode.toLocaleString()}
                  </span>
                </div>
                <dl className="mt-4 grid grid-cols-2 gap-3 font-mono text-xs">
                  <Meta
                    label="Best reward"
                    value={`${state.best.reward >= 0 ? "+" : ""}${state.best.reward}`}
                    accent
                  />
                  <Meta label="Win rate" value={`${state.best.winRate}%`} accent />
                  <Meta label="Saved" value="auto-checkpoint" />
                  <Meta label="Status" value="deployed" />
                </dl>
              </>
            ) : (
              <p className="mt-6 flex items-center gap-2 font-mono text-xs text-muted-foreground">
                <Award className="size-4" /> Training to first checkpoint…
              </p>
            )}
          </div>
        </section>
      </div>

      <ReplayDialog open={replayOpen} onClose={() => setReplayOpen(false)} best={state.best} />
    </main>
  )
}

function ChartCard({
  title,
  subtitle,
  icon: Icon,
  value,
  valueClass,
  children,
}: {
  title: string
  subtitle: string
  icon: typeof Activity
  value: string
  valueClass: string
  children: React.ReactNode
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <Icon className="size-4 text-muted-foreground" aria-hidden="true" />
          <div>
            <h2 className="text-sm font-semibold text-card-foreground">{title}</h2>
            <p className="text-xs text-muted-foreground">{subtitle}</p>
          </div>
        </div>
        <span className={`font-mono text-lg font-semibold tabular-nums ${valueClass}`}>{value}</span>
      </div>
      <div className="mt-3">{children}</div>
    </div>
  )
}

function Meta({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div>
      <dt className="text-muted-foreground">{label}</dt>
      <dd className={accent ? "text-primary" : "text-foreground"}>{value}</dd>
    </div>
  )
}
