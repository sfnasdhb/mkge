import { useState } from "react";
import { motion } from "framer-motion";
import { Activity, ShieldCheck, Sparkles } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";
import LoginForm from "@/features/auth/components/LoginForm";
import RegisterForm from "@/features/auth/components/RegisterForm";

interface Props {
  defaultTab?: "login" | "register";
}

export default function AuthPage({ defaultTab = "login" }: Props) {
  const [tab, setTab] = useState<"login" | "register">(defaultTab);

  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      <BackgroundDecor />

      <div className="relative grid min-h-screen lg:grid-cols-[1.1fr_1fr]">
        <aside className="hidden flex-col justify-between border-r border-border/60 bg-card/30 p-12 lg:flex">
          <div className="flex items-center gap-2.5">
            <Logo />
            <span className="text-sm font-semibold tracking-tight">MKGE</span>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="max-w-md space-y-8"
          >
            <div className="space-y-4">
              <span className="inline-flex items-center gap-2 rounded-full border border-border/80 bg-card/60 px-3 py-1 text-xs font-medium text-muted-foreground">
                <span className="h-1.5 w-1.5 rounded-full bg-success" />
                Medical-grade · GraphRAG
              </span>
              <h1 className="text-4xl font-semibold leading-tight tracking-tight text-foreground">
                Knowledge Graph cho mọi tài liệu y khoa.
              </h1>
              <p className="text-md leading-relaxed text-muted-foreground">
                Trích xuất Thuốc · Bệnh · Triệu chứng từ PDF, kết nối thành đồ
                thị tri thức và hỏi đáp với trích dẫn nguồn chính xác.
              </p>
            </div>

            <ul className="space-y-3.5">
              {[
                { icon: Sparkles, text: "Dual-model verification chống hallucination" },
                { icon: Activity, text: "Real-time pipeline với trạng thái xử lý chi tiết" },
                { icon: ShieldCheck, text: "Citation chuẩn xác về trang PDF gốc" },
              ].map((item, i) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.15 + i * 0.05, duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                  className="flex items-start gap-3 text-sm text-foreground/80"
                >
                  <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary ring-1 ring-primary/20">
                    <item.icon className="h-3.5 w-3.5" />
                  </span>
                  {item.text}
                </motion.li>
              ))}
            </ul>
          </motion.div>

          <div className="space-y-3">
            <p className="text-xs uppercase tracking-widest text-muted-foreground/70">
              Đang được sử dụng tại
            </p>
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs font-medium text-muted-foreground">
              <span>Bach Mai Hospital</span>
              <span>·</span>
              <span>HMU Research Lab</span>
              <span>·</span>
              <span>VinUni Medicine</span>
            </div>
          </div>
        </aside>

        <main className="flex items-center justify-center p-6 sm:p-12">
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="w-full max-w-md"
          >
            <div className="mb-8 flex items-center gap-2.5 lg:hidden">
              <Logo />
              <span className="text-sm font-semibold tracking-tight">MKGE</span>
            </div>

            <div className="space-y-2 pb-6">
              <h2 className="text-2xl font-semibold tracking-tight">
                {tab === "login" ? "Đăng nhập" : "Tạo tài khoản"}
              </h2>
              <p className="text-sm text-muted-foreground">
                {tab === "login"
                  ? "Tiếp tục công việc nghiên cứu của bạn."
                  : "Bắt đầu khai thác tri thức từ tài liệu y khoa."}
              </p>
            </div>

            <Tabs value={tab} onValueChange={(v) => setTab(v as typeof tab)} className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="login">Đăng nhập</TabsTrigger>
                <TabsTrigger value="register">Đăng ký</TabsTrigger>
              </TabsList>
              <TabsContent value="login" className="mt-6">
                <LoginForm />
              </TabsContent>
              <TabsContent value="register" className="mt-6">
                <RegisterForm />
              </TabsContent>
            </Tabs>

            <p className="mt-8 text-xs text-muted-foreground">
              Bằng việc tiếp tục, bạn đồng ý với điều khoản sử dụng và chính
              sách bảo mật. Tài liệu tải lên được lưu trữ riêng tư.
            </p>
          </motion.div>
        </main>
      </div>
    </div>
  );
}

function Logo() {
  return (
    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm ring-1 ring-primary/20">
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

function BackgroundDecor() {
  return (
    <>
      <div
        aria-hidden
        className="absolute inset-0 bg-grid-pattern opacity-[0.03] [background-size:32px_32px] [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_70%)]"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -top-32 left-1/3 h-[500px] w-[500px] rounded-full bg-primary/10 blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -bottom-32 right-1/4 h-[400px] w-[400px] rounded-full bg-primary/5 blur-3xl"
      />
    </>
  );
}
