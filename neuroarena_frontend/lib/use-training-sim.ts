"use client"

import { useCallback, useEffect, useRef, useState } from "react"

export type Point = { episode: number; value: number }

export type BestModel = {
  version: string
  episode: number
  reward: number
  winRate: number
  savedAt: number
}

export type TrainingState = {
  episode: number
  reward: number
  winRate: number
  loss: number
  speed: number // episodes per second
  version: string
  lossHistory: Point[]
  rewardHistory: Point[]
  best: BestModel | null
}

const MAX_POINTS = 80
const TICK_MS = 220
const TOTAL_TARGET = 4000 // episode where the agent roughly converges

// Deterministic-ish noise helper
function noise(scale: number) {
  return (Math.random() - 0.5) * 2 * scale
}

// Logistic-style learning progress in [0, 1]
function progress(episode: number) {
  const k = 4.5
  const x = episode / TOTAL_TARGET
  return 1 / (1 + Math.exp(-k * (x - 0.45)))
}

function versionFor(episode: number) {
  const major = 1
  const minor = Math.floor(episode / 500)
  const patch = Math.floor((episode % 500) / 50)
  return `v${major}.${minor}.${patch}`
}

function initialState(): TrainingState {
  return {
    episode: 0,
    reward: -100,
    winRate: 0,
    loss: 2.4,
    speed: 0,
    version: "v1.0.0",
    lossHistory: [],
    rewardHistory: [],
    best: null,
  }
}

export function useTrainingSim() {
  const [state, setState] = useState<TrainingState>(initialState)
  const [running, setRunning] = useState(true)
  const [speedMultiplier, setSpeedMultiplier] = useState(1)
  const lastTick = useRef<number>(Date.now())

  const tick = useCallback(() => {
    setState((prev) => {
      const now = Date.now()
      const dt = (now - lastTick.current) / 1000
      lastTick.current = now

      const step = Math.max(1, Math.round(4 * speedMultiplier))
      const episode = prev.episode + step
      const p = progress(episode)

      // Reward climbs from -100 to ~ +200 with decreasing volatility
      const rewardTarget = -100 + p * 300
      const reward = rewardTarget + noise(40 * (1 - p * 0.7))

      // Win rate climbs to ~92%
      const winTarget = p * 92
      const winRate = Math.max(0, Math.min(99, winTarget + noise(6 * (1 - p * 0.6))))

      // Loss decays from ~2.4 toward ~0.05
      const lossTarget = 0.05 + (1 - p) * 2.35
      const loss = Math.max(0.02, lossTarget + noise(0.18 * (1 - p * 0.5)))

      const speed = dt > 0 ? step / dt : prev.speed

      const rewardHistory = [...prev.rewardHistory, { episode, value: reward }].slice(-MAX_POINTS)
      const lossHistory = [...prev.lossHistory, { episode, value: loss }].slice(-MAX_POINTS)

      // Track best model by smoothed reward
      let best = prev.best
      const smoothedReward = rewardTarget
      if (!best || smoothedReward > best.reward) {
        best = {
          version: versionFor(episode),
          episode,
          reward: Math.round(smoothedReward),
          winRate: Math.round(winTarget),
          savedAt: now,
        }
      }

      return {
        episode,
        reward,
        winRate,
        loss,
        speed,
        version: versionFor(episode),
        rewardHistory,
        lossHistory,
        best,
      }
    })
  }, [speedMultiplier])

  useEffect(() => {
    if (!running) return
    lastTick.current = Date.now()
    const id = setInterval(tick, TICK_MS)
    return () => clearInterval(id)
  }, [running, tick])

  const reset = useCallback(() => {
    lastTick.current = Date.now()
    setState(initialState())
  }, [])

  return {
    state,
    running,
    setRunning,
    speedMultiplier,
    setSpeedMultiplier,
    reset,
  }
}
