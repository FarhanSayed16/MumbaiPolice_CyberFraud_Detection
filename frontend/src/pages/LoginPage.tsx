import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/context/AuthContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Lock, User, AlertCircle, CheckCircle2, Database, Key } from 'lucide-react';

const envName = (import.meta.env.VITE_ENVIRONMENT || 'LOCAL').toUpperCase();
/** Seed / quick-role panel — LOCAL only; hidden for DEMO/DCP builds */
const showLocalSeedTools = envName === 'LOCAL';

export const LoginPage: React.FC = () => {
  const { t } = useTranslation();
  const { login, seedInitialUsers } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [seedStatus, setSeedStatus] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login({ email, password });
      navigate('/cases');
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Authentication failed. Verify backend is active.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  const handleSeed = async () => {
    if (!showLocalSeedTools) return;
    setLoading(true);
    setSeedStatus(null);
    setError(null);
    try {
      const res = await seedInitialUsers();
      setSeedStatus(res.message || 'Seeded local demo roles. Use credentials from local seed docs.');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to seed initial users (local only).');
    } finally {
      setLoading(false);
    }
  };

  const selectRoleDemo = (roleEmail: string) => {
    if (!showLocalSeedTools) return;
    setEmail(roleEmail);
    setPassword('SecurePolice@2026');
    setError(null);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 p-4">
      <div className="w-full max-w-lg space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center mb-2">
            <img
              src="/tracex-logo.png"
              alt="Trace-X"
              className="h-20 w-20 rounded-2xl object-contain shadow-md bg-white"
            />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white dark:text-slate-100">
            {t('login.title', 'Trace-X')}
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 dark:text-slate-400">
            {t('login.subtitle', 'Money-Trail Investigation Cockpit — Mumbai Police / Maharashtra Cyber')}
          </p>
        </div>

        <Card className="border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 dark:bg-slate-900 shadow-2xl">
          <CardHeader className="space-y-1 pb-4">
            <CardTitle className="text-lg font-semibold text-slate-900 dark:text-white dark:text-slate-100 flex items-center gap-2">
              <Lock className="h-4 w-4 text-blue-600 dark:text-blue-400" /> {t('login.portalTitle', 'Secure Law Enforcement Portal')}
            </CardTitle>
            <CardDescription className="text-slate-500 dark:text-slate-400">
              {t('login.portalDescription', 'Access is strictly restricted to authorized officers. All actions are audited.')}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/40 border border-red-200 text-red-900 text-sm flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {seedStatus && (
              <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-900/40 border border-emerald-200 text-emerald-900 text-sm flex items-start gap-2">
                <CheckCircle2 className="h-5 w-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                <span>{seedStatus}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 dark:text-slate-400">
                  {t('login.emailLabel', 'Official Email')}
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-2.5 h-4 w-4 text-slate-500 dark:text-slate-400" />
                  <input
                    type="email"
                    required
                    autoComplete="username"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="officer@example.gov.in"
                    className="w-full pl-9 pr-3 py-2 rounded-md bg-white dark:bg-slate-900 border border-slate-200 text-slate-900 dark:text-slate-100 text-sm focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 dark:text-slate-400">
                  {t('login.passwordLabel', 'Password')}
                </label>
                <div className="relative">
                  <Key className="absolute left-3 top-2.5 h-4 w-4 text-slate-500 dark:text-slate-400" />
                  <input
                    type="password"
                    required
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full pl-9 pr-3 py-2 rounded-md bg-white dark:bg-slate-900 border border-slate-200 text-slate-900 dark:text-slate-100 text-sm focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-500 !text-white font-medium py-2.5 shadow-md"
              >
                {loading ? t('login.submitting', 'Authenticating Session...') : t('login.submit', 'Log In')}
              </Button>
            </form>

            {showLocalSeedTools && (
              <div className="pt-4 border-t border-slate-200/80 dark:border-slate-700 space-y-3">
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 dark:text-slate-400">
                  <span className="font-semibold">Local demo only</span>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleSeed}
                    disabled={loading}
                    className="h-7 text-xs border-slate-200 bg-slate-50 dark:bg-slate-950 hover:bg-slate-100 text-slate-600 dark:text-slate-400"
                  >
                    <Database className="h-3 w-3 mr-1" /> Seed Roles
                  </Button>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <button type="button" onClick={() => selectRoleDemo('officer.mumbai@maharashtracyber.gov.in')} className="px-2.5 py-1.5 rounded bg-white dark:bg-slate-900 hover:bg-slate-100 border border-slate-200 text-left text-xs">
                    <div className="font-semibold text-blue-700 dark:text-blue-400">Officer</div>
                  </button>
                  <button type="button" onClick={() => selectRoleDemo('supervisor.mumbai@maharashtracyber.gov.in')} className="px-2.5 py-1.5 rounded bg-white dark:bg-slate-900 hover:bg-slate-100 border border-slate-200 text-left text-xs">
                    <div className="font-semibold text-purple-700 dark:text-purple-400">Supervisor</div>
                  </button>
                  <button type="button" onClick={() => selectRoleDemo('admin.mumbai@maharashtracyber.gov.in')} className="px-2.5 py-1.5 rounded bg-white dark:bg-slate-900 hover:bg-slate-100 border border-slate-200 text-left text-xs">
                    <div className="font-semibold text-emerald-700 dark:text-emerald-400">Admin</div>
                  </button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
