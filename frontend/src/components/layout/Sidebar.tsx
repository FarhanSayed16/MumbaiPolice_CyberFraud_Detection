import React from "react";
import { NavLink } from "react-router-dom";
import { LayoutDashboard, FolderGit2, ShieldAlert, FileSpreadsheet, Activity, Users, Lock } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/context/AuthContext";
import { useTranslation } from "react-i18next";

export const Sidebar: React.FC = () => {
  const { role } = useAuth();
  const { t } = useTranslation();

  const navItems = [
    { nameKey: "nav.dashboard", path: "/dashboard", icon: LayoutDashboard, allowed: ["officer", "supervisor", "admin"] },
    { nameKey: "nav.activeCases", path: "/cases", icon: FolderGit2, allowed: ["officer", "supervisor", "admin"] },
    { nameKey: "nav.watchlistRings", path: "/watchlist", icon: ShieldAlert, disabled: false, allowed: ["officer", "supervisor", "admin"] },
    { nameKey: "nav.bulkImport", path: "/import", icon: FileSpreadsheet, disabled: false, allowed: ["officer", "supervisor", "admin"] },
    { nameKey: "nav.systemHealth", path: "/health", icon: Activity, allowed: ["admin"] },
    { nameKey: "nav.auditTrail", path: "/audit", icon: Lock, allowed: ["supervisor", "admin"] },
    { nameKey: "nav.userAdmin", path: "/admin/users", icon: Users, allowed: ["admin"] },
  ];

  return (
    <aside className="w-64 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between h-[calc(100vh-4rem)] sticky top-16 shadow-sm">
      <div className="p-4 space-y-1">
        <div className="px-3 py-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
          {t("nav.investigationTriage", "Investigation Triage")}
        </div>
        {navItems.map((item) => {
          if (!role || !item.allowed.includes(role)) {
            return null;
          }

          const Icon = item.icon;
          const label = t(item.nameKey);
          if (item.disabled) {
            return (
              <div
                key={item.nameKey}
                className="flex items-center gap-3 px-3 py-2 text-sm font-medium text-slate-400 rounded-md cursor-not-allowed select-none"
                title="Coming soon"
              >
                <Icon className="h-4 w-4 text-slate-300 dark:text-slate-600" />
                <span>{label}</span>
                <span className="ml-auto text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 px-1.5 py-0.5 rounded">
                  Soon
                </span>
              </div>
            );
          }
          return (
            <NavLink
              key={item.nameKey}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors",
                  isActive
                    ? "bg-blue-50 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400 font-semibold border-l-4 border-blue-600"
                    : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white"
                )
              }
            >
              <Icon className="h-4 w-4" />
              <span>{label}</span>
            </NavLink>
          );
        })}
      </div>

      <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50">
        <div className="text-xs text-slate-500 dark:text-slate-400 space-y-1">
          <p className="font-semibold text-slate-700 dark:text-slate-300 dark:text-slate-600">{t("nav.govSoftware", "Gov Proprietary Software")}</p>
          <p>{t("nav.maharashtraCyber", "Maharashtra Cyber / Mumbai Police")}</p>
          <p className="font-mono text-[10px] text-slate-400">Auth Engine: RBAC</p>
        </div>
      </div>
    </aside>
  );
};
