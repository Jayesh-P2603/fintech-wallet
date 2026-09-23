import time
from fastapi import HTTPException
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from app.schemas.transactions import TransferRequest
from app.models.transactions import Transaction, TransactionType
from app.models.Account import Account
from app.models.transfers import Transfer
from app.schemas.history import HistoryResponse

class TransferService:
    
    def __init__(self, db: Session):
        self.db = db
    
    def execute_transfer(self, sender_id: int, req: TransferRequest):
        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            try:
                if req.amount <= 0:
                    raise HTTPException(status_code=400, detail="Transfer amount must be positive")

                if sender_id == req.receiver_account_id:
                    raise HTTPException(status_code=400, detail="Cannot transfer to same account")

                existing = self.db.query(Transfer).filter(Transfer.idempotency_key == req.idempotency_key).first()

                if existing:
                    return existing
                
                
                sender = self.db.query(Account).filter(Account.id == sender_id).first()
                receiver = self.db.query(Account).filter(Account.id == req.receiver_account_id).first()
                

                if not sender:
                    raise HTTPException(status_code=404, detail="Sender account not found")

                if not receiver:
                    raise HTTPException(status_code=404, detail="Receiver Account not found")
                
                sender_version = sender.version
                receiver_version = receiver.version
                    
                if sender.balance < req.amount:
                    raise HTTPException(status_code=400, detail="Insufficient Balance")
                
                sender_balance = sender.balance - req.amount
                receiver_balance = receiver.balance + req.amount

                sender_affected_rows = self.db.query(Account).filter(Account.id == sender_id, Account.version == sender_version).update({
                    "balance": sender_balance,
                    "version": Account.version +1
                }, synchronize_session='fetch')

                receiver_affected_rows = self.db.query(Account).filter(Account.id == req.receiver_account_id, Account.version == receiver_version).update({
                    "balance": receiver_balance,
                    "version": Account.version +1
                }, synchronize_session='fetch')

                affected_rows = sender_affected_rows + receiver_affected_rows

                if affected_rows < 2:
                    self.db.rollback()
                    self.db.expire_all()
                    retry_count += 1
                    if retry_count >= max_retries:
                        raise HTTPException(status_code=409, detail="Conflict. Funds not transfered")
                    time.sleep(0.01 * retry_count)
                    continue
                
                new_transfer = Transfer(
                    sender_account_id=sender.id,
                    receiver_account_id=receiver.id,
                    amount=req.amount,
                    idempotency_key=req.idempotency_key,
                    status="initiated"
                )

                self.db.add(new_transfer)
                self.db.flush()

                sender_txn = Transaction(
                    transfer_id=new_transfer.id,
                    account_id=sender.id, 
                    type=TransactionType.DEBIT, 
                    amount=req.amount,
                    balance_after=sender_balance,
                    idempotency_key=f"{req.idempotency_key}-out"
                    )

                receiver_txn = Transaction(
                    transfer_id=new_transfer.id,
                    account_id=receiver.id, 
                    type=TransactionType.CREDIT, 
                    amount=req.amount,
                    balance_after=receiver_balance,
                    idempotency_key=f"{req.idempotency_key}-in"
                    )
                
                self.db.add(sender_txn)
                self.db.add(receiver_txn)
                self.db.flush()

                new_transfer.status = "success"

                self.db.commit()
                self.db.refresh(new_transfer)

                return new_transfer
            
            except IntegrityError:
                self.db.rollback()
                existing = self.db.query(Transfer).filter(Transfer.idempotency_key == req.idempotency_key).first()
                if existing:
                    return existing
                raise
        
            except Exception:
                self.db.rollback()
                raise
    
    def get_account_history(self, account_id: int, limit: int = 10, cursor: Optional[int] = None):
        try:
            query = self.db.query(Transaction).options(joinedload(Transaction.transfer)).filter(Transaction.account_id == account_id)

            if cursor:
                query = query.filter(Transaction.id < cursor)
            
            txns = query.order_by(Transaction.id.desc()).limit(limit + 1).all()

            next_cursor = None
            if len(txns)>limit:
                next_cursor = txns[limit-1].id
                txns = txns[:limit]
            
            account_history = []

            for txn in txns:
                other_party = None
                if txn.transfer:
                    if txn.type == TransactionType.DEBIT:
                        other_party = txn.transfer.receiver_account_id
                    else:
                        other_party = txn.transfer.sender_account_id
                    
                event = HistoryResponse(
                    account_id=txn.account_id,
                    transaction_id=txn.id,
                    amount=txn.amount,
                    transaction_type=txn.type.value,
                    other_party=other_party,
                    created_at=txn.created_at,
                    balance_after=txn.balance_after
                )
                account_history.append(event)

            return {"items": account_history, "next_cursor": next_cursor}
        
        except Exception:
            raise