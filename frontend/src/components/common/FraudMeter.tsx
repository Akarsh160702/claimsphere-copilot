import { fraudColor } from "@/theme/tokens";

interface FraudMeterProps {
  score: number;
  width?: number;
}

/** Compact horizontal fraud-score bar with semantic coloring. */
export function FraudMeter({ score, width = 90 }: FraudMeterProps) {
  const color = fraudColor(score);
  return (
    <div
      style={{ display: "flex", alignItems: "center", gap: 8, width }}
      aria-label={`Fraud score ${score} of 100`}
    >
      <div
        style={{
          flex: 1,
          height: 5,
          background: "rgba(255,255,255,0.1)",
          borderRadius: 3,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${score}%`,
            height: "100%",
            background: color,
            borderRadius: 3,
            transition: "width 0.4s ease",
          }}
        />
      </div>
      <span
        style={{
          fontSize: 12,
          fontWeight: 700,
          color,
          minWidth: 22,
          textAlign: "right",
        }}
      >
        {score}
      </span>
    </div>
  );
}
