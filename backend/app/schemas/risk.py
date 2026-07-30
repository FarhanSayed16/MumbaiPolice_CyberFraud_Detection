from typing import Any, Optional
from pydantic import BaseModel, ConfigDict


class RiskRuleFired(BaseModel):
    account_id: str
    account_number: Optional[str] = None
    rules_fired: list[str] = []
    risk_score: float = 0.0


class AccountRiskResponse(BaseModel):
    account_id: str
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    upi_id: Optional[str] = None
    risk_score: float
    risk_explanation_json: Optional[dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class CaseRiskRollup(BaseModel):
    case_id: str
    account_count: int
    avg_risk_score: float
    max_risk_score: float
    top_explanations: list[RiskRuleFired]


class CaseRiskRecomputeResponse(BaseModel):
    case_id: str
    accounts_scored: int
    rollup: CaseRiskRollup
