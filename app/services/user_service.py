import time
from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.schemas.users import UserRequest
from app.schemas.auth import UserSignup
from app.models.users import User
from app.services.account_service import AccountService, AccountCreate
from app.core.security import hash_password, verify_password, create_access_token

def create_user(self, req: UserSignup):
    existing = self.db.query(User).filter(
        or_(User.username == req.username, User.email == req.email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")

    try:
        new_user = User(
            username=req.username,
            email=req.email,
            hashed_password=hash_password(req.password),
        )
        self.db.add(new_user)
        self.db.flush()

        self.account_service.create_user_account(
            AccountCreate(user_id=new_user.id, currency="GBP", initial_balance=0)
        )

        self.db.commit()
        self.db.refresh(new_user)
        return new_user
    except SQLAlchemyError:
        self.db.rollback()
        raise HTTPException(status_code=500, detail="User creation failed")

def authenticate(self, username: str, password: str) -> str:
    user = self.db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return create_access_token(subject=str(user.id))