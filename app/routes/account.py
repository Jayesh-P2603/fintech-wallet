from fastapi import APIRouter, Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional

from app.schemas.account import AccountCreate, AccountResponse
from app.db.deps import get_db
from app.core.deps import get_current_user
from app.services.user_service import UserService
from app.models.users import User
from app.models.Account import Account
from app.models.transactions import Transaction
from app.schemas.transactions import DepositRequest, TransactionResponse, WithdrawRequest, TransferRequest
from app.models.transfers import Transfer
from app.schemas.transfers import TransferResponse
from app.schemas.transactions import PaginatedTransactions
from app.services.transfer_service import TransferService
from app.services.account_service import AccountService
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.auth import Token

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    token = UserService(db).authenticate(form_data.username, form_data.password)
    return Token(access_token=token)

@router.post("/", response_model=AccountResponse)
def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    new_account = Account(
        user_id=account.user_id,
        balance=account.initial_balance
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return {
        "account_id": new_account.id,
        "user_id": account.user_id,
        "balance": account.initial_balance
    }

@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: int, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return {
        "account_id": account.id,
        "user_id": account.user_id,
        "balance": account.balance
    }

@router.post("/accounts/{account_id}/deposit")
def deposit(
    account_id: int,
    req: DepositRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),   
):
    return AccountService(db).execute_deposit(account_id, req, current_user.id)
    

@router.post("/{account_id}/withdraw", response_model=TransactionResponse)
def withdraw(account_id: int, req: WithdrawRequest, db: Session = Depends(get_db)):
    service = AccountService(db)
    return service.execute_withdraw(account_id, req)
    

@router.post("/{account_id}/transfer", response_model=TransferResponse)
def transfer(account_id: int, req: TransferRequest, db: Session = Depends(get_db)):
    service = TransferService(db)
    return service.execute_transfer(account_id, req)


@router.get("/{account_id}/transfers", response_model=list[TransferResponse])
def get_transfers(
    account_id: int,
    limit: int = 20,
    offset: int = 0,
    direction: Optional[str] = None,
    db: Session = Depends(get_db)
    ):
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    query = db.query(Transfer)

    if direction == 'sent':
        query = query.filter(Transfer.sender_account_id == account_id)
    
    elif direction == 'received':
        query = query.filter(Transfer.receiver_account_id == account_id)
    
    else:
        query = db.query(Transfer).filter(
            (Transfer.sender_account_id == account_id) |
            (Transfer.receiver_account_id == account_id)
        )

    transfers = query.order_by(Transfer.created_at.desc()).offset(offset).limit(limit).all()

    return transfers
    
@router.get("/{account_id}/transfers/{transfer_id}", response_model=TransferResponse)
def fetch_transfer(
    account_id: int,
    transfer_id: int,
    db: Session = Depends(get_db)
):
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()

    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer ID not found")
    
    if account_id != transfer.sender_account_id and account_id != transfer.receiver_account_id:
        raise HTTPException(status_code=403, detail="Not allowed")
    
    direction = "outgoing" if account_id == transfer.sender_account_id else "incoming"

    return {
        "id": transfer.id,
        "sender_account_id": transfer.sender_account_id,
        "receiver_account_id": transfer.receiver_account_id,
        "amount": transfer.amount,
        "status": transfer.status,
        "sender_txn_id": transfer.sender_txn_id,
        "receiver_txn_id": transfer.receiver_txn_id,
        "created_at": transfer.created_at
    }
    
@router.get("/{account_id}/history/", response_model=PaginatedTransactions)
def get_history(
    account_id: int,
    limit: int,
    cursor: Optional[int] = None,
    db: Session = Depends(get_db)
):
    service = TransferService(db)
    return service.get_account_history(account_id, limit, cursor)