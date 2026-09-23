from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum


MONEY = Numeric(precision=12, scale=2)

class CurrencyType(enum.Enum):
    GBP = "GBP"
    USD = "USD"
    INR = "INR"
    EUR = "EUR"

class AccountType(enum.Enum):
    USER = "user"
    SYSTEM = "system"


# High-level ownership of the account.
# USER accounts belong to customers.
# SYSTEM accounts are owned by the platform for internal ledger operations.

class AccountSubType(enum.Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    BUSINESS = "business"
    JOINT = "joint"
    CREDIT = "credit"
    LOAN = "loan"
    CASH = "cash"

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id") ,nullable=False, index=True)
    account_name = Column(String, default="Primary Account")
    currency = Column(String(3), default="GBP", nullable=False)
    balance = Column(MONEY,default=0.0)

    version = Column(Integer, default=1, nullable=False)

    type = Column(SQLEnum(AccountType), default=AccountType.USER, nullable=False)
    subtype = Column(SQLEnum(AccountSubType), default=AccountSubType.CHECKING, nullable=False)

    transactions = relationship("Transaction", back_populates="account")
    owner = relationship("User", back_populates="accounts")

"""
TODO: 
1. Add index to account_id and created_at columns in transactions table to keep get_account_history
as it grows to thousands of records.
2. Add user_name, account_name columns to account model.
3. create users table with id, email, hashed_password columns.
4. Add user_id as foreign key to accounts table.
5. Use asyncio script or locust to test optimistic concurrency logic.
6. Authentication - JWT and validations.
"""