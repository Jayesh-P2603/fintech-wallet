from fastapi import FastAPI
from app.routes.account import router as account_router
from app.db.database import Base, engine
from app.models import Account, Transaction

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fintech Ledger Service")

app.include_router(account_router)

@app.get("/")
def root():
    return {"message": "Ledger Service Running"}