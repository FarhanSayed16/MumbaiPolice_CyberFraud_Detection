import { api } from "./client";

export type NoticeTypeEnum = "section_94" | "section_168" | "section_106" | "unfreeze_order" | "clarification";
export type NoticeStatusEnum = "drafted" | "sent" | "acknowledged" | "action_taken" | "rejected" | "clarification_requested";

export interface NoticeTemplate {
  id: string;
  notice_type: NoticeTypeEnum;
  version: number;
  content_template: string;
  is_active: boolean;
  signed_off_by_name?: string;
  signed_off_at?: string;
  created_at: string;
  updated_at: string;
}

export interface NoticeCreate {
  case_id: string;
  target_account_id?: string;
  notice_type: NoticeTypeEnum;
  status?: NoticeStatusEnum;
  recipient_bank_name?: string;
  recipient_nodal_email?: string;
  recipient_bank_ifsc?: string;
  supersedes_notice_id?: string;
}

export interface Notice {
  id: string;
  notice_number: string;
  case_id: string;
  target_account_id?: string;
  notice_type: NoticeTypeEnum;
  status: NoticeStatusEnum;
  recipient_bank_name?: string;
  recipient_nodal_email?: string;
  recipient_bank_ifsc?: string;
  template_version?: number;
  pdf_file_path?: string;
  issued_by_user_id?: string;
  sent_at?: string;
  sla_deadline_at?: string;
  responded_at?: string;
  response_summary?: string;
  supersedes_notice_id?: string;
  created_at: string;
  updated_at: string;
}

export const noticeService = {
  getTemplates: async (): Promise<NoticeTemplate[]> => {
    const response = await api.get("/notices/templates");
    return response.data;
  },

  createTemplate: async (data: Partial<NoticeTemplate>): Promise<NoticeTemplate> => {
    const response = await api.post("/notices/templates", data);
    return response.data;
  },

  signOffTemplate: async (id: string, name: string): Promise<NoticeTemplate> => {
    const response = await api.put(`/notices/templates/${id}/sign-off`, { signed_off_by_name: name });
    return response.data;
  },

  generateNotice: async (data: NoticeCreate): Promise<Notice> => {
    const response = await api.post("/notices/generate", data);
    return response.data;
  },

  getNoticesForCase: async (caseId: string): Promise<Notice[]> => {
    const response = await api.get(`/notices/case/${caseId}`);
    return response.data;
  },

  updateNoticeStatus: async (id: string, status: NoticeStatusEnum, summary?: string): Promise<Notice> => {
    const response = await api.put(`/notices/${id}/status`, { status, response_summary: summary });
    return response.data;
  },

  getDownloadUrl: (noticeId: string): string => {
    return `${api.defaults.baseURL}/notices/${noticeId}/download`;
  },

  downloadNotice: async (noticeId: string): Promise<void> => {
    const response = await api.get(`/notices/${noticeId}/download`, {
      responseType: "blob",
    });
    const disposition = response.headers["content-disposition"] as string | undefined;
    let filename = `notice-${noticeId}.pdf`;
    if (disposition) {
      const match = disposition.match(/filename="?([^";\n]+)"?/);
      if (match?.[1]) filename = match[1];
    }
    const blob = new Blob([response.data], { type: "application/pdf" });
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(url);
  },

  downloadPack: async (noticeId: string): Promise<void> => {
    const response = await api.get(`/notices/${noticeId}/pack`, {
      responseType: "blob",
    });
    const disposition = response.headers["content-disposition"] as string | undefined;
    let filename = `notice-pack-${noticeId}.zip`;
    if (disposition) {
      const match = disposition.match(/filename="?([^";\n]+)"?/);
      if (match?.[1]) filename = match[1];
    }
    const blob = new Blob([response.data], { type: "application/zip" });
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(url);
  },
};
