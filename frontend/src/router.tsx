import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "@/shared/components/ProtectedRoute";
import AppShell from "@/shared/components/layout/AppShell";
import AuthPage from "@/pages/AuthPage";
import DocumentsPage from "@/pages/DocumentsPage";
import GraphPage from "@/pages/GraphPage";
import { QueryPage } from "@/pages/QueryPage";
import AdminPage from "@/pages/AdminPage";
import QueryHistoryPage from "@/pages/QueryHistoryPage";
import SettingsPage from "@/pages/SettingsPage";

export default function Router() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<AuthPage defaultTab="login" />} />
        <Route path="/register" element={<AuthPage defaultTab="register" />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/graph" element={<GraphPage />} />
            <Route path="/graph/:documentId" element={<GraphPage />} />
            <Route path="/ask" element={<QueryPage />} />
            <Route path="/history" element={<QueryHistoryPage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/documents" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
