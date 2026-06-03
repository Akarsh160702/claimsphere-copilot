import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  CheckmarkCircle20Filled,
  DismissCircle20Filled,
  Circle20Regular,
  ArrowRight16Regular,
} from "@fluentui/react-icons";
import { AppLayout } from "@/components/layout/AppLayout";
import { GlassCard } from "@/components/common/GlassCard";
import { Skeleton } from "@/components/common/Skeleton";
import { StatusBadge } from "@/components/common/StatusBadge";
import { palette } from "@/theme/tokens";
import { formatINR } from "@/utils/format";
import { apiClient } from "@/api/client";
import type { ClaimFull, ClaimListItem } from "@/api/types";

const PIPELINE = [
  { key: "RouterAgent",      short: "Router",     color: palette.brand },
  { key: "DocumentAgent",    short: "Doc",        color: "#22D3EE" },
  { key: "ValidationAgent",  short: "Validate",   color: palette.success },
  { key: "FraudAgent",       short: "Fraud",      color: palette.warning },
  { key: "MissingInfoAgent", short: "Info",       color: "#9B6DFF" },
  { key: "AdjudicationAgent",short: "Adjudicate", color: palette.info },
];

async function fetchRecentFull(): Promise<ClaimFull[]> {
  const listRes = await apiClient.get<ClaimListItem[]>("/claims/");
  const ids = (Array.isArray(listRes.data) ? listRes.data : [])
    .slice(0, 8)
    .map((c) => c.claim_id);
  const details = await Promise.allSettled(
    ids.map((id) => apiClient.get<ClaimFull>(`/claims/${id}/full`).then((r) => r.data))
  );
  return details.flatMap((r) => (r.status === "fulfilled" ? [r.value] : []));
}

