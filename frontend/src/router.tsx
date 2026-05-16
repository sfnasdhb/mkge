import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "@/shared/components/ProtectedRoute";
import AppShell from "@/shared/components/layout/AppShell";
import AuthPage from "@/pages/AuthPage";
import DocumentsPage from "@/pages/DocumentsPage";
import PlaceholderPage from "@/pages/PlaceholderPage";

export default function Router() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<AuthPage defaultTab="login" />} />
        <Route path="/register" element={<AuthPage defaultTab="register" />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route path="/documents" element={<DocumentsPage />} />
            <Route
              path="/graph"
              element={
                <PlaceholderPage
                  title="Đồ thị tri thức"
                  description="Cytoscape viewer sẽ có trong Phase 2."
                  phase="Phase 2"
                />
              }
            />
            <Route
              path="/ask"
              element={
                <PlaceholderPage
                  title="Hỏi đáp AI"
                  description="GraphRAG chat sẽ có trong Phase 3."
                  phase="Phase 3"
                />
              }
            />
            <Route
              path="/history"
              element={
                <PlaceholderPage
                  title="Lịch sử truy vấn"
                  description="Lưu trữ các câu hỏi đã đặt."
                  phase="Phase 3"
                />
              }
            />
            <Route
              path="/admin"
              element={
                <PlaceholderPage
                  title="Quản trị hệ thống"
                  description="Dashboard quản trị sẽ có trong Phase 4."
                  phase="Phase 4"
                />
              }
            />
            <Route
              path="/settings"
              element={
                <PlaceholderPage
                  title="Cài đặt"
                  description="Cấu hình tài khoản, API keys và chủ đề."
                  phase="Phase 4"
                />
              }
            />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/documents" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
