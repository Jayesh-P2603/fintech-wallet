from pydantic import BaseModel, ConfigDict
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from app.schemas.history import HistoryResponse

class DepositRequest(BaseModel):
    amount: Decimal
    idempotency_key: str

class WithdrawRequest(BaseModel):
    amount: Decimal
    idempotency_key: str

class TransactionResponse(BaseModel):
    id: int
    account_id: int
    type: str
    amount: Decimal
    created_at: datetime
    balance_after: Decimal

    model_config = ConfigDict(from_attributes=True)

class TransferRequest(BaseModel):
    receiver_account_id: int
    amount: Decimal
    idempotency_key: str

class PaginatedTransactions(BaseModel):
    items: List[HistoryResponse]
    next_cursor: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)