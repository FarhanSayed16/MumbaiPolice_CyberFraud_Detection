import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { publicCallProofService } from "@/api/client";
import { Button } from "@/components/ui/Button";
import { Upload, CheckCircle2, AlertTriangle } from "lucide-react";

export const PublicCallProofPage: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const [meta, setMeta] = useState<{
    ticket_number: string;
    demo_banner: string;
    already_converted: boolean;
    expires_at?: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!token) return;
    publicCallProofService
      .getMeta(token)
      .then(setMeta)
      .catch(() => setError("Invalid or expired proof link."));
  }, [token]);

  const onUpload = async (file: File | null) => {
    if (!token || !file) return;
    setBusy(true);
    setError(null);
    try {
      await publicCallProofService.upload(token, file);
      setDone(true);
    } catch {
      setError("Upload failed. Use PNG, JPEG, or PDF under 15 MB.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-lg shadow border p-6 space-y-4">
        <div className="text-xs font-semibold uppercase tracking-wide text-amber-800 bg-amber-50 border border-amber-200 rounded px-2 py-1">
          {meta?.demo_banner || "Training / demo portal — not the national 1930 website."}
        </div>
        <h1 className="text-xl font-bold text-slate-900">Upload payment proof</h1>
        {meta && (
          <p className="text-sm text-slate-600">
            Helpline ticket <span className="font-mono font-semibold">{meta.ticket_number}</span>
            {meta.expires_at && (
              <span className="block text-xs text-slate-400 mt-1">
                Link expires: {new Date(meta.expires_at).toLocaleString("en-IN")}
              </span>
            )}
          </p>
        )}

        {error && (
          <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2 flex gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            {error}
          </div>
        )}

        {done ? (
          <div className="text-sm text-emerald-800 bg-emerald-50 border border-emerald-200 rounded p-3 flex gap-2">
            <CheckCircle2 className="h-5 w-5 shrink-0" />
            Proof received. You may stay on the call; the officer can see the file on their console.
          </div>
        ) : meta?.already_converted ? (
          <p className="text-sm text-slate-600">This ticket is already closed. Contact the helpline if you need to add more documents.</p>
        ) : (
          <label className="flex flex-col items-center gap-2 border-2 border-dashed rounded-lg px-4 py-8 cursor-pointer hover:bg-slate-50">
            <Upload className="h-8 w-8 text-slate-400" />
            <span className="text-sm font-medium text-slate-700">Tap to upload UPI / bank SMS screenshot</span>
            <input
              type="file"
              accept="image/png,image/jpeg,application/pdf"
              className="hidden"
              disabled={busy || !meta}
              onChange={(e) => onUpload(e.target.files?.[0] || null)}
            />
            {busy && <span className="text-xs text-slate-500">Uploading…</span>}
          </label>
        )}

        <Button variant="outline" className="w-full" disabled>
          Stay on the call with the officer
        </Button>
      </div>
    </div>
  );
};
