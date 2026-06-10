import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getPalette, typeColor } from "@/theme/tokens";
import { useTheme } from "@/contexts/ThemeContext";
import { getChartTooltipStyle, getTooltipLabelStyle, getTooltipItemStyle } from "./chartTheme";
import type { DashboardMetrics } from "@/api/types";

export function TypeBar({ metrics }: { metrics: DashboardMetrics }) {
  const { theme } = useTheme();
  const palette = getPalette(theme);
  const data = Object.entries(metrics.byType).map(([name, value]) => ({ name, value }));

  return (
    <ResponsiveContainer width="100%" height={210}>
      <BarChart data={data} margin={{ top: 12, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid 
          strokeDasharray="3 3" 
          stroke={theme === 'dark' ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)"} 
          vertical={false} 
        />
        <XAxis dataKey="name" tick={{ fill: palette.textMuted, fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: palette.textMuted, fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} width={32} />
        <Tooltip 
          contentStyle={getChartTooltipStyle(theme)} 
          labelStyle={getTooltipLabelStyle(theme)}
          itemStyle={getTooltipItemStyle(theme)}
          cursor={{ fill: theme === 'dark' ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.04)" }} 
        />
        <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={48}>
          {data.map((d) => (
            <Cell key={d.name} fill={typeColor(d.name)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
