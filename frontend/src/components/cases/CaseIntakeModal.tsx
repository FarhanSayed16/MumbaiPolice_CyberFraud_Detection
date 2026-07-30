import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { caseService, type CreateCasePayload, type DuplicateWarning } from "@/api/client";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { AlertTriangle, X, ShieldAlert, CheckCircle2, Loader2 } from "lucide-react";

interface CaseIntakeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (caseId: string) => void;
}

const DRAFT_KEY = "case_intake_draft_v1";

export const CaseIntakeModal: React.FC<CaseIntakeModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [fraudCategory, setFraudCategory] = useState<string>("digital_arrest");
  const [amountAtRisk, setAmountAtRisk] = useState<string>("");
  const [ncrpNum, setNcrpNum] = useState<string>("");
  const [firNum, setFirNum] = useState<string>("");
  const [compName, setCompName] = useState<string>("");
  const [compPhone, setCompPhone] = useState<string>("");
  const [compEmail, setCompEmail] = useState<string>("");
  const [complaintChannel, setComplaintChannel] = useState<string>("ncrp");
  const [policeStation, setPoliceStation] = useState<string>("");
  const [district, setDistrict] = useState<string>("");
  const [unit, setUnit] = useState<string>("");
  const [narrative, setNarrative] = useState<string>("");
  const [initialTxnRef, setInitialTxnRef] = useState<string>("");
  const [victimAcc, setVictimAcc] = useState<string>("");
  const [victimIfsc, setVictimIfsc] = useState<string>("");
  const [victimBank, setVictimBank] = useState<string>("");
  const [victimUpi, setVictimUpi] = useState<string>("");

  const [accNum, setAccNum] = useState<string>("");
  const [ifsc, setIfsc] = useState<string>("");
  const [bankName, setBankName] = useState<string>("");
  const [upiId, setUpiId] = useState<string>("");
  const [accHolder, setAccHolder] = useState<string>("");
  const [suspectPhone, setSuspectPhone] = useState<string>("");

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [duplicateWarnings, setDuplicateWarnings] = useState<DuplicateWarning[] | null>(null);
  const [acknowledgeDuplicate, setAcknowledgeDuplicate] = useState<boolean>(false);

  if (!isOpen) return null;

  const saveDraft = () => {
    const draft = {
      fraudCategory, amountAtRisk, ncrpNum, firNum, compName, compPhone, compEmail,
      complaintChannel, policeStation, district, unit, narrative, initialTxnRef,
      victimAcc, victimIfsc, victimBank, victimUpi,
      accNum, ifsc, bankName, upiId, accHolder, suspectPhone,
    };
    localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
  };

  const loadDraft = () => {
    try {
      const raw = localStorage.getItem(DRAFT_KEY);
      if (!raw) return;
      const d = JSON.parse(raw);
      setFraudCategory(d.fraudCategory || "digital_arrest");
      setAmountAtRisk(d.amountAtRisk || "");
      setNcrpNum(d.ncrpNum || "");
      setFirNum(d.firNum || "");
      setCompName(d.compName || "");
      setCompPhone(d.compPhone || "");
      setCompEmail(d.compEmail || "");
      setComplaintChannel(d.complaintChannel || "ncrp");
      setPoliceStation(d.policeStation || "");
      setDistrict(d.district || "");
      setUnit(d.unit || "");
      setNarrative(d.narrative || "");
      setInitialTxnRef(d.initialTxnRef || "");
      setVictimAcc(d.victimAcc || "");
      setVictimIfsc(d.victimIfsc || "");
      setVictimBank(d.victimBank || "");
      setVictimUpi(d.victimUpi || "");
      setAccNum(d.accNum || "");
      setIfsc(d.ifsc || "");
      setBankName(d.bankName || "");
      setUpiId(d.upiId || "");
      setAccHolder(d.accHolder || "");
      setSuspectPhone(d.suspectPhone || "");
    } catch {
      /* ignore corrupt draft */
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const amount = parseFloat(amountAtRisk);
    if (!amount || amount <= 0) {
      setError("Amount at risk must be greater than 0.");
      setLoading(false);
      return;
    }

    const payload: CreateCasePayload = {
      fraud_category: fraudCategory,
      amount_at_risk: amount,
      ncrp_acknowledgement_number: ncrpNum.trim() || undefined,
      fir_number: firNum.trim() || undefined,
      complainant_name: compName.trim() || undefined,
      complainant_phone: compPhone.trim() || undefined,
      complainant_email: compEmail.trim() || undefined,
      complaint_channel: complaintChannel || undefined,
      police_station: policeStation.trim() || undefined,
      district: district.trim() || undefined,
      unit: unit.trim() || undefined,
      narrative_summary: narrative.trim() || undefined,
      initial_txn_ref: initialTxnRef.trim() || undefined,
      victim_account_number: victimAcc.trim() || undefined,
      victim_ifsc: victimIfsc.trim() || undefined,
      victim_bank_label: victimBank.trim() || undefined,
      victim_upi_id: victimUpi.trim() || undefined,
      sla_days: 14,
      suspect_account: (accNum.trim() || upiId.trim()) ? {
        account_number: accNum.trim() || undefined,
        ifsc_code: ifsc.trim() || undefined,
        bank_name: bankName.trim() || undefined,
        upi_id: upiId.trim() || undefined,
        account_holder_name: accHolder.trim() || undefined,
        phone: suspectPhone.trim() || undefined,
      } : undefined,
      acknowledge_duplicate: acknowledgeDuplicate,
    };

    try {
      // E1: pre-submit duplicate preview (unless officer already acknowledged)
      if (!acknowledgeDuplicate) {
        const preview = await caseService.checkDuplicate(payload);
        if (preview && preview.length > 0) {
          setDuplicateWarnings(preview);
          setLoading(false);
          return;
        }
      }

      const created = await caseService.createCase(payload);
      localStorage.removeItem(DRAFT_KEY);
      onSuccess(created.id);
      onClose();
      navigate(`/cases/${created.id}`);
    } catch (err: any) {
      if (err.response && err.response.status === 409) {
        const detail = err.response.data?.detail;
        if (detail && detail.requires_acknowledgment) {
          setDuplicateWarnings(detail.warnings || []);
        } else {
          setError(detail?.message || "Potential duplicate conflict detected.");
        }
      } else if (err.response && err.response.data?.detail) {
        const detail = err.response.data.detail;
        setError(typeof detail === "string" ? detail : JSON.stringify(detail));
      } else {
        setError(err.message || "Failed to register case intake.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <Card className="w-full max-w-3xl max-h-[90vh] flex flex-col bg-white dark:bg-slate-900 shadow-2xl rounded-xl overflow-hidden border">
        <CardHeader className="flex flex-row items-center justify-between border-b bg-slate-50 dark:bg-slate-950 px-6 py-4">
          <div>
            <CardTitle className="text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-primary" />
              <span>{t("intake.title")}</span>
            </CardTitle>
            <CardDescription className="text-xs text-slate-500 dark:text-slate-400">
              {t("intake.description")}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button type="button" variant="outline" size="sm" onClick={saveDraft}>{t("intake.saveDraft")}</Button>
            <Button type="button" variant="outline" size="sm" onClick={loadDraft}>{t("intake.loadDraft")}</Button>
            <button onClick={onClose} className="rounded-full p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-600 dark:text-slate-400">
              <X className="h-5 w-5" />
            </button>
          </div>
        </CardHeader>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/40 border border-red-200 rounded-lg text-sm text-red-700 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {duplicateWarnings && duplicateWarnings.length > 0 && (
            <div className="p-4 bg-amber-50 dark:bg-amber-900/40 border-2 border-amber-300 rounded-lg space-y-3">
              <h4 className="font-bold text-amber-900 text-sm">Potential Duplicate / Suspicious Complaint Detected</h4>
              <div className="space-y-2 max-h-32 overflow-y-auto text-xs bg-white dark:bg-slate-900/60 p-2 rounded border border-amber-200">
                {duplicateWarnings.map((w, idx) => (
                  <div key={idx} className="flex items-center justify-between py-1 border-b last:border-b-0">
                    <span className="font-semibold text-slate-800 dark:text-slate-200">[{w.rule}] {w.message}</span>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${w.severity === "HIGH" ? "bg-red-100 text-red-800" : "bg-amber-100 text-amber-800"}`}>
                      {w.severity}
                    </span>
                  </div>
                ))}
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={acknowledgeDuplicate}
                  onChange={(e) => setAcknowledgeDuplicate(e.target.checked)}
                  className="rounded border-amber-400 h-4 w-4"
                />
                <span className="text-xs font-semibold text-amber-950">
                  I acknowledge these duplicate warnings and confirm registration.
                </span>
              </label>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase mb-1">{t("intake.fraudCategory")}</label>
              <select value={fraudCategory} onChange={(e) => setFraudCategory(e.target.value)} className="w-full px-3 py-2 border rounded-md text-sm" required>
                <option value="digital_arrest">Digital Arrest</option>
                <option value="investment_scam">Investment Scam</option>
                <option value="online_trading_scam">Online Trading Scam</option>
                <option value="hacking_digital_fraud">Hacking / Digital Fraud</option>
                <option value="sextortion">Sextortion</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase mb-1">{t("intake.amountAtRisk")}</label>
              <input type="number" min="1" step="any" value={amountAtRisk} onChange={(e) => setAmountAtRisk(e.target.value)} className="w-full px-3 py-2 border rounded-md text-sm" required />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase mb-1">{t("intake.complaintChannel")}</label>
              <select value={complaintChannel} onChange={(e) => setComplaintChannel(e.target.value)} className="w-full px-3 py-2 border rounded-md text-sm">
                <option value="1930">1930 Helpline</option>
                <option value="ncrp">NCRP Portal</option>
                <option value="walk_in">Walk-in / Station</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase mb-1">{t("intake.ncrpAck")}</label>
              <input type="text" value={ncrpNum} onChange={(e) => setNcrpNum(e.target.value)} className="w-full px-3 py-2 border rounded-md text-sm" />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase mb-1">{t("intake.firNumber")}</label>
              <input type="text" value={firNum} onChange={(e) => setFirNum(e.target.value)} className="w-full px-3 py-2 border rounded-md text-sm" />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase mb-1">{t("intake.policeStation")}</label>
              <input type="text" value={policeStation} onChange={(e) => setPoliceStation(e.target.value)} className="w-full px-3 py-2 border rounded-md text-sm" />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase mb-1">{t("intake.district")}</label>
              <input type="text" value={district} onChange={(e) => setDistrict(e.target.value)} className="w-full px-3 py-2 border rounded-md text-sm" />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase mb-1">{t("intake.unit")}</label>
              <input type="text" value={unit} onChange={(e) => setUnit(e.target.value)} className="w-full px-3 py-2 border rounded-md text-sm" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase mb-1">{t("intake.initialTxnRef")}</label>
            <input type="text" value={initialTxnRef} onChange={(e) => setInitialTxnRef(e.target.value)} className="w-full px-3 py-2 border rounded-md text-sm font-mono" />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase mb-1">{t("intake.narrative")}</label>
            <textarea value={narrative} onChange={(e) => setNarrative(e.target.value)} rows={2} className="w-full px-3 py-2 border rounded-md text-sm" />
          </div>

          <div className="border-t pt-4">
            <h4 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3">{t("intake.victimSection")}</h4>
            <div className="grid grid-cols-3 gap-3 mb-3">
              <input type="text" value={compName} onChange={(e) => setCompName(e.target.value)} placeholder="Full name" className="px-3 py-2 border rounded-md text-sm" />
              <input type="text" value={compPhone} onChange={(e) => setCompPhone(e.target.value)} placeholder="Phone" className="px-3 py-2 border rounded-md text-sm" />
              <input type="email" value={compEmail} onChange={(e) => setCompEmail(e.target.value)} placeholder="Email" className="px-3 py-2 border rounded-md text-sm" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <input type="text" value={victimAcc} onChange={(e) => setVictimAcc(e.target.value)} placeholder="Victim account no." className="px-3 py-2 border rounded-md text-sm font-mono" />
              <input type="text" value={victimIfsc} onChange={(e) => setVictimIfsc(e.target.value.toUpperCase())} placeholder="Victim IFSC" className="px-3 py-2 border rounded-md text-sm font-mono uppercase" />
              <input type="text" value={victimBank} onChange={(e) => setVictimBank(e.target.value)} placeholder="Victim bank" className="px-3 py-2 border rounded-md text-sm" />
              <input type="text" value={victimUpi} onChange={(e) => setVictimUpi(e.target.value)} placeholder="Victim UPI" className="px-3 py-2 border rounded-md text-sm" />
            </div>
          </div>

          <div className="border-t pt-4 bg-slate-50 dark:bg-slate-950/60 p-4 rounded-lg border">
            <h4 className="text-xs font-bold text-primary uppercase tracking-wider mb-3">{t("intake.suspectSection")}</h4>
            <div className="grid grid-cols-2 gap-3 mb-3">
              <input type="text" value={accNum} onChange={(e) => setAccNum(e.target.value)} placeholder="Account number" className="px-3 py-2 border rounded-md text-sm font-mono" />
              <input type="text" value={ifsc} onChange={(e) => setIfsc(e.target.value.toUpperCase())} placeholder="IFSC" className="px-3 py-2 border rounded-md text-sm font-mono uppercase" />
              <input type="text" value={bankName} onChange={(e) => setBankName(e.target.value)} placeholder="Bank name" className="px-3 py-2 border rounded-md text-sm" />
              <input type="text" value={upiId} onChange={(e) => setUpiId(e.target.value)} placeholder="UPI ID" className="px-3 py-2 border rounded-md text-sm" />
              <input type="text" value={accHolder} onChange={(e) => setAccHolder(e.target.value)} placeholder="Holder name" className="px-3 py-2 border rounded-md text-sm" />
              <input type="text" value={suspectPhone} onChange={(e) => setSuspectPhone(e.target.value)} placeholder="Suspect phone" className="px-3 py-2 border rounded-md text-sm" />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t">
            <Button type="button" variant="outline" onClick={onClose} disabled={loading}>{t("intake.cancel")}</Button>
            <Button type="submit" disabled={loading || (duplicateWarnings !== null && !acknowledgeDuplicate)} className="gap-2 font-bold">
              {loading ? (<><Loader2 className="h-4 w-4 animate-spin" /><span>{t("intake.registering")}</span></>) : (<><CheckCircle2 className="h-4 w-4" /><span>{duplicateWarnings ? t("intake.confirmOverride") : t("intake.submit")}</span></>)}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
