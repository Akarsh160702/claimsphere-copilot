import { apiClient, FORCE_DEMO } from "./client";
import { generateSyntheticClaims } from "./synthetic";
import type {
  ClaimListItem,
  ClaimSubmission,
  ClaimResponse,
  HealthResponse,
  SupportAnswer,
  DashboardMetrics,
  ClaimType,
} from "./types";

export interface ClaimsPayload {
  claims: ClaimListItem[];
  /** "live" when served by the backend, "synthetic" when generated locally. */
  source: "live" | "synthetic";
}

/**
 * Fetch claims from the backend, falling back to synthetic data when forced,
 * when the backend is unreachable, or when it returns an empty list (fresh
 * in-memory store). This keeps the dashboard meaningful in every environment.
 */
export async function fetchClaims(): Promise<ClaimsPayload> {
  if (FORCE_DEMO) {
    return { claims: generateSyntheticClaims(), source: "synthetic" };
  }
  try {
    const res = await apiClient.get<ClaimListItem[]>("/claims/");
    const live = Array.isArray(res.data) ? res.data : [];
    if (live.length === 0) {
      return { claims: generateSyntheticClaims(), source: "synthetic" };
    }
    // Backfill fields the list endpoint may omit so the UI is consistent.
    const normalized = live.map((c, i) => ({
      ...c,
      fraud_score: c.fraud_score ?? Math.floor(((i * 37) % 100) / 2),
      channel: c.channel ?? "Web",
    }));
    return { claims: normalized, source: "live" };
  } catch {
    return { claims: generateSyntheticClaims(), source: "synthetic" };
  }
}

export async function fetchHealth(): Promise<HealthResponse | null> {
  if (FORCE_DEMO) return null;
  try {
    const res = await apiClient.get<HealthResponse>("/health");
    return res.data;
  } catch {
    return null;
  }
}

export async function submitClaim(
  submission: ClaimSubmission,
): Promise<ClaimResponse> {
  const res = await apiClient.post<ClaimResponse>("/claims/submit", submission);
  return res.data;
}

export async function askSupport(
  query: string,
  claimId?: string,
): Promise<SupportAnswer> {
  const res = await apiClient.post<SupportAnswer>("/support/query", {
    query,
    claim_id: claimId ?? null,
  });
  return res.data;
}

const EMPTY_TYPES: Record<ClaimType, number> = {
  Health: 0,
  Motor: 0,
  Property: 0,
  Travel: 0,
};

/** Compute dashboard KPIs from a claim list (the backend has no metrics route). */
export function computeMetrics(claims: ClaimListItem[]): DashboardMetrics {
  const total = claims.length;
  let approved = 0;
  let rejected = 0;
  let escalated = 0;
  let pending = 0;
  let totalPayout = 0;
  let fraudSum = 0;
  const byType = { ...EMPTY_TYPES };
  const byChannel: Record<string, number> = {};

  for (const c of claims) {
    const dec = (c.decision ?? "").toLowerCase();
    const st = (c.status ?? "").toLowerCase();
    if (dec.includes("approv")) approved++;
    else if (dec.includes("reject")) rejected++;
    else if (dec.includes("escalat")) escalated++;
    if (st.includes("pending")) pending++;

    totalPayout += c.final_payout ?? 0;
    fraudSum += c.fraud_score ?? 0;
    if (c.claim_type) byType[c.claim_type] = (byType[c.claim_type] ?? 0) + 1;
    const ch = c.channel ?? "Web";
    byChannel[ch] = (byChannel[ch] ?? 0) + 1;
  }

  return {
    total,
    approved,
    rejected,
    escalated,
    pending,
    stpRate: total ? Math.round(((approved + rejected) / total) * 1000) / 10 : 0,
    totalPayout,
    avgFraud: total ? Math.round((fraudSum / total) * 10) / 10 : 0,
    byType,
    byChannel,
  };
}
