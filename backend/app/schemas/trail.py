from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TrailRequest(BaseModel):
    start_account_id: Optional[str] = Field(
        None,
        description="Starting account ID for traversal (`Sub-phase 9.1`). If None, defaults to case's layer 1 suspect account."
    )
    max_depth: Optional[int] = Field(
        None,
        ge=1,
        le=15,
        description="Depth cap for traversal hops (`Sub-phase 9.1`). Default is 5, hard max is 15."
    )


class TrailNode(BaseModel):
    id: str
    stable_id: str
    account_number_masked: Optional[str] = None
    ifsc_code_masked: Optional[str] = None
    upi_id_masked: Optional[str] = None
    bank_name: Optional[str] = None
    account_holder: Optional[str] = None
    layer_depth: int = Field(..., description="Hop distance from the starting node (0 for start)")
    freeze_status: str = "unfrozen"
    is_mule: bool = False
    risk_score: float = 0.0
    risk_explanation_json: Optional[Dict[str, Any]] = None
    cash_out_detected: bool = False
    is_dead_end: bool = Field(
        False,
        description="True if node has no outgoing edges and is not pending bank response (`Sub-phase 9.2`)"
    )
    pending_hop: bool = Field(
        False,
        description="True if account is awaiting bank response or freeze requested (`Sub-phase 9.2`)"
    )
    is_cycle_target: bool = Field(
        False,
        description="True if node appeared earlier along the exact traversal path (`Sub-phase 9.2` loop bounded)"
    )
    incoming_total: float = 0.0
    outgoing_total: float = 0.0

    model_config = {"from_attributes": True}


class TrailEdge(BaseModel):
    id: str
    source_id: str
    target_id: str
    utr_number: Optional[str] = None
    rrn_number: Optional[str] = None
    transaction_date: Optional[datetime] = None
    amount: float = 0.0
    transaction_type: Optional[str] = None
    withdrawal_flag: bool = False
    raw_narration: Optional[str] = None
    provenance: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provenance fields (`Sub-phase 9.1`): source_file, reported_at, utr_number, etc."
    )

    model_config = {"from_attributes": True}


class TrailSummary(BaseModel):
    total_nodes: int
    total_edges: int
    max_layer_reached: int
    total_amount_traced: float
    dead_end_count: int
    cycle_count: int
    pending_hop_count: int
    split_transactions_count: int = Field(
        0,
        description="Number of accounts that transferred funds to multiple targets (`Sub-phase 9.1` split transactions)"
    )
    engine_source: str = Field(..., description="'postgres' (authoritative BFS). Neo4j used for sync/probe only until Cypher trail is wired.")
    execution_time_ms: float = 0.0
    neo4j_available: bool = False


class TrailResponse(BaseModel):
    case_id: str
    start_account_id: str
    depth_cap_applied: int
    nodes: List[TrailNode]
    edges: List[TrailEdge]
    summary: TrailSummary


class TrailExplainPlan(BaseModel):
    case_id: str
    engine_source: str
    query: str
    indexes_used: List[str]
    execution_plan: Dict[str, Any]
    sanity_check_passed: bool
