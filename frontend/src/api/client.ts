import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';

// Base API configuration (`Phase 2` & `Phase 4`)
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Required for httpOnly, Secure, SameSite=Strict cookies (`Sub-phase 4.4`)
});

function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp('(?:^|; )' + name.replace(/([.$?*|{}()[\]\\/+^])/g, '\\$1') + '=([^;]*)'));
  return match ? decodeURIComponent(match[1]) : null;
}

/** Attach double-submit CSRF header for cookie sessions (audit H2). */
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const method = (config.method || 'get').toUpperCase();
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    const csrf = getCookie('csrf_token');
    if (csrf) {
      config.headers = config.headers || {};
      config.headers['X-CSRF-Token'] = csrf;
    }
  }
  return config;
});

let refreshPromise: Promise<unknown> | null = null;

async function tryRefreshSession(): Promise<boolean> {
  try {
    if (!refreshPromise) {
      refreshPromise = api.post('/auth/refresh').finally(() => {
        refreshPromise = null;
      });
    }
    await refreshPromise;
    return true;
  } catch {
    return false;
  }
}

// Response interceptor: refresh once on 401, then redirect (audit H1)
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status === 401 && original && !original._retry) {
      const url = original.url || '';
      if (url.includes('/auth/login') || url.includes('/auth/refresh')) {
        return Promise.reject(error);
      }
      original._retry = true;
      const ok = await tryRefreshSession();
      if (ok) {
        return api(original);
      }
      console.warn('[AUTH] Session expired. Redirecting to login.');
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Types
export type RoleType = 'officer' | 'supervisor' | 'admin';

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  role: RoleType;
  badge_number?: string;
  police_station_unit?: string;
  is_active: boolean;
  email_notifications_enabled?: boolean;
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface CreateUserData {
  email: string;
  password: string;
  name: string;
  role: RoleType;
  badge_number?: string;
  police_station_unit?: string;
}

export interface AuditLogItem {
  id: string;
  user_id?: string;
  user_email?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  ip_address?: string;
  details_json?: Record<string, any>;
  timestamp: string;
}

export interface SystemHealth {
  status: string;
  project_name?: string;
  environment?: string;
  timestamp?: string;
  services: {
    postgres: { status: string; latency_ms?: number };
    neo4j: { status: string; latency_ms?: number };
    redis: { status: string; latency_ms?: number };
  };
  observability?: {
    sentry_configured: boolean;
    sentry_active: boolean;
    structured_logging: boolean;
    uptime_probe: string;
    hosted_uptime_monitoring: boolean;
    note: string;
  };
}

export type HealthStatus = SystemHealth;

export interface CaseStub {
  id: string;
  case_number: string;
  fraud_category: string;
  amount_at_risk: number;
  status: string;
  reported_at: string;
}

export interface DuplicateWarning {
  rule: string;
  severity: string;
  message: string;
  matched_case_id?: string;
  matched_case_number?: string;
}

export interface LinkedAccountSummary {
  id: string;
  stable_id: string;
  account_number_masked?: string;
  ifsc_code?: string;
  bank_name?: string;
  upi_id_masked?: string;
  role_in_case: string;
  amount_transferred: number;
  freeze_status: string;
  risk_score: number;
}

export interface CaseItem {
  id: string;
  case_number: string;
  fir_number?: string;
  ncrp_acknowledgement_number?: string;
  fraud_category: string;
  status: string;
  amount_at_risk: number;
  amount_frozen: number;
  amount_recovered: number;
  restoration_status: string;
  closure_reason?: string;
  closure_remarks?: string;
  complainant_name?: string;
  complainant_phone?: string;
  complainant_email?: string;
  complaint_channel?: string;
  police_station?: string;
  district?: string;
  unit?: string;
  narrative_summary?: string;
  initial_txn_ref?: string;
  victim_account_number?: string;
  victim_ifsc?: string;
  victim_bank_label?: string;
  victim_upi_id?: string;
  created_by_user_id?: string;
  assigned_to_user_id?: string;
  reported_at: string;
  sla_due_at?: string;
  suspicion_flags_json?: Record<string, any>;
  duplicate_of_case_id?: string;
  intake_source?: string;
  call_ticket_id?: string;
  created_at: string;
  updated_at: string;
}

export interface CaseDetail extends CaseItem {
  linked_accounts: LinkedAccountSummary[];
  duplicate_warnings: DuplicateWarning[];
  assigned_officer_name?: string;
}

export interface CaseListResponse {
  total: number;
  page: number;
  size: number;
  items: CaseItem[];
}

export interface CreateCasePayload {
  case_number?: string;
  fir_number?: string;
  ncrp_acknowledgement_number?: string;
  fraud_category: string;
  amount_at_risk: number;
  complainant_name?: string;
  complainant_phone?: string;
  complainant_email?: string;
  complaint_channel?: string;
  police_station?: string;
  district?: string;
  unit?: string;
  narrative_summary?: string;
  initial_txn_ref?: string;
  victim_account_number?: string;
  victim_ifsc?: string;
  victim_bank_label?: string;
  victim_upi_id?: string;
  sla_days?: number;
  suspect_account?: {
    account_number?: string;
    ifsc_code?: string;
    bank_name?: string;
    upi_id?: string;
    wallet_id?: string;
    account_holder_name?: string;
    phone?: string;
  };
  acknowledge_duplicate?: boolean;
}

// API Service Functions
export const authService = {
  login: async (credentials: LoginCredentials): Promise<UserProfile> => {
    const res = await api.post<UserProfile>('/auth/login', credentials);
    return res.data;
  },
  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },
  refresh: async (): Promise<UserProfile> => {
    const res = await api.post<UserProfile>('/auth/refresh');
    return res.data;
  },
  getCurrentUser: async (): Promise<UserProfile> => {
    const res = await api.get<UserProfile>('/auth/me');
    return res.data;
  },
  seedInitialUsers: async (): Promise<any> => {
    const res = await api.post('/auth/seed');
    return res.data;
  }
};

