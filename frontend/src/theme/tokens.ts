/**
 * ClaimSphere design tokens.
 * The single source of truth for colors, spacing, radii and motion used by the
 * custom (non-Fluent) components.
 *
 * Design language: premium dark, Azure-accented, Linear/Vercel-grade restraint.
 * Discipline rule — ONE brand accent (Azure blue). The semantic colors
 * (success / warning / danger) are reserved strictly for status meaning, never
 * for decoration. Claim-type hues live in a single controlled categorical set.
 */

export type Theme = 'dark' | 'light';

// Dark theme palette (original)
const darkPalette = {
  // Surfaces — deep, near-neutral navy with just enough blue to feel "Azure"
  bgBase: "#090D17",
  bgGradientTop: "#0B111F",
  bgGradientBottom: "#070A12",
  bgElevated: "#0E1422",
  sidebar: "#070A12",

  // Glass
  glassFill: "rgba(255, 255, 255, 0.040)",
  glassFillStrong: "rgba(255, 255, 255, 0.065)",
  glassBorder: "rgba(255, 255, 255, 0.075)",
  glassBorderStrong: "rgba(255, 255, 255, 0.15)",
  glassHighlight: "rgba(255, 255, 255, 0.10)",

  // Text
  textPrimary: "#ECF1FA",
  textSecondary: "#97A6BE",
  textMuted: "#5C6A82",

  // Brand — the single accent (Microsoft / Azure blue)
  brand: "#2E90FA",
  brandStrong: "#0078D4",
  brandHover: "#5AABFF",
  brandSoft: "rgba(46, 144, 250, 0.13)",

  // Semantic — status only
  success: "#34D399",
  successSoft: "rgba(52, 211, 153, 0.13)",
  warning: "#FBBF55",
  warningSoft: "rgba(251, 191, 85, 0.14)",
  danger: "#F4625A",
  dangerSoft: "rgba(244, 98, 90, 0.14)",
  info: "#5AABFF",
  infoSoft: "rgba(90, 171, 255, 0.13)",

  // Harmonious categorical ramp for charts (blue-led, lightly desaturated)
  chart: ["#2E90FA", "#34D399", "#FBBF55", "#F4625A", "#8B86F5", "#2DD4BF"],
} as const;

// Light theme palette (premium, clean, professional)
const lightPalette = {
  // Surfaces — pure white with subtle warm undertones
  bgBase: "#FFFFFF",
  bgGradientTop: "#FAFBFC",
  bgGradientBottom: "#F5F7FA",
  bgElevated: "#FFFFFF",
  sidebar: "#FAFBFC",

  // Glass (for light theme - subtle shadows)
  glassFill: "rgba(0, 0, 0, 0.02)",
  glassFillStrong: "rgba(0, 0, 0, 0.04)",
  glassBorder: "rgba(0, 0, 0, 0.08)",
  glassBorderStrong: "rgba(0, 0, 0, 0.12)",
  glassHighlight: "rgba(255, 255, 255, 0.95)",

  // Text
  textPrimary: "#1A2332",
  textSecondary: "#4A5568",
  textMuted: "#718096",

  // Brand — Microsoft / Azure blue (adjusted for light theme)
  brand: "#0078D4",
  brandStrong: "#005A9E",
  brandHover: "#106EBE",
  brandSoft: "rgba(0, 120, 212, 0.08)",

  // Semantic — status (adjusted for light theme readability)
  success: "#10B981",
  successSoft: "rgba(16, 185, 129, 0.10)",
  warning: "#F59E0B",
  warningSoft: "rgba(245, 158, 11, 0.10)",
  danger: "#EF4444",
  dangerSoft: "rgba(239, 68, 68, 0.10)",
  info: "#0EA5E9",
  infoSoft: "rgba(14, 165, 233, 0.10)",

  // Charts (vibrant but professional for light backgrounds)
  chart: ["#0078D4", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#06B6D4"],
} as const;

export const palette = darkPalette; // Default export for backwards compatibility

export const getPalette = (theme: Theme) => theme === 'light' ? lightPalette : darkPalette;

/**
 * Controlled categorical colors for claim types. Centralized so every page
 * (table, charts, intake, search) renders the same hue for the same type.
 * Non-semantic hues, kept distinct from status colors to avoid confusion.
 */
export const typeColors: Record<string, string> = {
  Health: "#5AABFF", // azure
  Motor: "#8B86F5", // soft indigo
  Property: "#2DD4BF", // teal
  Travel: "#E5B567", // muted gold
};

export const typeColor = (type?: string | null): string =>
  (type && typeColors[type]) || palette.textMuted;

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

/** Layered shadow tokens — used for the "expensive" glass depth. */
export const shadow = {
  card: "0 1px 0 0 rgba(255,255,255,0.05) inset, 0 12px 32px -14px rgba(0,0,0,0.65), 0 2px 8px -3px rgba(0,0,0,0.45)",
  cardHover:
    "0 1px 0 0 rgba(255,255,255,0.08) inset, 0 22px 48px -16px rgba(0,0,0,0.7), 0 4px 12px -4px rgba(0,0,0,0.5)",
  brandGlow: "0 8px 24px -6px rgba(46,144,250,0.45)",
} as const;

export const motionTokens = {
  spring: { type: "spring", stiffness: 260, damping: 26 } as const,
  ease: [0.16, 1, 0.3, 1] as [number, number, number, number],
};
