import { create } from "zustand";

interface AppState {
  /** Whether the backend reported healthy on the last probe. */
  backendOnline: boolean;
  setBackendOnline: (v: boolean) => void;

  /** Whether the dashboard is showing live or synthetic data. */
  dataSource: "live" | "synthetic";
  setDataSource: (s: "live" | "synthetic") => void;

  /** Currently selected claim id (for detail view / CSR context). */
  selectedClaimId: string | null;
  setSelectedClaimId: (id: string | null) => void;

  /** Whether the global ⌘K command palette is open. */
  commandOpen: boolean;
  setCommandOpen: (v: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  backendOnline: false,
  setBackendOnline: (v) => set({ backendOnline: v }),
  dataSource: "synthetic",
  setDataSource: (s) => set({ dataSource: s }),
  selectedClaimId: null,
  setSelectedClaimId: (id) => set({ selectedClaimId: id }),
  commandOpen: false,
  setCommandOpen: (v) => set({ commandOpen: v }),
}));
