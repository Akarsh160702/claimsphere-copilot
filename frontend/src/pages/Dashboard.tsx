import {
  DocumentBulletList20Regular,
  CheckmarkCircle20Regular,
  Warning20Regular,
  DismissCircle20Regular,
  Money20Regular,
  Timer20Regular,
  ShieldCheckmark20Regular,
  Target20Regular,
} from "@fluentui/react-icons";
import { AppLayout } from "@/components/layout/AppLayout";
import { GlassCard } from "@/components/common/GlassCard";
import { SectionHeader } from "@/components/common/SectionHeader";
import { Skeleton } from "@/components/common/Skeleton";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { ImpactBand } from "@/components/dashboard/ImpactBand";
import { ClaimsVolumeChart } from "@/components/dashboard/ClaimsVolumeChart";
import { DecisionDonut } from "@/components/dashboard/DecisionDonut";
import { TypeBar } from "@/components/dashboard/TypeBar";
import { ClaimsTable } from "@/components/dashboard/ClaimsTable";
import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import { useClaimsData } from "@/hooks/useClaimsData";
import { palette } from "@/theme/tokens";
import { formatINR } from "@/utils/format";

export function Dashboard() {
  const { claims, metrics, isLoading } = useClaimsData();

  return (
    <AppLayout
      title="Claims Dashboard"
      subtitle="AI-powered claims processing overview · Azure AI Foundry"
    >
      {isLoading ? (
        <LoadingState />
      ) : (
        <>
          {/* KPI row 1 */}
          <div style={kpiGrid}>
            <KpiCard label="Total Claims" value={metrics.total} delta="+3 today" trend="up" icon={DocumentBulletList20Regular} accent={palette.brand} delay={0.02} />
            <KpiCard label="Approved" value={metrics.approved} delta={`${metrics.stpRate}% STP`} trend="up" icon={CheckmarkCircle20Regular} accent={palette.success} delay={0.06} />
            <KpiCard label="Escalated" value={metrics.escalated} delta="Pending review" trend="neutral" icon={Warning20Regular} accent={palette.warning} delay={0.1} />
            <KpiCard label="Rejected" value={metrics.rejected} delta="Policy exclusion" trend="down" icon={DismissCircle20Regular} accent={palette.danger} delay={0.14} />
          </div>

          {/* KPI row 2 */}
          <div style={{ ...kpiGrid, marginTop: 16 }}>
            <KpiCard label="Total Payout" value={formatINR(metrics.totalPayout, true)} delta="+18% vs last week" trend="up" icon={Money20Regular} accent={palette.brand} delay={0.02} />
            <KpiCard label="Avg TAT" value="3.1s" delta="0.8s faster" trend="up" icon={Timer20Regular} accent={palette.info} delay={0.06} />
            <KpiCard label="Avg Fraud Score" value={`${metrics.avgFraud}/100`} delta="Low-risk portfolio" trend="up" icon={ShieldCheckmark20Regular} accent={palette.brand} delay={0.1} />
            <KpiCard label="AI Accuracy" value="97.3%" delta="+1.2% this month" trend="up" icon={Target20Regular} accent={palette.success} delay={0.14} />
          </div>

          {/* Business impact — translates STP rate into ROI for judges/execs */}
          <ImpactBand metrics={metrics} />

          {/* Charts + feed */}
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16, marginTop: 16, alignItems: "start" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <GlassCard delay={0.05}>
                <SectionHeader title="Claims Volume — Last 14 Days" live />
                <ClaimsVolumeChart claims={claims} />
              </GlassCard>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                <GlassCard delay={0.1}>
                  <SectionHeader title="Decision Split" />
                  <DecisionDonut metrics={metrics} />
                </GlassCard>
                <GlassCard delay={0.14}>
                  <SectionHeader title="By Claim Type" />
                  <TypeBar metrics={metrics} />
                </GlassCard>
              </div>
            </div>

            <GlassCard delay={0.08}>
              <SectionHeader title="Live Activity" live />
              <ActivityFeed claims={claims} />
            </GlassCard>
          </div>

          {/* Claims table */}
          <GlassCard delay={0.1} style={{ marginTop: 16 }}>
            <SectionHeader
              title="Recent Claims"
              right={
                <span style={{ fontSize: 12, color: palette.textMuted }}>
                  {claims.length} claims · click a row for detail
                </span>
              }
            />
            <ClaimsTable claims={claims.slice(0, 10)} />
          </GlassCard>
        </>
      )}
    </AppLayout>
  );
}

const kpiGrid: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(4, 1fr)",
  gap: 16,
};

function LoadingState() {
  return (
    <>
      <div style={kpiGrid}>
        {Array.from({ length: 4 }).map((_, i) => (
          <GlassCard key={i} style={{ height: 116 }}>
            <Skeleton width={90} height={11} />
            <Skeleton width={70} height={26} style={{ marginTop: 14 }} />
            <Skeleton width={110} height={11} style={{ marginTop: 12 }} />
          </GlassCard>
        ))}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16, marginTop: 16 }}>
        <GlassCard style={{ height: 300 }}>
          <Skeleton width={220} height={14} />
          <Skeleton height={230} style={{ marginTop: 16 }} />
        </GlassCard>
        <GlassCard style={{ height: 300 }}>
          <Skeleton width={120} height={14} />
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} height={36} style={{ marginTop: 12 }} />
          ))}
        </GlassCard>
      </div>
    </>
  );
}
