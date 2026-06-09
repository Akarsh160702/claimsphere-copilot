import { useState, useEffect } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft20Regular,
  CheckmarkCircle20Filled,
  DismissCircle20Filled,
  DocumentBulletList20Regular,
  ShieldCheckmark20Regular,
  Person20Regular,
} from "@fluentui/react-icons";
import { AppLayout } from "@/components/layout/AppLayout";
import { GlassCard } from "@/components/common/GlassCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { FraudMeter } from "@/components/common/FraudMeter";
import { Skeleton } from "@/components/common/Skeleton";
import { palette, radius, statusColor } from "@/theme/tokens";
import { formatINR, formatDate } from "@/utils/format";
import { fetchClaimFull, recordHumanDecision } from "@/api/claims";

export function ClaimDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [reviewNotes, setReviewNotes] = useState("");
  const [searchParams, setSearchParams] = useSearchParams();

  const { data: claim, isLoading, isError } = useQuery({
    queryKey: ["claim", id],
    queryFn: () => fetchClaimFull(id!),
    enabled: !!id,
    retry: 1,
  });

  const mutation = useMutation({
    mutationFn: ({ decision }: { decision: "Approve" | "Reject" | "MoreInfo" }) =>
      recordHumanDecision(id!, decision, reviewNotes || "Human adjudicator decision", "adjudicator@nexora.com"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["claim", id] });
      queryClient.invalidateQueries({ queryKey: ["claims"] });
    },
  });

  // Auto-apply decision when arriving from Teams card buttons (?decision=Approve&reviewer=teams-adjudicator)
  useEffect(() => {
    const decision = searchParams.get("decision") as "Approve" | "Reject" | "MoreInfo" | null;
    if (decision && !mutation.isPending && !mutation.isSuccess && claim) {
      setSearchParams({}, { replace: true }); // remove query params from URL
      mutation.mutate({ decision });
    }
  }, [claim, searchParams]);

  if (isLoading) return (
    <AppLayout title="Claim Detail" subtitle="Loading…">
      <div style={{ display: "flex", flexDirection: "column", gap: 16, maxWidth: 800 }}>
        <GlassCard style={{ height: 80 }}><Skeleton height={40} /></GlassCard>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <GlassCard style={{ height: 200 }}><Skeleton height={160} /></GlassCard>
          <GlassCard style={{ height: 200 }}><Skeleton height={160} /></GlassCard>
        </div>
      </div>
    </AppLayout>
  );

  if (isError || !claim) return (
    <AppLayout title="Claim Not Found" subtitle="">
      <GlassCard style={{ maxWidth: 400, textAlign: "center", padding: 40 }}>
        <p style={{ color: palette.textSecondary }}>Claim not found. It may have been cleared from memory on server restart.</p>
        <button onClick={() => navigate("/claims")} style={outlineBtnStyle}>Back to Claims</button>
      </GlassCard>
    </AppLayout>
  );

  const adj = claim.adjudication_result;
  const fraud = claim.fraud_result;
  const val = claim.validation_result;
  const missing = claim.missing_info_result;
  const needsReview = claim.status === "Under Human Review" || claim.status === "Escalated";
  const decisionColor = statusColor(adj?.decision ?? claim.status ?? "");
  const isRuleBased = claim.audit_trail?.some((a) => a.action === "PRE_ADJUDICATION_DECISION");
  const modelLabel = isRuleBased ? "rule-based" : "gpt-4o";

  return (
    <AppLayout
      title={claim.claim_id}
      subtitle={`${claim.claim_type} · ${claim.priority} priority · submitted ${formatDate(claim.created_at)}`}
    >
      {/* Back + status header */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
        <button onClick={() => navigate(-1)} style={{ ...outlineBtnStyle, padding: "6px 12px", display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}>
          <ArrowLeft20Regular /> Back
        </button>
        <StatusBadge value={claim.status ?? "Processing"} />
        {adj?.decision && <StatusBadge value={adj.decision} />}
        {needsReview && (
          <span
            title="A Teams Adaptive Card was sent to the review channel via Power Automate"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              padding: "4px 11px",
              borderRadius: 999,
              fontSize: 11.5,
              fontWeight: 600,
              color: "#5B5FC7",
              background: "rgba(91,95,199,0.14)",
              border: "1px solid rgba(91,95,199,0.35)",
              whiteSpace: "nowrap",
            }}
          >
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#5B5FC7" }} />
            Teams notified
          </span>
        )}
      </div>

      {/* ── Top metrics row ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 16 }}>
        <MetricTile icon={<DocumentBulletList20Regular />} label="Claim Amount" value={formatINR(claim.submission.claim_amount)} />
        <MetricTile icon={<CheckmarkCircle20Filled style={{ color: palette.success }} />} label="Approved Amount"
          value={formatINR(adj?.approved_amount ?? 0)} valueColor={palette.success} />
        <MetricTile icon={<ShieldCheckmark20Regular />} label="Fraud Score"
          value={`${fraud?.fraud_score ?? 0}/100`}
          valueColor={fraud && fraud.fraud_score < 30 ? palette.success : fraud && fraud.fraud_score < 60 ? palette.warning : palette.danger} />
        <MetricTile icon={<Person20Regular />} label="Claimant" value={claim.submission.claimant.name} />
      </div>

      {/* ── Main grid ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, alignItems: "start" }}>
        {/* Left col */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

          {/* Agent pipeline */}
          <GlassCard>
            <SectionLabel>Agent Pipeline</SectionLabel>
            <AgentTimeline audit={claim.audit_trail} />
          </GlassCard>

          {/* Validation result */}
          {val && (
            <GlassCard>
              <SectionLabel>Policy Validation</SectionLabel>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <CheckRow label="Policy Active" ok={val.policy_active} />
                <CheckRow label="Claim Type Covered" ok={val.claim_type_covered} />
                <CheckRow label="Within Sum Insured" ok={val.within_sum_insured} />
                {val.exclusions_hit.length > 0 && (
                  <div style={{ padding: "8px 12px", borderRadius: 6, background: palette.dangerSoft, fontSize: 12.5, color: palette.danger }}>
                    Exclusions hit: {val.exclusions_hit.join(", ")}
                  </div>
                )}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginTop: 4 }}>
                  <SmallMetric label="Coverage" value={formatINR(val.coverage_amount)} color={palette.success} />
                  <SmallMetric label="Deductible" value={formatINR(val.deductible_amount)} color={palette.warning} />
                </div>
                {val.validation_notes && (
                  <p style={{ margin: "8px 0 0", fontSize: 12.5, color: palette.textSecondary, lineHeight: 1.6 }}>
                    {val.validation_notes}
                  </p>
                )}
              </div>
            </GlassCard>
          )}

          {/* Missing info */}
          {missing?.has_missing_info && (
            <GlassCard>
              <SectionLabel>Missing Information</SectionLabel>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {missing.missing_fields.map((f) => (
                  <div key={f} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: palette.textSecondary }}>
                    <span style={{ width: 5, height: 5, borderRadius: "50%", background: palette.warning, flexShrink: 0 }} />
                    {f}
                  </div>
                ))}
              </div>
            </GlassCard>
          )}
        </div>

        {/* Right col */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

          {/* Claim info */}
          <GlassCard>
            <SectionLabel>Claim Information</SectionLabel>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <InfoRow label="Policy ID" value={claim.submission.policy_id} mono />
              <InfoRow label="Email" value={claim.submission.claimant.email} />
              <InfoRow label="Phone" value={claim.submission.claimant.phone} />
              <InfoRow label="Incident Date" value={claim.submission.incident_date} />
              <InfoRow label="Channel" value={claim.submission.channel} />
              <div>
                <div style={smallLabelStyle}>Description</div>
                <p style={{ margin: "4px 0 0", fontSize: 13, color: palette.textSecondary, lineHeight: 1.65 }}>
                  {claim.submission.description}
                </p>
              </div>
            </div>
          </GlassCard>

          {/* Fraud analysis */}
          {fraud && (
            <GlassCard>
              <SectionLabel>Fraud Analysis</SectionLabel>
              <div style={{ marginBottom: 12 }}>
                <FraudMeter score={fraud.fraud_score} width="100%" />
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10 }}>
                <span style={{
                  padding: "3px 10px", borderRadius: 4, fontSize: 11, fontWeight: 700,
                  background: fraud.fraud_score < 30 ? palette.successSoft : fraud.fraud_score < 60 ? palette.warningSoft : palette.dangerSoft,
                  color: fraud.fraud_score < 30 ? palette.success : fraud.fraud_score < 60 ? palette.warning : palette.danger,
                  border: `1px solid currentColor`, lineHeight: 1.5,
                }}>
                  {fraud.risk_level}
                </span>
                {fraud.flags.map((flag) => (
                  <span key={flag} style={{
                    padding: "3px 10px", borderRadius: 4, fontSize: 11, fontWeight: 500,
                    background: palette.warningSoft, color: palette.warning,
                    border: `1px solid ${palette.warning}40`, lineHeight: 1.5,
                  }}>
                    {flag}
                  </span>
                ))}
              </div>
              {fraud.reasoning && (
                <p style={{ margin: 0, fontSize: 12.5, color: palette.textSecondary, lineHeight: 1.65 }}>
                  {fraud.reasoning}
                </p>
              )}
            </GlassCard>
          )}

          {/* Adjudication */}
          {adj && (
            <GlassCard style={{ border: `1px solid ${decisionColor}30` }}>
              <SectionLabel>Adjudication Result</SectionLabel>
              <div style={{ display: "flex", gap: 10, marginBottom: 14, alignItems: "center" }}>
                <div style={{ fontSize: 20, fontWeight: 800, color: decisionColor }}>{adj.decision}</div>
                <div style={{ fontSize: 12, color: palette.textMuted }}>
                  Confidence: {Math.round(adj.confidence_score * 100)}%
                </div>
                <div style={{ fontSize: 11, color: palette.textMuted, marginLeft: "auto" }}>
                  model: {modelLabel}
                </div>
              </div>
              <p style={{ margin: "0 0 12px", fontSize: 13, color: palette.textSecondary, lineHeight: 1.65 }}>
                {adj.rationale}
              </p>
              {adj.escalation_reason && (
                <div style={{ fontSize: 12.5, color: palette.warning, padding: "6px 10px", borderRadius: 6, background: palette.warningSoft }}>
                  Escalation reason: {adj.escalation_reason}
                </div>
              )}
              {adj.rejection_reason && (
                <div style={{ fontSize: 12.5, color: palette.danger, padding: "6px 10px", borderRadius: 6, background: palette.dangerSoft }}>
                  Rejection reason: {adj.rejection_reason}
                </div>
              )}
              {adj.supporting_evidence.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <div style={smallLabelStyle}>Supporting Evidence</div>
                  {adj.supporting_evidence.map((e, i) => (
                    <div key={i} style={{ display: "flex", gap: 8, alignItems: "flex-start", marginTop: 6, fontSize: 12.5, color: palette.textSecondary }}>
                      <span style={{ width: 5, height: 5, borderRadius: "50%", background: palette.success, flexShrink: 0, marginTop: 5 }} />
                      {e}
                    </div>
                  ))}
                </div>
              )}
            </GlassCard>
          )}

          {/* Human review panel */}
          {needsReview && (
            <GlassCard style={{ border: `1px solid ${palette.warning}40` }}>
              <SectionLabel>Human Review Required</SectionLabel>
              <p style={{ margin: "0 0 12px", fontSize: 13, color: palette.textSecondary }}>
                This claim has been escalated for human adjudication.
              </p>
              <textarea
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Add review notes (optional)…"
                rows={2}
                style={{
                  width: "100%", padding: "8px 12px", borderRadius: 8, fontSize: 13,
                  background: palette.glassFill, border: `1px solid ${palette.glassBorder}`,
                  color: palette.textPrimary, outline: "none", resize: "vertical",
                  fontFamily: "inherit", boxSizing: "border-box", marginBottom: 12,
                }}
              />
              <div style={{ display: "flex", gap: 8 }}>
                <DecisionBtn
                  label="Approve" color={palette.success} softColor={palette.successSoft}
                  loading={mutation.isPending}
                  onClick={() => mutation.mutate({ decision: "Approve" })}
                />
                <DecisionBtn
                  label="Reject" color={palette.danger} softColor={palette.dangerSoft}
                  loading={mutation.isPending}
                  onClick={() => mutation.mutate({ decision: "Reject" })}
                />
                <DecisionBtn
                  label="More Info" color={palette.warning} softColor={palette.warningSoft}
                  loading={mutation.isPending}
                  onClick={() => mutation.mutate({ decision: "MoreInfo" })}
                />
              </div>
              {mutation.isSuccess && (
                <div
                  style={{
                    marginTop: 10,
                    fontSize: 13,
                    color: mutation.data?.dataverse_updated === false ? palette.warning : palette.success,
                  }}
                >
                  {mutation.data?.dataverse_updated === false
                    ? "Decision recorded, but Power Apps sync needs attention."
                    : "Decision recorded and Power Apps table updated."}
                </div>
              )}
            </GlassCard>
          )}
        </div>
      </div>
    </AppLayout>
  );
}

