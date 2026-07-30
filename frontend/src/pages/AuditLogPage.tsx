import { useTranslation } from 'react-i18next';
import React, { useEffect, useState } from 'react';
import { auditService, type AuditLogItem } from '@/api/client';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { ShieldAlert, RefreshCw, Filter, Database, Lock, AlertCircle } from 'lucide-react';

export const AuditLogPage: React.FC = () => {
  const { t } = useTranslation();
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [actionFilter, setActionFilter] = useState<string>('');
  const [resourceFilter, setResourceFilter] = useState<string>('');
  const [emailFilter, setEmailFilter] = useState<string>('');

  const loadAuditLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = { limit: 200 };
      if (actionFilter) params.action = actionFilter;
      if (resourceFilter) params.resource_type = resourceFilter;
      if (emailFilter) params.user_email = emailFilter;

      const data = await auditService.queryLogs(params);
      setLogs(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to query audit logs. Ensure you are logged in as Supervisor or Admin.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAuditLogs();
  }, []);

  const clearFilters = () => {
    setActionFilter('');
    setResourceFilter('');
    setEmailFilter('');
    setTimeout(loadAuditLogs, 50);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <ShieldAlert className="h-6 w-6 text-purple-600" /> Immutable Governance Audit Trail
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            {t("auditTrail.subtitle")}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={loadAuditLogs}
            disabled={loading}
            className="border-slate-300 bg-white dark:bg-slate-900 hover:bg-slate-100 text-slate-700 dark:text-slate-300 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} /> Refresh Trail
          </Button>
        </div>
      </div>

      {/* Evidentiary Guarantee Banner (`Sub-phase 4.3`) */}
      <div className="p-4 rounded-lg bg-purple-50 dark:bg-purple-900/40 border border-purple-200 dark:border-purple-700 text-purple-900 dark:text-purple-200 text-sm flex items-start gap-3">
        <Lock className="h-5 w-5 text-purple-600 flex-shrink-0 mt-0.5" />
        <div>
          <div className="font-semibold text-purple-900 dark:text-purple-100">{t("auditTrail.complianceGuar")}</div>
          <div className="text-purple-800 dark:text-purple-200 mt-0.5">
            {t("auditTrail.complianceSub")}
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/40 border border-red-200 text-red-900 text-sm flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Query Permission Error</div>
            <div className="text-slate-600 dark:text-slate-400 mt-0.5">{error}</div>
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <Card className="border-slate-200 bg-white dark:bg-slate-900">
        <CardHeader className="pb-3 border-b border-slate-200 dark:border-slate-800">
          <CardTitle className="text-sm font-semibold text-slate-600 dark:text-slate-400 flex items-center gap-2">
            <Filter className="h-4 w-4 text-blue-600" /> Filter Governance Records
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">Officer / Admin Email</label>
              <input
                type="text"
                value={emailFilter}
                onChange={(e) => setEmailFilter(e.target.value)}
                placeholder="e.g. officer.mumbai@..."
                className="w-full px-3 py-1.5 rounded bg-slate-50 dark:bg-slate-950 border border-slate-200 text-slate-900 dark:text-slate-100 text-xs focus:outline-none focus:border-blue-500"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">Action String</label>
              <input
                type="text"
                value={actionFilter}
                onChange={(e) => setActionFilter(e.target.value)}
                placeholder="e.g. LOGIN_SUCCESS, CREATE_CASE"
                className="w-full px-3 py-1.5 rounded bg-slate-50 dark:bg-slate-950 border border-slate-200 text-slate-900 dark:text-slate-100 text-xs focus:outline-none focus:border-blue-500"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">Resource Type</label>
              <select
                value={resourceFilter}
                onChange={(e) => setResourceFilter(e.target.value)}
                className="w-full px-3 py-1.5 rounded bg-slate-50 dark:bg-slate-950 border border-slate-200 text-slate-900 dark:text-slate-100 text-xs focus:outline-none focus:border-blue-500"
              >
                <option value="">{t("auditTrail.allResources")}</option>
                <option value="AUTH">AUTH (Login / Logout)</option>
                <option value="USER">USER (Provisioning / Status)</option>
                <option value="CASE">CASE (Intake / Triage)</option>
                <option value="NOTICE">NOTICE (BNSS Orders)</option>
                <option value="EVIDENCE">EVIDENCE (Attachments)</option>
              </select>
            </div>
            <div className="flex items-end gap-2">
              <Button onClick={loadAuditLogs} size="sm" className="bg-blue-600 hover:bg-blue-500 text-slate-900 dark:text-slate-100 flex-1 text-xs focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900">
                Apply Filters
              </Button>
              <Button onClick={clearFilters} size="sm" variant="outline" className="border-slate-300 bg-slate-100 text-slate-600 dark:text-slate-400 text-xs focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900">
                Clear
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Audit Log Table */}
      <Card className="border-slate-200 bg-white dark:bg-slate-900 overflow-hidden">
        <CardHeader className="pb-3 border-b border-slate-200 dark:border-slate-800">
          <CardTitle className="text-md font-semibold text-slate-900 dark:text-slate-100">{t("auditTrail.tableTitle")}</CardTitle>
          <CardDescription className="text-slate-500 dark:text-slate-400">
            Displaying top {logs.length} immutable events ordered by timestamp descending.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  <th className="py-3.5 px-4">Timestamp (UTC)</th>
                  <th className="py-3.5 px-4">Actor / Email</th>
                  <th className="py-3.5 px-4">Action</th>
                  <th className="py-3.5 px-4">Resource & ID</th>
                  <th className="py-3.5 px-4">Client IP</th>
                  <th className="py-3.5 px-4">Event Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800 text-xs font-mono">
                {loading && logs.length === 0 ? (
                  [1, 2, 3, 4, 5].map((i) => (
                    <tr key={i} className="animate-pulse">
                      <td className="py-3 px-4"><Skeleton className="h-4 w-24 bg-slate-100" /></td>
                      <td className="py-3 px-4"><Skeleton className="h-4 w-32 bg-slate-100" /></td>
                      <td className="py-3 px-4"><Skeleton className="h-6 w-24 bg-slate-100" /></td>
                      <td className="py-3 px-4"><Skeleton className="h-4 w-32 bg-slate-100 mb-1" /><Skeleton className="h-3 w-48 bg-slate-100" /></td>
                      <td className="py-3 px-4"><Skeleton className="h-4 w-20 bg-slate-100" /></td>
                      <td className="py-3 px-4"><Skeleton className="h-10 w-48 bg-slate-100" /></td>
                    </tr>
                  ))
                ) : logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-100/40 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 text-slate-600 dark:text-slate-400 whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-blue-700 dark:text-blue-400 font-semibold">
                      {log.user_email || 'SYSTEM'}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded font-sans font-semibold ${
                        log.action.includes('SUCCESS') || log.action.includes('CREATE')
                          ? 'bg-emerald-50 dark:bg-emerald-900/40 text-emerald-700 border border-emerald-200'
                          : log.action.includes('FAILED')
                          ? 'bg-red-50 dark:bg-red-900/40 text-red-700 border border-red-200'
                          : 'bg-slate-100 text-slate-600 dark:text-slate-400 border border-slate-300'
                      }`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900 dark:text-slate-100">{log.resource_type}</div>
                      <div className="text-slate-500 dark:text-slate-400 text-[11px]">{log.resource_id || '—'}</div>
                    </td>
                    <td className="py-3 px-4 text-slate-500 dark:text-slate-400">
                      {log.ip_address || '—'}
                    </td>
                    <td className="py-3 px-4 text-slate-600 dark:text-slate-400">
                      {log.details_json && Object.keys(log.details_json).length > 0 ? (
                        <pre className="text-[11px] bg-slate-50 dark:bg-slate-950 p-1.5 rounded border border-slate-200 max-w-[280px] overflow-x-auto">
                          {JSON.stringify(log.details_json, null, 2)}
                        </pre>
                      ) : (
                        <span className="text-slate-500 dark:text-slate-400 font-sans">—</span>
                      )}
                    </td>
                  </tr>
                ))}
                {logs.length === 0 && !loading && (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500 dark:text-slate-400 font-sans">
                      No audit events match your criteria. Perform actions on the platform to generate immutable trail.
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
