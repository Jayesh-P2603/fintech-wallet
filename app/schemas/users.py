from pydantic import BaseModel, ConfigDict
from datetime import datetime
from decimal import Decimal
from typing import Optional

class UserRequest(BaseModel):
    username: str
    email: str