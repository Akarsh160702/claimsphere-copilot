import type { ClaimListItem, DashboardMetrics } from "@/api/types";
import { localDateKey } from "./format";

type Trend = "up" | "down" | "neutral";

export interface KpiDeltas {
  totalDelta: string;
  totalTrend: Trend;
  escalatedDelta: string;
  rejectedDelta: string;
  payoutDelta: string;
  payoutTrend: Trend;
  fraudLabel: string;
  fraudTrend: Trend;
}

/**
 * Real day-over-day / week-over-week KPI deltas derived from the claim list,
 * replacing the previously hardcoded "+3 today" style strings.
 */
export function computeDeltas(
  claims: ClaimListItem[],
  metrics: DashboardMetrics,
): KpiDeltas {
  const now = new Date();
  const todayKey = localDateKey(now);
  const yest = new Date(now);
  yest.setDate(yest.getDate() - 1);
  const yestKey = localDateKey(yest);

  let todayCount = 0;
  let yesterdayCount = 0;
  let payout7 = 0;
  let payoutPrev7 = 0;

  for (const c of claims) {
    if (!c.submitted_at) continue;
    const dt = new Date(c.submitted_at);
    const key = localDateKey(dt);
    if (key === todayKey) todayCount++;
    else if (key === yestKey) yesterdayCount++;

    const ageDays = (now.getTime() - dt.getTime()) / 86_400_000;
    if (ageDays >= 0 && ageDays <= 7) payout7 += c.final_payout ?? 0;
    else if (ageDays > 7 && ageDays <= 14) payoutPrev7 += c.final_payout ?? 0;
  }

  // Total claims — today vs yesterday.
  const totalTrend: Trend =
    todayCount > yesterdayCount ? "up" : todayCount < yesterdayCount ? "down" : "neutral";
  const totalDelta = todayCount > 0 ? `+${todayCount} today` : "None today";

  // Escalated — share of book awaiting review.
  const escPct = metrics.total ? Math.round((metrics.escalated / metrics.total) * 100) : 0;
  const escalatedDelta = metrics.escalated > 0 ? `${escPct}% awaiting review` : "Queue clear";

  // Rejected — share of book.
  const rejPct = metrics.total ? Math.round((metrics.rejected / metrics.total) * 100) : 0;
  const rejectedDelta = metrics.rejected > 0 ? `${rejPct}% of claims` : "None rejected";

  // Payout — last 7 days vs prior 7 days.
  let payoutDelta = "this week";
  let payoutTrend: Trend = "neutral";
  if (payoutPrev7 > 0) {
    const pct = Math.round(((payout7 - payoutPrev7) / payoutPrev7) * 100);
    payoutDelta = `${pct >= 0 ? "+" : ""}${pct}% vs last week`;
    payoutTrend = pct >= 0 ? "up" : "down";
  } else if (payout7 > 0) {
    payoutDelta = "Up from last week";
    payoutTrend = "up";
  }

  // Fraud — portfolio risk descriptor.
  const fraudLabel =
    metrics.avgFraud < 30
      ? "Low-risk portfolio"
      : metrics.avgFraud < 60
        ? "Moderate-risk portfolio"
        : "Elevated risk";
  const fraudTrend: Trend = metrics.avgFraud < 30 ? "up" : metrics.avgFraud < 60 ? "neutral" : "down";

  return {
    totalDelta,
    totalTrend,
    escalatedDelta,
    rejectedDelta,
    payoutDelta,
    payoutTrend,
    fraudLabel,
    fraudTrend,
  };
}
