import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { AlertCircle, Lock, Mail, User } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { registerSchema, type RegisterInput } from "../schemas";
import { useRegister } from "../hooks";

export default function RegisterForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterInput>({
    resolver: zodResolver(registerSchema),
    defaultValues: { full_name: "", email: "", password: "" },
  });
  const reg = useRegister();

  return (
    <form onSubmit={handleSubmit((v) => reg.mutate(v))} className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="reg-name">Họ và tên</Label>
        <div className="relative">
          <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input id="reg-name" placeholder="Nguyễn Văn A" className="pl-9" {...register("full_name")} />
        </div>
        {errors.full_name ? <FieldError message={errors.full_name.message!} /> : null}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="reg-email">Email</Label>
        <div className="relative">
          <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input id="reg-email" type="email" autoComplete="email" placeholder="bsi@benhvien.vn" className="pl-9" {...register("email")} />
        </div>
        {errors.email ? <FieldError message={errors.email.message!} /> : null}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="reg-password">Mật khẩu</Label>
        <div className="relative">
          <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input id="reg-password" type="password" autoComplete="new-password" placeholder="Tối thiểu 8 ký tự" className="pl-9" {...register("password")} />
        </div>
        {errors.password ? (
          <FieldError message={errors.password.message!} />
        ) : (
          <p className="text-xs text-muted-foreground">Tối thiểu 8 ký tự, tối đa 72 ký tự.</p>
        )}
      </div>

      <Button type="submit" loading={reg.isPending} className="w-full" size="lg">
        Tạo tài khoản
      </Button>
    </form>
  );
}

function FieldError({ message }: { message: string }) {
  return (
    <p className="flex items-center gap-1.5 text-xs text-destructive">
      <AlertCircle className="h-3.5 w-3.5" />
      {message}
    </p>
  );
}
