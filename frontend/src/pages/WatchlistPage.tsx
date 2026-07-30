import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { WatchlistEntry, WatchlistEntryCreate, watchlistApi } from '../api/watchlist';
import { ClusterList } from '../components/network/ClusterList';
import { PspHeatTable } from '../components/network/PspHeatTable';

const WatchlistPage: React.FC = () => {
  const { t } = useTranslation();
  const [entries, setEntries] = useState<WatchlistEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'watchlist' | 'rings' | 'heatmap'>('watchlist');

  const [newEntry, setNewEntry] = useState<WatchlistEntryCreate>({
    account_number: '',
    ifsc_code: '',
    upi_id: '',
    phone: '',
    reason: '',
    risk_score: 100,
    is_active: true
  });

  const loadEntries = async () => {
    try {
      setLoading(true);
      const data = await watchlistApi.list();
      setEntries(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load watchlist');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEntries();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (!newEntry.account_number && !newEntry.upi_id && !newEntry.phone) {
        throw new Error('Must provide Account Number, UPI ID, or Phone');
      }
      const dataToSubmit = { ...newEntry };
      if (!dataToSubmit.account_number) dataToSubmit.account_number = null;
      if (!dataToSubmit.ifsc_code) dataToSubmit.ifsc_code = null;
      if (!dataToSubmit.upi_id) dataToSubmit.upi_id = null;
      if (!dataToSubmit.phone) dataToSubmit.phone = null;

      await watchlistApi.create(dataToSubmit);
      setNewEntry({
        account_number: '',
        ifsc_code: '',
        upi_id: '',
        phone: '',
        reason: '',
        risk_score: 100,
        is_active: true
      });
      loadEntries();
    } catch (err: any) {
      alert(err.message || 'Failed to create entry');
    }
  };

  const handleToggleActive = async (entry: WatchlistEntry) => {
    try {
      await watchlistApi.update(entry.id, { is_active: !entry.is_active });
      loadEntries();
    } catch (err: any) {
      alert(err.message || 'Failed to update entry');
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Deactivate this watchlist entry?')) return;
    try {
      await watchlistApi.delete(id);
      loadEntries();
    } catch (err: any) {
      alert(err.message || 'Failed to delete entry');
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-200">{t('watchlist.pageTitle', 'Network & Intelligence')}</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">{t('watchlist.pageSubtitle', 'Cross-case pattern detection, mule rings, and PSP exposure.')}</p>
      </div>

      <div className="flex gap-4 border-b border-slate-200 dark:border-slate-700">
        <button
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${activeTab === 'watchlist' ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400' : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-white'}`}
          onClick={() => setActiveTab('watchlist')}
        >
          Watchlist Management
        </button>
        <button
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${activeTab === 'rings' ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400' : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-white'}`}
          onClick={() => setActiveTab('rings')}
        >
          Discovered Mule Rings
        </button>
        <button
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${activeTab === 'heatmap' ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400' : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-white'}`}
          onClick={() => setActiveTab('heatmap')}
        >
          PSP / Bank Heatmap
        </button>
      </div>

      {activeTab === 'watchlist' && (
        <>
          <div className="bg-white dark:bg-slate-900 shadow dark:shadow-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-800 p-6">
        <h2 className="text-lg font-medium mb-4">{t("watchlist.addTitle")}</h2>
        <form onSubmit={handleCreate} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">{t("watchlist.accNumber")}</label>
              <input
                type="text"
                className="mt-1 block w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                value={newEntry.account_number || ''}
                onChange={e => setNewEntry({ ...newEntry, account_number: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">{t("watchlist.ifsc")}</label>
              <input
                type="text"
                className="mt-1 block w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                value={newEntry.ifsc_code || ''}
                onChange={e => setNewEntry({ ...newEntry, ifsc_code: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">{t("watchlist.upi")}</label>
              <input
                type="text"
                className="mt-1 block w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                value={newEntry.upi_id || ''}
                onChange={e => setNewEntry({ ...newEntry, upi_id: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">{t("watchlist.phone")}</label>
              <input
                type="text"
                className="mt-1 block w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                value={newEntry.phone || ''}
                onChange={e => setNewEntry({ ...newEntry, phone: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">{t("watchlist.reasonLabel")}</label>
              <input
                type="text"
                required
                className="mt-1 block w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                value={newEntry.reason}
                onChange={e => setNewEntry({ ...newEntry, reason: e.target.value })}
              />
            </div>
          </div>
          <button
            type="submit"
            className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none"
          >
            {t("watchlist.addBtn")}
          </button>
        </form>
      </div>

      <div className="bg-white dark:bg-slate-900 shadow dark:shadow-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-800 overflow-hidden">
        {loading ? (
          <div className="p-6 text-center text-slate-500 dark:text-slate-400">{t("watchlist.loading")}</div>
        ) : error ? (
          <div className="p-6 text-center text-red-500">{error}</div>
        ) : (
          <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
            <thead className="bg-slate-50 dark:bg-slate-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">{t("watchlist.target")}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">{t("watchlist.reasonLabel")}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">{t("watchlist.status")}</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">{t("watchlist.actions")}</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-slate-900 divide-y divide-slate-200 dark:divide-slate-800">
              {entries.map(entry => (
                <tr key={entry.id} className={!entry.is_active ? 'opacity-50' : ''}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900 dark:text-slate-100">
                    {entry.account_number && <div>Acc: {entry.account_number} {entry.ifsc_code && `(${entry.ifsc_code})`}</div>}
                    {entry.upi_id && <div>UPI: {entry.upi_id}</div>}
                    {entry.phone && <div>Phone: {entry.phone}</div>}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">
                    {entry.reason}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${entry.is_active ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300' : 'bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-300'}`}>
                      {entry.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onClick={() => handleToggleActive(entry)} className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-300 mr-4">
                      {entry.is_active ? t("watchlist.deactivate") : t("watchlist.active")}
                    </button>
                    <button onClick={() => handleDelete(entry.id)} className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300">
                      {t("watchlist.delete")}
                    </button>
                  </td>
                </tr>
              ))}
              {entries.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-4 text-center text-sm text-slate-500 dark:text-slate-400">No watchlist entries found</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
      </>
      )}

      {activeTab === 'rings' && (
        <ClusterList />
      )}

      {activeTab === 'heatmap' && (
        <PspHeatTable />
      )}
    </div>
  );
};

export { WatchlistPage };
