import { useState, useMemo } from "react";
import { Search20Regular, Filter20Regular } from "@fluentui/react-icons";
import { AppLayout } from "@/components/layout/AppLayout";
import { GlassCard } from "@/components/common/GlassCard";
import { ClaimsTable } from "@/components/dashboard/ClaimsTable";
import { Skeleton } from "@/components/common/Skeleton";
import { useClaimsData } from "@/hooks/useClaimsData";
import { palette } from "@/theme/tokens";
import type { ClaimType, ClaimStatus } from "@/api/types";

const TYPES: (ClaimType | "All")[] = ["All", "Health", "Motor", "Property", "Travel"];
const STATUSES: (ClaimStatus | "All")[] = ["All", "Approved", "Rejected", "Under Human Review", "Pending Information", "Processing"];

export function ClaimsRegister() {
  const { claims, isLoading } = useClaimsData();
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<ClaimType | "All">("All");
  const [statusFilter, setStatusFilter] = useState<ClaimStatus | "All">("All");

  const filtered = useMemo(() => {
    return claims.filter((c) => {
      const q = search.toLowerCase();
      const matchSearch =
        !q ||
        c.claim_id.toLowerCase().includes(q) ||
        (c.claimant_name ?? "").toLowerCase().includes(q);
      const matchType = typeFilter === "All" || c.claim_type === typeFilter;
      const matchStatus = statusFilter === "All" || c.status === statusFilter;
      return matchSearch && matchType && matchStatus;
    });
  }, [claims, search, typeFilter, statusFilter]);

  return (
    <AppLayout title="Claims Register" subtitle={`${claims.length} claims · searchable and filterable`}>
      {/* Search + filters */}
      <GlassCard style={{ marginBottom: 16, padding: "14px 18px" }}>
        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          {/* Search bar */}
          <div style={{
            display: "flex", alignItems: "center", gap: 8, flex: 1, minWidth: 220,
            padding: "8px 12px", borderRadius: 8,
            background: palette.glassFill, border: `1px solid ${palette.glassBorder}`,
          }}>
            <Search20Regular style={{ color: palette.textMuted, flexShrink: 0 }} />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by claim ID or claimant name…"
              style={{
                background: "none", border: "none", outline: "none",
                fontSize: 13.5, color: palette.textPrimary, width: "100%",
                fontFamily: "inherit",
              }}
            />
          </div>

          {/* Type filter */}
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <Filter20Regular style={{ color: palette.textMuted, fontSize: 15 }} />
            <div style={{ display: "flex", gap: 6 }}>
              {TYPES.map((t) => (
                <Chip key={t} label={t} active={typeFilter === t} onClick={() => setTypeFilter(t as ClaimType | "All")} />
              ))}
            </div>
          </div>
        </div>

        {/* Status filter row */}
        <div style={{ display: "flex", gap: 6, marginTop: 10, flexWrap: "wrap" }}>
          {STATUSES.map((s) => (
            <Chip key={s} label={s} active={statusFilter === s} onClick={() => setStatusFilter(s as ClaimStatus | "All")} small />
          ))}
        </div>
      </GlassCard>

      {/* Results count */}
      <div style={{ fontSize: 12.5, color: palette.textMuted, marginBottom: 10 }}>
        {isLoading ? "Loading…" : `${filtered.length} of ${claims.length} claims`}
        {(search || typeFilter !== "All" || statusFilter !== "All") && (
          <button
            onClick={() => { setSearch(""); setTypeFilter("All"); setStatusFilter("All"); }}
            style={{ marginLeft: 10, background: "none", border: "none", color: palette.brand, cursor: "pointer", fontSize: 12.5 }}
          >
            Clear filters
          </button>
        )}
      </div>

      <GlassCard style={{ padding: 0, overflow: "hidden" }}>
        {isLoading ? (
          <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 12 }}>
            {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} height={44} />)}
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: 48, textAlign: "center", color: palette.textMuted, fontSize: 14 }}>
            No claims match the current filters.
          </div>
        ) : (
          <ClaimsTable claims={filtered} />
        )}
      </GlassCard>
    </AppLayout>
  );
}

function Chip({ label, active, onClick, small }: {
  label: string; active: boolean; onClick: () => void; small?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: small ? "3px 10px" : "4px 12px",
        borderRadius: 999,
        fontSize: small ? 11 : 12,
        fontWeight: 600,
        cursor: "pointer",
        border: `1px solid ${active ? palette.brand : palette.glassBorder}`,
        background: active ? palette.brandSoft : palette.glassFill,
        color: active ? palette.brand : palette.textSecondary,
        transition: "all 0.12s",
      }}
    >
      {label}
    </button>
  );
}
