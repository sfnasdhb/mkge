import { useEffect, useState } from "react";
import { Bell, Search } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { ThemeToggle } from "@/shared/components/ThemeToggle";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/shared/components/ui/tooltip";
import { CommandPalette } from "./CommandPalette";
import { useHotkey } from "@/shared/hooks/useHotkey";

export function Topbar() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useHotkey("k", () => setOpen((p) => !p), { modifiers: ["meta"] });

  useEffect(() => {
    function onScroll() {
      setScrolled(window.scrollY > 4);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <>
      <header
        className={
          "sticky top-0 z-30 flex h-14 items-center gap-3 border-b px-6 transition-all duration-200 " +
          (scrolled ? "glass border-border" : "border-transparent bg-background")
        }
      >
        <button
          onClick={() => setOpen(true)}
          className="group flex h-9 flex-1 items-center gap-2 rounded-md border border-border bg-background/50 px-3 text-sm text-muted-foreground transition-colors hover:bg-accent/50 max-w-md"
        >
          <Search className="h-4 w-4" />
          <span>Tìm tài liệu, entity, câu hỏi...</span>
          <kbd className="ml-auto hidden items-center gap-1 rounded border border-border bg-muted px-1.5 py-0.5 font-mono text-[10px] font-medium text-muted-foreground sm:flex">
            <span className="text-xs">⌘</span>K
          </kbd>
        </button>

        <div className="flex items-center gap-1">
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" aria-label="Thông báo" className="relative">
                <Bell className="h-4 w-4" />
                <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-primary ring-2 ring-background" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Thông báo</TooltipContent>
          </Tooltip>
          <ThemeToggle />
        </div>
      </header>

      <CommandPalette open={open} onOpenChange={setOpen} />
    </>
  );
}
