import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { CommandPalette } from "./CommandPalette";

interface AppLayoutProps {
  title: string;
  subtitle: string;
  children: ReactNode;
}

export function AppLayout({ title, subtitle, children }: AppLayoutProps) {
  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden" }}>
      <Sidebar />
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        <TopBar title={title} subtitle={subtitle} />
        <main style={{ flex: 1, overflowY: "auto", padding: "24px 28px 40px" }}>
          {children}
        </main>
      </div>
      {/* Global ⌘K / Ctrl-K search — mounted once, available on every app page. */}
      <CommandPalette />
    </div>
  );
}
