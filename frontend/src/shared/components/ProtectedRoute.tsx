import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/features/auth/store";

export default function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated());
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}
