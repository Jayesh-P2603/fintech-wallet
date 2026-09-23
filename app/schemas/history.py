from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

class HistoryResponse(BaseModel):
    account_id: int
    transaction_id: int
    amount: Decimal
    transaction_type: str
    other_party: int | None = None
    created_at: datetime
    balance_after: Decimal