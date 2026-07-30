import { useTranslation } from 'react-i18next';
import React, { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { BulkImportModal } from "@/components/ingestion/BulkImportModal";
import { ingestionService, type ImportJobItem } from "@/api/client";
import {
  FileSpreadsheet, FileText, Upload, RefreshCw
} from "lucide-react";

export const IngestionQueuePage: React.FC = () => {
  const { t } = useTranslation();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [targetCaseId, setTargetCaseId] = useState<string>("");
  const [jobs, setJobs] = useState<ImportJobItem[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(false);

  const loadJobs = async () => {
    setLoadingJobs(true);
    try {
      const data = await ingestionService.listJobs(targetCaseId.trim() || undefined);
      setJobs(data || []);
    } catch {
      setJobs([]);
    } finally {
      setLoadingJobs(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, []);

  return (
    <div className="space-y-6 max-w-6xl mx-auto p-4">
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b pb-4 bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 gap-4">
        <div className="flex items-center gap-4">
          <div className="rounded-xl bg-blue-600 p-3 text-white shadow-md">
            <Upload className="h-7 w-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                {t("ingestion.title")}
              </h1>
              <Badge className="bg-slate-100 text-slate-700 dark:text-slate-300 border-slate-300 font-semibold uppercase">
                Bulk intake
              </Badge>
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              {t("ingestion.subtitle")}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <input
            type="text"
            value={targetCaseId}
            onChange={(e) => setTargetCaseId(e.target.value)}
            placeholder={t("ingestion.targetPlaceholder")}
            className="text-sm border rounded-md px-3 py-2 w-64 font-mono"
          />
          <Button
            variant="default"
            size="sm"
            className="gap-2 font-semibold shadow-sm"
            disabled={!targetCaseId.trim()}
            onClick={() => setIsModalOpen(true)}
          >
            <Upload className="h-4 w-4" />
            <span>{t("ingestion.launchBtn")}</span>
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="shadow-sm border border-slate-200">
          <CardHeader className="border-b bg-slate-50 dark:bg-slate-950/50 pb-4">
            <CardTitle className="text-base font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
              <FileSpreadsheet className="h-5 w-5 text-blue-600" />
              {t("ingestion.templates")}
            </CardTitle>
            <CardDescription className="text-xs">
              {t("ingestion.templatesSub")}
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6 flex flex-wrap gap-3">
            <Button variant="outline" size="sm" onClick={() => ingestionService.downloadTemplate("csv")}>
              <FileText className="h-4 w-4 mr-1.5" /> CSV Template
            </Button>
            <Button size="sm" onClick={() => ingestionService.downloadTemplate("xlsx")}>
              <FileSpreadsheet className="h-4 w-4 mr-1.5" /> XLSX Template
            </Button>
          </CardContent>
        </Card>

        <Card className="shadow-sm border border-slate-200">
          <CardHeader className="border-b bg-slate-50 dark:bg-slate-950/50 pb-4 flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-base font-bold text-slate-800 dark:text-slate-200">{t("ingestion.recent")}</CardTitle>
              <CardDescription className="text-xs">queued → processing → completed / failed</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={loadJobs} disabled={loadingJobs}>
              <RefreshCw className={`h-3.5 w-3.5 mr-1 ${loadingJobs ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            {jobs.length === 0 ? (
              <p className="p-6 text-sm text-slate-500 dark:text-slate-400">No import jobs yet.</p>
            ) : (
              <div className="max-h-72 overflow-y-auto divide-y">
                {jobs.map((j) => (
                  <div key={j.id} className="px-4 py-3 text-xs flex items-center justify-between gap-3">
                    <div>
                      <div className="font-mono text-slate-800 dark:text-slate-200">{j.id}</div>
                      <div className="text-slate-500 dark:text-slate-400">{j.file_name} · case {j.case_id || "—"}</div>
                    </div>
                    <div className="text-right">
                      <Badge variant="outline" className="uppercase">{j.status}</Badge>
                      <div className="text-slate-500 dark:text-slate-400 mt-1">
                        {j.processed_records}/{j.total_records} · graph: {j.graph_sync_status || "—"}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <BulkImportModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        caseId={targetCaseId.trim()}
        onSuccess={loadJobs}
      />
    </div>
  );
};