export function AgentMonitor() {
  const navigate = useNavigate();

  const { data: claims = [], isLoading } = useQuery({
    queryKey: ["agent-monitor"],
    queryFn: fetchRecentFull,
    refetchInterval: 30000,
    staleTime: 15000,
  });

  // Aggregate stats
  const agentStats = PIPELINE.map(({ key }) => {
    const runs = claims.flatMap((c) => c.audit_trail.filter((a) => a.agent_name === key && a.action !== "DEMO_SEED"));
    const successes = runs.filter((a) => !a.action.includes("FAIL")).length;
    return { key, runs: runs.length, successes, rate: runs.length ? Math.round((successes / runs.length) * 100) : 100 };
  });

  const totalClaims = claims.length;
  const avgAgents = totalClaims
    ? Math.round(claims.reduce((s, c) => s + c.audit_trail.filter((a) => a.action !== "DEMO_SEED").length, 0) / totalClaims)
    : 0;

  return (
    <AppLayout title="Agent Monitor" subtitle="Real-time view of the multi-agent AI pipeline">
      {/* Stats row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14, marginBottom: 16 }}>
        <StatCard label="Claims Monitored" value={totalClaims} color={palette.brand} />
        <StatCard label="Avg Agent Steps" value={avgAgents} color={palette.success} />
        <StatCard label="Pipeline Agents" value={6} color="#9B6DFF" />
      </div>

      {/* Agent success rate bar */}
      <GlassCard style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: palette.textMuted, marginBottom: 14 }}>
          Agent Success Rates
        </div>
        <div style={{ display: "flex", gap: 0 }}>
          {PIPELINE.map(({ key, short }, i) => {
            const stat = agentStats.find((s) => s.key === key);
            const rate = stat?.rate ?? 100;
            return (
              <div key={key} style={{ flex: 1, borderRight: i < PIPELINE.length - 1 ? `1px solid ${palette.glassBorder}` : "none", padding: "0 16px 0 0", marginRight: i < PIPELINE.length - 1 ? 16 : 0 }}>
                <div style={{ fontSize: 11, color: palette.textMuted, marginBottom: 6 }}>{short}</div>
                <div style={{ height: 4, borderRadius: 2, background: palette.glassFill, marginBottom: 5, overflow: "hidden" }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${rate}%` }}
                    transition={{ duration: 0.8, delay: i * 0.1 }}
                    style={{ height: "100%", borderRadius: 2, background: rate > 80 ? palette.success : palette.warning }}
                  />
                </div>
                <div style={{ fontSize: 13, fontWeight: 700, color: palette.textPrimary }}>{rate}%</div>
                <div style={{ fontSize: 11, color: palette.textMuted }}>{stat?.runs ?? 0} runs</div>
              </div>
            );
          })}
        </div>
      </GlassCard>

      {/* Per-claim pipeline cards */}
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: palette.textMuted, marginBottom: 12 }}>
        Recent Claims — Pipeline View
      </div>

      {isLoading ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {Array.from({ length: 4 }).map((_, i) => <GlassCard key={i} style={{ height: 80 }}><Skeleton height={50} /></GlassCard>)}
        </div>
      ) : claims.length === 0 ? (
        <GlassCard>
          <p style={{ color: palette.textMuted, fontSize: 13, textAlign: "center", padding: "20px 0" }}>
            No claims to monitor yet. Submit a claim to see the pipeline.
          </p>
        </GlassCard>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {claims.map((claim) => (
            <PipelineCard key={claim.claim_id} claim={claim} onView={() => navigate(`/claims/${claim.claim_id}`)} />
          ))}
        </div>
      )}
    </AppLayout>
  );
}

function PipelineCard({ claim, onView }: { claim: ClaimFull; onView: () => void }) {
  const agentMap = new Map(
    claim.audit_trail
      .filter((a) => a.action !== "DEMO_SEED")
      .map((a) => [a.agent_name, a])
  );
  const adj = claim.adjudication_result;
  const fraud = claim.fraud_result;

  return (
    <GlassCard interactive onClick={onView} style={{ padding: "14px 18px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
        {/* Claim info */}
        <div style={{ minWidth: 180 }}>
          <div style={{ fontSize: 12.5, fontWeight: 700, color: palette.textPrimary, fontFamily: "monospace" }}>
            {claim.claim_id}
          </div>
          <div style={{ fontSize: 11.5, color: palette.textMuted, marginTop: 2 }}>
            {claim.submission.claimant.name} · {formatINR(claim.submission.claim_amount)}
          </div>
        </div>

        {/* Pipeline dots */}
        <div style={{ display: "flex", gap: 6, alignItems: "center", flex: 1 }}>
          {PIPELINE.map(({ key, short, color }) => {
            const entry = agentMap.get(key);
            const done = !!entry && entry.action !== "DEMO_SEED";
            const failed = done && entry.action.includes("FAIL");
            return (
              <div key={key} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 3 }}>
                {done && !failed ? (
                  <CheckmarkCircle20Filled style={{ color: palette.success, fontSize: 16 }} />
                ) : done && failed ? (
                  <DismissCircle20Filled style={{ color: palette.danger, fontSize: 16 }} />
                ) : (
                  <Circle20Regular style={{ color: palette.glassBorder, fontSize: 16 }} />
                )}
                <span style={{ fontSize: 9.5, color: done ? color : palette.textMuted, fontWeight: 600 }}>{short}</span>
              </div>
            );
          })}
        </div>

        {/* Status + decision */}
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <StatusBadge value={claim.status ?? "Processing"} size="sm" />
          {fraud && (
            <span style={{
              fontSize: 11, fontWeight: 600, padding: "2px 8px", borderRadius: 999,
              background: fraud.fraud_score < 30 ? palette.successSoft : palette.warningSoft,
              color: fraud.fraud_score < 30 ? palette.success : palette.warning,
              border: `1px solid ${fraud.fraud_score < 30 ? palette.success : palette.warning}40`,
            }}>
              Fraud {fraud.fraud_score}
            </span>
          )}
          <ArrowRight16Regular style={{ color: palette.textMuted }} />
        </div>
      </div>

      {/* Confidence bar if adjudication done */}
      {adj && (
        <div style={{ marginTop: 10, display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 11, color: palette.textMuted, flexShrink: 0 }}>Confidence</span>
          <div style={{ flex: 1, height: 3, borderRadius: 2, background: palette.glassFill, overflow: "hidden" }}>
            <div style={{ width: `${adj.confidence_score * 100}%`, height: "100%", background: palette.brand, borderRadius: 2 }} />
          </div>
          <span style={{ fontSize: 11, color: palette.textMuted, flexShrink: 0 }}>{Math.round(adj.confidence_score * 100)}%</span>
        </div>
      )}
    </GlassCard>
  );
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <GlassCard style={{ padding: "16px 20px" }}>
      <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: "0.07em", textTransform: "uppercase", color: palette.textMuted, marginBottom: 8 }}>
        {label}
      </div>
      <div style={{ fontSize: 28, fontWeight: 800, color }}>{value}</div>
    </GlassCard>
  );
}
