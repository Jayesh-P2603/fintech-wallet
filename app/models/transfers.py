from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.Account import MONEY

class Transfer(Base):
    __tablename__ = "transfers"
    id = Column(Integer, primary_key=True, index=True)
    sender_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    receiver_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount = Column(MONEY, nullable=False)
    idempotency_key = Column(String, unique=True, nullable=False)
    status = Column(String, default="success", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sender = relationship("Account", foreign_keys=[sender_account_id])
    receiver = relationship("Account", foreign_keys=[receiver_account_id])