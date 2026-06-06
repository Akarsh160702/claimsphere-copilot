import { Search20Regular, Alert20Regular } from "@fluentui/react-icons";
import { palette } from "@/theme/tokens";
import { useAppStore } from "@/store/useAppStore";

interface TopBarProps {
  title: string;
  subtitle: string;
}

export function TopBar({ title, subtitle }: TopBarProps) {
  const dataSource = useAppStore((s) => s.dataSource);

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
        <div
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
            cursor: "text",
            transition: "border-color 0.15s, background 0.15s",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.borderColor = palette.glassBorderStrong)}
          onMouseLeave={(e) => (e.currentTarget.style.borderColor = palette.glassBorder)}
        >
          <Search20Regular />
          <span style={{ flex: 1 }}>Search claims, policies…</span>
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
            ⌘K
          </kbd>
        </div>

        <button
          aria-label="Notifications"
          style={{
            width: 38,
            height: 38,
            borderRadius: 10,
            background: palette.glassFill,
            border: `1px solid ${palette.glassBorder}`,
            color: palette.textSecondary,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
          }}
        >
          <Alert20Regular />
        </button>

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
