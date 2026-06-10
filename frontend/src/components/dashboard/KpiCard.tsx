import type { FluentIcon } from "@fluentui/react-icons";
import { ArrowUp12Filled, ArrowDown12Filled } from "@fluentui/react-icons";
import { GlassCard } from "@/components/common/GlassCard";
import { getPalette } from "@/theme/tokens";
import { useTheme } from "@/contexts/ThemeContext";

interface KpiCardProps {
  label: string;
  value: string | number;
  delta?: string;
  trend?: "up" | "down" | "neutral";
  icon: FluentIcon;
  accent: string;
  delay?: number;
}

export function KpiCard({ label, value, delta, trend = "neutral", icon: Icon, accent, delay }: KpiCardProps) {
  const { theme } = useTheme();
  const palette = getPalette(theme);
  const trendColor =
    trend === "up" ? palette.success : trend === "down" ? palette.danger : palette.textMuted;

  return (
    <GlassCard delay={delay} interactive style={{ padding: "18px 20px", position: "relative", overflow: "hidden" }}>
      {/* accent edge */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          bottom: 0,
          width: 3,
          background: accent,
          borderRadius: "16px 0 0 16px",
        }}
      />
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <span
          style={{
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: palette.textMuted,
          }}
        >
          {label}
        </span>
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: 9,
            background: `${accent}22`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Icon style={{ color: accent, fontSize: 18 }} />
        </div>
      </div>
      <div
        style={{
          fontSize: 28,
          fontWeight: 700,
          letterSpacing: "-0.03em",
          color: palette.textPrimary,
          margin: "10px 0 4px",
        }}
      >
        {value}
      </div>
      {delta && (
        <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12, color: trendColor }}>
          {trend === "up" && <ArrowUp12Filled />}
          {trend === "down" && <ArrowDown12Filled />}
          <span style={{ fontWeight: 600 }}>{delta}</span>
        </div>
      )}
    </GlassCard>
  );
}
