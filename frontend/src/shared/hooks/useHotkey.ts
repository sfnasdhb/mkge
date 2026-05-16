import { useEffect } from "react";

type Modifier = "meta" | "ctrl" | "shift" | "alt";

interface Options {
  modifiers?: Modifier[];
  enabled?: boolean;
  preventDefault?: boolean;
}

export function useHotkey(key: string, handler: (e: KeyboardEvent) => void, options: Options = {}) {
  const { modifiers = [], enabled = true, preventDefault = true } = options;

  useEffect(() => {
    if (!enabled) return;

    function onKey(e: KeyboardEvent) {
      const needsMeta = modifiers.includes("meta") || modifiers.includes("ctrl");
      const isMod = e.metaKey || e.ctrlKey;
      if (needsMeta && !isMod) return;
      if (modifiers.includes("shift") && !e.shiftKey) return;
      if (modifiers.includes("alt") && !e.altKey) return;
      if (e.key.toLowerCase() !== key.toLowerCase()) return;

      if (preventDefault) e.preventDefault();
      handler(e);
    }

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [key, handler, modifiers, enabled, preventDefault]);
}
