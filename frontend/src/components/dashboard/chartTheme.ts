import type { CSSProperties } from "react";
import { getPalette, type Theme } from "@/theme/tokens";

/** Get theme-aware Recharts tooltip styling */
export const getChartTooltipStyle = (theme: Theme): CSSProperties => {
  const palette = getPalette(theme);
  return {
    background: theme === 'dark' ? "rgba(12, 20, 38, 0.95)" : "rgba(255, 255, 255, 0.98)",
    border: `1px solid ${palette.glassBorderStrong}`,
    borderRadius: 10,
    color: palette.textPrimary,
    fontSize: 12,
    boxShadow: theme === 'dark' 
      ? "0 8px 24px rgba(2,6,16,0.5)" 
      : "0 8px 24px rgba(0,0,0,0.12)",
    padding: "8px 12px",
  };
};

/** Get theme-aware tooltip label style */
export const getTooltipLabelStyle = (theme: Theme): CSSProperties => {
  const palette = getPalette(theme);
  return {
    color: palette.textPrimary,
    fontWeight: 600,
    marginBottom: "4px",
  };
};

/** Get theme-aware tooltip item style */
export const getTooltipItemStyle = (theme: Theme): CSSProperties => {
  const palette = getPalette(theme);
  return {
    color: palette.textPrimary,
  };
};
