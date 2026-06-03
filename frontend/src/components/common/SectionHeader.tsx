import type { ReactNode } from "react";
import { palette } from "@/theme/tokens";

interface SectionHeaderProps {
  title: string;
  live?: boolean;
  right?: ReactNode;
}

export function SectionHeader({ title, live, right }: SectionHeaderProps) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: 14,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <h3
          style={{
            margin: 0,
            fontSize: 14,
            fontWeight: 600,
            letterSpacing: "-0.01em",
            color: palette.textPrimary,
          }}
        >
          {title}
        </h3>
        {live && (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 5,
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: palette.success,
              background: palette.successSoft,
              border: `1px solid ${palette.success}40`,
              padding: "2px 8px",
              borderRadius: 999,
            }}
          >
            <span
              className="cs-pulse-dot"
              style={{
                width: 5,
                height: 5,
                borderRadius: "50%",
                background: palette.success,
              }}
            />
            Live
          </span>
        )}
      </div>
      {right}
    </div>
  );
}
