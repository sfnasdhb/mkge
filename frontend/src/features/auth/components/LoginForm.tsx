import { useState } from "react";
import { Link } from "react-router-dom";
import { useLogin } from "../hooks";

export default function LoginForm() {
  const login = useLogin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login.mutate({ email, password });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          placeholder="you@example.com"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Mật khẩu</label>
        <input
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          placeholder="••••••••"
        />
      </div>
      <button
        type="submit"
        disabled={login.isPending}
        className="w-full rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-50 transition-colors"
      >
        {login.isPending ? "Đang đăng nhập..." : "Đăng nhập"}
      </button>
      <p className="text-center text-sm text-gray-500">
        Chưa có tài khoản?{" "}
        <Link to="/register" className="font-medium text-brand-600 hover:underline">
          Đăng ký
        </Link>
      </p>
    </form>
  );
}
