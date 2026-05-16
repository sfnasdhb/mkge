import { LogOut, Settings, UserCircle } from "lucide-react";
import { Avatar, AvatarFallback } from "@/shared/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";
import { cn } from "@/shared/lib/utils";
import { useAuthStore } from "@/features/auth/store";
import { useLogout } from "@/features/auth/hooks";

interface Props {
  collapsed?: boolean;
}

export function UserMenu({ collapsed }: Props) {
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();

  if (!user) return null;

  const initials = user.full_name
    .split(" ")
    .slice(-2)
    .map((s) => s[0])
    .join("")
    .toUpperCase();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className={cn(
            "flex w-full items-center gap-2.5 rounded-md p-2 text-left transition-colors hover:bg-accent",
            collapsed && "justify-center p-1.5"
          )}
        >
          <Avatar className="h-7 w-7">
            <AvatarFallback className="bg-primary/10 text-primary text-[11px] font-semibold">
              {initials}
            </AvatarFallback>
          </Avatar>
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-medium leading-tight">{user.full_name}</p>
              <p className="truncate text-[10px] text-muted-foreground leading-tight mt-0.5">
                {user.email}
              </p>
            </div>
          )}
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent side="right" align="end" className="w-56">
        <DropdownMenuLabel>
          <p className="text-sm font-medium leading-tight">{user.full_name}</p>
          <p className="text-xs text-muted-foreground font-normal leading-tight mt-1 capitalize">
            {user.role}
          </p>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem className="gap-2">
          <UserCircle className="h-4 w-4" />
          Hồ sơ
        </DropdownMenuItem>
        <DropdownMenuItem className="gap-2">
          <Settings className="h-4 w-4" />
          Cài đặt
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={logout} className="gap-2 text-destructive focus:text-destructive">
          <LogOut className="h-4 w-4" />
          Đăng xuất
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
