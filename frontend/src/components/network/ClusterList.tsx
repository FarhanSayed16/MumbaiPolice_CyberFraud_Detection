import React, { useEffect, useState } from 'react';
import { networkApi, NetworkCluster } from '@/api/network';
import { Network, Search, AlertCircle, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';

export const ClusterList: React.FC = () => {
  const [clusters, setClusters] = useState<NetworkCluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [computing, setComputing] = useState(false);

  const fetchClusters = async () => {
    try {
      setLoading(true);
      const res = await networkApi.listClusters();
      setClusters(res);
    } catch (err) {
      console.error('Failed to fetch clusters', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClusters();
  }, []);

  const handleCompute = async () => {
    try {
      setComputing(true);
      await networkApi.triggerCompute();
      await fetchClusters();
    } catch (err) {
      alert('Failed to compute clusters. Check server logs.');
    } finally {
      setComputing(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-500 dark:text-slate-400 animate-pulse">Loading Mule Rings...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center bg-white dark:bg-slate-900 p-4 border rounded-lg shadow-sm">
        <div className="flex items-center gap-2">
          <Network className="h-5 w-5 text-indigo-600" />
          <span className="font-semibold text-slate-800 dark:text-slate-200">Auto-Detected Mule Rings</span>
        </div>
        <button
          onClick={handleCompute}
          disabled={computing}
          className="flex items-center gap-2 px-3 py-1.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 rounded text-sm font-medium transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${computing ? 'animate-spin' : ''}`} />
          {computing ? 'Computing...' : 'Run Clustering Job'}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {clusters.map(cluster => (
          <Link key={cluster.id} to={`/network/clusters/${cluster.id}`} className="block">
            <div className="bg-white dark:bg-slate-900 border hover:border-indigo-400 hover:shadow-md transition-all rounded-lg p-5">
              <div className="flex justify-between items-start mb-3 gap-2">
                <h4 className="font-bold text-slate-900 dark:text-slate-100 text-sm line-clamp-2">{cluster.cluster_name}</h4>
                <span className={`px-2 py-0.5 rounded text-xs font-bold whitespace-nowrap flex-shrink-0 ${cluster.risk_score >= 90 ? 'bg-red-100 text-red-700' : 'bg-orange-100 text-orange-700'}`}>
                  Score: {cluster.risk_score}
                </span>
              </div>
              
              <div className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
                <div className="flex justify-between">
                  <span>Cases Linked:</span>
                  <span className="font-semibold text-slate-900 dark:text-slate-100">{cluster.total_cases_involved}</span>
                </div>
                <div className="flex justify-between">
                  <span>Accounts Involved:</span>
                  <span className="font-semibold text-slate-900 dark:text-slate-100">{cluster.total_accounts_involved}</span>
                </div>
                <div className="flex justify-between">
                  <span>Total Exposure:</span>
                  <span className="font-semibold text-rose-600">
                    ₹{cluster.total_amount_involved.toLocaleString('en-IN')}
                  </span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t text-xs text-slate-400 flex items-center justify-between">
                <span>ID: {cluster.id.substring(0, 12)}...</span>
                <span className="text-indigo-600 font-medium group-hover:underline">View Graph &rarr;</span>
              </div>
            </div>
          </Link>
        ))}
        {clusters.length === 0 && (
          <div className="col-span-full p-12 text-center bg-white dark:bg-slate-900 border rounded-lg text-slate-500 dark:text-slate-400">
            <AlertCircle className="h-8 w-8 mx-auto text-slate-300 mb-2" />
            <p>No mule rings detected.</p>
            <p className="text-sm">Run the clustering job to discover networks.</p>
          </div>
        )}
      </div>
    </div>
  );
};
