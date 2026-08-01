from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from app.models.enums import CaseStatusEnum, FraudCategoryEnum


class SuspectAccountInput(BaseModel):
    """
    Initial suspect / layer-1 account encountered in complaint intake.
    """
    account_number: Optional[str] = Field(None, description="Bank account number")
    ifsc_code: Optional[str] = Field(None, description="IFSC code (e.g. SBIN0001234)")
    bank_name: Optional[str] = Field(None, description="Name of bank")
    upi_id: Optional[str] = Field(None, description="UPI ID (e.g. suspect@okaxis)")
    wallet_id: Optional[str] = Field(None, description="Digital wallet ID or phone")
    account_holder_name: Optional[str] = Field(None, description="Account holder name if known")
    phone: Optional[str] = Field(None, description="Suspect / fraudster phone if known")

    @model_validator(mode="after")
    def check_at_least_one_identifier(self) -> "SuspectAccountInput":
        if not any([self.account_number, self.upi_id, self.wallet_id]):
            raise ValueError("At least one suspect identifier (account_number, upi_id, or wallet_id) must be provided.")
        return self


class CaseCreate(BaseModel):
    """
    Schema for creating a new investigation case (`Sub-phase 6.1` + discovery §3.4).
    """
    case_number: Optional[str] = Field(None, description="Custom or generated case number (e.g. MH-CYBER-2026-0001)")
    fir_number: Optional[str] = Field(None, description="Police FIR number if registered")
    ncrp_acknowledgement_number: Optional[str] = Field(None, description="NCRP 1930 Acknowledgement Number")
    fraud_category: FraudCategoryEnum = Field(..., description="Category of fraud")
    amount_at_risk: float = Field(..., gt=0, description="Total amount reported defrauded / at risk in INR (must be > 0)")

    complainant_name: Optional[str] = Field(None, description="Full name of complainant/victim")
    complainant_phone: Optional[str] = Field(None, description="Contact phone of complainant")
    complainant_email: Optional[str] = Field(None, description="Contact email of complainant")

    complaint_channel: Optional[str] = Field(None, description="1930 | ncrp | walk_in | other")
    police_station: Optional[str] = None
    district: Optional[str] = None
    unit: Optional[str] = None
    narrative_summary: Optional[str] = None
    initial_txn_ref: Optional[str] = Field(None, description="Initial UTR / RRN if known")
    victim_account_number: Optional[str] = None
    victim_ifsc: Optional[str] = None
    victim_bank_label: Optional[str] = None
    victim_upi_id: Optional[str] = None

    reported_at: Optional[datetime] = Field(None, description="Timestamp when complaint was lodged")
    sla_days: int = Field(14, description="SLA target days for initial action/notice")

    suspect_account: Optional[SuspectAccountInput] = Field(None, description="Initial layer-1 suspect account")
    acknowledge_duplicate: bool = Field(False, description="Officer checks to override potential duplicate warnings")

    @field_validator("amount_at_risk")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("amount_at_risk must be greater than 0.")
        return v


class CaseUpdate(BaseModel):
    """
    Schema for updating an existing case status, assignment, or flags.
    """
    fir_number: Optional[str] = None
    ncrp_acknowledgement_number: Optional[str] = None
    fraud_category: Optional[FraudCategoryEnum] = None
    status: Optional[CaseStatusEnum] = None
    amount_at_risk: Optional[float] = None
    amount_frozen: Optional[float] = None
    complainant_name: Optional[str] = None
    complainant_phone: Optional[str] = None
    complainant_email: Optional[str] = None
    complaint_channel: Optional[str] = None
    police_station: Optional[str] = None
    district: Optional[str] = None
    unit: Optional[str] = None
    narrative_summary: Optional[str] = None
    initial_txn_ref: Optional[str] = None
    assigned_to_user_id: Optional[str] = None
    duplicate_of_case_id: Optional[str] = None
    closure_reason: Optional[str] = None
    closure_remarks: Optional[str] = None
    amount_recovered: Optional[float] = Field(None, ge=0, description="Supervisor-only: recovered amount in INR")
    restoration_status: Optional[str] = Field(
        None,
        description="Supervisor-only: pending | partial | complete | failed",
    )


class DuplicateWarning(BaseModel):
    rule: str
    severity: str  # HIGH, MEDIUM
    message: str
    matched_case_id: Optional[str] = None
    matched_case_number: Optional[str] = None


class LinkedAccountSummary(BaseModel):
    id: str
    stable_id: str
    account_number_masked: Optional[str] = None
    ifsc_code: Optional[str] = None
    bank_name: Optional[str] = None
    upi_id_masked: Optional[str] = None
    role_in_case: str
    amount_transferred: float
    freeze_status: str
    risk_score: float = 0.0


class CaseResponse(BaseModel):
    id: str
    case_number: str
    fir_number: Optional[str] = None
    ncrp_acknowledgement_number: Optional[str] = None
    fraud_category: FraudCategoryEnum
    status: CaseStatusEnum
    amount_at_risk: float
    amount_frozen: float
    amount_recovered: float = 0.0
    restoration_status: str = "pending"
    complainant_name: Optional[str] = None
    complainant_phone: Optional[str] = None
    complainant_email: Optional[str] = None
    complaint_channel: Optional[str] = None
    police_station: Optional[str] = None
    district: Optional[str] = None
    unit: Optional[str] = None
    narrative_summary: Optional[str] = None
    initial_txn_ref: Optional[str] = None
    victim_account_number: Optional[str] = None
    victim_ifsc: Optional[str] = None
    victim_bank_label: Optional[str] = None
    victim_upi_id: Optional[str] = None
    created_by_user_id: Optional[str] = None
    assigned_to_user_id: Optional[str] = None
    reported_at: datetime
    sla_due_at: Optional[datetime] = None
    suspicion_flags_json: Optional[dict[str, Any]] = None
    duplicate_of_case_id: Optional[str] = None
    closure_reason: Optional[str] = None
    closure_remarks: Optional[str] = None
    intake_source: Optional[str] = None
    call_ticket_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseDetailResponse(CaseResponse):
    linked_accounts: list[LinkedAccountSummary] = []
    duplicate_warnings: list[DuplicateWarning] = []
    assigned_officer_name: Optional[str] = None


class CaseListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[CaseResponse]
