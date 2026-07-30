from datetime import datetime
from typing import Optional, Any, List
from sqlalchemy import String, Float, Integer, DateTime, JSON, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class NetworkCluster(Base):
    """
    Multi-case organized syndicate or mule ring cluster discovered by graph heuristics.
    Versioned by run_id; stale runs are soft-deactivated (audit H8).
    """
    __tablename__ = "network_clusters"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    cluster_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, index=True, nullable=False)

    total_cases_involved: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_accounts_involved: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_amount_involved: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    linked_case_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    linked_account_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    next_account_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    graph_summary_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
