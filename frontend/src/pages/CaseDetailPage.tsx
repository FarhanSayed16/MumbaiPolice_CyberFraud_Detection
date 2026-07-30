import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { caseService, accountService, timelineService, userService, type CaseDetail, type TimelineEventItem, type UserProfile } from "@/api/client";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { BulkImportModal } from "@/components/ingestion/BulkImportModal";
import { CaseTrailGraph } from "@/components/cases/CaseTrailGraph";
import { CaseEvidenceTab } from "@/components/cases/CaseEvidenceTab";
import { CaseTimelineTab } from "@/components/cases/CaseTimelineTab";
import { RelatedCasesPanel } from "@/components/cases/RelatedCasesPanel";
import { CaseNoticesTab } from "@/components/cases/CaseNoticesTab";
import { CaseRiskTab } from "@/components/cases/CaseRiskTab";
import { useAuth } from "@/context/AuthContext";
import {
  ArrowLeft, FileText, Upload, AlertTriangle, CheckCircle, RefreshCw, User, ShieldAlert, Edit, Save, Printer
} from "lucide-react";
import { Skeleton } from "@/components/ui/Skeleton";

type DetailTab = "trail" | "risk" | "patterns" | "notices" | "evidence" | "timeline";

export const CaseDetailPage: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();
  const { t } = useTranslation();

  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<DetailTab>("trail");
  const [dupBusy, setDupBusy] = useState(false);
  const [revealBusy, setRevealBusy] = useState<string | null>(null);
  const [revealed, setRevealed] = useState<Record<string, { account_number?: string; ifsc_code?: string; upi_id?: string }>>({});
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [trailRefreshToken, setTrailRefreshToken] = useState(0);

  // Assignment and Status
  const { user } = useAuth();
  const [isAssigning, setIsAssigning] = useState(false);
  const [assigneeId, setAssigneeId] = useState("");
  const [assignableOfficers, setAssignableOfficers] = useState<UserProfile[]>([]);
  const [revealModalOpen, setRevealModalOpen] = useState(false);
  const [revealTargetId, setRevealTargetId] = useState<string | null>(null);
  const [revealReason, setRevealReason] = useState("");
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [newStatus, setNewStatus] = useState("");
  const [closureReason, setClosureReason] = useState("");
  const [closureRemarks, setClosureRemarks] = useState("");
  const [printTimeline, setPrintTimeline] = useState<TimelineEventItem[]>([]);

  const loadCaseDetail = async () => {
    if (!caseId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await caseService.getCaseDetail(caseId);
      setCaseDetail(data);
    } catch {
      setError("Failed to fetch case detail. Verify backend is running and you have access to this case.");
      setCaseDetail(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCaseDetail();
  }, [caseId]);

  useEffect(() => {
    if (!caseId) return;
    timelineService.list(caseId, "asc").then(setPrintTimeline).catch(() => setPrintTimeline([]));
  }, [caseId]);

  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(amount || 0);

  const handleAckDuplicate = async () => {
    if (!caseId) return;
    setDupBusy(true);
    try {
      await caseService.acknowledgeDuplicate(caseId);
      await loadCaseDetail();
    } catch {
      setError("Failed to acknowledge duplicate warning.");
    } finally {
      setDupBusy(false);
    }
  };

  const handleDismissDuplicate = async () => {
    if (!caseId) return;
    setDupBusy(true);
    try {
      await caseService.dismissDuplicate(caseId);
      await loadCaseDetail();
    } catch {
      setError("Failed to dismiss duplicate warning.");
    } finally {
      setDupBusy(false);
    }
  };

  const handleRevealAccount = (accountId: string) => {
    setRevealTargetId(accountId);
    setRevealReason("");
    setRevealModalOpen(true);
    setError(null);
  };

  const confirmRevealAccount = async () => {
    if (!revealTargetId || !caseId) return;
    if (revealReason.trim().length < 10) {
      setError("Reveal reason must be at least 10 characters for audit compliance.");
      return;
    }
    setRevealBusy(revealTargetId);
    setError(null);
    try {
      const data = await accountService.reveal(revealTargetId, revealReason.trim(), caseId);
      setRevealed((prev) => ({
        ...prev,
        [revealTargetId]: {
          account_number: data.account_number,
          ifsc_code: data.ifsc_code,
          upi_id: data.upi_id,
        },
      }));
      setRevealModalOpen(false);
      setRevealTargetId(null);
      setRevealReason("");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Account reveal failed (audit required).");
    } finally {
      setRevealBusy(null);
    }
  };

  const openAssignPanel = async () => {
    setIsAssigning(true);
    setError(null);
    try {
      const officers = await userService.listAssignable();
      setAssignableOfficers(officers);
    } catch {
      setAssignableOfficers([]);
      setError("Could not load officer list for assignment.");
    }
  };

  const handleUpdateStatus = async () => {
    if (!caseId || !newStatus) return;
    if ((newStatus === "closed" || newStatus === "dead_end") && !closureReason) {
      setError("Closure reason is required when closing a case.");
      return;
    }
    setError(null);
    try {
      await caseService.updateCase(caseId, {
        status: newStatus,
        closure_reason: closureReason || undefined,
        closure_remarks: closureRemarks || undefined,
      });
      setIsUpdatingStatus(false);
      setNewStatus("");
      setClosureReason("");
      setClosureRemarks("");
      await loadCaseDetail();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to update case status.");
    }
  };

  const handleAssign = async () => {
    if (!caseId || !assigneeId) return;
    setError(null);
    try {
      await caseService.updateCase(caseId, { assigned_to_user_id: assigneeId });
      setIsAssigning(false);
      setAssigneeId("");
      await loadCaseDetail();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to assign case.");
    }
  };

  const tabs: { id: DetailTab; labelKey: string }[] = [
    { id: "trail", labelKey: "case.tabs.trail" },
    { id: "risk", labelKey: "case.tabs.risk" },
    { id: "patterns", labelKey: "case.tabs.patterns" },
    { id: "notices", labelKey: "case.tabs.notices" },
    { id: "evidence", labelKey: "case.tabs.evidence" },
    { id: "timeline", labelKey: "case.tabs.timeline" },
  ];

  if (loading && !caseDetail) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between border-b pb-4 bg-white dark:bg-slate-900 p-4 rounded-lg shadow-sm border">
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-10 w-64" />
        </div>
        <div className="flex gap-1 border-b">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-10 w-24 mx-1" />
          ))}
        </div>
        <Skeleton className="h-[400px] w-full" />
      </div>
    );
  }

  if (!caseDetail) {
    return (
      <div className="space-y-4 p-6">
        <Link to="/cases"><Button variant="outline" size="sm" className="gap-2"><ArrowLeft className="h-4 w-4" />Back</Button></Link>
        <div className="p-4 bg-red-50 dark:bg-red-900/40 border border-red-200 rounded-lg text-red-800 text-sm flex items-center justify-between">
          <span>{error || "Case not found."}</span>
          <Button variant="outline" size="sm" onClick={loadCaseDetail}>Retry</Button>
        </div>
      </div>
    );
  }

  const flags = caseDetail.suspicion_flags_json || {};
  const watchlistHits = (flags.watchlist_hits as Array<Record<string, unknown>> | undefined) || [];
  const showDupActions = (caseDetail.duplicate_warnings?.length || 0) > 0 && !flags.dismissed_at;

  return (
    <div className="space-y-6 case-brief-print">
      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/40 border border-red-200 rounded-lg flex items-center justify-between text-red-800 text-sm no-print">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <Button variant="outline" size="sm" onClick={loadCaseDetail}>Retry</Button>
        </div>
      )}

      <div className="flex items-center justify-between border-b pb-4 bg-white dark:bg-slate-900 p-4 rounded-lg shadow-sm border">
        <div className="flex items-center gap-4">
          <Link to="/cases" className="no-print">
            <Button variant="outline" size="sm" className="gap-2 focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary">
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Queue</span>
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-200 tracking-tight font-mono">{caseDetail.case_number}</h2>
              <Badge className="bg-emerald-100 text-emerald-800 border-emerald-300 uppercase font-semibold">
                {caseDetail.fraud_category?.replace(/_/g, " ")}
              </Badge>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-blue-700 bg-blue-50 dark:bg-blue-900/40 border-blue-200 uppercase font-semibold cursor-pointer" onClick={() => setIsUpdatingStatus(true)}>
                  Status: {caseDetail.status.replace(/_/g, " ")}
                  <Edit className="h-3 w-3 ml-1 inline" />
                </Badge>
                {caseDetail.closure_reason && (
                  <Badge variant="secondary" className="text-xs ml-1 bg-slate-100 text-slate-600 dark:text-slate-400">
                    Reason: {caseDetail.closure_reason}
                  </Badge>
                )}
              </div>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-4 flex-wrap">
              <span>Reported: {new Date(caseDetail.reported_at).toLocaleDateString("en-IN")}</span>
              <span className="inline-flex items-center gap-1 group relative">
                <User className="h-3 w-3" />
                Assignee: <strong>{caseDetail.assigned_officer_name || "Unassigned"}</strong>
                {(user?.role === "admin" || user?.role === "supervisor") && (
                  <Button variant="ghost" size="sm" className="h-5 px-1 ml-1" onClick={() => openAssignPanel()}>
                    <Edit className="h-3 w-3" />
                  </Button>
                )}
              </span>
              {caseDetail.ncrp_acknowledgement_number && (
                <span className="font-mono bg-slate-100 px-1.5 py-0.5 rounded">NCRP: {caseDetail.ncrp_acknowledgement_number}</span>
              )}
              <span>Amount at Risk: <strong className="text-slate-800 dark:text-slate-200">{formatCurrency(caseDetail.amount_at_risk)}</strong></span>
              <span>Recovered: <strong className="text-emerald-700">{formatCurrency(caseDetail.amount_recovered)}</strong></span>
              {caseDetail.restoration_status && caseDetail.restoration_status !== 'pending' && (
                <Badge variant="outline" className="text-emerald-700 bg-emerald-50 dark:bg-emerald-900/40 border-emerald-200 text-[10px] h-5 py-0 uppercase">
                  {caseDetail.restoration_status.replace(/_/g, " ")}
                </Badge>
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 no-print">
          <Button
            variant="outline"
            size="sm"
            className="gap-2 font-medium border-slate-300 focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary"
            onClick={() => window.print()}
          >
            <Printer className="h-4 w-4 text-slate-600 dark:text-slate-400" />
            <span>Print Case Brief</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="gap-2 font-medium border-blue-200 text-blue-700 bg-blue-50 dark:bg-blue-900/40/50 hover:bg-blue-100/80 hover:text-blue-900 shadow-2xs transition-colors focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary"
            onClick={() => setIsImportModalOpen(true)}
          >
            <Upload className="h-4 w-4 text-blue-600" />
            <span>Import Transactions (CSV/XLSX)</span>
          </Button>
        </div>
      </div>

      {showDupActions && (
        <div className="p-4 bg-amber-50 dark:bg-amber-900/40 border-2 border-amber-300 rounded-lg flex items-center justify-between gap-4 flex-wrap no-print">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-6 w-6 text-amber-600 flex-shrink-0" />
            <div>
              <h4 className="font-bold text-amber-900 text-sm">Duplicate / suspicion flags present</h4>
              <p className="text-xs text-amber-800 mt-0.5">
                {caseDetail.duplicate_warnings.length} match rule(s). Acknowledge or dismiss with audit.
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" disabled={dupBusy} onClick={handleDismissDuplicate}>Dismiss</Button>
            <Button size="sm" disabled={dupBusy} onClick={handleAckDuplicate} className="gap-1">
              <CheckCircle className="h-4 w-4" /> Acknowledge
            </Button>
          </div>
        </div>
      )}

      {watchlistHits.length > 0 && (
        <div className="p-4 bg-red-50 dark:bg-red-900/40 border-2 border-red-300 rounded-lg flex items-center gap-4 flex-wrap shadow-sm no-print">
          <ShieldAlert className="h-6 w-6 text-red-600 flex-shrink-0" />
          <div>
            <h4 className="font-bold text-red-900 text-sm">WATCHLIST HIT DETECTED</h4>
            <p className="text-xs text-red-800 mt-0.5">
              {watchlistHits.length} watchlist match(es) flagged on intake or ingestion. Priority action required.
            </p>
          </div>
        </div>
      )}

      {isUpdatingStatus && (
        <div className="p-4 bg-white dark:bg-slate-900 border rounded-lg shadow-sm space-y-4 no-print">
          <h4 className="font-bold text-slate-800 dark:text-slate-200">Update Case Status</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">New Status</label>
              <select
                className="flex h-9 w-full rounded-md border border-slate-300 bg-transparent px-3 py-1 text-sm shadow-sm"
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
              >
                <option value="">-- Select Status --</option>
                <option value="reported">Reported</option>
                <option value="intake_complete">Intake Complete</option>
                <option value="tracing">Tracing</option>
                <option value="notice_pending">Notice Pending</option>
                <option value="notice_sent">Notice Sent</option>
                <option value="awaiting_bank">Awaiting Bank</option>
                <option value="action_taken">Action Taken</option>
                <option value="partially_recovered">Partially Recovered</option>
                <option value="closed">Closed</option>
                <option value="dead_end">Dead End</option>
              </select>
            </div>
            
            {(newStatus === "closed" || newStatus === "dead_end") && (
              <>
                <div>
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Closure Reason *</label>
                  <select
                    className="flex h-9 w-full rounded-md border border-slate-300 bg-transparent px-3 py-1 text-sm shadow-sm"
                    value={closureReason}
                    onChange={(e) => setClosureReason(e.target.value)}
                  >
                    <option value="">-- Select Reason --</option>
                    <option value="resolved">Resolved / Recovered</option>
                    <option value="insufficient_evidence">Insufficient Evidence</option>
                    <option value="transferred">Transferred to another agency</option>
                    <option value="duplicate">Duplicate Case</option>
                    <option value="no_funds">No Funds in Suspect Accounts</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Closure Remarks (Optional)</label>
                  <input
                    type="text"
                    className="flex h-9 w-full rounded-md border border-slate-300 bg-transparent px-3 py-1 text-sm shadow-sm"
                    value={closureRemarks}
                    onChange={(e) => setClosureRemarks(e.target.value)}
                    placeholder="Enter additional remarks..."
                  />
                </div>
              </>
            )}
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => { setIsUpdatingStatus(false); setNewStatus(""); }}>Cancel</Button>
            <Button size="sm" onClick={handleUpdateStatus} disabled={!newStatus}>Save Status</Button>
          </div>
        </div>
      )}

      {isAssigning && (
        <div className="p-4 bg-white dark:bg-slate-900 border rounded-lg shadow-sm space-y-4 no-print">
          <h4 className="font-bold text-slate-800 dark:text-slate-200">Assign Case</h4>
          <div>
            <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Assign to officer</label>
            <select
              className="flex h-9 w-full md:w-1/2 rounded-md border border-slate-300 bg-transparent px-3 py-1 text-sm shadow-sm mt-1"
              value={assigneeId}
              onChange={(e) => setAssigneeId(e.target.value)}
            >
              <option value="">Select officer…</option>
              {assignableOfficers.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name} {o.badge_number ? `(${o.badge_number})` : ""} — {o.role}
                </option>
              ))}
            </select>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => { setIsAssigning(false); setAssigneeId(""); }}>Cancel</Button>
            <Button size="sm" onClick={handleAssign} disabled={!assigneeId}>Assign Case</Button>
          </div>
        </div>
      )}

      {revealModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 no-print">
          <div className="w-full max-w-md rounded-lg bg-white dark:bg-slate-900 border shadow-xl p-5 space-y-4">
            <h4 className="font-bold text-slate-800 dark:text-slate-100">Unmask account (audited)</h4>
            <p className="text-xs text-slate-500">
              Provide a statutory / investigative justification (minimum 10 characters). This action is logged.
            </p>
            <textarea
              className="w-full min-h-[90px] rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={revealReason}
              onChange={(e) => setRevealReason(e.target.value)}
              placeholder="e.g. Required to draft BNSS Sec 94 notice to nodal bank…"
            />
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setRevealModalOpen(false);
                  setRevealTargetId(null);
                  setRevealReason("");
                }}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={confirmRevealAccount}
                disabled={revealReason.trim().length < 10 || !!revealBusy}
              >
                {revealBusy ? "Revealing…" : "Confirm reveal"}
              </Button>
            </div>
          </div>
        </div>
      )}

      <div className="flex gap-1 border-b no-print">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-semibold border-b-2 -mb-px focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
              activeTab === tab.id
                ? "border-blue-600 text-blue-700"
                : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:text-slate-200"
            }`}
          >
            {t(tab.labelKey)}
          </button>
        ))}
      </div>

      <div className="print-only case-brief-timeline">
        <h3>{t("timeline.printTitle", "Case Timeline (Chronological)")}</h3>
        {printTimeline.length === 0 ? (
          <p className="text-sm">{t("timeline.empty", "No events recorded yet.")}</p>
        ) : (
          <ul>
            {printTimeline.map((event) => (
              <li key={event.id}>
                <time dateTime={event.created_at}>{new Date(event.created_at).toLocaleString()}</time>
                <span>{event.description}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="mt-4">
        {activeTab === "trail" && (
          <div className="w-full">
            <CaseTrailGraph
              caseId={caseDetail.id}
              onAccountRevealed={loadCaseDetail}
              refreshToken={trailRefreshToken}
            />
          </div>
        )}
        {activeTab === "evidence" && <CaseEvidenceTab caseId={caseId!} />}
        {activeTab === "timeline" && <CaseTimelineTab caseId={caseId!} />}
        {activeTab === "notices" && <CaseNoticesTab caseId={caseId!} caseDetail={caseDetail} />}
        {activeTab === "risk" && <CaseRiskTab caseId={caseId!} />}
        {activeTab === "patterns" && (
          <RelatedCasesPanel caseId={caseId!} />
        )}
      </div>

      {activeTab !== "trail" && activeTab !== "evidence" && activeTab !== "timeline" && activeTab !== "patterns" && activeTab !== "notices" && activeTab !== "risk" && (
        <Card>
          <CardContent className="p-8 text-center text-slate-500 dark:text-slate-400 text-sm">
            <p className="font-semibold text-slate-700 dark:text-slate-300 mb-1">{tabs.find((tab) => tab.id === activeTab) ? t(tabs.find((tab) => tab.id === activeTab)!.labelKey) : ""} — placeholder</p>
            <p>This tab shell is ready for later phases (Risk 12, Patterns 13, Notices 15).</p>
          </CardContent>
        </Card>
      )}

      <BulkImportModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        caseId={caseDetail.id}
        onSuccess={() => {
          loadCaseDetail();
          setTrailRefreshToken((n) => n + 1);
          setActiveTab("trail");
        }}
      />    </div>
  );
};
