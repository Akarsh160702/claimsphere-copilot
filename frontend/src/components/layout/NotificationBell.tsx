import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Alert20Regular, ChevronRight16Regular } from "@fluentui/react-icons";
import { palette, typeColor } from "@/theme/tokens";
import { formatINR, timeAgo } from "@/utils/format";
import { useClaimsData } from "@/hooks/useClaimsData";
import type { ClaimListItem } from "@/api/types";

/** True for claims awaiting a human decision. */
function isEscalated(c: ClaimListItem): boolean {
  const s = (c.status ?? "").toLowerCase();
  const d = (c.decision ?? "").toLowerCase();
  return s.includes("review") || s.includes("escalat") || d.includes("escalat");
}

/**
 * Notification bell — opens a panel of claims escalated for human review.
 * Previously a dead button; now a live work-queue shortcut.
 */
export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const { claims } = useClaimsData();

  const escalated = claims
    .filter(isEscalated)
    .sort(
      (a, b) =>
        new Date(b.submitted_at ?? 0).getTime() -
        new Date(a.submitted_at ?? 0).getTime(),
    );
  const count = escalated.length;

  const goTo = (path: string) => {
    setOpen(false);
    navigate(path);
  };

  return (
    <div style={{ position: "relative" }}>
      <button
        aria-label={`Notifications — ${count} claims awaiting review`}
        onClick={() => setOpen((v) => !v)}
        style={{
          position: "relative",
          width: 38,
          height: 38,
          borderRadius: 10,
          background: open ? palette.glassFillStrong : palette.glassFill,
          border: `1px solid ${open ? palette.glassBorderStrong : palette.glassBorder}`,
          color: palette.textSecondary,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
          transition: "background 0.15s, border-color 0.15s",
        }}
      >
        <Alert20Regular />
        {count > 0 && (
          <span
            style={{
              position: "absolute",
              top: -5,
              right: -5,
              minWidth: 17,
              height: 17,
              padding: "0 4px",
              borderRadius: 999,
              background: palette.warning,
              color: "#1a1205",
              fontSize: 10.5,
              fontWeight: 800,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              border: `2px solid ${palette.bgBase}`,
            }}
          >
            {count > 9 ? "9+" : count}
          </span>
        )}
      </button>

      <AnimatePresence>
        {open && (
          <>
            {/* click-catcher */}
            <div
              onClick={() => setOpen(false)}
              style={{ position: "fixed", inset: 0, zIndex: 90 }}
            />
            <motion.div
              initial={{ opacity: 0, y: -8, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.98 }}
              transition={{ type: "spring", stiffness: 360, damping: 28 }}
              className="cs-glass"
              style={{
                position: "absolute",
                top: 46,
                right: 0,
                width: 340,
                zIndex: 91,
                padding: 0,
                overflow: "hidden",
                borderRadius: 14,
              }}
            >
              {/* header */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "13px 16px",
                  borderBottom: `1px solid ${palette.glassBorder}`,
                }}
              >
                <span style={{ fontSize: 13, fontWeight: 700, color: palette.textPrimary }}>
                  Human Review Queue
                </span>
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    color: count > 0 ? palette.warning : palette.textMuted,
                    background: count > 0 ? palette.warningSoft : palette.glassFill,
                    border: `1px solid ${count > 0 ? palette.warning + "40" : palette.glassBorder}`,
                    padding: "2px 9px",
                    borderRadius: 999,
                  }}
                >
                  {count} pending
                </span>
              </div>

              {/* list */}
              <div style={{ maxHeight: 320, overflowY: "auto" }}>
                {count === 0 ? (
                  <div
                    style={{
                      padding: "30px 18px",
                      textAlign: "center",
                      color: palette.textMuted,
                      fontSize: 12.5,
                      lineHeight: 1.6,
                    }}
                  >
                    No claims awaiting review.
                    <br />
                    Everything is straight-through right now.
                  </div>
                ) : (
                  escalated.slice(0, 6).map((c) => {
                    const color = typeColor(c.claim_type);
                    return (
                      <button
                        key={c.claim_id}
                        onClick={() => goTo(`/claims/${c.claim_id}`)}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 11,
                          width: "100%",
                          padding: "11px 16px",
                          background: "none",
                          border: "none",
                          borderBottom: `1px solid ${palette.glassBorder}`,
                          cursor: "pointer",
                          textAlign: "left",
                          fontFamily: "inherit",
                          transition: "background 0.12s",
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.03)")}
                        onMouseLeave={(e) => (e.currentTarget.style.background = "none")}
                      >
                        <span
                          style={{
                            width: 8,
                            height: 8,
                            borderRadius: "50%",
                            background: color,
                            flexShrink: 0,
                          }}
                        />
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: 12.5, fontWeight: 600, color: palette.textPrimary }}>
                            {c.claimant_name ?? "Unknown"}
                            <span style={{ color: palette.textMuted, fontWeight: 400 }}>
                              {" · "}
                              {c.claim_type ?? "—"}
                            </span>
                          </div>
                          <div style={{ fontSize: 11, color: palette.textMuted, marginTop: 1 }}>
                            {c.claim_id} · {timeAgo(c.submitted_at)}
                          </div>
                        </div>
                        <span style={{ fontSize: 12.5, fontWeight: 700, color: palette.textSecondary, whiteSpace: "nowrap" }}>
                          {formatINR(c.claim_amount ?? 0, true)}
                        </span>
                      </button>
                    );
                  })
                )}
              </div>

              {/* footer */}
              <button
                onClick={() => goTo("/review")}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 4,
                  width: "100%",
                  padding: "11px 16px",
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  fontFamily: "inherit",
                  fontSize: 12.5,
                  fontWeight: 600,
                  color: palette.brand,
                }}
              >
                Open Review Queue
                <ChevronRight16Regular />
              </button>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
