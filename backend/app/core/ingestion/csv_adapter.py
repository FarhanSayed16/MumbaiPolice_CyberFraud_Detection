import csv
import io
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.core.ingestion.base import IngestionAdapter, NormalizedTransactionRow

logger = logging.getLogger(__name__)


class CsvTransactionAdapter(IngestionAdapter):
    """
    CSV file reader and normalizer (`Sub-phase 7.1`).
    Supports standard official template CSV headers as well as common bank variations.
    """

    def parse_rows(self, file_content: bytes) -> List[Dict[str, Any]]:
        # Handle UTF-8 with optional BOM or Latin-1 fallback
        try:
            text = file_content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = file_content.decode("latin-1", errors="replace")

        reader = csv.DictReader(io.StringIO(text.strip()))
        rows = []
        for row in reader:
            # Strip whitespace from keys and values
            clean_row = {k.strip().lower(): (v.strip() if isinstance(v, str) else v) for k, v in row.items() if k}
            if any(clean_row.values()):
                rows.append(clean_row)
        return rows

    def _get_val(self, row: Dict[str, Any], keys: List[str]) -> Optional[str]:
        for k in keys:
            val = row.get(k.lower())
            if val is not None and str(val).strip() != "":
                return str(val).strip()
        return None

    def _parse_date(self, val: Optional[str]) -> Optional[datetime]:
        if not val:
            return None
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(val, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        logger.warning(f"Unable to parse transaction date string: '{val}'")
        return None

    def normalize(self, raw_row: Dict[str, Any], row_index: int) -> NormalizedTransactionRow:
        src_acc = self._get_val(raw_row, ["source_account_number", "source account", "source_acc", "from_account", "src_acc", "debit_account"])
        src_ifsc = self._get_val(raw_row, ["source_ifsc", "source ifsc", "src_ifsc", "from_ifsc"])
        src_bank = self._get_val(raw_row, ["source_bank", "source bank", "src_bank", "from_bank"])
        src_holder = self._get_val(raw_row, ["source_holder_name", "source_holder", "src_name"])

        tgt_acc = self._get_val(raw_row, ["target_account_number", "target account", "target_acc", "to_account", "tgt_acc", "credit_account", "beneficiary_account"])
        tgt_ifsc = self._get_val(raw_row, ["target_ifsc", "target ifsc", "tgt_ifsc", "to_ifsc", "beneficiary_ifsc"])
        tgt_bank = self._get_val(raw_row, ["target_bank", "target bank", "tgt_bank", "to_bank", "beneficiary_bank"])
        tgt_holder = self._get_val(raw_row, ["target_holder_name", "target_holder", "tgt_name", "beneficiary_name"])

        utr = self._get_val(raw_row, ["utr_number", "utr", "transaction_id", "txn_id", "reference_number", "ref_no"])
        rrn = self._get_val(raw_row, ["rrn_number", "rrn"])
        
        date_str = self._get_val(raw_row, ["transaction_date", "date", "txn_date", "timestamp", "time"])
        parsed_date = self._parse_date(date_str) if date_str else None

        amt_str = self._get_val(raw_row, ["amount", "txn_amount", "value", "debit_amount", "credit_amount"])
        amt = 0.0
        if amt_str:
            try:
                amt = float(amt_str.replace(",", "").replace("INR", "").replace("₹", "").strip())
            except ValueError:
                amt = 0.0

        txn_type = self._get_val(raw_row, ["transaction_type", "txn_type", "type", "channel"]) or "IMPS"
        
        withdrawal_val = self._get_val(raw_row, ["withdrawal_flag", "is_withdrawal", "cash_out", "atm_withdrawal"])
        withdrawal_flag = False
        if withdrawal_val and withdrawal_val.lower() in ("true", "1", "yes", "atm", "cashout", "y"):
            withdrawal_flag = True

        narration = self._get_val(raw_row, ["narration", "raw_narration", "remarks", "description"])

        layer_str = self._get_val(raw_row, ["layer_number", "layer", "hop"])
        layer = 1
        if layer_str and layer_str.isdigit():
            layer = int(layer_str)

        return NormalizedTransactionRow(
            row_index=row_index,
            source_account_number=src_acc,
            source_ifsc=src_ifsc.upper() if src_ifsc else None,
            source_bank=src_bank,
            source_holder_name=src_holder,
            target_account_number=tgt_acc,
            target_ifsc=tgt_ifsc.upper() if tgt_ifsc else None,
            target_bank=tgt_bank,
            target_holder_name=tgt_holder,
            utr_number=utr,
            rrn_number=rrn,
            transaction_date=parsed_date,
            amount=amt,
            transaction_type=txn_type.upper(),
            withdrawal_flag=withdrawal_flag,
            raw_narration=narration,
            layer_number=layer,
        )
