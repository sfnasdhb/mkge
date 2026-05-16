import api from "@/shared/lib/axios";
import type { AuthTokens } from "@/shared/types";

export const authApi = {
  register: (data: { email: string; password: string; full_name: string }) =>
    api.post<AuthTokens>("/auth/register", data).then((r) => r.data),

  login: (data: { email: string; password: string }) =>
    api.post<AuthTokens>("/auth/login", data).then((r) => r.data),

  logout: (refresh_token: string) =>
    api.post("/auth/logout", { refresh_token }),

  me: () => api.get("/users/me").then((r) => r.data),
};
