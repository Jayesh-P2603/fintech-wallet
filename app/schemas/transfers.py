from pydantic import BaseModel, ConfigDict
from datetime import datetime
from decimal import Decimal

class TransferRequest(BaseModel):
    receiver_account_id: int
    amount: Decimal
    idempotency_key: str

class TransferResponse(BaseModel):
    id: int
    sender_account_id: int
    receiver_account_id: int
    amount: Decimal
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)