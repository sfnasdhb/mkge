import { NavLink } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ChevronsLeft,
  ChevronsRight,
  FileText,
  GitGraph,
  History,
  LayoutDashboard,
  MessageSquare,
  Settings,
  Shield,
} from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/shared/components/ui/tooltip";
import { cn } from "@/shared/lib/utils";
import { useSidebar } from "@/shared/stores/sidebar";
import { useAuthStore } from "@/features/auth/store";
import { UserMenu } from "./UserMenu";

interface NavItem {
  to: string;
  label: string;
  icon: typeof FileText;
  roles?: string[];
  badge?: string;
}

const NAV: NavItem[] = [
  { to: "/documents", label: "Tài liệu", icon: FileText },
  { to: "/graph", label: "Đồ thị tri thức", icon: GitGraph },
  { to: "/ask", label: "Hỏi đáp AI", icon: MessageSquare },
  { to: "/history", label: "Lịch sử", icon: History },
  { to: "/admin", label: "Quản trị", icon: Shield, roles: ["admin"] },
];

export function Sidebar() {
  const { collapsed, toggle } = useSidebar();
  const role = useAuthStore((s) => s.user?.role);

  const items = NAV.filter((item) => !item.roles || (role && item.roles.includes(role)));

  return (
    <aside
      className={cn(
        "sticky top-0 flex h-screen shrink-0 flex-col border-r border-border bg-card/40 transition-[width] duration-300 ease-out-expo",
        collapsed ? "w-[68px]" : "w-[240px]"
      )}
    >
      <div className="flex h-14 items-center justify-between border-b border-border px-4">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <Logo />
          {!collapsed && (
            <div className="flex flex-col">
              <span className="text-sm font-semibold tracking-tight leading-none">MKGE</span>
              <span className="text-[10px] uppercase tracking-widest text-muted-foreground/70 mt-1">
                v0.1
              </span>
            </div>
          )}
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-3 scrollbar-thin">
        {items.map((item) => (
          <SidebarLink key={item.to} item={item} collapsed={collapsed} />
        ))}
      </nav>

      <div className="border-t border-border p-3 space-y-1">
        <SidebarLink
          item={{ to: "/settings", label: "Cài đặt", icon: Settings }}
          collapsed={collapsed}
        />
        <UserMenu collapsed={collapsed} />
      </div>

      <div className="border-t border-border p-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggle}
          className="w-full"
          aria-label={collapsed ? "Mở rộng" : "Thu gọn"}
        >
          {collapsed ? (
            <ChevronsRight className="h-4 w-4" />
          ) : (
            <ChevronsLeft className="h-4 w-4" />
          )}
        </Button>
      </div>
    </aside>
  );
}

function SidebarLink({ item, collapsed }: { item: NavItem; collapsed: boolean }) {
  const link = (
    <NavLink
      to={item.to}
      className={({ isActive }) =>
        cn(
          "group relative flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
          "hover:bg-accent hover:text-accent-foreground",
          isActive
            ? "bg-accent text-accent-foreground"
            : "text-muted-foreground",
          collapsed && "justify-center"
        )
      }
    >
      {({ isActive }) => (
        <>
          {isActive && (
            <motion.span
              layoutId="sidebar-active"
              className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-r bg-primary"
              transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            />
          )}
          <item.icon className="h-4 w-4 shrink-0" />
          {!collapsed && <span className="truncate">{item.label}</span>}
        </>
      )}
    </NavLink>
  );

  if (collapsed) {
    return (
      <Tooltip delayDuration={300}>
        <TooltipTrigger asChild>{link}</TooltipTrigger>
        <TooltipContent side="right">{item.label}</TooltipContent>
      </Tooltip>
    );
  }
  return link;
}

function Logo() {
  return (
    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm ring-1 ring-primary/20">
      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="6" cy="6" r="2.2" />
        <circle cx="18" cy="6" r="2.2" />
        <circle cx="12" cy="18" r="2.2" />
        <path d="M7.5 7.5 L11 16.5" />
        <path d="M16.5 7.5 L13 16.5" />
        <path d="M8 6 L16 6" />
      </svg>
    </div>
  );
}
