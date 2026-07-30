import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/context/AuthContext';
import { 
  dashboardService, 
  OfficerDashboardResponse, 
  SupervisorDashboardResponse,
  DashboardCaseItem
} from '@/api/client';
import { Link } from 'react-router-dom';
import { Shield, AlertTriangle, IndianRupee, Clock, Search, FolderOpen, ArrowRight, FileText } from 'lucide-react';

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(amount);
};

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [data, setData] = useState<OfficerDashboardResponse | SupervisorDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const res = await dashboardService.getDashboard();
        setData(res);
      } catch (e) {
        console.error("Failed to load dashboard", e);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  if (loading) {
    return <div className="p-8 text-slate-500 dark:text-slate-400">{t('dashboard.loading')}</div>;
  }

  if (!data) {
    return <div className="p-8 text-red-600">{t('dashboard.error')}</div>;
  }

  const isSupervisor = user?.role === 'admin' || user?.role === 'supervisor';

  const renderCaseList = (title: string, cases: DashboardCaseItem[], emptyMessage: string) => (
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="p-4 border-b border-slate-200 bg-slate-50 dark:bg-slate-950">
        <h3 className="font-semibold text-slate-800 dark:text-slate-200">{title}</h3>
      </div>
      <div className="divide-y divide-slate-100 dark:divide-slate-800">
        {cases.length === 0 ? (
          <div className="p-8 text-center text-slate-500 dark:text-slate-400 text-sm">{emptyMessage}</div>
        ) : (
          cases.map(c => (
            <div key={c.id} className="p-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
              <div className="flex flex-col gap-1">
                <Link to={`/cases/${c.id}`} className="text-blue-700 dark:text-blue-400 font-medium hover:underline flex items-center gap-2">
                  {c.case_number}
                  {c.is_breached && <AlertTriangle className="w-3 h-3 text-red-500" />}
                </Link>
                <div className="flex gap-3 text-xs text-slate-500 dark:text-slate-400">
                  <span className="uppercase tracking-wider">{c.fraud_category}</span>
                  <span>{formatCurrency(c.amount_at_risk)}</span>
                  <span className={`px-1.5 rounded-sm ${c.status === 'intake_complete' ? 'bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400' : 'bg-blue-50 dark:bg-blue-900/40 text-blue-700'}`}>
                    {c.status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                </div>
              </div>
              <Link to={`/cases/${c.id}`} className="p-2 text-slate-400 hover:text-slate-700 dark:text-slate-300 transition-colors">
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          ))
        )}
      </div>
    </div>
  );

  if (isSupervisor) {
    const supData = data as SupervisorDashboardResponse;
    return (
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-200">{t('dashboard.supervisorTitle')}</h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">{t('dashboard.supervisorSubtitle')}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-3">
            <div className="flex justify-between items-center text-slate-500 dark:text-slate-400">
              <span className="font-medium">{t("dashboard.totalOpenCases")}</span>
              <FolderOpen className="w-5 h-5 text-slate-400" />
            </div>
            <div className="text-3xl font-bold text-slate-800 dark:text-slate-200">{supData.total_open_cases}</div>
          </div>
          <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-3">
            <div className="flex justify-between items-center text-slate-500 dark:text-slate-400">
              <span className="font-medium">{t("dashboard.slaBreached")}</span>
              <AlertTriangle className="w-5 h-5 text-red-500" />
            </div>
            <div className="text-3xl font-bold text-red-600">{supData.sla_breached_cases_count}</div>
          </div>
          <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-3">
            <div className="flex justify-between items-center text-slate-500 dark:text-slate-400">
              <span className="font-medium">{t("dashboard.totalAtRisk")}</span>
              <IndianRupee className="w-5 h-5 text-amber-500" />
            </div>
            <div className="text-2xl font-bold text-slate-800 dark:text-slate-200">{formatCurrency(supData.total_amount_at_risk)}</div>
          </div>
          <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-3">
            <div className="flex justify-between items-center text-slate-500 dark:text-slate-400">
              <span className="font-medium">{t("dashboard.totalRecovered")}</span>
              <Shield className="w-5 h-5 text-emerald-500" />
            </div>
            <div className="text-2xl font-bold text-slate-800 dark:text-slate-200">{formatCurrency(supData.total_amount_recovered)}</div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {renderCaseList(t("dashboard.slaBreachedCases"), supData.breached_cases, t("dashboard.noBreached"))}
          
          <div className="space-y-6">
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 shadow-sm p-4">
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 border-b border-slate-200 pb-2 mb-4">{t("dashboard.networkSummary")}</h3>
              <div className="flex gap-4">
                <div className="flex-1 bg-slate-50 dark:bg-slate-950 p-3 rounded-lg text-center border border-slate-100 dark:border-slate-800">
                  <div className="text-2xl font-bold text-slate-800 dark:text-slate-200">{supData.network_summary.total_clusters}</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">{t("dashboard.totalClusters")}</div>
                </div>
                <div className="flex-1 bg-red-50 dark:bg-red-900/40 p-3 rounded-lg text-center border border-red-100 dark:border-red-800/40">
                  <div className="text-2xl font-bold text-red-600">{supData.network_summary.high_risk_clusters}</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">{t("dashboard.highRisk")}</div>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 shadow-sm p-4">
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 border-b border-slate-200 pb-2 mb-4">{t("dashboard.officerWorkload")}</h3>
              <div className="space-y-2">
                {supData.workload.map(w => (
                  <div key={w.officer_name} className="flex justify-between items-center p-2 bg-slate-50 dark:bg-slate-950 rounded border border-slate-100 dark:border-slate-800">
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{w.officer_name}</span>
                    <span className="text-xs bg-blue-50 dark:bg-blue-900/40 text-blue-700 px-2 py-1 rounded border border-blue-100 dark:border-blue-800/40">{t("dashboard.activeCount", { count: w.active_cases })}</span>
                  </div>
                ))}
                {supData.workload.length === 0 && <div className="text-sm text-slate-500 dark:text-slate-400">{t("dashboard.noActiveWorkload")}</div>}
              </div>
            </div>
            
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 shadow-sm p-4">
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 border-b border-slate-200 pb-2 mb-4">{t("dashboard.externalPanel")}</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-slate-600 dark:text-slate-400">CFCFRMS / MHA (Demo Mode)</span>
                  <span className="px-2 py-1 bg-amber-50 dark:bg-amber-900/40 text-amber-700 rounded text-xs font-semibold border border-amber-100 dark:border-amber-800/40">{t("dashboard.simulated")}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600 dark:text-slate-400">Bank Pilot</span>
                  <span className="px-2 py-1 bg-amber-50 dark:bg-amber-900/40 text-amber-700 rounded text-xs font-semibold border border-amber-100 dark:border-amber-800/40">{t("dashboard.notConnected")}</span>
                </div>
                <div className="mt-2 text-[10px] text-slate-400 italic">* CFCFRMS runs in demo/simulated mode. Bank Pilot has no live bank integration.</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const offData = data as OfficerDashboardResponse;
  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-200">{t('dashboard.officerTitle')}</h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">{t('dashboard.officerSubtitle', { name: user?.name })}</p>
        </div>
        <div className="flex gap-3">
          <Link to="/cases" className="px-4 py-2 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:bg-slate-950 text-slate-700 dark:text-slate-300 text-sm font-medium rounded-lg border border-slate-200 transition-colors flex items-center gap-2 shadow-sm">
            <Search className="w-4 h-4" /> Global Search
          </Link>
          <Link to="/cases" className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2 shadow-sm">
            <FolderOpen className="w-4 h-4" /> View All Cases
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-3">
          <div className="flex justify-between items-center text-slate-500 dark:text-slate-400">
            <span className="font-medium">{t("dashboard.totalOpenCases")}</span>
            <FolderOpen className="w-5 h-5 text-slate-400" />
          </div>
          <div className="text-3xl font-bold text-slate-800 dark:text-slate-200">{offData.assigned_open_cases}</div>
        </div>
        <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-3">
          <div className="flex justify-between items-center text-slate-500 dark:text-slate-400">
            <span className="font-medium">{t("dashboard.awaitingBank")}</span>
            <Clock className="w-5 h-5 text-amber-500" />
          </div>
          <div className="text-3xl font-bold text-amber-600">{offData.awaiting_bank_count ?? 0}</div>
        </div>
        <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-3">
          <div className="flex justify-between items-center text-slate-500 dark:text-slate-400">
            <span className="font-medium">{t("dashboard.noticeSent")}</span>
            <FileText className="w-5 h-5 text-blue-500" />
          </div>
          <div className="text-3xl font-bold text-blue-600">{offData.notice_sent_count ?? 0}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-3">
          <div className="flex justify-between items-center text-slate-500 dark:text-slate-400">
            <span className="font-medium">{t("dashboard.slaBreached")}</span>
            <AlertTriangle className="w-5 h-5 text-red-500" />
          </div>
          <div className="text-3xl font-bold text-red-600">{offData.sla_breached_cases_count}</div>
        </div>
        <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-3">
          <div className="flex justify-between items-center text-slate-500 dark:text-slate-400">
            <span className="font-medium">{t("dashboard.myPortfolioRisk")}</span>
            <IndianRupee className="w-5 h-5 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-slate-800 dark:text-slate-200">{formatCurrency(offData.total_amount_at_risk)}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {renderCaseList(t("dashboard.myBreachedCases"), offData.breached_cases, t("dashboard.noBreached"))}
        {renderCaseList(t("dashboard.myPrioritizedQueue"), offData.recent_cases, t("dashboard.noOpenCases"))}
      </div>
    </div>
  );
};
