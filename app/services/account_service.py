import time
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.schemas.transactions import DepositRequest, WithdrawRequest
from app.schemas.account import AccountCreate
from app.models.Account import Account
from app.models.transactions import Transaction, TransactionType

class AccountService:

    def __init__(self, db: Session):
        self.db = db
    
    def create_user_account(self, req: AccountCreate):

        existing = self.db.query(Account).filter(
            Account.user_id == req.user_id,
            Account.currency == req.currency
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail=f"User already has a {req.currency} account")
        
        new_account = Account(
            user_id=req.user_id,
            currency=req.currency,
            balance=req.initial_balance,
            account_name=req.account_name or "Primary Account"
        )

        self.db.add(new_account)
        self.db.flush()
        self.db.refresh(new_account)

        return new_account

    
    def execute_deposit(self, account_id: int, req: DepositRequest, user_id: int):
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not Found")
        if account.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized for this account")

        max_reties = 3
        retry_count = 0
        if req.amount <= 0:
            raise HTTPException(status_code=400, detail=" Deposit amount must be greate than 0.0")

        existing = self.db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.idempotency_key == req.idempotency_key
        ).first()

        if existing:
            return existing

        while retry_count < max_reties:
            try:
                account = self.db.query(Account).filter(Account.id == account_id).first()

                if not account:
                    raise HTTPException(status_code=404, detail="Account not Found")
                
                current_version = account.version
                new_balance = account.balance + req.amount

                affected_rows = self.db.query(Account).filter(Account.id == account_id, Account.version == current_version).update({
                    "balance": new_balance,
                    "version": Account.version +1
                }, synchronize_session='fetch')

                if affected_rows == 0:
                    self.db.rollback()
                    self.db.expire_all()
                    retry_count += 1
                    if retry_count >= max_reties:
                        raise HTTPException(status_code=409, detail="Conflict. Please retry.")
                    time.sleep(0.01 * retry_count)
                    continue
                    
                txn = Transaction(
                    account_id=account.id, 
                    type=TransactionType.CREDIT, 
                    amount=req.amount,
                    balance_after=new_balance,
                    idempotency_key=req.idempotency_key
                )

                self.db.add(txn)
                self.db.commit()
                self.db.refresh(txn)

                return txn
            
            except IntegrityError:
                self.db.rollback()
                return self.db.query(Transaction).filter(Transaction.idempotency_key == req.idempotency_key).first()
            
            except Exception:
                self.db.rollback()
                raise
    

    def execute_withdraw(self, account_id, req: WithdrawRequest):
        max_retries = 3
        retry_count = 0
        if req.amount <= 0:
            raise HTTPException(status_code=400, detail="Withdraw amount must be positive")

        existing_txn = (
                self.db.query(Transaction).filter(
                    Transaction.account_id == account_id,
                    Transaction.idempotency_key == req.idempotency_key
                ).first()
            )

        if existing_txn:
            return existing_txn

        while retry_count < max_retries:
            try:
                account = self.db.query(Account).filter(Account.id == account_id).first()
                if not account:
                    raise HTTPException(status_code=404, detail="Account not found")
                
                
                if req.amount > account.balance:
                    raise HTTPException(status_code=400, detail="Insufficient Balance")
                
                current_version = account.version
                new_balance = account.balance - req.amount

                affected_rows=self.db.query(Account).filter(Account.id == account_id, Account.version == current_version).update({
                    "balance": new_balance,
                    "version": Account.version +1
                }, synchronize_session='fetch')

                if affected_rows == 0:
                    retry_count += 1
                    if retry_count >= max_retries:
                        raise HTTPException(status_code=409, detail="Conflict. Please try again")
                    time.sleep(0.01*retry_count)
                    continue

                txn = Transaction(
                    account_id=account.id, 
                    type=TransactionType.DEBIT, 
                    amount=req.amount,
                    balance_after=new_balance,
                    idempotency_key=req.idempotency_key
                )

                self.db.add(txn)
                self.db.commit()
                self.db.refresh(txn)

                return txn
            
            except IntegrityError:
                self.db.rollback()
                return self.db.query(Transaction).filter(Transaction.idempotency_key == req.idempotency_key).first()
            
            except Exception:
                self.db.rollback()
                raise