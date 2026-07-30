# Ingestion adapters package (`Phase 7`)
from app.core.ingestion.base import IngestionAdapter, NormalizedTransactionRow, IngestionResult
from app.core.ingestion.csv_adapter import CsvTransactionAdapter
from app.core.ingestion.excel_adapter import ExcelTransactionAdapter
from app.core.ingestion.engine import IngestionEngine, ingestion_engine

__all__ = [
    "IngestionAdapter",
    "NormalizedTransactionRow",
    "IngestionResult",
    "CsvTransactionAdapter",
    "ExcelTransactionAdapter",
    "IngestionEngine",
    "ingestion_engine",
]
