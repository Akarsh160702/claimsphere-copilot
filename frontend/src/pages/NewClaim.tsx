import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Heart20Regular,
  VehicleRv20Regular,
  Home20Regular,
  Airplane20Regular,
  ArrowRight20Regular,
  ArrowLeft20Regular,
  Attach20Regular,
  Dismiss20Regular,
  CheckmarkCircle20Filled,
  Circle20Regular,
  ArrowClockwise20Regular,
} from "@fluentui/react-icons";
import { AppLayout } from "@/components/layout/AppLayout";
import { GlassCard } from "@/components/common/GlassCard";
import { palette, radius, typeColor } from "@/theme/tokens";
import { formatINR } from "@/utils/format";
import { submitClaimSync, uploadDocument } from "@/api/claims";
import type { ClaimType, Channel, ClaimFull } from "@/api/types";

// ── Step types ────────────────────────────────────────────────────────────────
type Step = 0 | 1 | 2 | 3 | 4;

interface FormState {
  claimType: ClaimType | "";
  channel: Channel;
  policyId: string;
  name: string;
  email: string;
  phone: string;
  amount: string;
  incidentDate: string;
  description: string;
}

const CLAIM_TYPES: { type: ClaimType; icon: React.ElementType; desc: string }[] = [
  { type: "Health", icon: Heart20Regular, desc: "Medical expenses, hospitalization, surgery" },
  { type: "Motor", icon: VehicleRv20Regular, desc: "Vehicle damage, accident, theft" },
  { type: "Property", icon: Home20Regular, desc: "Fire, flood, structural damage" },
  { type: "Travel", icon: Airplane20Regular, desc: "Trip cancellation, lost baggage, medical abroad" },
];

const AGENTS = [
  { name: "RouterAgent", label: "Classifying claim type & priority", model: "gpt-4o-mini" },
  { name: "DocumentAgent", label: "Extracting document data", model: "Azure Doc Intelligence" },
  { name: "ValidationAgent", label: "Validating policy coverage", model: "gpt-4o-mini + RAG" },
  { name: "FraudAgent", label: "Fraud risk assessment", model: "gpt-4o-mini" },
  { name: "MissingInfoAgent", label: "Checking for missing documents", model: "gpt-4o-mini" },
  { name: "AdjudicationAgent", label: "Final decision", model: "gpt-4o" },
];

