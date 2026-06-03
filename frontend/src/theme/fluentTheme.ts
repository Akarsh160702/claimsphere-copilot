import {
  createDarkTheme,
  type BrandVariants,
  type Theme,
} from "@fluentui/react-components";
import { palette } from "./tokens";

/**
 * Brand ramp built around Microsoft blue (#0078D4 at shade 80).
 * Drives Fluent's accented components (buttons, inputs, tabs, etc.).
 */
const claimSphereBrand: BrandVariants = {
  10: "#020305",
  20: "#0B1A2C",
  30: "#0E2A49",
  40: "#103864",
  50: "#114780",
  60: "#0F579D",
  70: "#0A67BB",
  80: "#0078D4",
  90: "#2B8CE6",
  100: "#479BEB",
  110: "#63AAF0",
  120: "#80BAF5",
  130: "#9FCAF9",
  140: "#BFDBFC",
  150: "#DFEDFE",
  160: "#F2F8FF",
};

const base = createDarkTheme(claimSphereBrand);

/**
 * ClaimSphere dark theme — Fluent's generated dark theme with the neutral
 * surfaces re-pointed at our navy palette so Fluent controls sit naturally
 * on the glassmorphic background.
 */
export const claimSphereDarkTheme: Theme = {
  ...base,
  fontFamilyBase:
    "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  colorNeutralBackground1: palette.bgBase,
  colorNeutralBackground2: palette.bgElevated,
  colorNeutralBackground3: "#121C30",
  colorNeutralBackground1Hover: "#131D31",
  colorNeutralBackground1Pressed: "#0C1322",
  colorNeutralStroke1: palette.glassBorder,
  colorNeutralStroke2: palette.glassBorder,
  colorNeutralForeground1: palette.textPrimary,
  colorNeutralForeground2: palette.textSecondary,
  colorNeutralForeground3: palette.textMuted,
  colorBrandForegroundLink: palette.brand,
  colorBrandForegroundLinkHover: palette.brandHover,
};
