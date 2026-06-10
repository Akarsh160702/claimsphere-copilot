import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { getPalette } from "@/theme/tokens";
import { useTheme } from "@/contexts/ThemeContext";
import { getChartTooltipStyle, getTooltipLabelStyle, getTooltipItemStyle } from "./chartTheme";
import type { DashboardMetrics } from "@/api/types";

export function DecisionDonut({ metrics }: { metrics: DashboardMetrics }) {
  const { theme } = useTheme();
  const palette = getPalette(theme);
  
  const data = [
    { name: "Approved", value: metrics.approved, color: palette.success },
    { name: "Rejected", value: metrics.rejected, color: palette.danger },
    { name: "Escalated", value: metrics.escalated, color: palette.warning },
  ].filter((d) => d.value > 0);

  return (
    <div style={{ position: "relative" }}>
      <ResponsiveContainer width="100%" height={210}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius={62}
            outerRadius={92}
            paddingAngle={2}
            stroke="none"
          >
            {data.map((d) => (
              <Cell key={d.name} fill={d.color} />
            ))}
          </Pie>
          <Tooltip 
            contentStyle={getChartTooltipStyle(theme)} 
            labelStyle={getTooltipLabelStyle(theme)}
            itemStyle={getTooltipItemStyle(theme)}
          />
        </PieChart>
      </ResponsiveContainer>
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          pointerEvents: "none",
        }}
      >
        <div style={{ fontSize: 26, fontWeight: 700, color: palette.textPrimary, letterSpacing: "-0.03em" }}>
          {metrics.stpRate}%
        </div>
        <div style={{ fontSize: 11, color: palette.textMuted, letterSpacing: "0.06em", textTransform: "uppercase" }}>
          STP Rate
        </div>
      </div>
      <div style={{ display: "flex", justifyContent: "center", gap: 16, marginTop: 8, flexWrap: "wrap" }}>
        {data.map((d) => (
          <div key={d.name} style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ width: 9, height: 9, borderRadius: 3, background: d.color }} />
            <span style={{ fontSize: 12, color: palette.textSecondary }}>
              {d.name} <strong style={{ color: palette.textPrimary }}>{d.value}</strong>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
