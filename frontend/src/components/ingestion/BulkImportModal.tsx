import React, { useState } from "react";
import { ingestionService, type IngestionUploadResponse, type IngestionErrorRow } from "@/api/client";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import {
  Upload, FileSpreadsheet, FileText, CheckCircle2, AlertCircle,
  X, RefreshCw, Download, Layers, ShieldAlert
} from "lucide-react";

interface BulkImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  caseId?: string;
  onSuccess?: () => void;
}

export const BulkImportModal: React.FC<BulkImportModalProps> = ({
  isOpen,
  onClose,
  caseId,
  onSuccess,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<IngestionUploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errorsList, setErrorsList] = useState<IngestionErrorRow[]>([]);
  const [loadingErrors, setLoadingErrors] = useState(false);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.size > 15 * 1024 * 1024) {
        setError("File size exceeds 15 MB boundary. Please select a smaller file.");
        return;
      }
      setSelectedFile(file);
      setError(null);
      setResult(null);
      setErrorsList([]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    if (!caseId) {
      setError("case_id is required. Open bulk import from a case detail page.");
      return;
    }
    setUploading(true);
    setError(null);
    try {
      let res = await ingestionService.uploadFile(selectedFile, caseId);
      // Poll when queued/processing (ARQ path)
      if (res.status === "queued" || res.status === "processing") {
        for (let i = 0; i < 60; i++) {
          await new Promise((r) => setTimeout(r, 1000));
          const job = await ingestionService.getJobStatus(res.job_id);
          if (job.status === "completed" || job.status === "failed") {
            res = {
              ...res,
              status: job.status,
              message: job.error_summary || res.message,
              summary: {
                total_records: job.total_records,
                processed_records: job.processed_records,
                rejected_records: job.rejected_records,
                duplicates_skipped: 0,
                new_accounts_created: 0,
                new_transactions_created: job.processed_records,
              },
            };
            break;
          }
        }
      }
      setResult(res);
      const rejected = res.summary?.rejected_records || 0;
      const processed = res.summary?.processed_records || 0;
      if (rejected > 0) {
        fetchErrors(res.job_id);
      }
      if (onSuccess && processed > 0) {
        onSuccess();
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || "Bulk import failed.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setUploading(false);
    }
  };

  const fetchErrors = async (jobId: string) => {
    setLoadingErrors(true);
    try {
      const report = await ingestionService.getJobErrors(jobId);
      setErrorsList(report.errors || []);
    } catch {
      // ignore error details failure
    } finally {
      setLoadingErrors(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setResult(null);
    setError(null);
    setErrorsList([]);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-2xl rounded-xl bg-white dark:bg-slate-900 shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 dark:bg-slate-950 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-blue-600 p-2 text-white shadow-sm">
              <Upload className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                Bulk Transaction Ingestion Framework
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {caseId ? `Target Case: ${caseId}` : "Global Money-Trail Import Pipeline"}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-200 hover:text-slate-700 dark:text-slate-300 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Official Templates Section (`Sub-phase 7.1`) */}
          <div className="rounded-lg border border-blue-100 bg-blue-50 dark:bg-blue-900/40/50 p-4">
            <div className="flex items-start justify-between">
              <div>
                <h4 className="text-sm font-semibold text-blue-900 flex items-center gap-1.5">
                  <FileSpreadsheet className="h-4 w-4 text-blue-600" />
                  Official Import Templates
                </h4>
                <p className="text-xs text-blue-700 mt-1">
                  Download standardized multi-hop templates. Includes source/target IFSC, UTR, RRN, and withdrawal flags.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => ingestionService.downloadTemplate("csv")}
                  className="inline-flex items-center gap-1.5 rounded-md bg-white dark:bg-slate-900 border border-blue-200 px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-50 dark:bg-blue-900/40 shadow-2xs transition-colors"
                >
                  <FileText className="h-3.5 w-3.5" />
                  CSV Template
                </button>
                <button
                  type="button"
                  onClick={() => ingestionService.downloadTemplate("xlsx")}
                  className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 shadow-2xs transition-colors"
                >
                  <FileSpreadsheet className="h-3.5 w-3.5" />
                  XLSX Template
                </button>
              </div>
            </div>
          </div>

          {/* File Upload Zone */}
          {!result ? (
            <div className="space-y-4">
              <div
                className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all ${
                  selectedFile ? "border-blue-500 bg-blue-50 dark:bg-blue-900/40/30" : "border-slate-300 hover:border-slate-400 bg-slate-50 dark:bg-slate-950"
                }`}
              >
                <input
                  type="file"
                  accept=".csv,.xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv"
                  onChange={handleFileChange}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <div className="flex flex-col items-center justify-center space-y-2">
                  <div className="rounded-full bg-slate-100 p-3 text-slate-600 dark:text-slate-400 shadow-xs">
                    <Upload className="h-6 w-6" />
                  </div>
                  <div className="text-sm font-medium text-slate-800 dark:text-slate-200">
                    {selectedFile ? (
                      <span className="text-blue-700 font-semibold">{selectedFile.name}</span>
                    ) : (
                      <span>
                        Drop your CSV or XLSX statement here, or <span className="text-blue-600 underline">browse</span>
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Supports up to 15 MB boundary. Validated by magic byte verification (`validate_file_upload`).
                  </p>
                </div>
              </div>

              {error && (
                <div className="rounded-lg bg-red-50 dark:bg-red-900/40 border border-red-200 p-3.5 flex items-start gap-2.5 text-red-800 text-sm">
                  <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <span className="font-semibold block">Upload Gate Warning:</span>
                    {error}
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* Ingestion Results Summary (`Sub-phase 7.2 & 7.3`) */
            <div className="space-y-5">
              <div className="rounded-xl border border-emerald-200 bg-emerald-50 dark:bg-emerald-900/40/60 p-5">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="h-6 w-6 text-emerald-600 shrink-0" />
                  <div>
                    <h4 className="text-base font-bold text-emerald-950">
                      Ingestion Pipeline Completed
                    </h4>
                    <p className="text-xs text-emerald-800 mt-0.5">
                      Job ID: <code className="font-mono bg-emerald-100 px-1 py-0.5 rounded">{result.job_id}</code> | File: {result.file_name}
                    </p>
                  </div>
                </div>

                <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-3">
                  <div className="rounded-lg bg-white dark:bg-slate-900/80 p-3 border border-emerald-100">
                    <span className="text-xs text-slate-500 dark:text-slate-400 block">Total Rows</span>
                    <span className="text-lg font-bold text-slate-900 dark:text-slate-100">{result.summary?.total_records ?? "—"}</span>
                  </div>
                  <div className="rounded-lg bg-white dark:bg-slate-900/80 p-3 border border-emerald-100">
                    <span className="text-xs text-slate-500 dark:text-slate-400 block">Imported</span>
                    <span className="text-lg font-bold text-emerald-600">{result.summary?.processed_records ?? "—"}</span>
                  </div>
                  <div className="rounded-lg bg-white dark:bg-slate-900/80 p-3 border border-emerald-100">
                    <span className="text-xs text-slate-500 dark:text-slate-400 block">Duplicates Skipped</span>
                    <span className="text-lg font-bold text-amber-600">{result.summary?.duplicates_skipped ?? "—"}</span>
                  </div>
                  <div className="rounded-lg bg-white dark:bg-slate-900/80 p-3 border border-emerald-100">
                    <span className="text-xs text-slate-500 dark:text-slate-400 block">New Accounts</span>
                    <span className="text-lg font-bold text-blue-600">{result.summary?.new_accounts_created ?? "—"}</span>
                  </div>
                  <div className="rounded-lg bg-white dark:bg-slate-900/80 p-3 border border-emerald-100">
                    <span className="text-xs text-slate-500 dark:text-slate-400 block">New Transactions</span>
                    <span className="text-lg font-bold text-blue-600">{result.summary?.new_transactions_created ?? "—"}</span>
                  </div>
                  <div className="rounded-lg bg-white dark:bg-slate-900/80 p-3 border border-emerald-100">
                    <span className="text-xs text-slate-500 dark:text-slate-400 block">Rejected</span>
                    <span className="text-lg font-bold text-red-600">{result.summary?.rejected_records ?? "—"}</span>
                  </div>
                </div>
              </div>

              {/* Per-Row Errors Table (`Sub-phase 7.2 Checkpoint`) */}
              {(result.summary?.rejected_records || 0) > 0 && (
                <div className="rounded-lg border border-red-200 bg-red-50 dark:bg-red-900/40/40 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h5 className="text-sm font-semibold text-red-900 flex items-center gap-1.5">
                      <ShieldAlert className="h-4 w-4 text-red-600" />
                      Rejected Rows Detail ({result.summary?.rejected_records})
                    </h5>
                    {loadingErrors && <RefreshCw className="h-4 w-4 text-red-600 animate-spin" />}
                  </div>

                  {errorsList.length > 0 ? (
                    <div className="max-h-48 overflow-y-auto rounded border border-red-200 bg-white dark:bg-slate-900">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-red-50 dark:bg-red-900/40 text-red-900 font-semibold sticky top-0">
                          <tr>
                            <th className="p-2 border-b">Row #</th>
                            <th className="p-2 border-b">Error Reason</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {errorsList.map((err, i) => (
                            <tr key={i} className="hover:bg-slate-50 dark:bg-slate-950">
                              <td className="p-2 font-mono text-slate-700 dark:text-slate-300 w-16">{err.row}</td>
                              <td className="p-2 text-red-700 font-medium">{err.error}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-xs text-red-600">Loading error log from server...</p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-3 border-t border-slate-100 bg-slate-50 dark:bg-slate-950 px-6 py-4">
          {result ? (
            <>
              <Button variant="outline" size="sm" onClick={handleReset}>
                Upload Another Statement
              </Button>
              <Button variant="default" size="sm" onClick={onClose}>
                Done & View Case Trail
              </Button>
            </>
          ) : (
            <>
              <Button variant="outline" size="sm" onClick={onClose} disabled={uploading}>
                Cancel
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={handleUpload}
                disabled={!selectedFile || uploading}
              >
                {uploading ? (
                  <span className="flex items-center gap-2">
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Ingesting & Normalizing...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Upload className="h-4 w-4" />
                    Start Ingestion
                  </span>
                )}
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
