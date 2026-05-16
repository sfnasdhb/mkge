import { useState } from "react";
import { Link } from "react-router-dom";
import { useRegister } from "../hooks";

export default function RegisterForm() {
  const register = useRegister();
  const [form, setForm] = useState({ email: "", password: "", full_name: "" });

  const update = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((p) => ({ ...p, [field]: e.target.value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    register.mutate(form);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Họ và tên</label>
        <input
          type="text"
          required
          value={form.full_name}
          onChange={update("full_name")}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          placeholder="Nguyễn Văn A"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
        <input
          type="email"
          required
          value={form.email}
          onChange={update("email")}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          placeholder="you@example.com"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Mật khẩu</label>
        <input
          type="password"
          required
          minLength={8}
          value={form.password}
          onChange={update("password")}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          placeholder="Tối thiểu 8 ký tự"
        />
      </div>
      <button
        type="submit"
        disabled={register.isPending}
        className="w-full rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-50 transition-colors"
      >
        {register.isPending ? "Đang tạo tài khoản..." : "Đăng ký"}
      </button>
      <p className="text-center text-sm text-gray-500">
        Đã có tài khoản?{" "}
        <Link to="/login" className="font-medium text-brand-600 hover:underline">
          Đăng nhập
        </Link>
      </p>
    </form>
  );
}
