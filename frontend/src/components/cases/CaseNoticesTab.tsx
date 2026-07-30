import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Notice, NoticeTypeEnum, noticeService } from "@/api/notice";
import { CaseDetail } from "@/api/client";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { FileText, Download, PlusCircle, Link as LinkIcon, Edit3, Archive } from "lucide-react";

interface Props {
  caseId: string;
  caseDetail: CaseDetail;
}

export const CaseNoticesTab: React.FC<Props> = ({ caseId, caseDetail }) => {
  const { t } = useTranslation();
  const [notices, setNotices] = useState<Notice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  // Form states
  const [selectedType, setSelectedType] = useState<NoticeTypeEnum>("section_94");
  const [selectedAccount, setSelectedAccount] = useState<string>("");

  const loadNotices = async () => {
    try {
      const data = await noticeService.getNoticesForCase(caseId);
      setNotices(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to load notices.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotices();
  }, [caseId]);

  const handleGenerate = async (supersedesId?: string) => {
    setGenerating(true);
    setError(null);
    try {
      await noticeService.generateNotice({
        case_id: caseId,
        notice_type: selectedType,
        target_account_id: selectedAccount || undefined,
        supersedes_notice_id: supersedesId
      });
      await loadNotices();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to generate notice.");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async (id: string) => {
    try {
      await noticeService.downloadNotice(id);
    } catch (err: any) {
      setError(err?.response?.data?.detail || t("notice.downloadFailed", "Failed to download notice."));
    }
  };

  const handleDownloadPack = async (id: string) => {
    try {
      await noticeService.downloadPack(id);
    } catch (err: any) {
      setError(err?.response?.data?.detail || t("notice.packDownloadFailed", "Failed to download notice pack."));
    }
  };

  if (loading) return <div className="p-4">{t("notice.loading", "Loading notices...")}</div>;

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2">
      {error && <div className="p-4 bg-red-100 text-red-800 rounded">{error}</div>}

      {/* Generation Panel */}
      <Card>
        <CardHeader className="bg-slate-50 dark:bg-slate-950 border-b pb-4">
          <CardTitle className="text-lg flex items-center gap-2">
            <PlusCircle className="h-5 w-5 text-blue-600" />
            {t("notice.generateTitle", "Generate New Legal Notice")}
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4 flex flex-wrap gap-4 items-end">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">{t("notice.typeLabel", "Notice Type")}</label>
            <select
              className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value as NoticeTypeEnum)}
            >
              <option value="section_94">BNSS Section 94 (Document Production)</option>
              <option value="section_168">BNSS Section 168 (Information Request)</option>
              <option value="section_106">BNSS Section 106 (Freeze/Seize)</option>
            </select>
          </div>
          
          <div className="space-y-1 flex-1 min-w-[200px]">
            <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">{t("notice.targetAccount", "Target Account (Optional)")}</label>
            <select
              className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              value={selectedAccount}
              onChange={(e) => setSelectedAccount(e.target.value)}
            >
              <option value="">-- No specific account (Case Level) --</option>
              {caseDetail.linked_accounts.map(acc => (
                <option key={acc.id} value={acc.id}>
                  {acc.bank_name || "Bank"} - {acc.account_number_masked || "Masked"}
                </option>
              ))}
            </select>
          </div>

          <Button onClick={() => handleGenerate()} disabled={generating} className="gap-2">
            <FileText className="h-4 w-4" />
            {generating ? t("notice.generating", "Generating...") : t("notice.generateDraft", "Generate Draft")}
          </Button>
        </CardContent>
      </Card>

      {/* Existing Notices List */}
      <h3 className="text-md font-bold text-slate-700 dark:text-slate-300 px-1">{t("notice.issuedTitle", "Issued Notices")}</h3>
      {notices.length === 0 ? (
        <div className="p-8 text-center text-slate-500 dark:text-slate-400 border-2 border-dashed rounded-lg bg-slate-50 dark:bg-slate-950">
          <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
          {t("notice.empty", "No notices generated for this case yet.")}
        </div>
      ) : (
        <div className="space-y-4">
          {notices.map(notice => (
            <Card key={notice.id} className="overflow-hidden">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 bg-white dark:bg-slate-900 border-b gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 dark:text-slate-100">{notice.notice_number}</span>
                    <Badge variant={notice.status === 'sent' ? 'default' : 'outline'}>
                      {notice.status.toUpperCase()}
                    </Badge>
                    {notice.supersedes_notice_id && (
                      <Badge variant="secondary" className="bg-amber-100 text-amber-800 border-amber-200">
                        <LinkIcon className="h-3 w-3 mr-1" /> Addendum
                      </Badge>
                    )}
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">
                    Type: <span className="font-medium text-slate-700 dark:text-slate-300">{notice.notice_type.toUpperCase().replace('_', ' ')}</span>
                    {notice.recipient_bank_name && ` • Bank: ${notice.recipient_bank_name}`}
                    {notice.template_version && ` • Template v${notice.template_version}`}
                  </div>
                  <div className="text-xs text-slate-400">
                    Generated: {new Date(notice.created_at).toLocaleString()}
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => handleGenerate(notice.id)} title="Generate an Addendum to this notice">
                    <Edit3 className="h-4 w-4 mr-1" /> Addendum
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => handleDownloadPack(notice.id)}>
                    <Archive className="h-4 w-4 mr-1" /> {t("notice.packDownload", "Pack")}
                  </Button>
                  <Button size="sm" onClick={() => handleDownload(notice.id)}>
                    <Download className="h-4 w-4 mr-1" /> PDF
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
