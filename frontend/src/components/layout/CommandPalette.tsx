import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search20Regular,
  DocumentBulletList20Regular,
  ArrowRight16Regular,
  type FluentIcon,
} from "@fluentui/react-icons";
import { getPalette, typeColor, statusColor } from "@/theme/tokens";
import { useTheme } from "@/contexts/ThemeContext";
import { useAppStore } from "@/store/useAppStore";
import { useClaimsData } from "@/hooks/useClaimsData";
import { NAV_ITEMS } from "./navItems";

interface Result {
  id: string;
  group: "Claims" | "Go to";
  label: string;
  sublabel?: string;
  icon: FluentIcon;
  /** Accent dot color (claims: type/decision hue). */
  dot?: string;
  /** Right-aligned hint (e.g. amount or status). */
  meta?: string;
  metaColor?: string;
  onSelect: () => void;
}

/**
 * Global ⌘K / Ctrl-K command palette.
 *
 * Real, working search across the live claims list (by id, claimant, type,
 * status, decision) plus quick navigation. Fully keyboard-driven — this is the
 * functional replacement for the old decorative search box in the TopBar.
 */
export function CommandPalette() {
  const open = useAppStore((s) => s.commandOpen);
  const setOpen = useAppStore((s) => s.setCommandOpen);
  const navigate = useNavigate();
  const { claims } = useClaimsData();
  const { theme } = useTheme();
  const palette = getPalette(theme);

  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Reset state each time the palette opens.
  useEffect(() => {
    if (open) {
      setQuery("");
      setActive(0);
      // Focus after the entrance animation paints.
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [open]);

  const go = (path: string) => {
    setOpen(false);
    navigate(path);
  };

  const results = useMemo<Result[]>(() => {
    const q = query.trim().toLowerCase();

    // Claim matches — search id, claimant, type, status, decision.
    const claimMatches = claims
      .filter((c) => {
        if (!q) return true;
        return (
          c.claim_id.toLowerCase().includes(q) ||
          (c.claimant_name ?? "").toLowerCase().includes(q) ||
          (c.claim_type ?? "").toLowerCase().includes(q) ||
          (c.status ?? "").toLowerCase().includes(q) ||
          (c.decision ?? "").toLowerCase().includes(q)
        );
      })
      .slice(0, q ? 8 : 5)
      .map<Result>((c) => ({
        id: `claim-${c.claim_id}`,
        group: "Claims",
        label: c.claim_id,
        sublabel: `${c.claimant_name ?? "Unknown"} · ${c.claim_type ?? "—"}`,
        icon: DocumentBulletList20Regular,
        dot: typeColor(c.claim_type),
        meta: c.decision ?? c.status ?? undefined,
        metaColor: statusColor(c.decision ?? c.status ?? ""),
        onSelect: () => go(`/claims/${c.claim_id}`),
      }));

    // Navigation matches.
    const navMatches = NAV_ITEMS.filter(
      (n) => !q || n.label.toLowerCase().includes(q),
    ).map<Result>((n) => ({
      id: `nav-${n.path}`,
      group: "Go to",
      label: n.label,
      sublabel: n.path,
      icon: n.icon,
      onSelect: () => go(n.path),
    }));

    return [...claimMatches, ...navMatches];
  }, [query, claims]); // eslint-disable-line react-hooks/exhaustive-deps

  // Keep the active index in range as results change.
  useEffect(() => {
    setActive((a) => Math.min(a, Math.max(0, results.length - 1)));
  }, [results.length]);

  // Scroll the active row into view.
  useEffect(() => {
    const el = listRef.current?.querySelector<HTMLElement>(`[data-idx="${active}"]`);
    el?.scrollIntoView({ block: "nearest" });
  }, [active]);

  // Global open shortcut + in-palette navigation.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      // Open with ⌘K / Ctrl-K from anywhere.
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen(true);
        return;
      }
      if (!open) return;

      if (e.key === "Escape") {
        e.preventDefault();
        setOpen(false);
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setActive((a) => Math.min(a + 1, results.length - 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setActive((a) => Math.max(a - 1, 0));
      } else if (e.key === "Enter") {
        e.preventDefault();
        results[active]?.onSelect();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, results, active, setOpen]);

  // Build kbd style inline so it can reference palette
  const kbdStyle: React.CSSProperties = {
    fontSize: 10.5,
    fontWeight: 600,
    fontFamily: "inherit",
    padding: "2px 6px",
    borderRadius: 5,
    background: theme === "light" ? "rgba(0,0,0,0.05)" : "rgba(255,255,255,0.05)",
    border: `1px solid ${palette.glassBorder}`,
    color: palette.textMuted,
    minWidth: 16,
    textAlign: "center",
    lineHeight: 1.4,
  };

  // Render section headers inline by tracking group changes.
  let lastGroup = "";

  return createPortal(
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.14 }}
          onMouseDown={() => setOpen(false)}
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 1000,
            background: theme === "light" ? "rgba(15, 23, 42, 0.45)" : "rgba(4, 7, 14, 0.62)",
            backdropFilter: "blur(4px)",
            WebkitBackdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "center",
            paddingTop: "12vh",
          }}
        >
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.985 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.985 }}
            transition={{ type: "spring", stiffness: 320, damping: 30 }}
            onMouseDown={(e) => e.stopPropagation()}
            className="cs-glass"
            style={{
              width: "min(620px, 92vw)",
              maxHeight: "70vh",
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
              padding: 0,
              borderRadius: 16,
            }}
          >
            {/* Search input */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: "16px 18px",
                borderBottom: `1px solid ${palette.glassBorder}`,
              }}
            >
              <Search20Regular style={{ color: palette.textMuted, flexShrink: 0 }} />
              <input
                ref={inputRef}
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setActive(0);
                }}
                placeholder="Search claims by ID, claimant, type, status — or jump to a page…"
                style={{
                  flex: 1,
                  background: "none",
                  border: "none",
                  outline: "none",
                  fontSize: 15,
                  color: palette.textPrimary,
                  fontFamily: "inherit",
                }}
              />
              <kbd style={kbdStyle}>esc</kbd>
            </div>

            {/* Results */}
            <div ref={listRef} style={{ overflowY: "auto", padding: 8 }}>
              {results.length === 0 ? (
                <div
                  style={{
                    padding: "36px 18px",
                    textAlign: "center",
                    color: palette.textMuted,
                    fontSize: 13.5,
                  }}
                >
                  No matches for "{query}". Try a claim ID, a name, or a page.
                </div>
              ) : (
                results.map((r, i) => {
                  const showHeader = r.group !== lastGroup;
                  lastGroup = r.group;
                  const isActive = i === active;
                  return (
                    <div key={r.id}>
                      {showHeader && (
                        <div
                          style={{
                            fontSize: 10.5,
                            fontWeight: 700,
                            letterSpacing: "0.08em",
                            textTransform: "uppercase",
                            color: palette.textMuted,
                            padding: "10px 12px 6px",
                          }}
                        >
                          {r.group}
                        </div>
                      )}
                      <div
                        data-idx={i}
                        onMouseEnter={() => setActive(i)}
                        onMouseDown={(e) => {
                          e.preventDefault();
                          r.onSelect();
                        }}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 12,
                          padding: "9px 12px",
                          borderRadius: 10,
                          cursor: "pointer",
                          background: isActive ? palette.brandSoft : "transparent",
                          border: `1px solid ${isActive ? palette.brand + "55" : "transparent"}`,
                          transition: "background 0.1s",
                        }}
                      >
                        <div
                          style={{
                            position: "relative",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            color: isActive ? palette.brand : palette.textMuted,
                            flexShrink: 0,
                          }}
                        >
                          <r.icon />
                          {r.dot && (
                            <span
                              style={{
                                position: "absolute",
                                right: -2,
                                bottom: -2,
                                width: 7,
                                height: 7,
                                borderRadius: "50%",
                                background: r.dot,
                                border: `1.5px solid ${palette.bgBase}`,
                              }}
                            />
                          )}
                        </div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div
                            style={{
                              fontSize: 13.5,
                              fontWeight: 600,
                              color: palette.textPrimary,
                              whiteSpace: "nowrap",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                            }}
                          >
                            {r.label}
                          </div>
                          {r.sublabel && (
                            <div style={{ fontSize: 11.5, color: palette.textMuted, marginTop: 1 }}>
                              {r.sublabel}
                            </div>
                          )}
                        </div>
                        {r.meta && (
                          <span
                            style={{
                              fontSize: 11,
                              fontWeight: 600,
                              color: r.metaColor ?? palette.textMuted,
                              whiteSpace: "nowrap",
                            }}
                          >
                            {r.meta}
                          </span>
                        )}
                        {isActive && (
                          <ArrowRight16Regular style={{ color: palette.brand, flexShrink: 0 }} />
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Footer hints */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 16,
                padding: "10px 16px",
                borderTop: `1px solid ${palette.glassBorder}`,
                fontSize: 11,
                color: palette.textMuted,
              }}
            >
              <Hint keys={["↑", "↓"]} label="navigate" kbdStyle={kbdStyle} />
              <Hint keys={["↵"]} label="open" kbdStyle={kbdStyle} />
              <Hint keys={["esc"]} label="close" kbdStyle={kbdStyle} />
              <span style={{ marginLeft: "auto", color: palette.textMuted }}>
                {claims.length} claims indexed
              </span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body,
  );
}

function Hint({ keys, label, kbdStyle }: { keys: string[]; label: string; kbdStyle: React.CSSProperties }) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
      {keys.map((k) => (
        <kbd key={k} style={kbdStyle}>
          {k}
        </kbd>
      ))}
      <span>{label}</span>
    </span>
  );
}
