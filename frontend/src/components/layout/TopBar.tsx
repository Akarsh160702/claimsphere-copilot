import { Search20Regular } from "@fluentui/react-icons";
import { palette } from "@/theme/tokens";
import { useAppStore } from "@/store/useAppStore";
import { NotificationBell } from "./NotificationBell";

interface TopBarProps {
  title: string;
  subtitle: string;
}

const IS_MAC =
  typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(navigator.platform);

export function TopBar({ title, subtitle }: TopBarProps) {
  const dataSource = useAppStore((s) => s.dataSource);
  const setCommandOpen = useAppStore((s) => s.setCommandOpen);

  return (
    <header
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "18px 28px",
        borderBottom: `1px solid ${palette.glassBorder}`,
        flexShrink: 0,
      }}
    >
      <div>
        <h1
          style={{
            margin: 0,
            fontSize: 19,
            fontWeight: 700,
            letterSpacing: "-0.02em",
            color: palette.textPrimary,
          }}
        >
          {title}
        </h1>
        <p style={{ margin: "3px 0 0", fontSize: 12.5, color: palette.textMuted }}>{subtitle}</p>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <button
          onClick={() => setCommandOpen(true)}
          aria-label="Search claims and pages"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            padding: "8px 12px 8px 14px",
            borderRadius: 10,
            background: palette.glassFill,
            border: `1px solid ${palette.glassBorder}`,
            color: palette.textMuted,
            fontSize: 13,
            minWidth: 248,
            cursor: "pointer",
            fontFamily: "inherit",
            transition: "border-color 0.15s, background 0.15s",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = palette.glassBorderStrong;
            e.currentTarget.style.background = palette.glassFillStrong;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = palette.glassBorder;
            e.currentTarget.style.background = palette.glassFill;
          }}
        >
          <Search20Regular />
          <span style={{ flex: 1, textAlign: "left" }}>Search claims, policies…</span>
          <kbd
            style={{
              fontSize: 10.5,
              fontWeight: 600,
              fontFamily: "inherit",
              padding: "2px 6px",
              borderRadius: 5,
              background: "rgba(255,255,255,0.05)",
              border: `1px solid ${palette.glassBorder}`,
              color: palette.textMuted,
            }}
          >
            {IS_MAC ? "⌘K" : "Ctrl K"}
          </kbd>
        </button>

        <NotificationBell />

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            fontSize: 11,
            fontWeight: 600,
            letterSpacing: "0.04em",
            textTransform: "uppercase",
            color: dataSource === "live" ? palette.success : palette.info,
            background: dataSource === "live" ? palette.successSoft : palette.infoSoft,
            border: `1px solid ${(dataSource === "live" ? palette.success : palette.info) + "40"}`,
            padding: "7px 12px",
            borderRadius: 999,
          }}
        >
          {dataSource === "live" ? "Live" : "Demo"} Mode
        </div>
      </div>
    </header>
  );
}
