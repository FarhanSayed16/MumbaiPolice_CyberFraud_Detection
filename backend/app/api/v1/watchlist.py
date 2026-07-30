import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User, RoleEnum
from app.models.watchlist import WatchlistEntry
from app.schemas.watchlist import WatchlistEntryCreate, WatchlistEntryUpdate, WatchlistEntryOut
from app.services.audit_service import log_audit

router = APIRouter()

def check_admin_or_supervisor(current_user: User):
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.SUPERVISOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges"
        )

@router.get("/", response_model=List[WatchlistEntryOut])
async def list_watchlist(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(WatchlistEntry).order_by(WatchlistEntry.created_at.desc())
    res = await db.execute(query)
    entries = res.scalars().all()

    await log_audit(
        db,
        action="VIEW_WATCHLIST",
        resource_type="watchlist",
        user_id=current_user.id,
        user_email=current_user.email,
    )
    return entries

@router.post("/", response_model=WatchlistEntryOut, status_code=status.HTTP_201_CREATED)
async def create_watchlist_entry(
    entry_in: WatchlistEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin_or_supervisor(current_user)

    if not any([entry_in.account_number, entry_in.upi_id, entry_in.phone]):
        raise HTTPException(status_code=400, detail="Must provide account_number, upi_id, or phone")

    entry = WatchlistEntry(
        id=f"wl_{uuid.uuid4().hex[:16]}",
        account_number=entry_in.account_number,
        ifsc_code=entry_in.ifsc_code,
        upi_id=entry_in.upi_id,
        phone=entry_in.phone,
        reason=entry_in.reason,
        risk_score=entry_in.risk_score,
        is_active=entry_in.is_active,
        added_by_user_id=current_user.id
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    await log_audit(
        db,
        action="CREATE_WATCHLIST_ENTRY",
        resource_type="watchlist",
        resource_id=entry.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={"identifier": entry.account_number or entry.upi_id or entry.phone},
    )
    return entry

@router.put("/{entry_id}", response_model=WatchlistEntryOut)
async def update_watchlist_entry(
    entry_id: str,
    entry_in: WatchlistEntryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin_or_supervisor(current_user)

    res = await db.execute(select(WatchlistEntry).where(WatchlistEntry.id == entry_id))
    entry = res.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Watchlist entry not found")

    update_data = entry_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)

    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    await log_audit(
        db,
        action="UPDATE_WATCHLIST_ENTRY",
        resource_type="watchlist",
        resource_id=entry.id,
        user_id=current_user.id,
        user_email=current_user.email,
    )
    return entry

@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft-deactivate watchlist entry (audit H6)."""
    check_admin_or_supervisor(current_user)

    res = await db.execute(select(WatchlistEntry).where(WatchlistEntry.id == entry_id))
    entry = res.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Watchlist entry not found")

    entry.is_active = False
    db.add(entry)
    await db.commit()

    await log_audit(
        db,
        action="DEACTIVATE_WATCHLIST_ENTRY",
        resource_type="watchlist",
        resource_id=entry.id,
        user_id=current_user.id,
        user_email=current_user.email,
    )
