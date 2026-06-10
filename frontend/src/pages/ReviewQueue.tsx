import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckmarkCircle20Regular,
  DismissCircle20Regular,
  Info20Regular,
  ArrowRight16Regular,
  Person20Regular,
} from "@fluentui/react-icons";
import { AppLayout } from "@/components/layout/AppLayout";
import { GlassCard } from "@/components/common/GlassCard";
import { FraudMeter } from "@/components/common/FraudMeter";
import { Skeleton } from "@/components/common/Skeleton";
import { getPalette, radius } from "@/theme/tokens";
import { useTheme } from "@/contexts/ThemeContext";
import { formatINR, formatDate } from "@/utils/format";
import { apiClient } from "@/api/client";
import { recordHumanDecision } from "@/api/claims";
import type { ClaimFull, ClaimListItem } from "@/api/types";

async function fetchEscalatedClaims(): Promise<ClaimFull[]> {
  const listRes = await apiClient.get<ClaimListItem[]>("/claims/");
  const escalated = (Array.isArray(listRes.data) ? listRes.data : []).filter(
    (c) => c.status === "Under Human Review" || c.status === "Escalated" || c.decision === "Escalate"
  );
  const details = await Promise.allSettled(
    escalated.map((c) => apiClient.get<ClaimFull>(`/claims/${c.claim_id}/full`).then((r) => r.data))
  );
  return details.flatMap((r) => (r.status === "fulfilled" ? [r.value] : []));
}

export function ReviewQueue() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { theme } = useTheme();
  const palette = getPalette(theme);

  const { data: claims = [], isLoading } = useQuery({
    queryKey: ["review-queue"],
    queryFn: fetchEscalatedClaims,
    refetchInterval: 20000,
  });

  return (
    <AppLayout
      title="Review Queue"
      subtitle={`${claims.length} claim${claims.length !== 1 ? "s" : ""} awaiting human adjudication`}
    >
      {isLoading ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {Array.from({ length: 3 }).map((_, i) => <GlassCard key={i} style={{ height: 180 }}><Skeleton height={140} /></GlassCard>)}
        </div>
      ) : claims.length === 0 ? (
        <GlassCard style={{ textAlign: "center", padding: 52 }}>
          <CheckmarkCircle20Regular style={{ color: palette.success, fontSize: 36, marginBottom: 12 }} />
          <h3 style={{ margin: "0 0 8px", color: palette.textPrimary, fontSize: 16 }}>Queue is clear</h3>
          <p style={{ margin: 0, color: palette.textSecondary, fontSize: 13.5 }}>
            No claims are awaiting human review right now.
          </p>
        </GlassCard>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <AnimatePresence>
            {claims.map((claim, i) => (
              <ReviewCard
                key={claim.claim_id}
                claim={claim}
                delay={i * 0.06}
                onView={() => navigate(`/claims/${claim.claim_id}`)}
                onDecision={(decision, notes) => {
                  recordHumanDecision(claim.claim_id, decision, notes, "adjudicator@nexora.com").then(() => {
                    queryClient.invalidateQueries({ queryKey: ["review-queue"] });
                    queryClient.invalidateQueries({ queryKey: ["claims"] });
                    queryClient.invalidateQueries({ queryKey: ["claim", claim.claim_id] });
                  });
                }}
              />
            ))}
          </AnimatePresence>
        </div>
      )}
    </AppLayout>
  );
}

