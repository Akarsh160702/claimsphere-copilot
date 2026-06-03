import type { CSSProperties } from "react";
import { palette } from "@/theme/tokens";

/** Shared Recharts tooltip styling for the dark glass theme. */
export const chartTooltipStyle: CSSProperties = {
  background: "rgba(12, 20, 38, 0.95)",
  border: `1px solid ${palette.glassBorderStrong}`,
  borderRadius: 10,
  color: palette.textPrimary,
  fontSize: 12,
  boxShadow: "0 8px 24px rgba(2,6,16,0.5)",
};
