import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { riskService, type CaseRiskRollup } from "@/api/risk";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { RefreshCw, AlertTriangle } from "lucide-react";

interface CaseRiskTabProps {
  caseId: string;
}

export const CaseRiskTab: React.FC<CaseRiskTabProps> = ({ caseId }) => {
  const { t } = useTranslation();
  const [rollup, setRollup] = useState<CaseRiskRollup | null>(null);
  const [loading, setLoading] = useState(true);
  const [recomputing, setRecomputing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadRisk = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await riskService.getCaseRisk(caseId);
      setRollup(data);
    } catch {
      setError("Failed to load risk scores for this case.");
      setRollup(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRisk();
  }, [caseId]);

  const handleRecompute = async () => {
    setRecomputing(true);
    setError(null);
    try {
      const result = await riskService.recomputeCaseRisk(caseId);
      setRollup(result.rollup);
    } catch {
      setError("Failed to recompute risk scores.");
    } finally {
      setRecomputing(false);
    }
  };

  if (loading && !rollup) {
    return <Skeleton className="h-64 w-full" />;
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/40 border border-red-200 rounded text-red-800 text-sm flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          {error}
        </div>
      )}

      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200">{t("risk.title", "Case Risk Rollup")}</h3>
        <Button size="sm" variant="outline" onClick={handleRecompute} disabled={recomputing} className="gap-2">
          <RefreshCw className={`h-4 w-4 ${recomputing ? "animate-spin" : ""}`} />
          Recompute
        </Button>
      </div>

      {rollup && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-slate-500 dark:text-slate-400">Accounts Scored</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{rollup.account_count}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-slate-500 dark:text-slate-400">Average Risk</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{rollup.avg_risk_score.toFixed(1)}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-slate-500 dark:text-slate-400">Max Risk</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold text-red-700">{rollup.max_risk_score.toFixed(1)}</p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Rules Fired (Top Accounts)</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {rollup.top_explanations.length === 0 ? (
                <p className="text-sm text-slate-500 dark:text-slate-400">No risk rules fired yet. Import transactions or recompute.</p>
              ) : (
                rollup.top_explanations.map((item) => (
                  <div key={item.account_id} className="border rounded-lg p-3 bg-slate-50 dark:bg-slate-950">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono text-sm">{item.account_number || item.account_id}</span>
                      <Badge variant={item.risk_score >= 80 ? "destructive" : "secondary"}>
                        Score: {item.risk_score.toFixed(0)}
                      </Badge>
                    </div>
                    <ul className="text-xs text-slate-700 dark:text-slate-300 space-y-1 list-disc list-inside">
                      {item.rules_fired.map((rule, idx) => (
                        <li key={idx}>{rule}</li>
                      ))}
                    </ul>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};
