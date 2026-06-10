import { NavLink, useNavigate } from "react-router-dom";
import { ShieldTask24Filled } from "@fluentui/react-icons";
import { getPalette, shadow } from "@/theme/tokens";
import { useTheme } from "@/contexts/ThemeContext";
import { NAV_ITEMS } from "./navItems";
import { useAppStore } from "@/store/useAppStore";

export function Sidebar() {
  const { theme } = useTheme();
  const palette = getPalette(theme);
  const navigate = useNavigate();
  const backendOnline = useAppStore((s) => s.backendOnline);
  const dataSource = useAppStore((s) => s.dataSource);

  return (
    <aside
      style={{
        width: 232,
        flexShrink: 0,
        height: "100vh",
        background: palette.sidebar,
        borderRight: `1px solid ${palette.glassBorder}`,
        display: "flex",
        flexDirection: "column",
        padding: "20px 14px",
      }}
    >
      {/* Brand */}
      <div
        onClick={() => navigate("/")}
        style={{ display: "flex", alignItems: "center", gap: 11, padding: "0 8px 18px", cursor: "pointer" }}
      >
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: 10,
            background: `linear-gradient(140deg, ${palette.brandHover}, ${palette.brandStrong})`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            boxShadow: shadow.brandGlow,
          }}
        >
          <ShieldTask24Filled style={{ color: "#fff" }} />
        </div>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: "-0.01em", color: palette.textPrimary, lineHeight: 1.1 }}>
            ClaimSphere
          </div>
          <div style={{ fontSize: 10.5, color: palette.textMuted, marginTop: 2, letterSpacing: "0.06em", textTransform: "uppercase" }}>
            Copilot
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ display: "flex", flexDirection: "column", gap: 3, flex: 1 }}>
        {NAV_ITEMS.map(({ path, label, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            end={path === "/"}
            style={({ isActive }) => ({
              display: "flex",
              alignItems: "center",
              gap: 11,
              padding: "9px 12px",
              borderRadius: 9,
              fontSize: 13.5,
              fontWeight: isActive ? 600 : 500,
              textDecoration: "none",
              color: isActive ? palette.textPrimary : palette.textSecondary,
              background: isActive ? palette.brandSoft : "transparent",
              border: `1px solid ${isActive ? palette.brand + "55" : "transparent"}`,
              transition: "background 0.15s, color 0.15s",
            })}
          >
            {({ isActive }) => (
              <>
                <Icon style={{ color: isActive ? palette.brand : palette.textMuted }} />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* System status */}
      <div
        style={{
          marginTop: 16,
          padding: "12px 12px",
          borderRadius: 12,
          background: palette.glassFill,
          border: `1px solid ${palette.glassBorder}`,
        }}
      >
        <div
          style={{
            fontSize: 10,
            fontWeight: 700,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            color: palette.textMuted,
            marginBottom: 9,
          }}
        >
          System Status
        </div>
        <StatusLine
          color={backendOnline ? palette.success : palette.warning}
          label={backendOnline ? "API Connected" : "API Offline"}
        />
        <StatusLine
          color={dataSource === "live" ? palette.success : palette.info}
          label={dataSource === "live" ? "Live Data" : "Demo Data"}
        />
        <div style={{ fontSize: 10.5, color: palette.textMuted, marginTop: 11, lineHeight: 1.6 }}>
          Team NEXORA<br />
          Hack2Future 2026
        </div>
      </div>
    </aside>
  );
}

function StatusLine({ color, label }: { color: string; label: string }) {
  const { theme } = useTheme();
  const palette = getPalette(theme);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 7 }}>
      <span style={{ width: 7, height: 7, borderRadius: "50%", background: color, flexShrink: 0 }} />
      <span style={{ fontSize: 12, color: palette.textSecondary }}>{label}</span>
    </div>
  );
}
