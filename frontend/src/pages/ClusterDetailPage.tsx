import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { networkApi, NetworkCluster } from '@/api/network';
import { ClusterGraph } from '@/components/network/ClusterGraph';
import { ArrowLeft, Network, AlertTriangle, UserCheck } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

export const ClusterDetailPage: React.FC = () => {
  const { clusterId } = useParams<{ clusterId: string }>();
  const [cluster, setCluster] = useState<NetworkCluster | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCluster = async () => {
      if (!clusterId) return;
      try {
        setLoading(true);
        const data = await networkApi.getCluster(clusterId);
        setCluster(data);
      } catch (err) {
        setError('Failed to fetch cluster details.');
      } finally {
        setLoading(false);
      }
    };
    fetchCluster();
  }, [clusterId]);

  if (loading) return <div className="p-8 text-center animate-pulse">Loading Cluster...</div>;
  if (error || !cluster) return <div className="p-8 text-center text-red-600">{error || 'Not found'}</div>;

  const suggested = cluster.next_account_to_notice;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/watchlist">
          <Button variant="outline" size="sm" className="gap-2">
            <ArrowLeft className="h-4 w-4" /> Back
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Network className="h-6 w-6 text-indigo-600" />
            {cluster.cluster_name}
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">ID: {cluster.id}</p>
        </div>
        <div className="ml-auto flex gap-2">
          <Badge className="bg-red-100 text-red-800">Risk Score: {cluster.risk_score}</Badge>
          <Badge className="bg-blue-100 text-blue-800">{cluster.total_cases_involved} Cases</Badge>
          <Badge className="bg-amber-100 text-amber-800">₹{cluster.total_amount_involved.toLocaleString('en-IN')}</Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          <div className="bg-white dark:bg-slate-900 border rounded-lg shadow-sm p-4 h-[600px] flex flex-col">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-2">Cluster Topology Map</h3>
            <div className="flex-1">
              {cluster.graph_summary_json ? (
                <ClusterGraph graphData={cluster.graph_summary_json} />
              ) : (
                <div className="h-full flex items-center justify-center text-slate-500 dark:text-slate-400">
                  No topology graph available.
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-900 border rounded-lg shadow-sm p-4">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2 mb-3">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              Strategic Insight
            </h3>
            <div className="text-sm text-slate-600 dark:text-slate-400 space-y-4">
              <p>
                This cluster connects <strong>{cluster.total_cases_involved}</strong> separate investigations via{' '}
                <strong>{cluster.total_accounts_involved}</strong> shared beneficiary accounts.
              </p>

              {suggested && (
                <div className="p-3 bg-indigo-50 border border-indigo-200 rounded text-indigo-900">
                  <div className="font-semibold mb-1 flex items-center gap-1">
                    <UserCheck className="h-4 w-4" /> Next Account to Notice
                  </div>
                  <p>
                    Prioritize <strong>{suggested.label}</strong> — outflow ₹
                    {suggested.outflow_amount.toLocaleString('en-IN')}, linked to {suggested.case_count} case(s),{' '}
                    freeze status: {suggested.freeze_status}.
                  </p>
                  <p className="text-xs mt-1 text-indigo-700">{suggested.reason}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
