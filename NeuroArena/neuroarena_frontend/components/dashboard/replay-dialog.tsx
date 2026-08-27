"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { Trophy, X, RotateCcw } from "lucide-react"
import { Button } from "@/components/ui/button"
import type { BestModel } from "@/lib/use-training-sim"

type ReplayDialogProps = {
  open: boolean
  onClose: () => void
  best: BestModel | null
}

const GRID = 9

// A fixed set of walls for the demo grid-world.
const WALLS = new Set([
  "2,1", "2,2", "2,3", "4,4", "4,5", "4,6", "6,2", "6,3", "1,6", "5,7", "3,7",
])

const START = { r: 0, c: 0 }
const GOAL = { r: GRID - 1, c: GRID - 1 }

// A hand-picked near-optimal path the "trained" agent follows.
const PATH: Array<{ r: number; c: number }> = [
  { r: 0, c: 0 }, { r: 1, c: 0 }, { r: 1, c: 1 }, { r: 1, c: 2 }, { r: 1, c: 3 },
  { r: 1, c: 4 }, { r: 2, c: 4 }, { r: 3, c: 4 }, { r: 3, c: 3 }, { r: 4, c: 3 },
  { r: 5, c: 3 }, { r: 5, c: 4 }, { r: 5, c: 5 }, { r: 5, c: 6 }, { r: 6, c: 6 },
  { r: 7, c: 6 }, { r: 7, c: 7 }, { r: 8, c: 7 }, { r: 8, c: 8 },
]

export function ReplayDialog({ open, onClose, best }: ReplayDialogProps) {
  const [step, setStep] = useState(0)
  const [playing, setPlaying] = useState(true)
  const timer = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (open) {
      setStep(0)
      setPlaying(true)
    }
  }, [open])

  useEffect(() => {
    if (!open || !playing) return
    timer.current = setInterval(() => {
      setStep((s) => {
        if (s >= PATH.length - 1) {
          setPlaying(false)
          return s
        }
        return s + 1
      })
    }, 240)
    return () => {
      if (timer.current) clearInterval(timer.current)
    }
  }, [open, playing])

  const visited = useMemo(() => {
    const set = new Set<string>()
    for (let i = 0; i <= step; i++) set.add(`${PATH[i].r},${PATH[i].c}`)
    return set
  }, [step])

  if (!open) return null

  const agent = PATH[step]
  const reward = best ? Math.round((best.reward * (step + 1)) / PATH.length) : 0
  const done = step >= PATH.length - 1

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label="Best model replay"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-xl border border-border bg-card p-5 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Trophy className="size-4 text-primary" aria-hidden="true" />
            <div>
              <h2 className="text-sm font-semibold text-card-foreground">Best Model Replay</h2>
              <p className="font-mono text-xs text-muted-foreground">
                {best ? `${best.version} · episode ${best.episode.toLocaleString()}` : "No model yet"}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            aria-label="Close replay"
          >
            <X className="size-4" />
          </button>
        </div>

        <div
          className="mt-4 grid gap-1 rounded-lg border border-border bg-background p-2"
          style={{ gridTemplateColumns: `repeat(${GRID}, minmax(0, 1fr))` }}
        >
          {Array.from({ length: GRID * GRID }).map((_, i) => {
            const r = Math.floor(i / GRID)
            const c = i % GRID
            const key = `${r},${c}`
            const isWall = WALLS.has(key)
            const isAgent = agent.r === r && agent.c === c
            const isGoal = GOAL.r === r && GOAL.c === c
            const isStart = START.r === r && START.c === c
            const isVisited = visited.has(key)
            return (
              <div
                key={key}
                className="aspect-square rounded-[3px] transition-colors duration-150"
                style={{
                  background: isAgent
                    ? "var(--primary)"
                    : isGoal
                      ? "color-mix(in oklab, var(--chart-4) 55%, transparent)"
                      : isWall
                        ? "var(--secondary)"
                        : isVisited
                          ? "color-mix(in oklab, var(--primary) 22%, transparent)"
                          : isStart
                            ? "color-mix(in oklab, var(--chart-2) 40%, transparent)"
                            : "var(--muted)",
                }}
              />
            )
          })}
        </div>

        <div className="mt-4 grid grid-cols-3 gap-3">
          <ReplayStat label="Step" value={`${step + 1}/${PATH.length}`} />
          <ReplayStat label="Reward" value={`${reward >= 0 ? "+" : ""}${reward}`} />
          <ReplayStat label="Status" value={done ? "Goal ✓" : "Running"} />
        </div>

        <div className="mt-4 flex gap-2">
          <Button
            variant="secondary"
            className="flex-1"
            onClick={() => {
              setStep(0)
              setPlaying(true)
            }}
          >
            <RotateCcw className="size-4" />
            Replay again
          </Button>
          <Button className="flex-1" onClick={onClose}>
            Done
          </Button>
        </div>
      </div>
    </div>
  )
}

function ReplayStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-background px-2 py-1.5 text-center">
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="font-mono text-sm font-semibold tabular-nums text-foreground">{value}</div>
    </div>
  )
}
