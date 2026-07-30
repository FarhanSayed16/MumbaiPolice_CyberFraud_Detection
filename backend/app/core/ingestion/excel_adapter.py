import io
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import openpyxl
from app.core.ingestion.base import NormalizedTransactionRow
from app.core.ingestion.csv_adapter import CsvTransactionAdapter

logger = logging.getLogger(__name__)


class ExcelTransactionAdapter(CsvTransactionAdapter):
    """
    Excel (.xlsx) file reader (`Sub-phase 7.1`).
    Reads worksheet rows via openpyxl and delegates normalization to CsvTransactionAdapter.
    """

    def parse_rows(self, file_content: bytes) -> List[Dict[str, Any]]:
        wb = openpyxl.load_workbook(io.BytesIO(file_content), read_only=True, data_only=True)
        sheet = wb.active
        if sheet is None:
            wb.close()
            return []

        rows_iter = sheet.iter_rows(values_only=True)
        try:
            headers = next(rows_iter)
        except StopIteration:
            wb.close()
            return []

        if not headers:
            wb.close()
            return []

        clean_headers = [str(h).strip().lower() if h is not None else "" for h in headers]
        rows = []
        for row_tuple in rows_iter:
            if not any(row_tuple):
                continue
            row_dict = {}
            for idx, cell_val in enumerate(row_tuple):
                if idx < len(clean_headers) and clean_headers[idx]:
                    if isinstance(cell_val, datetime):
                        # Format datetime cleanly
                        if cell_val.tzinfo is None:
                            cell_val = cell_val.replace(tzinfo=timezone.utc)
                        row_dict[clean_headers[idx]] = cell_val.isoformat()
                    elif cell_val is not None:
                        row_dict[clean_headers[idx]] = str(cell_val).strip()
                    else:
                        row_dict[clean_headers[idx]] = ""
            if any(row_dict.values()):
                rows.append(row_dict)

        wb.close()
        return rows
