from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.Account import MONEY
import enum

class TransactionType(enum.Enum):
    DEBIT = "debit"
    CREDIT = "credit"

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    transfer_id = Column(Integer, ForeignKey("transfers.id"), nullable=True)
    type = Column(SQLEnum(TransactionType), nullable=False)
    amount = Column(MONEY, nullable=False)
    balance_after = Column(MONEY, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    idempotency_key = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("account_id", "idempotency_key", name="uq_account_id_idempotency"),
    )

    transfer = relationship("Transfer")
    account = relationship("Account", back_populates="transactions")