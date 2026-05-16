import { useNavigate } from "react-router-dom";
import { FileText, GitGraph, History, MessageSquare, Moon, Settings, Sun } from "lucide-react";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from "@/shared/components/ui/command";
import { useTheme } from "@/shared/stores/theme";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: Props) {
  const navigate = useNavigate();
  const setMode = useTheme((s) => s.setMode);

  function go(path: string) {
    navigate(path);
    onOpenChange(false);
  }

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Gõ lệnh hoặc tìm kiếm..." />
      <CommandList>
        <CommandEmpty>Không tìm thấy kết quả.</CommandEmpty>
        <CommandGroup heading="Điều hướng">
          <CommandItem onSelect={() => go("/documents")}>
            <FileText /> Tài liệu
            <CommandShortcut>G D</CommandShortcut>
          </CommandItem>
          <CommandItem onSelect={() => go("/graph")}>
            <GitGraph /> Đồ thị tri thức
            <CommandShortcut>G G</CommandShortcut>
          </CommandItem>
          <CommandItem onSelect={() => go("/ask")}>
            <MessageSquare /> Hỏi đáp AI
            <CommandShortcut>G A</CommandShortcut>
          </CommandItem>
          <CommandItem onSelect={() => go("/history")}>
            <History /> Lịch sử
          </CommandItem>
          <CommandItem onSelect={() => go("/settings")}>
            <Settings /> Cài đặt
          </CommandItem>
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Chủ đề">
          <CommandItem onSelect={() => { setMode("light"); onOpenChange(false); }}>
            <Sun /> Chế độ sáng
          </CommandItem>
          <CommandItem onSelect={() => { setMode("dark"); onOpenChange(false); }}>
            <Moon /> Chế độ tối
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
