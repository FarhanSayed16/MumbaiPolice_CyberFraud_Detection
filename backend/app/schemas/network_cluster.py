from datetime import datetime
from typing import Optional, Any, List
from pydantic import BaseModel, Field, ConfigDict


class NextAccountSuggestion(BaseModel):
    account_id: str
    label: str
    outflow_amount: float
    case_count: int
    freeze_status: str
    reason: str


class NetworkClusterBase(BaseModel):
    cluster_name: str
    risk_score: float = 0.0
    total_cases_involved: int = 1
    total_accounts_involved: int = 1
    total_amount_involved: float = 0.0


class NetworkClusterCreate(NetworkClusterBase):
    graph_summary_json: Optional[dict[str, Any]] = None


class NetworkClusterResponse(NetworkClusterBase):
    id: str
    run_id: Optional[str] = None
    linked_case_ids: Optional[List[str]] = None
    linked_account_ids: Optional[List[str]] = None
    next_account_id: Optional[str] = None
    next_account_to_notice: Optional[NextAccountSuggestion] = None
    graph_summary_json: Optional[dict[str, Any]] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_cluster(cls, cluster) -> "NetworkClusterResponse":
        data = cls.model_validate(cluster)
        meta = (cluster.graph_summary_json or {}).get("next_account_to_notice")
        if meta:
            data.next_account_to_notice = NextAccountSuggestion(**meta)
        return data
