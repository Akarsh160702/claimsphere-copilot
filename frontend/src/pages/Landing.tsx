import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ShieldTask24Filled,
  ArrowRight20Filled,
  Flash20Regular,
  BrainCircuit20Regular,
  Shield20Regular,
} from "@fluentui/react-icons";
import { palette, shadow } from "@/theme/tokens";
import { useAppStore } from "@/store/useAppStore";

const PILLARS = [
  { icon: BrainCircuit20Regular, title: "7-agent pipeline", desc: "Router → Document → Validation → Fraud → Adjudication" },
  { icon: Flash20Regular, title: "Seconds, not days", desc: "End-to-end straight-through processing on Azure AI Foundry" },
  { icon: Shield20Regular, title: "Audit-grade decisions", desc: "Every step explained, scored, and traceable for compliance" },
];

const STATS = [
  { value: "97.3%", label: "AI accuracy" },
  { value: "3.1s", label: "Avg. turnaround" },
  { value: "7", label: "Agents" },
];

export function Landing() {
  const navigate = useNavigate();
  const backendOnline = useAppStore((s) => s.backendOnline);

  return (
    <div
      style={{
        height: "100vh",
        width: "100%",
        overflow: "hidden",
        position: "relative",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Ambient hero glow */}
      <div
        aria-hidden
        className="cs-drift"
        style={{
          position: "absolute",
          top: "-30%",
          left: "50%",
          transform: "translateX(-50%)",
          width: 800,
          height: 800,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(46,144,250,0.18), transparent 62%)",
          filter: "blur(20px)",
          pointerEvents: "none",
        }}
      />

      {/* Top bar */}
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "18px 40px",
          flexShrink: 0,
          position: "relative",
          zIndex: 1,
        }}
      >
        <BrandMark />
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: palette.textSecondary }}>
          <span
            className={backendOnline ? "cs-pulse-dot" : undefined}
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: backendOnline ? palette.success : palette.warning,
            }}
          />
          {backendOnline ? "Platform online" : "Demo environment"}
        </div>
      </header>

      {/* Hero — flex:1 centers the content in the remaining space */}
      <main
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          padding: "0 24px",
          position: "relative",
          zIndex: 1,
          minHeight: 0,
        }}
      >
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 7,
            padding: "5px 13px",
            borderRadius: 999,
            background: palette.brandSoft,
            border: `1px solid ${palette.brand}40`,
            fontSize: 11.5,
            fontWeight: 600,
            letterSpacing: "0.04em",
            color: palette.brandHover,
            marginBottom: 18,
          }}
        >
          <span style={{ width: 6, height: 6, borderRadius: "50%", background: palette.brand }} />
          Powered by Microsoft Azure AI Foundry
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.05, ease: [0.16, 1, 0.3, 1] }}
          style={{
            margin: 0,
            fontSize: "clamp(32px, 5vw, 58px)",
            fontWeight: 800,
            lineHeight: 1.06,
            letterSpacing: "-0.035em",
            color: palette.textPrimary,
            maxWidth: 820,
          }}
        >
          Insurance claims,{" "}
          <span
            style={{
              background: `linear-gradient(100deg, ${palette.brandHover}, ${palette.brand} 55%, #8B86F5)`,
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            adjudicated by agents.
          </span>
        </motion.h1>

        {/* Subtext */}
        <motion.p
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
          style={{
            margin: "16px 0 0",
            fontSize: "clamp(14px, 1.5vw, 16px)",
            lineHeight: 1.6,
            color: palette.textSecondary,
            maxWidth: 540,
          }}
        >
          ClaimSphere Copilot ingests, validates, scores and decides health,
          motor and property claims end-to-end — with a transparent, audit-ready
          trail behind every outcome.
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.16, ease: [0.16, 1, 0.3, 1] }}
          style={{ display: "flex", gap: 10, marginTop: 24, flexWrap: "wrap", justifyContent: "center" }}
        >
          <button
            onClick={() => navigate("/dashboard")}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              padding: "11px 22px",
              borderRadius: 11,
              fontSize: 14,
              fontWeight: 600,
              cursor: "pointer",
              color: "#fff",
              background: `linear-gradient(135deg, ${palette.brandHover}, ${palette.brandStrong})`,
              border: "none",
              boxShadow: shadow.brandGlow,
              transition: "transform 0.15s",
            }}
            onMouseEnter={(e) => { e.currentTarget.style.transform = "translateY(-2px)"; }}
            onMouseLeave={(e) => { e.currentTarget.style.transform = "translateY(0)"; }}
          >
            Enter Dashboard <ArrowRight20Filled />
          </button>
          <button
            onClick={() => navigate("/intake")}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              padding: "11px 20px",
              borderRadius: 11,
              fontSize: 14,
              fontWeight: 600,
              cursor: "pointer",
              color: palette.textPrimary,
              background: palette.glassFill,
              border: `1px solid ${palette.glassBorderStrong}`,
              transition: "background 0.15s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = palette.glassFillStrong)}
            onMouseLeave={(e) => (e.currentTarget.style.background = palette.glassFill)}
          >
            Submit a claim
          </button>
        </motion.div>

        {/* Stats strip */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.24 }}
          style={{ display: "flex", gap: 0, marginTop: 32 }}
        >
          {STATS.map((s, i) => (
            <div
              key={s.label}
              style={{
                padding: "0 24px",
                borderLeft: i > 0 ? `1px solid ${palette.glassBorder}` : "none",
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: 24, fontWeight: 800, letterSpacing: "-0.03em", color: palette.textPrimary }}>
                {s.value}
              </div>
              <div style={{ fontSize: 11, color: palette.textMuted, marginTop: 2, letterSpacing: "0.04em" }}>
                {s.label}
              </div>
            </div>
          ))}
        </motion.div>
      </main>

      {/* Pillar cards — pinned to bottom */}
      <motion.footer
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.32 }}
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 10,
          padding: "0 40px 24px",
          maxWidth: 1040,
          margin: "0 auto",
          width: "100%",
          flexShrink: 0,
          position: "relative",
          zIndex: 1,
        }}
      >
        {PILLARS.map(({ icon: Icon, title, desc }) => (
          <div
            key={title}
            className="cs-glass"
            style={{ padding: "13px 16px", display: "flex", gap: 12, alignItems: "flex-start" }}
          >
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: 8,
                flexShrink: 0,
                background: palette.brandSoft,
                border: `1px solid ${palette.brand}33`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Icon style={{ color: palette.brand }} />
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: palette.textPrimary }}>{title}</div>
              <div style={{ fontSize: 11.5, color: palette.textMuted, marginTop: 2, lineHeight: 1.5 }}>{desc}</div>
            </div>
          </div>
        ))}
      </motion.footer>
    </div>
  );
}

function BrandMark() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <div
        style={{
          width: 34,
          height: 34,
          borderRadius: 9,
          background: `linear-gradient(140deg, ${palette.brandHover}, ${palette.brandStrong})`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: shadow.brandGlow,
        }}
      >
        <ShieldTask24Filled style={{ color: "#fff" }} />
      </div>
      <div>
        <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: "-0.01em", color: palette.textPrimary, lineHeight: 1.1 }}>
          ClaimSphere
        </div>
        <div style={{ fontSize: 10, color: palette.textMuted, letterSpacing: "0.07em", textTransform: "uppercase" }}>
          Copilot
        </div>
      </div>
    </div>
  );
}
