/**
 * ClaimSphere design tokens.
 * The single source of truth for colors, spacing, radii and motion used by the
 * custom (non-Fluent) components. Dark-first, Microsoft-accented.
 */

export const palette = {
  // Surfaces
  bgBase: "#0A0F1E",
  bgGradientTop: "#0C1426",
  bgGradientBottom: "#070B16",
  bgElevated: "#0F1729",
  sidebar: "#080C18",

  // Glass
  glassFill: "rgba(255, 255, 255, 0.045)",
  glassFillStrong: "rgba(255, 255, 255, 0.07)",
  glassBorder: "rgba(255, 255, 255, 0.09)",
  glassBorderStrong: "rgba(255, 255, 255, 0.16)",

  // Text
  textPrimary: "#EAF0F9",
  textSecondary: "#9FB0C7",
  textMuted: "#647288",

  // Brand (Microsoft blue)
  brand: "#0078D4",
  brandHover: "#2B8CE6",
  brandSoft: "rgba(0, 120, 212, 0.14)",

  // Semantic
  success: "#00B894",
  successSoft: "rgba(0, 184, 148, 0.14)",
  warning: "#FDCB6E",
  warningSoft: "rgba(253, 203, 110, 0.16)",
  danger: "#D63031",
  dangerSoft: "rgba(214, 48, 49, 0.16)",
  info: "#5AB0FF",
  infoSoft: "rgba(90, 176, 255, 0.14)",

  // Accent ramp for charts
  chart: ["#0078D4", "#00B894", "#FDCB6E", "#D63031", "#9B6DFF", "#22D3EE"],
} as const;

/** Maps a claim decision / status to a semantic color. */
export const statusColor = (value: string): string => {
  const v = value.toLowerCase();
  if (v.includes("approv")) return palette.success;
  if (v.includes("reject")) return palette.danger;
  if (v.includes("escalat") || v.includes("review") || v.includes("pending"))
    return palette.warning;
  if (v.includes("process") || v.includes("receiv")) return palette.info;
  return palette.textMuted;
};

/** Maps a fraud score (0-100) to a semantic color. */
export const fraudColor = (score: number): string => {
  if (score < 30) return palette.success;
  if (score < 60) return palette.warning;
  return palette.danger;
};

export const radius = {
  sm: "8px",
  md: "12px",
  lg: "16px",
  xl: "20px",
  pill: "999px",
} as const;

export const space = {
  xs: "4px",
  sm: "8px",
  md: "12px",
  lg: "16px",
  xl: "24px",
  xxl: "32px",
} as const;

export const motionTokens = {
  spring: { type: "spring", stiffness: 260, damping: 26 } as const,
  ease: [0.16, 1, 0.3, 1] as [number, number, number, number],
};