function ReviewCard({ claim, delay, onView, onDecision }: {
  claim: ClaimFull;
  delay: number;
  onView: () => void;
  onDecision: (decision: "Approve" | "Reject" | "MoreInfo", notes: string) => void;
}) {
  const [notes, setNotes] = useState("");
  const [decided, setDecided] = useState(false);
  const [decisionMade, setDecisionMade] = useState<string | null>(null);
  const { theme } = useTheme();
  const palette = getPalette(theme);

  const adj = claim.adjudication_result;
  const fraud = claim.fraud_result;
  const missing = claim.missing_info_result;

  function decide(d: "Approve" | "Reject" | "MoreInfo") {
    onDecision(d, notes);
    setDecisionMade(d);
    setDecided(true);
  }

  if (decided) {
    const color = decisionMade === "Approve" ? palette.success : decisionMade === "Reject" ? palette.danger : palette.warning;
    return (
      <motion.div initial={{ opacity: 1 }} animate={{ opacity: 0, height: 0 }} transition={{ delay: 1.5, duration: 0.4 }}>
        <GlassCard style={{ border: `1px solid ${color}40`, padding: "14px 20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 13, fontWeight: 700, color }}>{decisionMade === "MoreInfo" ? "More Info Requested" : `${decisionMade}d`}</span>
            <span style={{ fontSize: 12.5, color: palette.textMuted }}>· {claim.claim_id}</span>
          </div>
        </GlassCard>
      </motion.div>
    );
  }

  return (
    <GlassCard delay={delay} style={{ border: `1px solid ${palette.warning}25` }}>
      {/* Header row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
        <div>
          <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 4 }}>
            <span style={{ fontSize: 13.5, fontWeight: 700, color: palette.textPrimary, fontFamily: "monospace" }}>
              {claim.claim_id}
            </span>
            <span style={{
              fontSize: 10.5, fontWeight: 700, padding: "2px 8px", borderRadius: 999,
              background: palette.warningSoft, color: palette.warning, border: `1px solid ${palette.warning}40`,
            }}>
              Awaiting Review
            </span>
          </div>
          <div style={{ display: "flex", gap: 10, fontSize: 12.5, color: palette.textMuted }}>
            <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <Person20Regular style={{ fontSize: 13 }} /> {claim.submission.claimant.name}
            </span>
            <span>·</span>
            <span>{claim.claim_type}</span>
            <span>·</span>
            <span>{formatINR(claim.submission.claim_amount)}</span>
            <span>·</span>
            <span>{formatDate(claim.created_at)}</span>
          </div>
        </div>
        <button
          onClick={onView}
          style={{
            display: "flex", alignItems: "center", gap: 4, padding: "5px 12px",
            borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: "pointer",
            background: palette.glassFill, border: `1px solid ${palette.glassBorder}`,
            color: palette.textSecondary,
          }}
        >
          Full Detail <ArrowRight16Regular />
        </button>
      </div>

      {/* Content grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14, marginBottom: 16 }}>
        {/* Escalation reason */}
        <div style={{ padding: "10px 12px", borderRadius: 8, background: palette.warningSoft, border: `1px solid ${palette.warning}30` }}>
          <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: "0.07em", textTransform: "uppercase", color: palette.warning, marginBottom: 6 }}>
            Escalation Reason
          </div>
          <div style={{ fontSize: 12.5, color: palette.textSecondary, lineHeight: 1.5 }}>
            {adj?.escalation_reason ?? "Human review required"}
          </div>
        </div>

        {/* AI recommendation */}
        <div style={{ padding: "10px 12px", borderRadius: 8, background: palette.glassFill, border: `1px solid ${palette.glassBorder}` }}>
          <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: "0.07em", textTransform: "uppercase", color: palette.textMuted, marginBottom: 6 }}>
            AI Recommendation
          </div>
          <div style={{ fontSize: 13, fontWeight: 700, color: palette.info }}>{adj?.decision ?? "Escalate"}</div>
          <div style={{ fontSize: 11.5, color: palette.textMuted, marginTop: 2 }}>
            {adj ? `${Math.round(adj.confidence_score * 100)}% confidence` : ""}
          </div>
          <div style={{ fontSize: 11.5, color: palette.success, marginTop: 2 }}>
            Payout: {formatINR(adj?.approved_amount ?? 0)}
          </div>
        </div>

        {/* Fraud score */}
        <div style={{ padding: "10px 12px", borderRadius: 8, background: palette.glassFill, border: `1px solid ${palette.glassBorder}` }}>
          <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: "0.07em", textTransform: "uppercase", color: palette.textMuted, marginBottom: 8 }}>
            Fraud Risk
          </div>
          <FraudMeter score={fraud?.fraud_score ?? 0} width="100%" />
          <div style={{ fontSize: 11.5, color: palette.textMuted, marginTop: 4 }}>
            {fraud?.risk_level ?? "—"} risk · {fraud?.flags.length ?? 0} flags
          </div>
        </div>
      </div>

      {/* AI rationale */}
      {adj?.rationale && (
        <div style={{ marginBottom: 14, padding: "10px 12px", borderRadius: 8, background: palette.glassFill, border: `1px solid ${palette.glassBorder}` }}>
          <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: "0.07em", textTransform: "uppercase", color: palette.textMuted, marginBottom: 6 }}>
            AI Rationale
          </div>
          <p style={{ margin: 0, fontSize: 12.5, color: palette.textSecondary, lineHeight: 1.6 }}>
            {adj.rationale.length > 280 ? adj.rationale.slice(0, 280) + "…" : adj.rationale}
          </p>
        </div>
      )}

      {/* Missing info warning */}
      {missing?.has_missing_info && (
        <div style={{ display: "flex", gap: 6, alignItems: "flex-start", marginBottom: 14, fontSize: 12.5, color: palette.warning }}>
          <Info20Regular style={{ flexShrink: 0, marginTop: 1 }} />
          <span>Missing: {missing.missing_fields.slice(0, 3).join(", ")}{missing.missing_fields.length > 3 ? ` +${missing.missing_fields.length - 3} more` : ""}</span>
        </div>
      )}

      {/* Notes + decision buttons */}
      <div style={{ borderTop: `1px solid ${palette.glassBorder}`, paddingTop: 14 }}>
        <input
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Add review notes (optional)…"
          style={{
            width: "100%", padding: "8px 12px", borderRadius: 8, fontSize: 13,
            background: palette.glassFill, border: `1px solid ${palette.glassBorder}`,
            color: palette.textPrimary, outline: "none", fontFamily: "inherit",
            boxSizing: "border-box", marginBottom: 12,
          }}
        />
        <div style={{ display: "flex", gap: 10 }}>
          <DecisionButton label="Approve" icon={<CheckmarkCircle20Regular />} color={palette.success} softColor={palette.successSoft} onClick={() => decide("Approve")} />
          <DecisionButton label="Reject" icon={<DismissCircle20Regular />} color={palette.danger} softColor={palette.dangerSoft} onClick={() => decide("Reject")} />
          <DecisionButton label="Request Info" icon={<Info20Regular />} color={palette.warning} softColor={palette.warningSoft} onClick={() => decide("MoreInfo")} />
        </div>
      </div>
    </GlassCard>
  );
}

function DecisionButton({ label, icon, color, softColor, onClick }: {
  label: string; icon: React.ReactNode; color: string; softColor: string; onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 7,
        padding: "9px 0", borderRadius: radius.md, fontSize: 13, fontWeight: 600,
        cursor: "pointer", transition: "opacity 0.15s",
        background: softColor, border: `1px solid ${color}50`, color,
      }}
    >
      {icon} {label}
    </button>
  );
}
