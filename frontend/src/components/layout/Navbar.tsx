import React from "react";
import { User, LogOut, Globe, Settings, Moon, Sun } from "lucide-react";
import { Link } from "react-router-dom";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeProvider";
import { GlobalSearch } from "./GlobalSearch";
import { NotificationBell } from "./NotificationBell";
import { useTranslation } from "react-i18next";

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const env = import.meta.env.VITE_ENVIRONMENT || "LOCAL";
  const { t, i18n } = useTranslation();

  const toggleLanguage = () => {
    i18n.changeLanguage(i18n.language === 'en' ? 'mr' : 'en');
  };

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  return (
    <header className="h-16 border-b bg-white dark:bg-slate-900 dark:border-slate-800 px-6 flex items-center justify-between sticky top-0 z-30 shadow-sm no-print transition-colors">
      <div className="flex items-center gap-3">
        <img
          src="/tracex-logo.png"
          alt="Trace-X"
          className="h-10 w-10 rounded-lg object-contain bg-white shadow-sm border border-slate-100 dark:border-slate-700"
        />
        <div>
          <h1 className="font-bold text-slate-800 dark:text-slate-200 dark:text-white text-base leading-tight transition-colors">
            Trace-X
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium transition-colors">
            Money-Trail Investigation Cockpit
          </p>
        </div>
        <Badge variant="outline" className="ml-3 border-amber-200 bg-amber-50 dark:bg-amber-900/30 text-amber-800 dark:border-amber-500/30 dark:text-amber-300 text-[11px] font-medium tracking-wide transition-colors">
          {env === "LOCAL" || env === "DEMO"
            ? "Training Prototype — Synthetic Data"
            : `${env}`}
        </Badge>
      </div>

      <div className="flex-1 flex justify-center px-6">
        <GlobalSearch />
      </div>

      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleTheme}
          className="h-8 w-8 p-0 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:text-slate-100 dark:hover:text-white transition-colors"
          title="Toggle Theme"
        >
          {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={toggleLanguage}
          className="h-8 px-2.5 text-xs text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 transition-colors"
          title="Toggle Language"
        >
          <Globe className="h-3.5 w-3.5 mr-1" />
          {i18n.language === 'en' ? 'मराठी' : 'EN'}
        </Button>

        {user && <NotificationBell />}

        {user ? (
          <div className="flex items-center gap-3 border-l dark:border-slate-800 pl-4 py-1 transition-colors">
            <Link
              to="/profile/preferences"
              className="h-8 w-8 bg-blue-100 dark:bg-blue-900/50 border border-blue-300 dark:border-blue-600 rounded-full flex items-center justify-center text-blue-700 dark:text-blue-400 font-semibold text-sm hover:bg-blue-200"
              title="Notification preferences"
            >
              <User className="h-4 w-4" />
            </Link>
            <div className="text-sm">
              <div className="flex items-center gap-1.5">
                <p className="font-semibold text-slate-800 dark:text-slate-200 leading-none">{user.name}</p>
                <Link to="/profile/preferences" title="Preferences">
                  <Settings className="h-3.5 w-3.5 text-slate-400 hover:text-slate-600 dark:hover:text-white dark:text-slate-400" />
                </Link>
                <Badge className={`text-[10px] px-1.5 py-0 uppercase ${
                  user.role === 'admin'
                    ? 'bg-emerald-600 text-white'
                    : user.role === 'supervisor'
                    ? 'bg-purple-600 text-white'
                    : 'bg-blue-600 text-white'
                }`}>
                  {user.role}
                </Badge>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{user.badge_number || user.email}</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={logout}
              className="h-8 px-2.5 text-xs text-slate-600 dark:text-slate-400 hover:text-red-600 hover:bg-red-50 dark:bg-red-900/40 border-slate-200 ml-2 focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-red-500"
              title="Log Out of Session"
            >
              <LogOut className="h-3.5 w-3.5 mr-1" /> {t('nav.logout', 'Log Out')}
            </Button>
          </div>
        ) : (
          <div className="text-xs text-slate-500 dark:text-slate-400 italic">Not logged in</div>
        )}
      </div>
    </header>
  );
};
