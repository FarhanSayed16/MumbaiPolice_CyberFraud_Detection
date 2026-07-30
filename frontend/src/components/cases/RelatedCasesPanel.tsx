import React, { useState, useEffect } from 'react';
import { caseService } from '@/api/client';
import { Link } from 'react-router-dom';
import { Network, AlertTriangle } from 'lucide-react';

interface RelatedCasesPanelProps {
  caseId: string;
}

export const RelatedCasesPanel: React.FC<RelatedCasesPanelProps> = ({ caseId }) => {
  const [related, setRelated] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRelated = async () => {
      try {
        setLoading(true);
        const data = await caseService.getRelatedCases(caseId);
        setRelated(data);
      } catch (err) {
        console.error('Failed to fetch related cases', err);
      } finally {
        setLoading(false);
      }
    };
    fetchRelated();
  }, [caseId]);

  if (loading) {
    return <div className="text-sm text-slate-500 dark:text-slate-400 animate-pulse p-4">Detecting cross-case patterns...</div>;
  }

  if (related.length === 0) {
    return (
      <div className="bg-white dark:bg-slate-900 border rounded-lg p-6 text-center text-slate-500 dark:text-slate-400">
        <Network className="h-8 w-8 mx-auto text-slate-300 mb-2" />
        <p className="text-sm">No related cases detected.</p>
        <p className="text-xs mt-1">This case does not share suspect accounts with any other case.</p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-900 border rounded-lg shadow-sm overflow-hidden">
      <div className="bg-slate-50 dark:bg-slate-950 px-4 py-3 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
        <h3 className="text-sm font-medium text-slate-800 dark:text-slate-200 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-orange-500" />
          Related Cases Detected
        </h3>
        <span className="bg-orange-100 text-orange-800 text-xs px-2 py-1 rounded-full font-semibold">
          {related.length} Linked Case(s)
        </span>
      </div>
      <ul className="divide-y divide-slate-100 dark:divide-slate-800">
        {related.map((r, idx) => (
          <li key={idx} className="p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
            <div className="flex justify-between items-start">
              <div>
                <Link to={`/cases/${r.case_id}`} className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1">
                  {r.case_number}
                </Link>
                <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  {r.fraud_category} &bull; {r.status}
                </div>
              </div>
              <div className="text-right">
                <span className="text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-1 rounded-full border border-slate-200 dark:border-slate-700">
                  {r.shared_account_count} Shared Account{r.shared_account_count > 1 ? 's' : ''}
                </span>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};
