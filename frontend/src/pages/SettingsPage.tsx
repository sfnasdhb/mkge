import React from "react";
import { useAuthStore } from "@/features/auth/store";
import { useTheme } from "@/shared/stores/theme";
import { PageHeader } from "@/shared/components/PageHeader";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { toast } from "sonner";
import { Shield, Key, Sliders, Monitor, Sun, Moon } from "lucide-react";

export const SettingsPage: React.FC = () => {
  const user = useAuthStore((s) => s.user);
  const { mode, setMode } = useTheme();

  // Local states for RAG settings
  const [topK, setTopK] = React.useState(20);
  const [temperature, setTemperature] = React.useState(0.2);
  const [model, setModel] = React.useState("gemini-2.5-flash");
  const [geminiKey, setGeminiKey] = React.useState("••••••••••••••••••••••••••••");
  const [groqKey, setGroqKey] = React.useState("••••••••••••••••••••••••••••");

  // Load values from LocalStorage on mount
  React.useEffect(() => {
    const savedTopK = localStorage.getItem("mkge_rag_top_k");
    const savedTemp = localStorage.getItem("mkge_rag_temperature");
    const savedModel = localStorage.getItem("mkge_rag_model");
    if (savedTopK) setTopK(parseInt(savedTopK, 10));
    if (savedTemp) setTemperature(parseFloat(savedTemp));
    if (savedModel) setModel(savedModel);
  }, []);

  const handleSaveSettings = () => {
    localStorage.setItem("mkge_rag_top_k", topK.toString());
    localStorage.setItem("mkge_rag_temperature", temperature.toString());
    localStorage.setItem("mkge_rag_model", model);
    toast.success("Đã lưu các tùy chỉnh cấu hình RAG thành công!");
  };

  const handleSaveKeys = () => {
    toast.success("Cập nhật API Keys thành công!");
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Cài Đặt"
        description="Cấu hình tài khoản, tham số RAG, khóa API và giao diện ứng dụng."
      />

      <div className="grid gap-6 md:grid-cols-2">
        {/* Account Info */}
        <Card className="border-border bg-card">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-primary" />
              <CardTitle>Thông Tin Tài Khoản</CardTitle>
            </div>
            <CardDescription>Chi tiết tài khoản đang sử dụng hệ thống.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1">
              <Label className="text-xs text-muted-foreground">Họ và Tên</Label>
              <p className="text-sm font-semibold text-foreground">{user?.full_name}</p>
            </div>
            <div className="space-y-1">
              <Label className="text-xs text-muted-foreground">Email</Label>
              <p className="text-sm font-semibold text-foreground">{user?.email}</p>
            </div>
            <div className="space-y-1">
              <Label className="text-xs text-muted-foreground">Vai Trò Hệ Thống</Label>
              <p className="text-sm font-semibold uppercase tracking-wider text-primary">
                {user?.role}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Theme Settings */}
        <Card className="border-border bg-card">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Monitor className="h-5 w-5 text-primary" />
              <CardTitle>Giao Diện & Chủ Đề</CardTitle>
            </div>
            <CardDescription>Cài đặt giao diện màu nền cho ứng dụng.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              <Button
                variant={mode === "light" ? "default" : "outline"}
                className="flex flex-col items-center gap-2 h-20"
                onClick={() => setMode("light")}
              >
                <Sun className="h-5 w-5" />
                <span className="text-xs font-semibold">Sáng</span>
              </Button>
              <Button
                variant={mode === "dark" ? "default" : "outline"}
                className="flex flex-col items-center gap-2 h-20"
                onClick={() => setMode("dark")}
              >
                <Moon className="h-5 w-5" />
                <span className="text-xs font-semibold">Tối</span>
              </Button>
              <Button
                variant={mode === "system" ? "default" : "outline"}
                className="flex flex-col items-center gap-2 h-20"
                onClick={() => setMode("system")}
              >
                <Monitor className="h-5 w-5" />
                <span className="text-xs font-semibold">Hệ thống</span>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* RAG Settings */}
        <Card className="border-border bg-card md:col-span-2">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Sliders className="h-5 w-5 text-primary" />
              <CardTitle>Cấu Hình RAG & Tham Số Trích Xuất</CardTitle>
            </div>
            <CardDescription>Căn chỉnh các chỉ số khi truy vấn tri thức y khoa.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="model-select">Mô Hình LLM Truy Vấn</Label>
                <select
                  id="model-select"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  <option value="gemini-2.5-flash">Gemini 2.5 Flash (Khuyên dùng - Nhanh & Chính xác)</option>
                  <option value="groq-llama-3">Groq Llama 3 (Mô hình nguồn mở)</option>
                </select>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label htmlFor="top-k" className="text-foreground">Số lượng Text Excerpts (Top K)</Label>
                  <span className="text-xs font-semibold text-primary">{topK}</span>
                </div>
                <input
                  id="top-k"
                  type="range"
                  min="5"
                  max="40"
                  value={topK}
                  onChange={(e) => setTopK(parseInt(e.target.value))}
                  className="w-full accent-primary"
                />
                <span className="text-xs text-muted-foreground block">
                  Số lượng đoạn trích từ tài liệu được gửi kèm câu hỏi vào prompt.
                </span>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label htmlFor="temp" className="text-foreground">Nhiệt Độ Sáng Tạo (Temperature)</Label>
                  <span className="text-xs font-semibold text-primary">{temperature}</span>
                </div>
                <input
                  id="temp"
                  type="range"
                  min="0.0"
                  max="1.0"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full accent-primary"
                />
                <span className="text-xs text-muted-foreground block">
                  Nhiệt độ càng thấp, câu trả lời của AI càng bám sát tài liệu gốc.
                </span>
              </div>
            </div>

            <Button onClick={handleSaveSettings} className="mt-2">
              Lưu cấu hình
            </Button>
          </CardContent>
        </Card>

        {/* API Keys */}
        <Card className="border-border bg-card md:col-span-2">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Key className="h-5 w-5 text-primary" />
              <CardTitle>Khóa API Bảo Mật (API Keys)</CardTitle>
            </div>
            <CardDescription>Cài đặt khóa API để giao tiếp với các nhà cung cấp mô hình ngôn ngữ lớn.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="gemini-key">GEMINI_API_KEY</Label>
                <Input
                  id="gemini-key"
                  type="password"
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  placeholder="Điền Gemini API Key..."
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="groq-key">GROQ_API_KEY</Label>
                <Input
                  id="groq-key"
                  type="password"
                  value={groqKey}
                  onChange={(e) => setGroqKey(e.target.value)}
                  placeholder="Điền Groq API Key..."
                />
              </div>
            </div>

            <Button onClick={handleSaveKeys} className="mt-2">
              Cập nhật Keys
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default SettingsPage;
