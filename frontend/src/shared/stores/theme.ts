import { create } from "zustand";
import { persist } from "zustand/middleware";

type ThemeMode = "light" | "dark" | "system";
type Resolved = "light" | "dark";

interface ThemeState {
  mode: ThemeMode;
  resolved: Resolved;
  setMode: (mode: ThemeMode) => void;
  init: () => void;
}

function resolveSystem(): Resolved {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(resolved: Resolved) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  root.classList.toggle("dark", resolved === "dark");
  root.style.colorScheme = resolved;
}

export const useTheme = create<ThemeState>()(
  persist(
    (set, get) => ({
      mode: "dark",
      resolved: "dark",
      setMode: (mode) => {
        const resolved = mode === "system" ? resolveSystem() : mode;
        applyTheme(resolved);
        set({ mode, resolved });
      },
      init: () => {
        const { mode } = get();
        const resolved = mode === "system" ? resolveSystem() : mode;
        applyTheme(resolved);
        set({ resolved });
        if (mode === "system" && typeof window !== "undefined") {
          window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
            const r = e.matches ? "dark" : "light";
            applyTheme(r);
            set({ resolved: r });
          });
        }
      },
    }),
    { name: "mkge-theme", partialize: (s) => ({ mode: s.mode }) }
  )
);
