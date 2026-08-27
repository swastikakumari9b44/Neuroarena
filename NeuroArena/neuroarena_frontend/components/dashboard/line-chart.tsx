"use client"

import { useId } from "react"
import type { Point } from "@/lib/use-training-sim"

type LineChartProps = {
  data: Point[]
  color: string
  /** invert so lower values sit higher (useful for loss) */
  fixedMin?: number
  fixedMax?: number
  height?: number
  valueFormat?: (v: number) => string
}

const W = 600
const PAD = 8

export function LineChart({
  data,
  color,
  fixedMin,
  fixedMax,
  height = 200,
  valueFormat = (v) => v.toFixed(2),
}: LineChartProps) {
  const gradId = useId()
  const H = height

  if (data.length < 2) {
    return (
      <div
        className="flex items-center justify-center text-xs text-muted-foreground"
        style={{ height: H }}
      >
        Waiting for data…
      </div>
    )
  }

  const values = data.map((d) => d.value)
  const min = fixedMin ?? Math.min(...values)
  const max = fixedMax ?? Math.max(...values)
  const range = max - min || 1

  const x = (i: number) => PAD + (i / (data.length - 1)) * (W - PAD * 2)
  const y = (v: number) => PAD + (1 - (v - min) / range) * (H - PAD * 2)

  const linePath = data
    .map((d, i) => `${i === 0 ? "M" : "L"} ${x(i).toFixed(2)} ${y(d.value).toFixed(2)}`)
    .join(" ")

  const areaPath = `${linePath} L ${x(data.length - 1).toFixed(2)} ${H - PAD} L ${PAD} ${H - PAD} Z`

  const last = data[data.length - 1]
  const lastX = x(data.length - 1)
  const lastY = y(last.value)

  return (
    <div className="relative w-full" style={{ height: H }}>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio="none"
        className="h-full w-full"
        role="img"
        aria-label="Training metric over time"
      >
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.28" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* gridlines */}
        {[0.25, 0.5, 0.75].map((t) => (
          <line
            key={t}
            x1={PAD}
            x2={W - PAD}
            y1={PAD + t * (H - PAD * 2)}
            y2={PAD + t * (H - PAD * 2)}
            stroke="currentColor"
            className="text-border"
            strokeWidth={1}
            strokeDasharray="2 4"
          />
        ))}

        <path d={areaPath} fill={`url(#${gradId})`} />
        <path
          d={linePath}
          fill="none"
          stroke={color}
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
        />
        <circle cx={lastX} cy={lastY} r={3.5} fill={color} vectorEffect="non-scaling-stroke" />
      </svg>

      <div
        className="pointer-events-none absolute rounded-md border border-border bg-popover px-1.5 py-0.5 font-mono text-[10px] tabular-nums text-popover-foreground"
        style={{
          left: `${(lastX / W) * 100}%`,
          top: `${(lastY / H) * 100}%`,
          transform: "translate(-110%, -140%)",
        }}
      >
        {valueFormat(last.value)}
      </div>
    </div>
  )
}
