import { api } from "./client";

export interface RiskRuleFired {
  account_id: string;
  account_number?: string;
  rules_fired: string[];
  risk_score: number;
}

export interface CaseRiskRollup {
  case_id: string;
  account_count: number;
  avg_risk_score: number;
  max_risk_score: number;
  top_explanations: RiskRuleFired[];
}

export interface CaseRiskRecomputeResponse {
  case_id: string;
  accounts_scored: number;
  rollup: CaseRiskRollup;
}

export const riskService = {
  getCaseRisk: async (caseId: string): Promise<CaseRiskRollup> => {
    const res = await api.get<CaseRiskRollup>(`/risk/cases/${caseId}`);
    return res.data;
  },
  recomputeCaseRisk: async (caseId: string): Promise<CaseRiskRecomputeResponse> => {
    const res = await api.post<CaseRiskRecomputeResponse>(`/risk/cases/${caseId}/recompute`);
    return res.data;
  },
  getAccountRisk: async (accountId: string) => {
    const res = await api.get(`/risk/accounts/${accountId}`);
    return res.data;
  },
};
