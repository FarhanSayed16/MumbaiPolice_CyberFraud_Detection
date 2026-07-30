import React, { useEffect, useState } from 'react';
import { analyticsApi, PspHeatRow } from '@/api/analytics';
import { Activity } from 'lucide-react';

export const PspHeatTable: React.FC = () => {
  const [data, setData] = useState<PspHeatRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const res = await analyticsApi.getPspHeatmap();
        setData(res);
      } catch (err) {
        console.error('Failed to load heatmap', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount || 0);

  if (loading) {
    return <div className="p-8 text-center text-slate-500 dark:text-slate-400 animate-pulse">Loading PSP Heatmap...</div>;
  }

  return (
    <div className="bg-white dark:bg-slate-900 shadow rounded-lg overflow-hidden border">
      <div className="px-6 py-4 border-b bg-slate-50 dark:bg-slate-950 flex items-center gap-2">
        <Activity className="h-5 w-5 text-indigo-600" />
        <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100">PSP / Bank Heatmap</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50 dark:bg-slate-950">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Bank / PSP</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">IFSC</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Cases Involved</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Accounts Mapped</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Total Amount at Risk</th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-slate-900 divide-y divide-slate-200">
            {data.map((row, idx) => (
              <tr key={idx} className="hover:bg-slate-50 dark:bg-slate-950">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-slate-900 dark:text-slate-100">
                  {row.bank_name || row.psp_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-slate-600 dark:text-slate-400">
                  {row.ifsc_code || '—'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700 dark:text-slate-300 text-right font-medium">
                  {row.total_cases}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700 dark:text-slate-300 text-right">
                  {row.total_accounts}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-rose-700 font-semibold text-right">
                  {formatCurrency(row.total_amount_at_risk)}
                </td>
              </tr>
            ))}
            {data.length === 0 && (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-slate-500 dark:text-slate-400 text-sm">
                  No heatmap data available.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
