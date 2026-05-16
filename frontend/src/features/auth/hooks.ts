import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { authApi } from "./api";
import { useAuthStore } from "./store";

export function useLogin() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      if (data.user) {
        setAuth(data.user, data.access_token, data.refresh_token);
        toast.success(`Chào mừng trở lại, ${data.user.full_name}`);
        navigate("/documents");
      }
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.error?.message ?? "Đăng nhập thất bại");
    },
  });
}

export function useRegister() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: authApi.register,
    onSuccess: (data) => {
      if (data.user) {
        setAuth(data.user, data.access_token, data.refresh_token);
        toast.success("Tài khoản đã được tạo");
        navigate("/documents");
      }
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.error?.message ?? "Đăng ký thất bại");
    },
  });
}

export function useLogout() {
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const navigate = useNavigate();

  return () => {
    if (refreshToken) authApi.logout(refreshToken).catch(() => {});
    clearAuth();
    navigate("/login");
  };
}
