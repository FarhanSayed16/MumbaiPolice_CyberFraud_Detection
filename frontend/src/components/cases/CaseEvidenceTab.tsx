import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { evidenceService, EvidenceItem } from '../../api/client';
import { noticeService, Notice } from '../../api/notice';
import { Download, Trash2, File, UploadCloud, Shield, CheckCircle } from 'lucide-react';

interface Props {
  caseId: string;
}

export function CaseEvidenceTab({ caseId }: Props) {
  const { t } = useTranslation();
  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);
  const [notices, setNotices] = useState<Notice[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [fileToUpload, setFileToUpload] = useState<File | null>(null);
  const [description, setDescription] = useState('');
  const [noticeId, setNoticeId] = useState('');
  const [transactionId, setTransactionId] = useState('');

  const loadEvidence = async () => {
    setLoading(true);
    try {
      const data = await evidenceService.list(caseId);
      setEvidenceList(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvidence();
    noticeService.getNoticesForCase(caseId).then(setNotices).catch(() => setNotices([]));
  }, [caseId]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFileToUpload(e.target.files[0]);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fileToUpload) return;
    setUploading(true);
    try {
      await evidenceService.upload(caseId, fileToUpload, {
        description: description || undefined,
        notice_id: noticeId || undefined,
        transaction_id: transactionId || undefined,
      });
      setFileToUpload(null);
      setDescription('');
      setNoticeId('');
      setTransactionId('');
      await loadEvidence();
    } catch (err) {
      console.error(err);
      alert(t('evidence.uploadFailed', 'Upload failed'));
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm(t('evidence.deleteConfirm', 'Are you sure you want to remove this evidence?'))) return;
    try {
      await evidenceService.delete(id);
      await loadEvidence();
    } catch (e) {
      console.error(e);
      alert(t('evidence.deleteFailed', 'Delete failed'));
    }
  };

  const handleDownload = async (id: string) => {
    try {
      await evidenceService.downloadEvidence(id);
    } catch (e) {
      console.error(e);
      alert(t('evidence.downloadFailed', 'Download failed'));
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-slate-900 p-6 rounded-lg shadow-sm border border-slate-200">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4 flex items-center">
          <UploadCloud className="h-5 w-5 mr-2 text-indigo-600" />
          {t('evidence.uploadTitle', 'Upload Evidence')}
        </h3>
        <form onSubmit={handleUpload} className="flex flex-col gap-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('evidence.fileLabel', 'File (PDF, CSV, Image)')}</label>
              <input
                type="file"
                onChange={handleFileChange}
                className="block w-full text-sm text-slate-500 dark:text-slate-400
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-md file:border-0
                  file:text-sm file:font-semibold
                  file:bg-indigo-50 file:text-indigo-700
                  hover:file:bg-indigo-100 border border-slate-300 rounded-md p-1.5"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('evidence.descriptionLabel', 'Description (Optional)')}</label>
              <input
                type="text"
                value={description}
                onChange={e => setDescription(e.target.value)}
                className="block w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:ring-indigo-500 focus:border-indigo-500"
                placeholder={t('evidence.descriptionPlaceholder', 'e.g. Bank statement for HDFC...')}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('evidence.linkNoticeLabel', 'Link to Notice (Optional)')}</label>
              <select
                value={noticeId}
                onChange={(e) => setNoticeId(e.target.value)}
                className="block w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:ring-indigo-500 focus:border-indigo-500"
                aria-label={t('evidence.linkNoticeLabel', 'Link to Notice (Optional)')}
              >
                <option value="">— None —</option>
                {notices.map((n) => (
                  <option key={n.id} value={n.id}>{n.notice_number}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{t('evidence.linkTxnLabel', 'Link to Transaction (Optional)')}</label>
              <input
                type="text"
                value={transactionId}
                onChange={(e) => setTransactionId(e.target.value)}
                className="block w-full border border-slate-300 rounded-md px-3 py-2 text-sm font-mono focus:ring-indigo-500 focus:border-indigo-500"
                placeholder={t('evidence.transactionIdPlaceholder', 'Transaction ID')}
                aria-label={t('evidence.linkTxnLabel', 'Link to Transaction (Optional)')}
              />
            </div>
          </div>
          <div>
            <button
              type="submit"
              disabled={!fileToUpload || uploading}
              className="w-full sm:w-auto bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploading ? t('evidence.uploading', 'Uploading...') : t('evidence.uploadButton', 'Upload')}
            </button>
          </div>
        </form>
      </div>

      <div className="bg-white dark:bg-slate-900 p-6 rounded-lg shadow-sm border border-slate-200">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4 flex items-center">
          <Shield className="h-5 w-5 mr-2 text-green-600" />
          {t('evidence.lockerTitle', 'Evidence Locker (Chain of Custody)')}
        </h3>
        {loading ? (
          <div className="text-sm text-slate-500 dark:text-slate-400">{t('evidence.loading', 'Loading evidence...')}</div>
        ) : evidenceList.length === 0 ? (
          <div className="text-sm text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-950 p-4 rounded-md text-center border border-slate-200 border-dashed">
            {t('evidence.empty', 'No evidence uploaded yet.')}
          </div>
        ) : (
          <div className="overflow-hidden border border-slate-200 rounded-md">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50 dark:bg-slate-950">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">{t('evidence.colFile', 'File')}</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">{t('evidence.colHash', 'Hash (SHA-256)')}</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">{t('evidence.colUploaded', 'Uploaded')}</th>
                  <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">{t('evidence.colActions', 'Actions')}</th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-slate-900 divide-y divide-slate-200">
                {evidenceList.map(ev => (
                  <tr key={ev.id} className="hover:bg-slate-50 dark:bg-slate-950">
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <File className="flex-shrink-0 h-5 w-5 text-slate-400 mr-3" />
                        <div>
                          <div className="text-sm font-medium text-slate-900 dark:text-slate-100">{ev.file_name}</div>
                          <div className="text-xs text-slate-500 dark:text-slate-400">{formatBytes(ev.file_size_bytes)} • {ev.description || t('evidence.noDescription', 'No description')}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center text-xs text-emerald-700 bg-emerald-50 dark:bg-emerald-900/40 px-2 py-1 rounded-md border border-emerald-200 w-max font-mono">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        {ev.sha256_hash.substring(0, 16)}...
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">
                      {new Date(ev.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-3">
                      <button
                        type="button"
                        onClick={() => handleDownload(ev.id)}
                        className="text-indigo-600 hover:text-indigo-900 inline-flex items-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-1 rounded"
                        title={t('evidence.downloadTitle', 'Download (Audited)')}
                      >
                        <Download className="h-4 w-4 mr-1" /> {t('evidence.downloadButton', 'Download')}
                      </button>
                      <button onClick={() => handleDelete(ev.id)} className="text-red-600 hover:text-red-900 inline-flex items-center">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
