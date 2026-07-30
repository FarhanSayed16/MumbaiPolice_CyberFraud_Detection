import { useTranslation } from 'react-i18next';
import React, { useEffect, useState } from "react";
import { fetchSystemHealth, type HealthStatus } from "@/api/client";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { CheckCircle2, XCircle, RefreshCw, Server, Database, Cpu, AlertTriangle, PhoneCall, ShieldCheck, FileText } from "lucide-react";

export const HealthPage: React.FC = () => {
  const { t } = useTranslation();
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const loadHealth = async () => {
    setLoading(true);
    try {
      const data = await fetchSystemHealth();
      setHealth(data);
    } catch (e) {
      setHealth({
        status: "unhealthy",
        project_name: "Mumbai Police Cyber Fraud Platform",
        environment: "local",
        timestamp: new Date().toISOString(),
        services: {
          postgres: { status: "error", latency_ms: 0 },
          neo4j: { status: "error", latency_ms: 0 },
          redis: { status: "error", latency_ms: 0 }
        }
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHealth();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Server className="h-6 w-6 text-blue-400" /> {t("health.title")}
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            {t("health.subtitle")}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={loadHealth}
            disabled={loading}
            className="border-slate-300 bg-white dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} /> Probes Refresh
          </Button>
        </div>
      </div>

      {/* Status Summary Banner */}
      {health && (
        <Card className={`border ${
          health.status === 'healthy'
            ? 'border-emerald-200 bg-emerald-50 dark:bg-emerald-900/40'
            : 'border-red-200 bg-red-50 dark:bg-red-900/40'
        }`}>
          <CardContent className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              {health.status === 'healthy' ? (
                <CheckCircle2 className="h-8 w-8 text-emerald-400 flex-shrink-0" />
              ) : (
                <XCircle className="h-8 w-8 text-red-400 flex-shrink-0" />
              )}
              <div>
                <div className="text-base font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
                  System Status: {health.status}
                  <Badge className={`text-xs ${health.status === 'healthy' ? 'bg-emerald-600 text-white' : 'bg-red-600 text-white'}`}>
                    {health.status.toUpperCase()}
                  </Badge>
                </div>
                <div className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                  {health.project_name} • Environment: <span className="font-mono text-blue-600 dark:text-blue-400">{health.environment}</span> • {t("health.checked")} {health.timestamp ? new Date(health.timestamp).toLocaleTimeString() : 'Just now'}
                </div>
              </div>
            </div>
            <div className="hidden sm:flex flex-col items-end gap-1 text-xs font-mono text-slate-500 dark:text-slate-400">
              <div className="flex items-center gap-2">
                <ShieldCheck className={`h-4 w-4 ${health.observability?.sentry_active ? 'text-emerald-400' : 'text-slate-500 dark:text-slate-400'}`} />
                <span>
                  Sentry:{' '}
                  {health.observability?.sentry_active
                    ? 'ACTIVE'
                    : health.observability?.sentry_configured
                      ? 'DSN SET / INACTIVE'
                      : 'NOT CONFIGURED'}
                </span>
              </div>
              <span className="text-[10px] text-slate-500 dark:text-slate-400 max-w-xs text-right">
                {health.observability?.note || 'Observability status from /health'}
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Service Grid */}
      {health && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* PostgreSQL */}
          <Card className="border-slate-200 bg-white dark:bg-slate-900">
            <CardHeader className="pb-3 border-b border-slate-200 flex flex-row items-center justify-between">
              <div className="flex items-center gap-2">
                <Database className="h-5 w-5 text-blue-400" />
                <CardTitle className="text-md font-semibold text-slate-900 dark:text-slate-100">{t("health.postgres")}</CardTitle>
              </div>
              <Badge className={health.services.postgres.status === 'ok' ? 'bg-emerald-600 text-white' : 'bg-red-600 text-white'}>
                {health.services.postgres.status.toUpperCase()}
              </Badge>
            </CardHeader>
            <CardContent className="pt-4 space-y-2 text-xs">
              <div className="flex justify-between text-slate-500 dark:text-slate-400">
                <span>{t("health.canonicalSchema")}</span>
                <span className="font-mono text-slate-700 dark:text-slate-300">13 Tables</span>
              </div>
              <div className="flex justify-between text-slate-500 dark:text-slate-400">
                <span>{t("health.evidentiaryTriggers")}</span>
                <span className="font-mono text-purple-600 dark:text-purple-400">Audit Integrity Trigger</span>
              </div>
              <div className="flex justify-between text-slate-500 dark:text-slate-400">
                <span>{t("health.probeLatency")}</span>
                <span className="font-mono text-emerald-400">{health.services.postgres.latency_ms ?? 0} ms</span>
              </div>
            </CardContent>
          </Card>

          {/* Neo4j Graph */}
          <Card className="border-slate-200 bg-white dark:bg-slate-900">
            <CardHeader className="pb-3 border-b border-slate-200 flex flex-row items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu className="h-5 w-5 text-purple-400" />
                <CardTitle className="text-md font-semibold text-slate-900 dark:text-slate-100">{t("health.neo4j")}</CardTitle>
              </div>
              <Badge className={health.services.neo4j.status === 'ok' ? 'bg-emerald-600 text-white' : 'bg-red-600 text-white'}>
                {health.services.neo4j.status.toUpperCase()}
              </Badge>
            </CardHeader>
            <CardContent className="pt-4 space-y-2 text-xs">
              <div className="flex justify-between text-slate-500 dark:text-slate-400">
                <span>{t("health.graphEngine")}</span>
                <span className="font-mono text-slate-700 dark:text-slate-300">Cypher Bolt Protocol</span>
              </div>
              <div className="flex justify-between text-slate-500 dark:text-slate-400">
                <span>{t("health.nodeIndexes")}</span>
                <span className="font-mono text-purple-600 dark:text-purple-400">Case / Account / Phone</span>
              </div>
              <div className="flex justify-between text-slate-500 dark:text-slate-400">
                <span>{t("health.probeLatency")}</span>
                <span className="font-mono text-emerald-400">{health.services.neo4j.latency_ms ?? 0} ms</span>
              </div>
            </CardContent>
          </Card>

          {/* Redis Worker Queue */}
          <Card className="border-slate-200 bg-white dark:bg-slate-900">
            <CardHeader className="pb-3 border-b border-slate-200 flex flex-row items-center justify-between">
              <div className="flex items-center gap-2">
                <Server className="h-5 w-5 text-amber-400" />
                <CardTitle className="text-md font-semibold text-slate-900 dark:text-slate-100">{t("health.redis")}</CardTitle>
              </div>
              <Badge className={health.services.redis.status === 'ok' ? 'bg-emerald-600 text-white' : 'bg-red-600 text-white'}>
                {health.services.redis.status.toUpperCase()}
              </Badge>
            </CardHeader>
            <CardContent className="pt-4 space-y-2 text-xs">
              <div className="flex justify-between text-slate-500 dark:text-slate-400">
                <span>{t("health.taskEngine")}</span>
                <span className="font-mono text-slate-700 dark:text-slate-300">ARQ Async Workers</span>
              </div>
              <div className="flex justify-between text-slate-500 dark:text-slate-400">
                <span>{t("health.rateLimitStore")}</span>
                <span className="font-mono text-blue-600 dark:text-blue-400">Sliding Window (5/min)</span>
              </div>
              <div className="flex justify-between text-slate-500 dark:text-slate-400">
                <span>{t("health.probeLatency")}</span>
                <span className="font-mono text-emerald-400">{health.services.redis.latency_ms ?? 0} ms</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* System Down & Incident Escalation Protocol */}
      <Card className="border-amber-200 dark:border-amber-800/40 bg-white dark:bg-slate-900 shadow-lg">
        <CardHeader className="pb-3 border-b border-slate-200 flex flex-row items-center gap-3">
          <AlertTriangle className="h-6 w-6 text-amber-400 flex-shrink-0" />
          <div>
            <CardTitle className="text-md font-semibold text-slate-900 dark:text-slate-100">System Down & Incident Reporting Protocol</CardTitle>
            <CardDescription className="text-slate-500 dark:text-slate-400">
              {t("health.incidentSub")}
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="pt-4 space-y-4 text-xs">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-3.5 rounded bg-slate-50 dark:bg-slate-950 border border-slate-200 space-y-2">
              <div className="font-semibold text-blue-700 dark:text-blue-400 flex items-center gap-2">
                <PhoneCall className="h-4 w-4" /> 1. Immediate Reporting & Hotline
              </div>
              <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                If the platform reports <span className="text-red-400 font-bold">DEGRADED</span> status or a database probe fails for more than 5 minutes, immediately alert your Station House Officer (SHO). For urgent live cash-out freezes while technical ops restores connectivity, call the **National Cybercrime Reporting Hotline (1930 / I4C)**.
              </p>
            </div>

            <div className="p-3.5 rounded bg-slate-50 dark:bg-slate-950 border border-slate-200 space-y-2">
              <div className="font-semibold text-purple-700 dark:text-purple-400 flex items-center gap-2">
                <FileText className="h-4 w-4" /> 2. Technical Outage Ticket Submission
              </div>
              <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                Send an urgent ticket to admin.mumbai@maharashtracyber.gov.in (Ext: 404). Include: Officer Name (R. K. Shinde), Badge Number (MH-CY-8412), exact screen URL, error screenshot, and the `X-Request-ID` from browser DevTools to correlate with structured JSON server logs.
              </p>
            </div>
          </div>

          <div className="p-3 rounded bg-blue-50 dark:bg-blue-900/40 border border-blue-200 text-blue-900 dark:text-blue-200 flex items-center justify-between">
            <div>
              <span className="font-semibold">CERT-In Mandatory Reporting:</span> Under IT Act Section 70B, critical breaches (P0) must be reported within **6 hours**.
            </div>
            <span className="font-mono text-[11px] bg-blue-100 dark:bg-blue-900/60 px-2 py-0.5 rounded border border-blue-300 dark:border-blue-600 text-blue-800 dark:text-blue-300">
              docs/incident-breach-response-plan.md
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
