import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  callDeskService,
  type CallTicket,
} from "@/api/client";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import {
  Phone,
  PhoneCall,
  Clock,
  Upload,
  Link2,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
} from "lucide-react";

const SCRIPT_PROMPTS: { key: string; prompt: string }[] = [
  { key: "complainant_name", prompt: "May I have your full name?" },
  { key: "complainant_phone", prompt: "Confirm the mobile you are calling from." },
  { key: "txn_relative_time", prompt: "When did you send the money — just now, few minutes, or longer?" },
  { key: "amount_at_risk", prompt: "How much money was transferred?" },
  { key: "layer1", prompt: "What UPI ID or account number did you send to?" },
  { key: "fraud_category", prompt: "Was this digital arrest, investment, trading, or other?" },
];

function formatElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export const CallDeskPage: React.FC = () => {
  const navigate = useNavigate();
  const [ticket, setTicket] = useState<CallTicket | null>(null);
  const [recent, setRecent] = useState<CallTicket[]>([]);
  const [scriptCard, setScriptCard] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [proofUrl, setProofUrl] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [promptIdx, setPromptIdx] = useState(0);

  const refreshList = useCallback(async () => {
    try {
      const list = await callDeskService.listTickets();
      setRecent(list);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    callDeskService.getScriptCard().then((d) => setScriptCard(d.card)).catch(() => null);
    refreshList();
  }, [refreshList]);

  useEffect(() => {
    if (!ticket || ticket.status === "converted" || ticket.status === "abandoned") return;
    const start = new Date(ticket.answered_at || ticket.started_at).getTime();
    const tick = () => setElapsed(Math.max(0, Math.floor((Date.now() - start) / 1000)));
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, [ticket]);

  const timerClass = useMemo(() => {
    if (elapsed >= 600) return "text-red-700 bg-red-100 border-red-300";
    if (elapsed >= 300) return "text-amber-800 bg-amber-100 border-amber-300";
    return "text-emerald-800 bg-emerald-50 border-emerald-200";
  }, [elapsed]);

  const applyPatch = async (patch: Record<string, unknown>) => {
    if (!ticket) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await callDeskService.updateTicket(ticket.id, patch as Partial<CallTicket>);
      setTicket(updated);
      setPromptIdx((i) => Math.min(i + 1, SCRIPT_PROMPTS.length - 1));
    } catch (e: unknown) {
      setError("Failed to save ticket fields.");
    } finally {
      setBusy(false);
    }
  };

  const handleSimulate = async () => {
    setBusy(true);
    setError(null);
    setProofUrl(null);
    try {
      const ringing = await callDeskService.simulateInbound();
      const answered = await callDeskService.answer(ringing.id);
      setTicket(answered);
      setPromptIdx(0);
      await refreshList();
    } catch {
      setError("Could not simulate inbound call. Is the backend running?");
    } finally {
      setBusy(false);
    }
  };

  const fillFromScriptCard = async () => {
    if (!ticket || !scriptCard) return;
    await applyPatch({
      complainant_name: scriptCard.complainant_name,
      complainant_phone: scriptCard.ani_phone,
      amount_at_risk: scriptCard.amount_at_risk,
      fraud_category: scriptCard.fraud_category,
      layer1_upi: scriptCard.layer1_upi,
      utr: scriptCard.utr,
      txn_relative_time: scriptCard.txn_relative_time,
      narrative_short: "Digital arrest video call — coerced UPI transfer. (DEMO)",
    });
  };

  const handleProofLink = async () => {
    if (!ticket) return;
    setBusy(true);
    try {
      const link = await callDeskService.issueProofLink(ticket.id);
      const full = `${window.location.origin}${link.proof_portal_path}`;
      setProofUrl(full);
      const refreshed = await callDeskService.getTicket(ticket.id);
      setTicket(refreshed);
    } catch {
      setError("Could not issue proof link.");
    } finally {
      setBusy(false);
    }
  };

  const handleDeskUpload = async (file: File | null) => {
    if (!ticket || !file) return;
    setBusy(true);
    try {
      await callDeskService.uploadDeskProof(ticket.id, file, "Desk-received screenshot");
      setTicket(await callDeskService.getTicket(ticket.id));
    } catch {
      setError("Proof upload failed (use PNG/JPEG/PDF ≤15MB).");
    } finally {
      setBusy(false);
    }
  };

  const handleConvert = async (ackDup = false) => {
    if (!ticket) return;
    setBusy(true);
    setError(null);
    try {
      const result = await callDeskService.convertToCase(ticket.id, ackDup);
      setTicket(result.ticket);
      await refreshList();
      navigate(`/cases/${result.case_id}`);
    } catch (err: unknown) {
      const ax = err as { response?: { status?: number; data?: { detail?: unknown } } };
      if (ax.response?.status === 409) {
        const ok = window.confirm("Possible duplicate detected. Create case anyway?");
        if (ok) {
          setBusy(false);
          await handleConvert(true);
          return;
        }
      }
      const detail = ax.response?.data?.detail;
      if (typeof detail === "object" && detail && "message" in (detail as object)) {
        setError(String((detail as { message: string }).message));
      } else {
        setError("Convert failed — complete freeze-critical fields first.");
      }
    } finally {
      setBusy(false);
    }
  };

  const openRecent = async (id: string) => {
    setBusy(true);
    try {
      setTicket(await callDeskService.getTicket(id));
      setProofUrl(null);
    } finally {
      setBusy(false);
    }
  };

  const checks = ticket?.completeness?.checks || {};

  return (
    <div className="space-y-4 p-4 md:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
              Helpline Intake Console
            </h1>
            <Badge className="bg-amber-100 text-amber-900 border-amber-300 font-semibold">
              Training Call Desk — Simulated Line
            </Badge>
          </div>
          <p className="text-sm text-slate-500 mt-1 max-w-2xl">
            Capture freeze-critical fields in the golden window, collect proofs, then create a case in the
            investigation cockpit. Not live 1930 / NCRP.
          </p>
        </div>
        <Button onClick={handleSimulate} disabled={busy} className="gap-2">
          <PhoneCall className="h-4 w-4" />
          Simulate inbound call
        </Button>
      </div>

      {error && (
        <div className="p-3 rounded-md border border-red-200 bg-red-50 text-red-800 text-sm flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
        {/* Left: context + script */}
        <Card className="xl:col-span-3">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Phone className="h-4 w-4" /> Call context
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {ticket ? (
              <>
                <div>
                  <div className="text-xs text-slate-500">Ticket</div>
                  <div className="font-mono font-semibold">{ticket.ticket_number}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-500">ANI / CLI</div>
                  <div className="font-mono">{ticket.ani_phone || "—"}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-500">Status</div>
                  <Badge variant="outline" className="uppercase">{ticket.status.replace(/_/g, " ")}</Badge>
                </div>
                <div className={`rounded-md border px-3 py-2 font-mono text-2xl font-bold text-center ${timerClass}`}>
                  <div className="flex items-center justify-center gap-2 text-xs font-sans font-medium mb-1 opacity-80">
                    <Clock className="h-3 w-3" /> Golden window
                  </div>
                  {ticket.status === "converted" && ticket.elapsed_to_case_seconds != null
                    ? formatElapsed(ticket.elapsed_to_case_seconds)
                    : formatElapsed(elapsed)}
                </div>
                <div className="border-t pt-3 space-y-2">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Script prompt</div>
                  <p className="text-slate-800 dark:text-slate-200">{SCRIPT_PROMPTS[promptIdx]?.prompt}</p>
                  <Button variant="outline" size="sm" onClick={fillFromScriptCard} disabled={busy || !scriptCard}>
                    Fill demo script card
                  </Button>
                </div>
              </>
            ) : (
              <p className="text-slate-500">Click <strong>Simulate inbound call</strong> to start the DCP demo path.</p>
            )}
          </CardContent>
        </Card>

        {/* Centre: form */}
        <Card className="xl:col-span-5">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Freeze-critical fields</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {!ticket ? (
              <p className="text-sm text-slate-500">No active ticket.</p>
            ) : (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <label className="text-xs space-y-1">
                    <span>Complainant name {checks.complainant_name ? "✓" : "*"}</span>
                    <input
                      className="w-full border rounded-md px-2 py-1.5 text-sm"
                      defaultValue={ticket.complainant_name || ""}
                      key={`name-${ticket.updated_at}`}
                      onBlur={(e) => applyPatch({ complainant_name: e.target.value })}
                    />
                  </label>
                  <label className="text-xs space-y-1">
                    <span>Phone {checks.complainant_phone ? "✓" : "*"}</span>
                    <input
                      className="w-full border rounded-md px-2 py-1.5 text-sm font-mono"
                      defaultValue={ticket.complainant_phone || ""}
                      key={`phone-${ticket.updated_at}`}
                      onBlur={(e) => applyPatch({ complainant_phone: e.target.value })}
                    />
                  </label>
                  <label className="text-xs space-y-1">
                    <span>Txn timing {checks.txn_relative_time ? "✓" : "*"}</span>
                    <select
                      className="w-full border rounded-md px-2 py-1.5 text-sm"
                      value={ticket.txn_relative_time || ""}
                      onChange={(e) => applyPatch({ txn_relative_time: e.target.value })}
                    >
                      <option value="">Select…</option>
                      <option value="just_now">Just now (&lt;2 min)</option>
                      <option value="few_minutes">Few minutes</option>
                      <option value="longer">Longer ago</option>
                    </select>
                  </label>
                  <label className="text-xs space-y-1">
                    <span>Amount (₹) {checks.amount_at_risk ? "✓" : "*"}</span>
                    <input
                      type="number"
                      className="w-full border rounded-md px-2 py-1.5 text-sm font-mono"
                      defaultValue={ticket.amount_at_risk ?? ""}
                      key={`amt-${ticket.updated_at}`}
                      onBlur={(e) => applyPatch({ amount_at_risk: Number(e.target.value) })}
                    />
                  </label>
                  <label className="text-xs space-y-1 sm:col-span-2">
                    <span>Fraud category {checks.fraud_category ? "✓" : "*"}</span>
                    <select
                      className="w-full border rounded-md px-2 py-1.5 text-sm"
                      value={ticket.fraud_category || ""}
                      onChange={(e) => applyPatch({ fraud_category: e.target.value })}
                    >
                      <option value="">Select…</option>
                      <option value="digital_arrest">Digital arrest</option>
                      <option value="investment_scam">Investment scam</option>
                      <option value="online_trading_scam">Online trading</option>
                      <option value="hacking_digital_fraud">Hacking / digital fraud</option>
                      <option value="sextortion">Sextortion</option>
                      <option value="other">Other</option>
                    </select>
                  </label>
                  <label className="text-xs space-y-1">
                    <span>Layer-1 UPI {checks.layer1 ? "✓" : "*"}</span>
                    <input
                      className="w-full border rounded-md px-2 py-1.5 text-sm font-mono"
                      defaultValue={ticket.layer1_upi || ""}
                      key={`upi-${ticket.updated_at}`}
                      onBlur={(e) => applyPatch({ layer1_upi: e.target.value })}
                      placeholder="name@oksbi"
                    />
                  </label>
                  <label className="text-xs space-y-1">
                    <span>Or account + IFSC</span>
                    <div className="flex gap-2">
                      <input
                        className="w-full border rounded-md px-2 py-1.5 text-sm font-mono"
                        defaultValue={ticket.layer1_account || ""}
                        key={`acc-${ticket.updated_at}`}
                        onBlur={(e) => applyPatch({ layer1_account: e.target.value })}
                        placeholder="Account"
                      />
                      <input
                        className="w-28 border rounded-md px-2 py-1.5 text-sm font-mono uppercase"
                        defaultValue={ticket.layer1_ifsc || ""}
                        key={`ifsc-${ticket.updated_at}`}
                        onBlur={(e) => applyPatch({ layer1_ifsc: e.target.value.toUpperCase() })}
                        placeholder="IFSC"
                      />
                    </div>
                  </label>
                  <label className="text-xs space-y-1">
                    <span>Bank (optional)</span>
                    <input
                      className="w-full border rounded-md px-2 py-1.5 text-sm"
                      defaultValue={ticket.layer1_bank || ""}
                      key={`bank-${ticket.updated_at}`}
                      onBlur={(e) => applyPatch({ layer1_bank: e.target.value })}
                    />
                  </label>
                  <label className="text-xs space-y-1">
                    <span>UTR / RRN (optional)</span>
                    <input
                      className="w-full border rounded-md px-2 py-1.5 text-sm font-mono"
                      defaultValue={ticket.utr || ""}
                      key={`utr-${ticket.updated_at}`}
                      onBlur={(e) => applyPatch({ utr: e.target.value })}
                    />
                  </label>
                  <label className="text-xs space-y-1 sm:col-span-2">
                    <span>Short narrative</span>
                    <textarea
                      className="w-full border rounded-md px-2 py-1.5 text-sm min-h-[64px]"
                      defaultValue={ticket.narrative_short || ""}
                      key={`narr-${ticket.updated_at}`}
                      onBlur={(e) => applyPatch({ narrative_short: e.target.value })}
                    />
                  </label>
                </div>
                <div className="text-xs text-slate-500">
                  Completeness: {ticket.completeness?.filled ?? 0}/{ticket.completeness?.total ?? 6}
                  {ticket.completeness?.ready_to_convert ? (
                    <span className="text-emerald-700 ml-2 inline-flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3" /> Ready to create case
                    </span>
                  ) : null}
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Right: proofs */}
        <Card className="xl:col-span-4">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Proofs</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {!ticket ? (
              <p className="text-slate-500">Active ticket required.</p>
            ) : (
              <>
                <Button variant="outline" size="sm" className="gap-2 w-full" onClick={handleProofLink} disabled={busy || ticket.status === "converted"}>
                  <Link2 className="h-4 w-4" /> Send upload link (demo)
                </Button>
                {proofUrl && (
                  <div className="p-2 rounded border bg-slate-50 dark:bg-slate-800 text-xs break-all space-y-1">
                    <div className="font-semibold">Share with caller:</div>
                    <a className="text-blue-700 underline" href={proofUrl} target="_blank" rel="noreferrer">
                      {proofUrl}
                    </a>
                    <div>
                      <Link to={ticket.proof_portal_path || "#"} className="inline-flex items-center gap-1 text-blue-700">
                        Open portal <ExternalLink className="h-3 w-3" />
                      </Link>
                    </div>
                  </div>
                )}
                <label className="flex items-center gap-2 border border-dashed rounded-md px-3 py-4 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800">
                  <Upload className="h-4 w-4 text-slate-500" />
                  <span>Desk upload screenshot</span>
                  <input
                    type="file"
                    accept="image/png,image/jpeg,application/pdf"
                    className="hidden"
                    disabled={busy || ticket.status === "converted"}
                    onChange={(e) => handleDeskUpload(e.target.files?.[0] || null)}
                  />
                </label>
                <ul className="space-y-1">
                  {(ticket.proofs || []).map((p) => (
                    <li key={p.id} className="text-xs font-mono flex justify-between gap-2 border-b py-1">
                      <span className="truncate">{p.file_name}</span>
                      <span className="text-slate-400">{p.uploaded_via}</span>
                    </li>
                  ))}
                  {!ticket.proofs?.length && <li className="text-slate-400 text-xs">No proofs yet</li>}
                </ul>
                <Button
                  className="w-full gap-2"
                  disabled={busy || ticket.status === "converted" || !ticket.completeness?.ready_to_convert}
                  onClick={() => handleConvert(false)}
                >
                  <CheckCircle2 className="h-4 w-4" />
                  Create case — Layer-1 ready for hold prep
                </Button>
                {ticket.status === "converted" && ticket.case_id && (
                  <Button variant="outline" className="w-full" onClick={() => navigate(`/cases/${ticket.case_id}`)}>
                    Open case {ticket.case_id.slice(0, 12)}…
                  </Button>
                )}
                <p className="text-[11px] text-slate-400">
                  Does not freeze bank accounts. Prepares case data for nodal hold process.
                </p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Recent tickets</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-500 border-b">
                  <th className="py-2 pr-3">Ticket</th>
                  <th className="py-2 pr-3">Status</th>
                  <th className="py-2 pr-3">ANI</th>
                  <th className="py-2 pr-3">Time-to-case</th>
                  <th className="py-2">Action</th>
                </tr>
              </thead>
              <tbody>
                {recent.map((t) => (
                  <tr key={t.id} className="border-b last:border-0">
                    <td className="py-2 pr-3 font-mono text-xs">{t.ticket_number}</td>
                    <td className="py-2 pr-3 uppercase text-xs">{t.status}</td>
                    <td className="py-2 pr-3 font-mono text-xs">{t.ani_phone}</td>
                    <td className="py-2 pr-3 font-mono text-xs">
                      {t.elapsed_to_case_seconds != null ? formatElapsed(t.elapsed_to_case_seconds) : "—"}
                    </td>
                    <td className="py-2">
                      <Button variant="ghost" size="sm" onClick={() => openRecent(t.id)}>
                        Open
                      </Button>
                      {t.case_id && (
                        <Button variant="ghost" size="sm" onClick={() => navigate(`/cases/${t.case_id}`)}>
                          Case
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
                {!recent.length && (
                  <tr>
                    <td colSpan={5} className="py-4 text-slate-400 text-center text-xs">
                      No tickets yet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
