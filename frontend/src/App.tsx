import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { ThemeProvider } from "@/context/ThemeProvider";
import { MainLayout } from "@/components/layout/MainLayout";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { CasesListPage } from "@/pages/CasesListPage";
import { CaseDetailPage } from "@/pages/CaseDetailPage";
import { WatchlistPage } from "@/pages/WatchlistPage";
import { ClusterDetailPage } from "@/pages/ClusterDetailPage";
import { HealthPage } from "@/pages/HealthPage";
import { AdminUserPage } from "@/pages/AdminUserPage";
import { AuditLogPage } from "@/pages/AuditLogPage";
import { IngestionQueuePage } from "@/pages/IngestionQueuePage";
import { ProfilePreferencesPage } from "@/pages/ProfilePreferencesPage";
import { type RoleType } from "@/api/client";

// Role guard component (`Sub-phase 4.2` & `4.4`)
const RequireRole: React.FC<{ allowed: RoleType[]; children: React.ReactElement }> = ({ allowed, children }) => {
  const { role } = useAuth();
  if (!role || !allowed.includes(role)) {
    return (
      <div className="p-8 bg-red-50 dark:bg-slate-900 rounded-lg border border-red-200 dark:border-red-500/40 text-center max-w-md mx-auto my-12 space-y-3">
        <div className="text-red-600 dark:text-red-400 font-bold text-lg">403 Access Denied</div>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Your current operational role ({role?.toUpperCase() || 'UNKNOWN'}) does not have permission to access this administration or audit screen.
        </p>
      </div>
    );
  }
  return children;
};

export const App: React.FC = () => {
  return (
    <ThemeProvider defaultTheme="light" storageKey="vite-ui-theme">
      <AuthProvider>
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            
            {/* Main protected layout (`Sub-phase 4.4`) */}
            <Route element={<MainLayout />}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/cases" element={<CasesListPage />} />
              <Route path="/cases/:caseId" element={<CaseDetailPage />} />
              <Route path="/watchlist" element={<WatchlistPage />} />
              <Route path="/network/clusters/:clusterId" element={<ClusterDetailPage />} />
              <Route path="/import" element={<IngestionQueuePage />} />
              <Route path="/profile/preferences" element={<ProfilePreferencesPage />} />
              <Route
                path="/health"
                element={
                  <RequireRole allowed={["admin"]}>
                    <HealthPage />
                  </RequireRole>
                }
              />
              <Route
                path="/audit"
                element={
                  <RequireRole allowed={["supervisor", "admin"]}>
                    <AuditLogPage />
                  </RequireRole>
                }
              />
              <Route
                path="/admin/users"
                element={
                  <RequireRole allowed={["admin"]}>
                    <AdminUserPage />
                  </RequireRole>
                }
              />
            </Route>

          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