export const accountService = {
  reveal: async (accountId: string, reason_for_reveal: string, case_id?: string) => {
    const res = await api.post(`/accounts/${accountId}/reveal`, { reason_for_reveal, case_id });
    return res.data as {
      id: string;
      account_number?: string;
      ifsc_code?: string;
      upi_id?: string;
      bank_name?: string;
      account_holder?: string;
      revealed_by_user: string;
      revealed_at: string;
    };
  },
};

export const userService = {
  listUsers: async (): Promise<UserProfile[]> => {
    const res = await api.get<UserProfile[]>('/users');
    return res.data;
  },
  listAssignable: async (): Promise<UserProfile[]> => {
    const res = await api.get<UserProfile[]>('/users/assignable');
    return res.data;
  },
  createUser: async (data: CreateUserData): Promise<UserProfile> => {
    const res = await api.post<UserProfile>('/users', data);
    return res.data;
  },
  toggleStatus: async (userId: string, isActive: boolean): Promise<UserProfile> => {
    const res = await api.patch<UserProfile>(`/users/${userId}/status`, { is_active: isActive });
    return res.data;
  },
  updatePreferences: async (id: string, email_notifications_enabled: boolean): Promise<UserProfile> => {
    const res = await api.patch<UserProfile>(`/users/${id}/preferences`, { email_notifications_enabled });
    return res.data;
  },
};

export const auditService = {
  queryLogs: async (params?: { user_email?: string; action?: string; resource_type?: string; limit?: number }): Promise<AuditLogItem[]> => {
    const res = await api.get<AuditLogItem[]>('/audit', { params });
    return res.data;
  }
};

export const healthService = {
  getHealth: async (): Promise<SystemHealth> => {
    const res = await api.get<SystemHealth>('/health');
    return res.data;
  },
};