// ── Agent timeline ────────────────────────────────────────────────────────────
function AgentTimeline({ audit }: { audit: { agent_name: string; action: string; timestamp: string; details: Record<string, unknown> }[] }) {
  if (!audit.length) return <p style={{ fontSize: 13, color: palette.textMuted }}>No agent data available.</p>;

  const isSeedAgent = (action: string) => action === "DEMO_SEED";
  const filtered = audit.filter((a) => !isSeedAgent(a.action));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
      {filtered.map((entry, i) => {
        const isLast = i === filtered.length - 1;
        const ok = !entry.action.includes("FAIL") && !entry.action.includes("ERROR");
        const color = ok ? palette.success : palette.danger;
        return (
          <div key={i} style={{ display: "flex", gap: 0, position: "relative" }}>
            {!isLast && (
              <div style={{ position: "absolute", left: 11, top: 26, width: 2, height: "calc(100% - 6px)", background: palette.glassBorder }} />
            )}
            <div style={{ display: "flex", gap: 12, alignItems: "flex-start", padding: "8px 0", zIndex: 1 }}>
              <div style={{ flexShrink: 0, width: 24, display: "flex", justifyContent: "center", marginTop: 1 }}>
                {ok ? <CheckmarkCircle20Filled style={{ color }} /> : <DismissCircle20Filled style={{ color }} />}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "baseline" }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: palette.textPrimary }}>{entry.agent_name}</span>
                  <span style={{ fontSize: 11, color: palette.textMuted, whiteSpace: "nowrap" }}>
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div style={{ fontSize: 11.5, color: palette.textMuted, marginTop: 1 }}>{entry.action}</div>
                {entry.details?.confidence !== undefined && (
                  <div style={{ fontSize: 11.5, color: palette.brand, marginTop: 2 }}>
                    confidence: {typeof entry.details.confidence === "number" ? `${Math.round((entry.details.confidence as number) * 100)}%` : String(entry.details.confidence)}
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Small helpers ─────────────────────────────────────────────────────────────
function MetricTile({ icon, label, value, valueColor }: { icon: React.ReactNode; label: string; value: string; valueColor?: string }) {
  return (
    <GlassCard style={{ padding: "14px 16px" }}>
      <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
        <div style={{ color: palette.textMuted, marginTop: 2 }}>{icon}</div>
        <div>
          <div style={smallLabelStyle}>{label}</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: valueColor ?? palette.textPrimary, marginTop: 4 }}>{value}</div>
        </div>
      </div>
    </GlassCard>
  );
}

function CheckRow({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 13 }}>
      <span style={{ color: palette.textSecondary }}>{label}</span>
      {ok ? <CheckmarkCircle20Filled style={{ color: palette.success }} /> : <DismissCircle20Filled style={{ color: palette.danger }} />}
    </div>
  );
}

