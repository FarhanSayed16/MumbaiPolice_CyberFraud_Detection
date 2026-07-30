from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, List, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class NormalizedTransactionRow:
    """
    Standardized in-memory representation of a money-trail transaction hop
    normalized across CSV, Excel, or custom bank response formats (`Sub-phase 7.1`).
    """
    row_index: int
    source_account_number: Optional[str] = None
    source_ifsc: Optional[str] = None
    source_bank: Optional[str] = None
    source_holder_name: Optional[str] = None

    target_account_number: Optional[str] = None
    target_ifsc: Optional[str] = None
    target_bank: Optional[str] = None
    target_holder_name: Optional[str] = None

    utr_number: Optional[str] = None
    rrn_number: Optional[str] = None
    transaction_date: Optional[datetime] = None
    amount: float = 0.0
    transaction_type: str = "IMPS"
    withdrawal_flag: bool = False
    raw_narration: Optional[str] = None
    layer_number: int = 1


@dataclass
class IngestionResult:
    """
    Summary result returned after processing an ingestion file or stream (`Sub-phase 7.2`).
    """
    job_id: str
    total_records: int = 0
    processed_records: int = 0
    rejected_records: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)  # [{'row': 2, 'error': 'Invalid amount', 'raw': {...}}]
    new_accounts_created: int = 0
    new_transactions_created: int = 0
    duplicates_skipped: int = 0


class IngestionAdapter(ABC):
    """
    Abstract adapter interface (`Sub-phase 7.1 Checkpoint`).
    All concrete ingestion format readers (CSV, Excel, bank proprietary) must inherit from this class.
    """

    @abstractmethod
    def parse_rows(self, file_content: bytes) -> List[Dict[str, Any]]:
        """
        Parses raw file bytes into a list of raw dictionary rows.
        """
        pass

    @abstractmethod
    def normalize(self, raw_row: Dict[str, Any], row_index: int) -> NormalizedTransactionRow:
        """
        Transforms a raw dictionary row into a clean NormalizedTransactionRow.
        Raises ValueError with descriptive message if structural mapping is impossible.
        """
        pass

    def validate(self, row: NormalizedTransactionRow) -> Tuple[bool, Optional[str]]:
        """
        Validates business and domain constraints on a normalized row (`Sub-phase 7.1`).
        Returns (True, None) if valid, or (False, error_message) if rejected.
        """
        if row.amount <= 0:
            return False, f"Row {row.row_index}: Transaction amount must be greater than 0 (Got {row.amount})"

        if not row.source_account_number and not row.target_account_number:
            return False, f"Row {row.row_index}: At least one account (source or target) must be specified"

        if not row.transaction_date:
            return False, f"Row {row.row_index}: Valid transaction_date timestamp is required"

        return True, None
