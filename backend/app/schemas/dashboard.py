from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class DashboardCaseItem(BaseModel):
    id: str
    case_number: str
    fraud_category: str
    amount_at_risk: float
    status: str
    sla_due_at: Optional[datetime]
    is_breached: bool

class DashboardNetworkSummary(BaseModel):
    total_clusters: int
    high_risk_clusters: int

class DashboardWorkload(BaseModel):
    officer_name: str
    active_cases: int

class OfficerDashboardResponse(BaseModel):
    assigned_open_cases: int
    sla_breached_cases_count: int
    total_amount_at_risk: float
    awaiting_bank_count: int = 0
    notice_sent_count: int = 0
    recent_cases: List[DashboardCaseItem]
    breached_cases: List[DashboardCaseItem]

class SupervisorDashboardResponse(BaseModel):
    total_open_cases: int
    total_amount_at_risk: float
    total_amount_recovered: float
    sla_breached_cases_count: int
    breached_cases: List[DashboardCaseItem]
    network_summary: DashboardNetworkSummary
    workload: List[DashboardWorkload]
