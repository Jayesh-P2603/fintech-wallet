from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import Optional

class AccountCreate(BaseModel):
    user_id: int
    currency: str
    initial_balance: Decimal
    account_name: Optional[str] = None

class AccountResponse(BaseModel):
    id: int
    user_id: int
    account_name: str
    currency: str
    balance: Decimal
    version: int

    model_config = ConfigDict(from_attributes=True)