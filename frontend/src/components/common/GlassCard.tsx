import { motion } from "framer-motion";
import type { CSSProperties, ReactNode } from "react";
import { motionTokens, shadow } from "@/theme/tokens";

interface GlassCardProps {
  children: ReactNode;
  style?: CSSProperties;
  /** Lift slightly on hover. */
  interactive?: boolean;
  /** Stagger index for entrance animation. */
  delay?: number;
  className?: string;
  onClick?: () => void;
}

/** Glassmorphic surface with a subtle entrance animation. */
export function GlassCard({
  children,
  style,
  interactive = false,
  delay = 0,
  className,
  onClick,
}: GlassCardProps) {
  return (
    <motion.div
      className={`cs-glass ${className ?? ""}`}
      onClick={onClick}
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ ...motionTokens.spring, delay }}
      whileHover={
        interactive
          ? { y: -3, boxShadow: shadow.cardHover, borderColor: "rgba(255,255,255,0.14)" }
          : undefined
      }
      style={{
        padding: "20px 22px",
        cursor: interactive ? "pointer" : "default",
        ...style,
      }}
    >
      {children}
    </motion.div>
  );
}
