import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/features/auth/store";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

const AUTH_PATHS = ["/auth/login", "/auth/register", "/auth/refresh"];
const isAuthPath = (url?: string) => !!url && AUTH_PATHS.some((p) => url.includes(p));

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token && !isAuthPath(config.url)) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Single-flight refresh: nếu nhiều request fail 401 cùng lúc,
// chỉ gọi /auth/refresh MỘT lần và queue phần còn lại
let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const { refreshToken, setTokens, clearAuth } = useAuthStore.getState();
  if (!refreshToken) throw new Error("No refresh token");

  try {
    const { data } = await axios.post("/api/v1/auth/refresh", {
      refresh_token: refreshToken,
    });
    setTokens(data.access_token, data.refresh_token);
    return data.access_token;
  } catch (err) {
    clearAuth();
    throw err;
  }
}

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (
      error.response?.status !== 401 ||
      !original ||
      original._retry ||
      isAuthPath(original.url)
    ) {
      return Promise.reject(error);
    }

    original._retry = true;

    try {
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
      }
      const newToken = await refreshPromise;
      original.headers.Authorization = `Bearer ${newToken}`;
      return api(original);
    } catch {
      if (typeof window !== "undefined") window.location.href = "/login";
      return Promise.reject(error);
    }
  }
);

export default api;
