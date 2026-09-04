import type { LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

type StatCardProps = {
  label: string
  value: string
  sub?: string
  icon: LucideIcon
  accent?: "primary" | "chart-2" | "chart-3" | "chart-4"
  trend?: "up" | "down" | "flat"
}

const accentMap: Record<NonNullable<StatCardProps["accent"]>, string> = {
  primary: "text-primary",
  "chart-2": "text-[var(--chart-2)]",
  "chart-3": "text-[var(--chart-3)]",
  "chart-4": "text-[var(--chart-4)]",
}

export function StatCard({ label, value, sub, icon: Icon, accent = "primary", trend }: StatCardProps) {
  return (
    <div className="flex flex-col justify-between rounded-lg border border-border bg-card p-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          {label}
        </span>
        <Icon className={cn("size-4", accentMap[accent])} aria-hidden="true" />
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="font-mono text-2xl font-semibold tabular-nums text-card-foreground">
          {value}
        </span>
        {trend && (
          <span
            className={cn(
              "font-mono text-xs",
              trend === "up" && "text-primary",
              trend === "down" && "text-[var(--chart-3)]",
              trend === "flat" && "text-muted-foreground",
            )}
          >
            {trend === "up" ? "▲" : trend === "down" ? "▼" : "—"}
          </span>
        )}
      </div>
      {sub && <span className="mt-1 font-mono text-xs text-muted-foreground">{sub}</span>}
    </div>
  )
}