export const caseService = {
  listCases: async (params?: {
    page?: number;
    size?: number;
    search?: string;
    fraud_category?: string;
    status?: string;
    sort_by?: 'risk' | 'created_at' | 'amount';
    min_risk?: number;
  }): Promise<CaseListResponse> => {
    const res = await api.get<CaseListResponse>('/cases', { params });
    return res.data;
  },
  getCaseDetail: async (caseId: string): Promise<CaseDetail> => {
    const res = await api.get<CaseDetail>(`/cases/${caseId}`);
    return res.data;
  },
  checkDuplicate: async (payload: CreateCasePayload): Promise<DuplicateWarning[]> => {
    const res = await api.post<DuplicateWarning[]>('/cases/check-duplicate', payload);
    return res.data;
  },
  createCase: async (payload: CreateCasePayload): Promise<CaseItem> => {
    const res = await api.post<CaseItem>('/cases', payload);
    return res.data;
  },
  acknowledgeDuplicate: async (caseId: string): Promise<CaseItem> => {
    const res = await api.post<CaseItem>(`/cases/${caseId}/acknowledge-duplicate`);
    return res.data;
  },
  dismissDuplicate: async (caseId: string): Promise<CaseItem> => {
    const res = await api.post<CaseItem>(`/cases/${caseId}/dismiss-duplicate`);
    return res.data;
  },
  updateCase: async (caseId: string, payload: Partial<CaseItem>): Promise<CaseItem> => {
    const res = await api.patch<CaseItem>(`/cases/${caseId}`, payload);
    return res.data;
  },
  getRelatedCases: async (caseId: string): Promise<any[]> => {
    const res = await api.get<any[]>(`/cases/${caseId}/related`);
    return res.data;
  },
  searchCases: async (query: string): Promise<CaseListResponse> => {
    const res = await api.get<CaseListResponse>(`/cases/search?q=${encodeURIComponent(query)}`);
    return res.data;
  }
};

export interface TrailNode {
  id: string;
  stable_id: string;
  account_number_masked?: string;
  ifsc_code_masked?: string;
  upi_id_masked?: string;
  bank_name?: string;
  account_holder?: string;
  layer_depth: number;
  freeze_status: string;
  is_mule: boolean;
  risk_score: number;
  risk_explanation_json?: {
    rules_fired: string[];
    base_score: number;
  };
  cash_out_detected: boolean;
  is_dead_end: boolean;
  pending_hop: boolean;
  is_cycle_target: boolean;
  incoming_total: number;
  outgoing_total: number;
}

export interface TrailEdge {
  id: string;
  source_id: string;
  target_id: string;
  utr_number?: string;
  rrn_number?: string;
  transaction_date?: string;
  amount: number;
  transaction_type?: string;
  withdrawal_flag: boolean;
  raw_narration?: string;
  provenance: Record<string, any>;
}

export interface TrailSummary {
  total_nodes: number;
  total_edges: number;
  max_layer_reached: number;
  total_amount_traced: number;
  dead_end_count: number;
  cycle_count: number;
  pending_hop_count: number;
  split_transactions_count: number;
  engine_source: string;
  execution_time_ms: number;
}

export interface TrailResponse {
  case_id: string;
  start_account_id: string;
  depth_cap_applied: number;
  nodes: TrailNode[];
  edges: TrailEdge[];
  summary: TrailSummary;
}

export interface TrailExplainPlan {
  case_id: string;
  engine_source: string;
  query: string;
  indexes_used: string[];
  execution_plan: Record<string, any>;
  sanity_check_passed: boolean;
}

export const trailService = {
  traverse: async (caseId: string, params?: { start_account_id?: string; max_depth?: number }): Promise<TrailResponse> => {
    const res = await api.get<TrailResponse>(`/trail/cases/${caseId}/traverse`, { params });
    return res.data;
  },
  explain: async (caseId: string, start_account_id?: string): Promise<TrailExplainPlan> => {
    const res = await api.get<TrailExplainPlan>(`/trail/cases/${caseId}/explain`, {
      params: start_account_id ? { start_account_id } : undefined,
    });
    return res.data;
  },
};

