import { motion } from "framer-motion";
import { Wrench24Regular } from "@fluentui/react-icons";
import { AppLayout } from "@/components/layout/AppLayout";
import { GlassCard } from "@/components/common/GlassCard";
import { palette } from "@/theme/tokens";

interface PlaceholderPageProps {
  title: string;
  subtitle: string;
  blurb: string;
  planned: string[];
}

/** Polished "next sprint" placeholder for pages not yet implemented. */
export function PlaceholderPage({ title, subtitle, blurb, planned }: PlaceholderPageProps) {
  return (
    <AppLayout title={title} subtitle={subtitle}>
      <div style={{ display: "flex", justifyContent: "center", paddingTop: 40 }}>
        <GlassCard style={{ maxWidth: 560, width: "100%", textAlign: "center", padding: "40px 36px" }}>
          <motion.div
            initial={{ scale: 0.85, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ type: "spring", stiffness: 220, damping: 18 }}
            style={{
              width: 64,
              height: 64,
              borderRadius: 16,
              margin: "0 auto 20px",
              background: palette.brandSoft,
              border: `1px solid ${palette.brand}55`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Wrench24Regular style={{ color: palette.brand, fontSize: 28 }} />
          </motion.div>
          <h2 style={{ margin: "0 0 8px", fontSize: 20, fontWeight: 700, color: palette.textPrimary }}>{title}</h2>
          <p style={{ margin: "0 auto 22px", fontSize: 13.5, color: palette.textSecondary, maxWidth: 420, lineHeight: 1.6 }}>
            {blurb}
          </p>
          <div style={{ textAlign: "left", display: "inline-block" }}>
            {planned.map((p) => (
              <div key={p} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 9 }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: palette.brand, flexShrink: 0 }} />
                <span style={{ fontSize: 13, color: palette.textSecondary }}>{p}</span>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </AppLayout>
  );
}
