from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.services.current_user import CurrentUserContext, get_current_user
from app.services.wallets import get_wallet_summary

router = APIRouter(prefix="/wallet", tags=["wallet"])
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserDep = Annotated[CurrentUserContext, Depends(get_current_user)]


class WalletTransactionResponse(BaseModel):
    id: UUID
    amount: int
    balance_after: int
    reason: str
    reference_type: str | None
    reference_id: UUID | None
    created_at: datetime


class WalletSummaryResponse(BaseModel):
    balance: int
    recent_transactions: list[WalletTransactionResponse]


@router.get("", response_model=WalletSummaryResponse)
async def get_wallet(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> WalletSummaryResponse:
    summary = await get_wallet_summary(session, user_id=current_user.user.id)
    return WalletSummaryResponse(
        balance=summary.balance,
        recent_transactions=[
            WalletTransactionResponse(
                id=transaction.id,
                amount=transaction.amount,
                balance_after=transaction.balance_after,
                reason=transaction.reason,
                reference_type=transaction.reference_type,
                reference_id=transaction.reference_id,
                created_at=transaction.created_at,
            )
            for transaction in summary.recent_transactions
        ],
    )