// ── Main component ────────────────────────────────────────────────────────────
export function NewClaim() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>(0);
  const [form, setForm] = useState<FormState>({
    claimType: "", channel: "Web", policyId: "", name: "", email: "",
    phone: "", amount: "", incidentDate: "", description: "",
  });
  const [files, setFiles] = useState<File[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [agentStep, setAgentStep] = useState(-1);
  const [result, setResult] = useState<ClaimFull | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const set = (k: keyof FormState, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const canProceedStep1 = form.claimType !== "";
  const canProceedStep2 =
    form.policyId && form.name && form.email && form.phone &&
    form.amount && form.incidentDate && form.description;

  async function handleSubmit() {
    setStep(3);
    setAgentStep(0);
    setError(null);

    // Animate agents firing (visual only — real call is happening in parallel)
    const interval = setInterval(() => {
      setAgentStep((s) => {
        if (s >= AGENTS.length - 1) { clearInterval(interval); return s; }
        return s + 1;
      });
    }, 3200);

    try {
      // Upload documents first
      const blobUrls: string[] = [];
      for (const f of files) {
        const docType = form.claimType === "Health" ? "hospital_bill"
          : form.claimType === "Motor" ? "repair_estimate" : "damage_photos";
        const up = await uploadDocument(f, `CLM-PENDING`, docType);
        blobUrls.push(up.blob_url);
      }

      const res = await submitClaimSync({
        policy_id: form.policyId,
        claimant: { name: form.name, email: form.email, phone: form.phone },
        claim_type: form.claimType as ClaimType,
        claim_amount: parseFloat(form.amount),
        incident_date: form.incidentDate,
        description: form.description,
        channel: form.channel,
        document_urls: blobUrls,
      });

      clearInterval(interval);
      setAgentStep(AGENTS.length);
      setTimeout(() => {
        setResult(res);
        setStep(4);
      }, 600);
    } catch (e: unknown) {
      clearInterval(interval);
      setError(e instanceof Error ? e.message : "Submission failed");
      setAgentStep(-1);
      setStep(2);
    }
  }

  function addFiles(incoming: FileList | null) {
    if (!incoming) return;
    setFiles((f) => [...f, ...Array.from(incoming)].slice(0, 5));
  }

  return (
    <AppLayout title="New Claim" subtitle="Submit a new insurance claim through the AI pipeline">
      {/* Step indicator */}
      <div style={{ display: "flex", alignItems: "center", gap: 0, marginBottom: 28, maxWidth: 560 }}>
        {["Claim Type", "Details", "Documents", "Processing", "Result"].map((label, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", flex: i < 4 ? 1 : undefined }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 5 }}>
              <div style={{
                width: 28, height: 28, borderRadius: "50%", display: "flex",
                alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700,
                background: step === i ? palette.brand : step > i ? palette.success : palette.glassFill,
                border: `1px solid ${step === i ? palette.brand : step > i ? palette.success : palette.glassBorder}`,
                color: step >= i ? palette.textPrimary : palette.textMuted,
                transition: "all 0.2s",
              }}>
                {step > i ? "✓" : i + 1}
              </div>
              <span style={{ fontSize: 10, color: step === i ? palette.textPrimary : palette.textMuted, whiteSpace: "nowrap" }}>
                {label}
              </span>
            </div>
            {i < 4 && (
              <div style={{
                height: 1, flex: 1, margin: "0 6px", marginBottom: 16,
                background: step > i ? palette.success : palette.glassBorder,
                transition: "background 0.3s",
              }} />
            )}
          </div>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {/* ── Step 0: Claim type ── */}
        {step === 0 && (
          <motion.div key="s0" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
            <p style={{ fontSize: 14, color: palette.textSecondary, marginBottom: 18 }}>
              Select the type of insurance claim you want to submit.
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, maxWidth: 640 }}>
              {CLAIM_TYPES.map(({ type, icon: Icon, desc }) => {
                const color = typeColor(type);
                const selected = form.claimType === type;
                return (
                  <GlassCard
                    key={type}
                    interactive
                    onClick={() => set("claimType", type)}
                    style={{
                      border: `1px solid ${selected ? color : palette.glassBorder}`,
                      background: selected ? `${color}14` : palette.glassFill,
                      transition: "all 0.15s",
                    }}
                  >
                    <div style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
                      <div style={{
                        width: 40, height: 40, borderRadius: 10, display: "flex",
                        alignItems: "center", justifyContent: "center", flexShrink: 0,
                        background: `${color}1f`, border: `1px solid ${color}40`,
                      }}>
                        <Icon style={{ color, fontSize: 20 }} />
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 15, color: palette.textPrimary, marginBottom: 4 }}>{type}</div>
                        <div style={{ fontSize: 12.5, color: palette.textSecondary, lineHeight: 1.5 }}>{desc}</div>
                      </div>
                    </div>
                  </GlassCard>
                );
              })}
            </div>
            <div style={{ marginTop: 24 }}>
              <NavBtn disabled={!canProceedStep1} onClick={() => setStep(1)} label="Continue" icon={<ArrowRight20Regular />} />
            </div>
          </motion.div>
        )}

        {/* ── Step 1: Details ── */}
        {step === 1 && (
          <motion.div key="s1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
            <div style={{ maxWidth: 640 }}>
              <GlassCard>
                <p style={{ margin: "0 0 20px", fontSize: 13.5, color: palette.textSecondary }}>
                  Enter claim and claimant details for your <strong style={{ color: typeColor(form.claimType) }}>{form.claimType}</strong> claim.
                </p>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                  <FormField label="Policy ID *" value={form.policyId} onChange={(v) => set("policyId", v)}
                    placeholder="e.g. POL-HEALTH-001" hint="POL-HEALTH-001 · POL-MOTOR-001 · POL-PROPERTY-001" />
                  <FormField label="Full Name *" value={form.name} onChange={(v) => set("name", v)} placeholder="Claimant name" />
                  <FormField label="Email *" type="email" value={form.email} onChange={(v) => set("email", v)} placeholder="email@example.com" />
                  <FormField label="Phone *" value={form.phone} onChange={(v) => set("phone", v)} placeholder="+91-9876543210" />
                  <FormField label="Claim Amount (₹) *" type="number" value={form.amount} onChange={(v) => set("amount", v)} placeholder="e.g. 85000" />
                  <FormField label="Incident Date *" type="date" value={form.incidentDate} onChange={(v) => set("incidentDate", v)} />
                  <div style={{ gridColumn: "span 2" }}>
                    <FormField label="Description *" value={form.description} onChange={(v) => set("description", v)}
                      placeholder="Describe the incident clearly — the AI agents use this to classify and validate your claim."
                      multiline />
                  </div>
                  <div>
                    <label style={labelStyle}>Channel</label>
                    <select value={form.channel} onChange={(e) => set("channel", e.target.value as Channel)} style={selectStyle}>
                      {(["Web", "Email", "Teams", "Phone", "CSR"] as Channel[]).map((c) => (
                        <option key={c} value={c} style={{
                          background: palette.bgElevated,
                          color: palette.textPrimary,
                          padding: "8px",
                        }}>{c}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </GlassCard>
              <div style={{ display: "flex", gap: 10, marginTop: 18 }}>
                <NavBtn secondary onClick={() => setStep(0)} label="Back" icon={<ArrowLeft20Regular />} iconLeft />
                <NavBtn disabled={!canProceedStep2} onClick={() => setStep(2)} label="Continue" icon={<ArrowRight20Regular />} />
              </div>
            </div>
          </motion.div>
        )}

        {/* ── Step 2: Documents ── */}
        {step === 2 && (
          <motion.div key="s2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
            <div style={{ maxWidth: 640 }}>
              <GlassCard>
                <p style={{ margin: "0 0 16px", fontSize: 13.5, color: palette.textSecondary }}>
                  Upload supporting documents (optional but improves AI accuracy). Max 5 files.
                </p>
                {error && (
                  <div style={{ padding: "10px 14px", borderRadius: 8, background: palette.dangerSoft, border: `1px solid ${palette.danger}40`, fontSize: 13, color: palette.danger, marginBottom: 14 }}>
                    {error}
                  </div>
                )}
                {/* Drop zone */}
                <div
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={(e) => { e.preventDefault(); setDragOver(false); addFiles(e.dataTransfer.files); }}
                  onClick={() => fileRef.current?.click()}
                  style={{
                    border: `2px dashed ${dragOver ? palette.brand : palette.glassBorder}`,
                    borderRadius: 12, padding: "32px 20px", textAlign: "center",
                    cursor: "pointer", transition: "border-color 0.15s",
                    background: dragOver ? palette.brandSoft : "transparent",
                  }}
                >
                  <Attach20Regular style={{ color: palette.brand, fontSize: 28, marginBottom: 8 }} />
                  <p style={{ margin: 0, fontSize: 13.5, color: palette.textSecondary }}>
                    Drag files here or <span style={{ color: palette.brand }}>browse</span>
                  </p>
                  <p style={{ margin: "4px 0 0", fontSize: 11.5, color: palette.textMuted }}>
                    PDF, JPG, PNG — hospital bills, FIR, repair estimates
                  </p>
                  <input ref={fileRef} type="file" multiple accept=".pdf,.jpg,.jpeg,.png" style={{ display: "none" }}
                    onChange={(e) => addFiles(e.target.files)} />
                </div>
                {files.length > 0 && (
                  <div style={{ marginTop: 14, display: "flex", flexDirection: "column", gap: 8 }}>
                    {files.map((f, i) => (
                      <div key={i} style={{
                        display: "flex", alignItems: "center", justifyContent: "space-between",
                        padding: "8px 12px", borderRadius: 8, background: palette.glassFill,
                        border: `1px solid ${palette.glassBorder}`,
                      }}>
                        <span style={{ fontSize: 13, color: palette.textSecondary }}>{f.name}</span>
                        <button onClick={() => setFiles((fs) => fs.filter((_, j) => j !== i))}
                          style={{ background: "none", border: "none", cursor: "pointer", color: palette.textMuted, display: "flex" }}>
                          <Dismiss20Regular />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </GlassCard>
              <div style={{ display: "flex", gap: 10, marginTop: 18 }}>
                <NavBtn secondary onClick={() => setStep(1)} label="Back" icon={<ArrowLeft20Regular />} iconLeft />
                <NavBtn onClick={handleSubmit} label="Submit Claim" icon={<ArrowRight20Regular />} />
              </div>
            </div>
          </motion.div>
        )}

        {/* ── Step 3: Processing ── */}
        {step === 3 && (
          <motion.div key="s3" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div style={{ maxWidth: 580 }}>
              <GlassCard>
                <div style={{ marginBottom: 20 }}>
                  <h3 style={{ margin: "0 0 4px", fontSize: 16, fontWeight: 700, color: palette.textPrimary }}>
                    Processing your claim
                  </h3>
                  <p style={{ margin: 0, fontSize: 13, color: palette.textSecondary }}>
                    The 7-agent Azure AI Foundry pipeline is running…
                  </p>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
                  {AGENTS.map((agent, i) => {
                    const done = agentStep > i;
                    const active = agentStep === i;
                    const pending = agentStep < i;
                    return (
                      <div key={agent.name} style={{ display: "flex", gap: 0, position: "relative" }}>
                        {/* Connector line */}
                        {i < AGENTS.length - 1 && (
                          <div style={{
                            position: "absolute", left: 11, top: 28, width: 2, height: "calc(100% - 8px)",
                            background: done ? palette.success : palette.glassBorder,
                            transition: "background 0.3s",
                          }} />
                        )}
                        <div style={{ display: "flex", gap: 14, alignItems: "flex-start", padding: "10px 0", zIndex: 1 }}>
                          <div style={{ flexShrink: 0, width: 24, display: "flex", justifyContent: "center", marginTop: 2 }}>
                            {done ? (
                              <CheckmarkCircle20Filled style={{ color: palette.success }} />
                            ) : active ? (
                              <motion.div animate={{ opacity: [1, 0.3, 1] }} transition={{ repeat: Infinity, duration: 1 }}>
                                <ArrowClockwise20Regular style={{ color: palette.brand }} />
                              </motion.div>
                            ) : (
                              <Circle20Regular style={{ color: palette.glassBorder }} />
                            )}
                          </div>
                          <div>
                            <div style={{ fontSize: 13.5, fontWeight: 600, color: pending ? palette.textMuted : palette.textPrimary }}>
                              {agent.name}
                            </div>
                            <div style={{ fontSize: 12, color: active ? palette.brand : palette.textMuted, marginTop: 1 }}>
                              {active ? agent.label : done ? "Complete" : agent.label}
                            </div>
                            <div style={{ fontSize: 11, color: palette.textMuted, marginTop: 2 }}>
                              {agent.model}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </GlassCard>
            </div>
          </motion.div>
        )}

        {/* ── Step 4: Result ── */}
        {step === 4 && result && (
          <motion.div key="s4" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <div style={{ maxWidth: 640 }}>
              <ResultCard result={result} onNew={() => {
                setStep(0); setForm({ claimType: "", channel: "Web", policyId: "", name: "", email: "", phone: "", amount: "", incidentDate: "", description: "" });
                setFiles([]); setResult(null); setAgentStep(-1);
              }} onView={() => navigate(`/claims/${result.claim_id}`)} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </AppLayout>
  );
}

// ── Result card ───────────────────────────────────────────────────────────────
function ResultCard({ result, onNew, onView }: { result: ClaimFull; onNew: () => void; onView: () => void }) {
  const adj = result.adjudication_result;
  const fraud = result.fraud_result;
  const decision = adj?.decision ?? "Escalate";
  const color = decision === "Approve" ? palette.success : decision === "Reject" ? palette.danger : palette.warning;

  return (
    <GlassCard>
      {/* Decision banner */}
      <div style={{
        padding: "16px 20px", borderRadius: 10, marginBottom: 20,
        background: `${color}14`, border: `1px solid ${color}40`,
        display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: palette.textMuted, marginBottom: 4 }}>
            AI Decision
          </div>
          <div style={{ fontSize: 22, fontWeight: 800, color }}>{decision}</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 11, color: palette.textMuted, marginBottom: 4 }}>Claim ID</div>
          <div style={{ fontSize: 13, fontWeight: 600, color: palette.textPrimary, fontFamily: "monospace" }}>
            {result.claim_id}
          </div>
        </div>
      </div>

      {/* Key metrics row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 20 }}>
        <Metric label="Claim Amount" value={formatINR(adj?.claim_amount ?? 0)} />
        <Metric label="Approved Amount" value={formatINR(adj?.approved_amount ?? 0)} color={palette.success} />
        <Metric label="Fraud Score" value={`${fraud?.fraud_score ?? 0}/100`}
          color={fraud && fraud.fraud_score < 30 ? palette.success : palette.warning} />
      </div>

      {/* Rationale */}
      {adj?.rationale && (
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.07em", textTransform: "uppercase", color: palette.textMuted, marginBottom: 8 }}>
            AI Rationale
          </div>
          <p style={{ margin: 0, fontSize: 13, color: palette.textSecondary, lineHeight: 1.65 }}>
            {adj.rationale}
          </p>
        </div>
      )}

      {/* Agents run count */}
      <div style={{ fontSize: 12, color: palette.textMuted, marginBottom: 20 }}>
        {result.audit_trail.length} agent steps completed · {result.claim_type} · {result.priority} priority
      </div>

      <div style={{ display: "flex", gap: 10 }}>
        <button onClick={onView} style={{ ...btnStyle, background: palette.brandSoft, border: `1px solid ${palette.brand}50`, color: palette.brand }}>
          View Full Detail
        </button>
        <button onClick={onNew} style={{ ...btnStyle, background: palette.glassFill, border: `1px solid ${palette.glassBorder}`, color: palette.textSecondary }}>
          Submit Another
        </button>
      </div>
    </GlassCard>
  );
}

// ── Small helpers ─────────────────────────────────────────────────────────────
function Metric({ label, value, color: _color }: { label: string; value: string; color?: string }) {
  const color = _color;
  return (
    <div style={{ padding: "12px 14px", borderRadius: 8, background: palette.glassFill, border: `1px solid ${palette.glassBorder}` }}>
      <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: "0.07em", textTransform: "uppercase", color: palette.textMuted, marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ fontSize: 16, fontWeight: 700, color: color ?? palette.textPrimary }}>{value}</div>
    </div>
  );
}

function FormField({ label, value, onChange, placeholder, type = "text", multiline = false, hint }: {
  label: string; value: string; onChange: (v: string) => void;
  placeholder?: string; type?: string; multiline?: boolean; hint?: string;
}) {
  return (
    <div>
      <label style={labelStyle}>{label}</label>
      {multiline ? (
        <textarea value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
          rows={3} style={{ ...inputStyle, resize: "vertical" }} />
      ) : (
        <input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
          style={inputStyle} />
      )}
      {hint && <div style={{ fontSize: 11, color: palette.textMuted, marginTop: 4 }}>{hint}</div>}
    </div>
  );
}

function NavBtn({ onClick, label, icon, disabled, secondary, iconLeft }: {
  onClick: () => void; label: string; icon: React.ReactNode;
  disabled?: boolean; secondary?: boolean; iconLeft?: boolean;
}) {
  return (
    <button onClick={onClick} disabled={disabled} style={{
      display: "inline-flex", alignItems: "center", gap: 8, padding: "10px 20px",
      borderRadius: radius.md, fontSize: 14, fontWeight: 600, cursor: disabled ? "not-allowed" : "pointer",
      border: `1px solid ${secondary ? palette.glassBorder : disabled ? palette.glassBorder : palette.brand}`,
      background: secondary ? palette.glassFill : disabled ? palette.glassFill : palette.brand,
      color: disabled ? palette.textMuted : secondary ? palette.textSecondary : "#fff",
      transition: "all 0.15s", flexDirection: iconLeft ? "row-reverse" : "row",
    }}>
      {label}{icon}
    </button>
  );
}

const labelStyle: React.CSSProperties = {
  display: "block", fontSize: 11.5, fontWeight: 600,
  letterSpacing: "0.05em", textTransform: "uppercase",
  color: palette.textMuted, marginBottom: 6,
};

const inputStyle: React.CSSProperties = {
  width: "100%", padding: "9px 12px", borderRadius: 8, fontSize: 13.5,
  background: palette.glassFill, border: `1px solid ${palette.glassBorder}`,
  color: palette.textPrimary, outline: "none", boxSizing: "border-box",
  fontFamily: "inherit",
};

const selectStyle: React.CSSProperties = {
  width: "100%", padding: "9px 12px", borderRadius: 8, fontSize: 13.5,
  background: palette.glassFill, border: `1px solid ${palette.glassBorder}`,
  color: palette.textPrimary, outline: "none", boxSizing: "border-box",
  fontFamily: "inherit", cursor: "pointer",
  WebkitAppearance: "none", /* Remove default Chrome/Safari styling */
  MozAppearance: "none", /* Remove default Firefox styling */
  appearance: "none", /* Standard property */
  backgroundImage: `url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2397A6BE' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e")`,
  backgroundRepeat: "no-repeat",
  backgroundPosition: "right 10px center",
  backgroundSize: "16px",
  paddingRight: "36px", /* Space for custom arrow */
};

const btnStyle: React.CSSProperties = {
  padding: "9px 18px", borderRadius: radius.md, fontSize: 13.5,
  fontWeight: 600, cursor: "pointer", transition: "opacity 0.15s",
};
