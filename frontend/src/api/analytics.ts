import { api } from './client';

export interface PspHeatRow {
  bank_name?: string;
  ifsc_code?: string;
  psp_name: string;
  total_cases: number;
  total_accounts: number;
  total_amount_at_risk: number;
}

export const analyticsApi = {
  getPspHeatmap: async (): Promise<PspHeatRow[]> => {
    const res = await api.get<PspHeatRow[]>('/analytics/psp-heat');
    return res.data;
  }
};
