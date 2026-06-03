import { statusColor } from "@/theme/tokens";

interface StatusBadgeProps {
  value: string;
  size?: "sm" | "md";
}

/** Pill badge whose color is derived from the status/decision text. */
export function StatusBadge({ value, size = "md" }: StatusBadgeProps) {
  const color = statusColor(value);
  return (
    <span
      aria-label={`Status: ${value}`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: size === "sm" ? "2px 9px" : "4px 11px",
        borderRadius: 999,
        fontSize: size === "sm" ? 11 : 12,
        fontWeight: 600,
        letterSpacing: "0.02em",
        color,
        background: `${color}1f`,
        border: `1px solid ${color}40`,
        whiteSpace: "nowrap",
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: color,
          flexShrink: 0,
        }}
      />
      {value}
    </span>
  );
}