function SmallMetric({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{ padding: "8px 12px", borderRadius: 6, background: palette.glassFill, border: `1px solid ${palette.glassBorder}` }}>
      <div style={smallLabelStyle}>{label}</div>
      <div style={{ fontSize: 14, fontWeight: 700, color, marginTop: 4 }}>{value}</div>
    </div>
  );
}

function InfoRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12, fontSize: 13 }}>
      <span style={{ color: palette.textMuted, flexShrink: 0 }}>{label}</span>
      <span style={{ color: palette.textPrimary, fontFamily: mono ? "monospace" : "inherit", textAlign: "right" }}>{value}</span>
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: palette.textMuted, marginBottom: 14 }}>
      {children}
    </div>
  );
}

function DecisionBtn({ label, color, softColor, onClick, loading }: {
  label: string; color: string; softColor: string; onClick: () => void; loading: boolean;
}) {
  return (
    <button onClick={onClick} disabled={loading} style={{
      flex: 1, padding: "9px 0", borderRadius: radius.md, fontSize: 13, fontWeight: 600,
      cursor: loading ? "not-allowed" : "pointer", transition: "opacity 0.15s",
      background: softColor, border: `1px solid ${color}50`, color,
    }}>
      {label}
    </button>
  );
}

const smallLabelStyle: React.CSSProperties = {
  fontSize: 10.5, fontWeight: 700, letterSpacing: "0.07em",
  textTransform: "uppercase", color: palette.textMuted,
};

const outlineBtnStyle: React.CSSProperties = {
  padding: "7px 14px", borderRadius: radius.md, fontSize: 13, fontWeight: 600,
  cursor: "pointer", background: palette.glassFill, border: `1px solid ${palette.glassBorder}`,
  color: palette.textSecondary, transition: "all 0.12s",
};
