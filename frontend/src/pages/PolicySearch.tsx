import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Search20Regular, Bot20Regular } from "@fluentui/react-icons";
import { AppLayout } from "@/components/layout/AppLayout";
import { GlassCard } from "@/components/common/GlassCard";
import { Skeleton } from "@/components/common/Skeleton";
import { getPalette, typeColor } from "@/theme/tokens";
import { useTheme } from "@/contexts/ThemeContext";
import { formatINR } from "@/utils/format";
import { askSupport, fetchPolicies } from "@/api/claims";

const SUGGESTED = [
  "What does my health policy cover for hospitalization?",
  "What are the motor policy exclusions?",
  "Is cosmetic surgery covered under health insurance?",
  "What is the room rent limit under POL-HEALTH-001?",
  "Does the property policy cover earthquake damage?",
];

export function PolicySearch() {
  const [query, setQuery] = useState("");
  const [selectedPolicy, setSelectedPolicy] = useState("POL-HEALTH-001");
  const { theme } = useTheme();
  const palette = getPalette(theme);

  const { data: policies = [], isLoading: policiesLoading } = useQuery({
    queryKey: ["policies"],
    queryFn: fetchPolicies,
    staleTime: 300000,
  });

  const { mutate: search, data: answer, isPending, reset } = useMutation({
    mutationFn: () => askSupport(query, selectedPolicy || undefined),
  });

  function handleSearch(q?: string) {
    const q2 = q ?? query;
    if (!q2.trim()) return;
    if (q) setQuery(q);
    setTimeout(() => search(), 0);
  }

  const labelStyle: React.CSSProperties = {
    display: "block", fontSize: 11, fontWeight: 700, letterSpacing: "0.07em",
    textTransform: "uppercase", color: palette.textMuted, marginBottom: 7,
  };

  const inputStyle: React.CSSProperties = {
    width: "100%", padding: "9px 12px", borderRadius: 8, fontSize: 13.5,
    background: palette.glassFill, border: `1px solid ${palette.glassBorder}`,
    color: palette.textPrimary, outline: "none", boxSizing: "border-box", fontFamily: "inherit",
  };

  return (
    <AppLayout title="Policy Search" subtitle="Ask questions about policies using Azure AI Search + RAG">
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16, alignItems: "start" }}>
        {/* Main search panel */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <GlassCard>
            {/* Policy selector */}
            <div style={{ marginBottom: 14 }}>
              <label style={labelStyle}>Policy context</label>
              <select
                value={selectedPolicy}
                onChange={(e) => setSelectedPolicy(e.target.value)}
                style={inputStyle}
              >
                <option value="">All policies</option>
                {(policies as Array<{ policy_id: string; policy_type: string; holder_name: string }>).map((p) => (
                  <option key={p.policy_id} value={p.policy_id}>
                    {p.policy_id} — {p.policy_type} ({p.holder_name})
                  </option>
                ))}
              </select>
            </div>

            {/* Search input */}
            <label style={labelStyle}>Your question</label>
            <div style={{ display: "flex", gap: 10 }}>
              <div style={{
                flex: 1, display: "flex", alignItems: "center", gap: 10,
                padding: "10px 14px", borderRadius: 10,
                background: palette.glassFill, border: `1px solid ${palette.glassBorderStrong}`,
              }}>
                <Search20Regular style={{ color: palette.textMuted, flexShrink: 0 }} />
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  placeholder="Ask anything about your policy coverage, exclusions, limits…"
                  style={{
                    background: "none", border: "none", outline: "none",
                    fontSize: 14, color: palette.textPrimary, width: "100%", fontFamily: "inherit",
                  }}
                />
              </div>
              <button
                onClick={() => handleSearch()}
                disabled={isPending || !query.trim()}
                style={{
                  padding: "10px 20px", borderRadius: 10, fontSize: 14, fontWeight: 600,
                  background: isPending || !query.trim() ? palette.glassFill : palette.brand,
                  border: `1px solid ${palette.brand}`,
                  color: isPending || !query.trim() ? palette.textMuted : "#fff",
                  cursor: isPending || !query.trim() ? "not-allowed" : "pointer",
                  transition: "all 0.15s", whiteSpace: "nowrap",
                }}
              >
                {isPending ? "Searching…" : "Ask AI"}
              </button>
            </div>

            {/* Suggested questions */}
            <div style={{ marginTop: 14 }}>
              <div style={labelStyle}>Suggested questions</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {SUGGESTED.map((s) => (
                  <button
                    key={s}
                    onClick={() => { setQuery(s); handleSearch(s); }}
                    style={{
                      padding: "4px 12px", borderRadius: 999, fontSize: 12, cursor: "pointer",
                      background: palette.glassFill, border: `1px solid ${palette.glassBorder}`,
                      color: palette.textSecondary, transition: "all 0.12s",
                    }}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          </GlassCard>

          {/* Answer panel */}
          <AnimatePresence>
            {isPending && (
              <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <GlassCard>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
                    <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
                      <Bot20Regular style={{ color: palette.brand }} />
                    </motion.div>
                    <span style={{ fontSize: 13, color: palette.textSecondary }}>
                      Searching Azure AI Search + generating answer…
                    </span>
                  </div>
                  <Skeleton height={14} style={{ marginBottom: 8 }} />
                  <Skeleton height={14} width="85%" style={{ marginBottom: 8 }} />
                  <Skeleton height={14} width="70%" />
                </GlassCard>
              </motion.div>
            )}

            {answer && !isPending && (
              <motion.div key="answer" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
                <GlassCard style={{ border: `1px solid ${palette.brand}30` }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
                    <Bot20Regular style={{ color: palette.brand }} />
                    <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: palette.brand }}>
                      AI Answer — Azure AI Search RAG
                    </span>
                    <button
                      onClick={() => { reset(); setQuery(""); }}
                      style={{ marginLeft: "auto", background: "none", border: "none", cursor: "pointer", fontSize: 12, color: palette.textMuted }}
                    >
                      Clear
                    </button>
                  </div>
                  <div style={{ fontSize: 14, color: palette.textPrimary, lineHeight: 1.75, whiteSpace: "pre-wrap" }}>
                    {String(answer.answer)}
                  </div>
                  <div style={{ marginTop: 14, paddingTop: 12, borderTop: `1px solid ${palette.glassBorder}`, fontSize: 11.5, color: palette.textMuted }}>
                    Powered by Azure AI Search (vector retrieval) · gpt-4o-mini
                  </div>
                </GlassCard>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Policy quick reference panel */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: palette.textMuted }}>
            Policy Reference
          </div>
          {policiesLoading ? (
            Array.from({ length: 3 }).map((_, i) => <GlassCard key={i} style={{ height: 100 }}><Skeleton height={70} /></GlassCard>)
          ) : (
            (policies as Array<Record<string, unknown>>).map((p) => (
              <PolicyCard
                key={String(p.policy_id)}
                policy={p}
                selected={selectedPolicy === String(p.policy_id)}
                onClick={() => setSelectedPolicy(String(p.policy_id))}
                palette={palette}
              />
            ))
          )}
        </div>
      </div>
    </AppLayout>
  );
}

function PolicyCard({ policy, selected, onClick, palette }: {
  policy: Record<string, unknown>; selected: boolean; onClick: () => void;
  palette: ReturnType<typeof getPalette>;
}) {
  const color = typeColor(String(policy.policy_type));

  return (
    <GlassCard
      interactive
      onClick={onClick}
      style={{
        border: `1px solid ${selected ? color : palette.glassBorder}`,
        background: selected ? `${color}0f` : palette.glassFill,
        transition: "all 0.15s",
        padding: "14px 16px",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
        <div>
          <div style={{ fontSize: 11.5, fontFamily: "monospace", color: color, fontWeight: 700 }}>
            {String(policy.policy_id)}
          </div>
          <div style={{ fontSize: 13.5, fontWeight: 700, color: palette.textPrimary, marginTop: 2 }}>
            {String(policy.holder_name)}
          </div>
        </div>
        <span style={{
          fontSize: 10.5, fontWeight: 700, padding: "2px 8px", borderRadius: 999,
          background: `${color}1f`, color, border: `1px solid ${color}40`,
        }}>
          {String(policy.policy_type)}
        </span>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: palette.textMuted }}>
        <span>Sum insured: <strong style={{ color: palette.textSecondary }}>{formatINR(Number(policy.sum_insured))}</strong></span>
        <span>Deductible: <strong style={{ color: palette.textSecondary }}>{formatINR(Number(policy.deductible))}</strong></span>
      </div>
    </GlassCard>
  );
}
