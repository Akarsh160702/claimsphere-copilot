import type {
  Channel,
  ClaimListItem,
  ClaimType,
  Decision,
  ClaimStatus,
} from "./types";

/**
 * Deterministic synthetic dataset (50 claims) used when the backend returns no
 * claims or is unreachable, so the dashboard is always demo-ready. All data is
 * fictional — no real PII.
 */

const FIRST = [
  "Arjun", "Sneha", "Vikram", "Priya", "Ravi", "Anita", "Suresh", "Meera",
  "Karthik", "Divya", "Rohan", "Neha", "Aditya", "Pooja", "Manish", "Kavya",
  "Sanjay", "Isha", "Vivek", "Tara",
];
const LAST = [
  "Mehta", "Reddy", "Nair", "Kumar", "Sharma", "Pillai", "Iyer", "Singh",
  "Gupta", "Rao", "Desai", "Menon", "Joshi", "Bose", "Shetty",
];
const TYPES: ClaimType[] = ["Health", "Motor", "Property", "Travel"];
const CHANNELS: Channel[] = ["Web", "Teams", "Email", "CSR", "Phone"];

/** Small seeded PRNG (mulberry32) for stable output across reloads. */
function rng(seed: number) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const pick = <T,>(arr: T[], r: number) => arr[Math.floor(r * arr.length)];

export function generateSyntheticClaims(count = 50): ClaimListItem[] {
  const rand = rng(20260603);
  const out: ClaimListItem[] = [];

  for (let i = 0; i < count; i++) {
    const type = pick(TYPES, rand());
    const channel = pick(CHANNELS, rand());
    const claimant = `${pick(FIRST, rand())} ${pick(LAST, rand())}`;

    const base =
      type === "Motor"
        ? 60000 + rand() * 900000
        : type === "Property"
        ? 80000 + rand() * 600000
        : type === "Health"
        ? 15000 + rand() * 250000
        : 8000 + rand() * 90000;
    const amount = Math.round(base / 1000) * 1000;

    const fraud = Math.min(
      98,
      Math.round(rand() < 0.78 ? rand() * 35 : 45 + rand() * 53),
    );

    let decision: Decision;
    let status: ClaimStatus;
    if (fraud >= 60) {
      decision = "Escalate";
      status = "Under Human Review";
    } else if (rand() < 0.16) {
      decision = "Reject";
      status = "Rejected";
    } else {
      decision = "Approve";
      status = "Approved";
    }

    const payout =
      decision === "Approve" ? Math.round(amount * (0.88 + rand() * 0.1)) : 0;

    // Spread claims across the last 14 days ending today, so the volume chart
    // always runs up to the current date.
    const daysAgo = Math.floor(rand() * 14);
    const d = new Date();
    d.setDate(d.getDate() - daysAgo);
    d.setHours(8 + Math.floor(rand() * 10), Math.floor(rand() * 60), 0, 0);

    const seq = String(count - i).padStart(3, "0");
    const ds = `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(
      d.getDate(),
    ).padStart(2, "0")}`;

    out.push({
      claim_id: `CLM-${ds}-${seq}`,
      status,
      claim_type: type,
      claim_amount: amount,
      claimant_name: claimant,
      submitted_at: d.toISOString(),
      decision,
      final_payout: payout,
      fraud_score: fraud,
      channel,
    });
  }

  return out.sort(
    (a, b) =>
      new Date(b.submitted_at ?? 0).getTime() -
      new Date(a.submitted_at ?? 0).getTime(),
  );
}
