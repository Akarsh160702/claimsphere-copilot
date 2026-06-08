import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useMemo } from "react";
import type { ClaimListItem } from "@/api/types";
import { palette } from "@/theme/tokens";
import { localDateKey } from "@/utils/format";
import { chartTooltipStyle } from "./chartTheme";

/** Builds a 14-day approved/escalated/rejected volume series from claims,
 *  ending on today (the viewer's local date). */
function buildSeries(claims: ClaimListItem[]) {
  const days: { key: string; label: string; Approved: number; Escalated: number; Rejected: number }[] = [];
  const today = new Date();
  for (let i = 13; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    days.push({
      key: localDateKey(d),
      label: d.toLocaleDateString("en-IN", { day: "2-digit", month: "short" }),
      Approved: 0,
      Escalated: 0,
      Rejected: 0,
    });
  }
  const index = new Map(days.map((d) => [d.key, d]));
  for (const c of claims) {
    if (!c.submitted_at) continue;
    const k = localDateKey(new Date(c.submitted_at));
    const bucket = index.get(k);
    if (!bucket) continue;
    const dec = (c.decision ?? "").toLowerCase();
    if (dec.includes("approv")) bucket.Approved++;
    else if (dec.includes("escalat")) bucket.Escalated++;
    else if (dec.includes("reject")) bucket.Rejected++;
  }
  return days;
}

export function ClaimsVolumeChart({ claims }: { claims: ClaimListItem[] }) {
  const data = useMemo(() => buildSeries(claims), [claims]);

  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
        <defs>
          {(
            [
              ["aApproved", palette.success],
              ["aEscalated", palette.warning],
              ["aRejected", palette.danger],
            ] as const
          ).map(([id, color]) => (
            <linearGradient key={id} id={id} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.35} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
        <XAxis dataKey="label" tick={{ fill: palette.textMuted, fontSize: 11 }} axisLine={false} tickLine={false} minTickGap={18} />
        <YAxis tick={{ fill: palette.textMuted, fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} width={34} />
        <Tooltip contentStyle={chartTooltipStyle} cursor={{ stroke: "rgba(255,255,255,0.15)" }} />
        <Area type="monotone" dataKey="Approved" stroke={palette.success} strokeWidth={2} fill="url(#aApproved)" />
        <Area type="monotone" dataKey="Escalated" stroke={palette.warning} strokeWidth={2} fill="url(#aEscalated)" />
        <Area type="monotone" dataKey="Rejected" stroke={palette.danger} strokeWidth={2} fill="url(#aRejected)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}
