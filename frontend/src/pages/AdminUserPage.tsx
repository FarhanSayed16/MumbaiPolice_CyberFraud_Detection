import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { userService, type UserProfile, type CreateUserData, type RoleType } from '@/api/client';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Users, UserPlus, RefreshCw, AlertCircle, CheckCircle2, UserCheck, UserX } from 'lucide-react';

export const AdminUserPage: React.FC = () => {
  const { t } = useTranslation();
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);

  const [email, setEmail] = useState<string>('');
  const [name, setName] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [role, setRole] = useState<RoleType>('officer');
  const [badgeNumber, setBadgeNumber] = useState<string>('');
  const [unit, setUnit] = useState<string>('Cyber Crime Investigation Cell');
  const [creating, setCreating] = useState<boolean>(false);

  const loadUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await userService.listUsers();
      setUsers(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || t('admin.fetchError', 'Failed to fetch user list. Ensure you are logged in as Admin.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      const payload: CreateUserData = {
        email,
        name,
        password,
        role,
        badge_number: badgeNumber || undefined,
        police_station_unit: unit || undefined,
      };
      await userService.createUser(payload);
      setShowCreateModal(false);
      setEmail('');
      setName('');
      setBadgeNumber('');
      await loadUsers();
    } catch (err: any) {
      setError(err?.response?.data?.detail || t('admin.createError', 'Failed to create user account.'));
    } finally {
      setCreating(false);
    }
  };

  const handleToggleStatus = async (user: UserProfile) => {
    try {
      const updated = await userService.toggleStatus(user.id, !user.is_active);
      setUsers(users.map((u) => (u.id === updated.id ? updated : u)));
    } catch (err: any) {
      alert(err?.response?.data?.detail || t('admin.statusError', 'Failed to update status.'));
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-800 dark:text-slate-200 flex items-center gap-2">
            <Users className="h-6 w-6 text-blue-600" /> {t('admin.pageTitle', 'Law Enforcement User Administration')}
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            {t('admin.pageSubtitle', 'Provision roles, manage unit assignments, and control platform access. No user history is ever hard-deleted.')}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={loadUsers}
            disabled={loading}
            className="gap-2 border-slate-200 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:bg-slate-950 text-slate-700 dark:text-slate-300"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> {t('admin.refresh', 'Refresh')}
          </Button>
          <Button
            size="sm"
            onClick={() => setShowCreateModal(true)}
            className="gap-2 bg-blue-600 hover:bg-blue-700 text-white"
          >
            <UserPlus className="h-4 w-4" /> {t('admin.provisionButton', 'Provision New Officer / User')}
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/40 border border-red-200 text-red-800 text-sm flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">{t('admin.errorTitle', 'Administration Error')}</div>
            <div className="text-red-700 mt-0.5">{error}</div>
          </div>
        </div>
      )}

      {showCreateModal && (
        <Card className="border-blue-200 bg-white dark:bg-slate-900 shadow-md">
          <CardHeader className="pb-3 border-b border-slate-200 dark:border-slate-800">
            <CardTitle className="text-lg font-semibold text-slate-800 dark:text-slate-200">{t('admin.createModalTitle', 'Provision New Law Enforcement Account')}</CardTitle>
            <CardDescription className="text-slate-500 dark:text-slate-400">
              {t('admin.createModalDescription', 'Assign appropriate BNSS investigation role (Officer, Supervisor, Admin).')}
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-4">
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase">{t('admin.nameLabel', 'Official Name & Rank')}</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. A. P. Kadam (Inspector)"
                    className="w-full px-3 py-2 rounded-md bg-white dark:bg-slate-900 border border-slate-300 text-slate-800 dark:text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase">{t('admin.emailLabel', 'Official Email Address')}</label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="kadam.a@maharashtracyber.gov.in"
                    className="w-full px-3 py-2 rounded-md bg-white dark:bg-slate-900 border border-slate-300 text-slate-800 dark:text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase">{t('admin.roleLabel', 'Operational Role')}</label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value as RoleType)}
                    className="w-full px-3 py-2 rounded-md bg-white dark:bg-slate-900 border border-slate-300 text-slate-800 dark:text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="officer">{t('admin.roleOfficer', 'Officer (Investigating IO)')}</option>
                    <option value="supervisor">{t('admin.roleSupervisor', 'Supervisor (SHO / ACP)')}</option>
                    <option value="admin">{t('admin.roleAdmin', 'Admin (System Config)')}</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase">{t('admin.badgeLabel', 'Badge / ID Number')}</label>
                  <input
                    type="text"
                    value={badgeNumber}
                    onChange={(e) => setBadgeNumber(e.target.value)}
                    placeholder="e.g. MH-CY-4921"
                    className="w-full px-3 py-2 rounded-md bg-white dark:bg-slate-900 border border-slate-300 text-slate-800 dark:text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase">{t('admin.passwordLabel', 'Initial Password')}</label>
                  <input
                    type="password"
                    required
                    autoComplete="new-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3 py-2 rounded-md bg-white dark:bg-slate-900 border border-slate-300 text-slate-800 dark:text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase">{t('admin.unitLabel', 'Police Station / Cyber Unit')}</label>
                <input
                  type="text"
                  value={unit}
                  onChange={(e) => setUnit(e.target.value)}
                  placeholder="e.g. Cyber Crime Investigation Cell, BKC Mumbai"
                  className="w-full px-3 py-2 rounded-md bg-white dark:bg-slate-900 border border-slate-300 text-slate-800 dark:text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowCreateModal(false)}
                  className="border-slate-200 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:bg-slate-950"
                >
                  {t('admin.cancel', 'Cancel')}
                </Button>
                <Button type="submit" disabled={creating} className="bg-blue-600 hover:bg-blue-700 text-white">
                  {creating ? t('admin.provisioning', 'Provisioning...') : t('admin.confirmProvision', 'Confirm Account Provisioning')}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <Card className="border-slate-200 bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
        <CardHeader className="pb-3 border-b border-slate-200 dark:border-slate-800 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-md font-semibold text-slate-800 dark:text-slate-200">{t('admin.tableTitle', 'Active & Inactive Platform Accounts')}</CardTitle>
            <CardDescription className="text-slate-500 dark:text-slate-400">
              {t('admin.tableDescription', 'Total {{count}} accounts provisioned across Mumbai Police.', { count: users.length })}
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  <th className="py-3.5 px-4">{t('admin.colName', 'Officer / Name')}</th>
                  <th className="py-3.5 px-4">{t('admin.colEmail', 'Contact Email')}</th>
                  <th className="py-3.5 px-4">{t('admin.colRole', 'Role')}</th>
                  <th className="py-3.5 px-4">{t('admin.colBadge', 'Badge & Unit')}</th>
                  <th className="py-3.5 px-4">{t('admin.colStatus', 'Account Status')}</th>
                  <th className="py-3.5 px-4 text-right">{t('admin.colActions', 'Actions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800 text-sm">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                    <td className="py-3 px-4 font-medium text-slate-800 dark:text-slate-200">{u.name}</td>
                    <td className="py-3 px-4 text-slate-600 dark:text-slate-400 font-mono text-xs">{u.email}</td>
                    <td className="py-3 px-4">
                      <Badge
                        variant={
                          u.role === 'admin'
                            ? 'default'
                            : u.role === 'supervisor'
                            ? 'secondary'
                            : 'outline'
                        }
                        className={
                          u.role === 'admin'
                            ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                            : u.role === 'supervisor'
                            ? 'bg-purple-100 text-purple-800 border-purple-200'
                            : 'border-blue-200 text-blue-700 bg-blue-50 dark:bg-blue-900/40'
                        }
                      >
                        {u.role.toUpperCase()}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-500 dark:text-slate-400">
                      <div className="font-semibold text-slate-700 dark:text-slate-300">{u.badge_number || 'N/A'}</div>
                      <div className="truncate max-w-[200px]">{u.police_station_unit || 'Central Cyber'}</div>
                    </td>
                    <td className="py-3 px-4">
                      {u.is_active ? (
                        <span className="inline-flex items-center gap-1.5 text-xs text-emerald-700 bg-emerald-50 dark:bg-emerald-900/40 px-2 py-0.5 rounded border border-emerald-200">
                          <CheckCircle2 className="h-3.5 w-3.5" /> {t('admin.statusActive', 'Active')}
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 text-xs text-red-700 bg-red-50 dark:bg-red-900/40 px-2 py-0.5 rounded border border-red-200">
                          <AlertCircle className="h-3.5 w-3.5" /> {t('admin.statusInactive', 'Deactivated')}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleToggleStatus(u)}
                        className={`h-7 text-xs ${
                          u.is_active
                            ? 'border-red-200 bg-red-50 dark:bg-red-900/40 hover:bg-red-100 text-red-700'
                            : 'border-emerald-200 bg-emerald-50 dark:bg-emerald-900/40 hover:bg-emerald-100 text-emerald-700'
                        }`}
                      >
                        {u.is_active ? (
                          <>
                            <UserX className="h-3 w-3 mr-1" /> {t('admin.deactivate', 'Deactivate')}
                          </>
                        ) : (
                          <>
                            <UserCheck className="h-3 w-3 mr-1" /> {t('admin.reactivate', 'Reactivate')}
                          </>
                        )}
                      </Button>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && !loading && (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500 dark:text-slate-400">
                      {t('admin.empty', 'No user records found. Provision accounts or run seed initialization.')}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
