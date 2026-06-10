import { useMemo } from "react";
import type { ClaimListItem } from "@/api/types";
import { getPalette, statusColor } from "@/theme/tokens";
import { useTheme } from "@/contexts/ThemeContext";
import { formatINR, timeAgo } from "@/utils/format";

/** Derives a human-readable activity stream from the most recent claims. */
function buildActivity(claims: ClaimListItem[]) {
  return claims.slice(0, 7).map((c) => {
    const dec = (c.decision ?? "").toLowerCase();
    let text: string;
    if (dec.includes("approv"))
      text = `${c.claim_id} approved — ${formatINR(c.final_payout ?? 0, true)} payout initiated`;
    else if (dec.includes("reject")) text = `${c.claim_id} rejected — policy exclusion applied`;
    else if (dec.includes("escalat"))
      text = `${c.claim_id} escalated — fraud score ${c.fraud_score ?? 0}/100`;
    else text = `${c.claim_id} received and processing`;
    return {
      id: c.claim_id,
      color: statusColor(c.decision ?? c.status ?? ""),
      text,
      time: timeAgo(c.submitted_at),
    };
  });
}

export function ActivityFeed({ claims }: { claims: ClaimListItem[] }) {
  const items = useMemo(() => buildActivity(claims), [claims]);
  const { theme } = useTheme();
  const palette = getPalette(theme);

  return (
    <div>
      {items.map((it, i) => (
        <div
          key={it.id}
          style={{
            display: "flex",
            gap: 11,
            alignItems: "flex-start",
            padding: "9px 0",
            borderBottom: i < items.length - 1 ? `1px solid ${palette.glassBorder}` : "none",
          }}
        >
          <span
            style={{
              width: 7,
              height: 7,
              borderRadius: "50%",
              background: it.color,
              marginTop: 5,
              flexShrink: 0,
              boxShadow: `0 0 8px ${it.color}99`,
            }}
          />
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: 12.5, color: palette.textSecondary, lineHeight: 1.45 }}>{it.text}</div>
            <div style={{ fontSize: 11, color: palette.textMuted, marginTop: 2 }}>{it.time}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
