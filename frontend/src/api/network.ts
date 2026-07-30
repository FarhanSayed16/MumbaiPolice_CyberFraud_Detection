import { api } from './client';

export interface NextAccountSuggestion {
  account_id: string;
  label: string;
  outflow_amount: number;
  case_count: number;
  freeze_status: string;
  reason: string;
}

export interface NetworkCluster {
  id: string;
  cluster_name: string;
  risk_score: number;
  total_cases_involved: number;
  total_accounts_involved: number;
  total_amount_involved: number;
  run_id?: string;
  linked_case_ids?: string[];
  linked_account_ids?: string[];
  next_account_id?: string;
  next_account_to_notice?: NextAccountSuggestion;
  graph_summary_json?: any;
  is_active?: boolean;
  created_at: string;
  updated_at: string;
}

export const networkApi = {
  listClusters: async (): Promise<NetworkCluster[]> => {
    const res = await api.get<NetworkCluster[]>('/network/clusters');
    return res.data;
  },

  getCluster: async (id: string): Promise<NetworkCluster> => {
    const res = await api.get<NetworkCluster>(`/network/clusters/${id}`);
    return res.data;
  },

  triggerCompute: async (): Promise<{ status: string; run_id?: string; clusters_created: number }> => {
    const res = await api.post('/network/clusters/compute');
    return res.data;
  },
};