export interface EvidenceItem {
  id: string;
  case_id: string;
  file_name: string;
  file_size_bytes: number;
  mime_type?: string;
  sha256_hash: string;
  uploaded_by_user_id?: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export const evidenceService = {
  upload: async (
    caseId: string,
    file: File,
    options?: { description?: string; notice_id?: string; transaction_id?: string }
  ): Promise<EvidenceItem> => {
    const formData = new FormData();
    formData.append('file', file);
    if (options?.description) {
      formData.append('description', options.description);
    }
    if (options?.notice_id?.trim()) {
      formData.append('notice_id', options.notice_id.trim());
    }
    if (options?.transaction_id?.trim()) {
      formData.append('transaction_id', options.transaction_id.trim());
    }
    const res = await api.post<EvidenceItem>(`/cases/${caseId}/evidence`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  list: async (caseId: string): Promise<EvidenceItem[]> => {
    const res = await api.get<EvidenceItem[]>(`/cases/${caseId}/evidence`);
    return res.data;
  },
  delete: async (evidenceId: string): Promise<void> => {
    await api.delete(`/evidence/${evidenceId}`);
  },
  getDownloadUrl: (evidenceId: string): string => {
    const baseURL = api.defaults.baseURL || '';
    return `${baseURL}/evidence/${evidenceId}/download`;
  },
  downloadEvidence: async (evidenceId: string): Promise<void> => {
    const response = await api.get(`/evidence/${evidenceId}/download`, {
      responseType: 'blob',
    });
    const disposition = response.headers['content-disposition'] as string | undefined;
    let filename = `evidence-${evidenceId}`;
    if (disposition) {
      const match = disposition.match(/filename="?([^";\n]+)"?/);
      if (match?.[1]) filename = match[1];
    }
    const blob = new Blob([response.data]);
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(url);
  },
};

export interface TimelineEventItem {
  id: string;
  case_id: string;
  event_type: string;
  description: string;
  created_by_user_id?: string;
  metadata_json?: Record<string, any>;
  created_at: string;
}

export const timelineService = {
  list: async (caseId: string, order: 'asc' | 'desc' = 'desc'): Promise<TimelineEventItem[]> => {
    const res = await api.get<TimelineEventItem[]>(`/cases/${caseId}/timeline`, {
      params: { order },
    });
    return res.data;
  },
  addNote: async (caseId: string, description: string): Promise<TimelineEventItem> => {
    const res = await api.post<TimelineEventItem>(`/cases/${caseId}/timeline/notes`, { description });
    return res.data;
  }
};


// Backwards compatibility & helper wrappers
export const fetchSystemHealth = healthService.getHealth;
export const fetchCasesStub = async (): Promise<CaseItem[] | CaseStub[]> => {
  try {
    const data = await caseService.listCases();
    return data.items || [];
  } catch {
    return [];
  }
};

export interface IngestionUploadSummary {
  total_records: number;
  processed_records: number;
  rejected_records: number;
  duplicates_skipped: number;
  new_accounts_created: number;
  new_transactions_created: number;
}

export interface IngestionUploadResponse {
  job_id: string;
  file_name: string;
  content_hash: string;
  status: string;
  message: string;
  summary?: IngestionUploadSummary | null;
}

export interface ImportJobItem {
  id: string;
  case_id?: string;
  file_name: string;
  status: string;
  total_records: number;
  processed_records: number;
  rejected_records: number;
  content_hash?: string;
  error_summary?: string;
  graph_sync_status?: string;
  created_at: string;
  updated_at: string;
}

export interface IngestionErrorRow {
  row: number;
  error: string;
  raw: Record<string, any>;
}

export interface IngestionErrorReport {
  job_id: string;
  file_name: string;
  total_records: number;
  rejected_records: number;
  errors: IngestionErrorRow[];
}

export const ingestionService = {
  uploadFile: async (file: File, caseId?: string): Promise<IngestionUploadResponse> => {
    if (!caseId) {
      throw new Error("case_id is required for bulk transaction ingestion.");
    }
    const formData = new FormData();
    formData.append("file", file);
    formData.append("case_id", caseId);
    const res = await api.post<IngestionUploadResponse>("/ingestion/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return res.data;
  },
  getJobStatus: async (jobId: string): Promise<ImportJobItem> => {
    const res = await api.get<ImportJobItem>(`/ingestion/jobs/${jobId}`);
    return res.data;
  },
  listJobs: async (caseId?: string): Promise<ImportJobItem[]> => {
    const res = await api.get<ImportJobItem[]>("/ingestion/jobs", {
      params: caseId ? { case_id: caseId } : undefined,
    });
    return res.data;
  },
  getJobErrors: async (jobId: string): Promise<IngestionErrorReport> => {
    const res = await api.get<IngestionErrorReport>(`/ingestion/jobs/${jobId}/errors`);
    return res.data;
  },
  downloadTemplate: async (format: "csv" | "xlsx"): Promise<void> => {
    const path = format === "csv" ? "/ingestion/template/csv" : "/ingestion/template/xlsx";
    const res = await api.get(path, { responseType: "blob" });
    const blob = new Blob([res.data]);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = format === "csv"
      ? "mumbai_police_ingestion_template.csv"
      : "mumbai_police_ingestion_template.xlsx";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },
  getTemplateCsvUrl: (): string => {
    const base = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
    return `${base}/ingestion/template/csv`;
  },
  getTemplateXlsxUrl: (): string => {
    const base = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
    return `${base}/ingestion/template/xlsx`;
  },
};

export interface NotificationItem {
  id: string;
  user_id: string;
  case_id?: string;
  notice_id?: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export const notificationService = {
  getNotifications: async (): Promise<NotificationItem[]> => {
    const res = await api.get<NotificationItem[]>('/notifications');
    return res.data;
  },
  markAsRead: async (id: string): Promise<NotificationItem> => {
    const res = await api.post<NotificationItem>(`/notifications/${id}/read`);
    return res.data;
  },
};

export interface DashboardCaseItem {
  id: string;
  case_number: string;
  fraud_category: string;
  amount_at_risk: number;
  status: string;
  sla_due_at: string | null;
  is_breached: boolean;
}

export interface OfficerDashboardResponse {
  assigned_open_cases: number;
  sla_breached_cases_count: number;
  total_amount_at_risk: number;
  awaiting_bank_count?: number;
  notice_sent_count?: number;
  recent_cases: DashboardCaseItem[];
  breached_cases: DashboardCaseItem[];
}

export interface DashboardNetworkSummary {
  total_clusters: number;
  high_risk_clusters: number;
}

export interface DashboardWorkload {
  officer_name: string;
  active_cases: number;
}

export interface SupervisorDashboardResponse {
  total_open_cases: number;
  total_amount_at_risk: number;
  total_amount_recovered: number;
  sla_breached_cases_count: number;
  breached_cases: DashboardCaseItem[];
  network_summary: DashboardNetworkSummary;
  workload: DashboardWorkload[];
}

export const dashboardService = {
  getDashboard: async (): Promise<OfficerDashboardResponse | SupervisorDashboardResponse> => {
    const res = await api.get('/dashboard');
    return res.data;
  }
};

/* —— CD-1 Helpline Intake Console —— */

export interface CallTicketProof {
  id: string;
  ticket_id: string;
  file_name: string;
  file_size_bytes: number;
  mime_type?: string;
  sha256_hash: string;
  description?: string;
  uploaded_via: string;
  created_at: string;
}

export interface CallTicket {
  id: string;
  ticket_number: string;
  status: string;
  ani_phone?: string;
  operator_user_id?: string;
  started_at: string;
  answered_at?: string;
  converted_at?: string;
  elapsed_to_case_seconds?: number;
  fraud_category?: string;
  amount_at_risk?: number;
  complainant_name?: string;
  complainant_phone?: string;
  txn_relative_time?: string;
  layer1_upi?: string;
  layer1_account?: string;
  layer1_ifsc?: string;
  layer1_bank?: string;
  utr?: string;
  narrative_short?: string;
  ncrp_acknowledgement_number?: string;
  case_id?: string;
  proof_token?: string;
  proof_token_expires_at?: string;
  source_channel: string;
  created_at: string;
  updated_at: string;
  proofs: CallTicketProof[];
  proof_portal_path?: string;
  completeness: {
    checks: Record<string, boolean>;
    ready_to_convert: boolean;
    filled: number;
    total: number;
  };
}

export interface CallOrigin {
  ticket_id: string;
  ticket_number: string;
  elapsed_to_case_seconds?: number;
  answered_at?: string;
  converted_at?: string;
  source_channel: string;
  proof_count: number;
}

export const callDeskService = {
  getScriptCard: async () => {
    const res = await api.get<{ banner: string; note: string; card: Record<string, unknown> }>('/call-desk/script-card');
    return res.data;
  },
  listTickets: async (): Promise<CallTicket[]> => {
    const res = await api.get<CallTicket[]>('/call-desk/tickets');
    return res.data;
  },
  simulateInbound: async (): Promise<CallTicket> => {
    const res = await api.post<CallTicket>('/call-desk/tickets/simulate-inbound');
    return res.data;
  },
  answer: async (ticketId: string): Promise<CallTicket> => {
    const res = await api.post<CallTicket>(`/call-desk/tickets/${ticketId}/answer`);
    return res.data;
  },
  getTicket: async (ticketId: string): Promise<CallTicket> => {
    const res = await api.get<CallTicket>(`/call-desk/tickets/${ticketId}`);
    return res.data;
  },
  updateTicket: async (ticketId: string, patch: Partial<CallTicket>): Promise<CallTicket> => {
    const res = await api.patch<CallTicket>(`/call-desk/tickets/${ticketId}`, patch);
    return res.data;
  },
  issueProofLink: async (ticketId: string) => {
    const res = await api.post<{
      ticket_id: string;
      proof_token: string;
      proof_portal_path: string;
      expires_at: string;
      message: string;
    }>(`/call-desk/tickets/${ticketId}/proof-link`);
    return res.data;
  },
  uploadDeskProof: async (ticketId: string, file: File, description?: string): Promise<CallTicketProof> => {
    const fd = new FormData();
    fd.append('file', file);
    if (description) fd.append('description', description);
    const res = await api.post<CallTicketProof>(`/call-desk/tickets/${ticketId}/proofs`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  convertToCase: async (ticketId: string, acknowledgeDuplicate = false) => {
    const res = await api.post<{
      ticket: CallTicket;
      case_id: string;
      case_number: string;
      evidence_ids: string[];
    }>(`/call-desk/tickets/${ticketId}/convert-to-case?acknowledge_duplicate=${acknowledgeDuplicate}`);
    return res.data;
  },
  getCallOrigin: async (caseId: string): Promise<CallOrigin | null> => {
    const res = await api.get<CallOrigin | null>(`/cases/${caseId}/call-origin`);
    return res.data;
  },
};

const publicApiBase =
  import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const publicCallProofService = {
  getMeta: async (token: string) => {
    const res = await axios.get(`${publicApiBase}/public/call-proof/${token}`);
    return res.data as {
      ticket_number: string;
      expires_at?: string;
      demo_banner: string;
      already_converted: boolean;
    };
  },
  upload: async (token: string, file: File, description?: string) => {
    const fd = new FormData();
    fd.append('file', file);
    if (description) fd.append('description', description);
    const res = await axios.post(`${publicApiBase}/public/call-proof/${token}/upload`, fd);
    return res.data as CallTicketProof;
  },
};
