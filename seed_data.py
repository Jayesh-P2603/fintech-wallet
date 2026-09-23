import random
import uuid
from decimal import Decimal
from faker import Faker
from app.db.database import SessionLocal
from app.models.users import User
from app.models.Account import Account, AccountSubType, AccountType
from app.models.transactions import Transaction, TransactionType
from sqlalchemy.sql import text

fake = Faker('en_GB')
db = SessionLocal()

def seed_db(num_records=1000):
    print(f"--- Seeding {num_records} Users, Accounts, and Ledger Entries ---")
    
    try:
        db.execute(text("TRUNCATE users, accounts, transactions, transfers RESTART IDENTITY CASCADE;"))
        db.commit()

        # 1. Create Users
        users = [
            User(
                username=fake.user_name() + str(i),
                email=fake.unique.email(),
                kyc_status="verified" if random.random() > 0.2 else "pending"
            ) for i in range(num_records)
        ]
        db.add_all(users)
        db.commit() 

        # 2. Create Accounts and Initial Transactions
        for user in users:
            balance = Decimal(f"{random.uniform(100, 10000):.2f}")

            ACCOUNT_NAMES = {
                AccountSubType.CHECKING: "Everyday Checking",
                AccountSubType.SAVINGS: "High Yield Savings",
                AccountSubType.BUSINESS: "Business Account",
                AccountSubType.JOINT: "Joint Account",
                AccountSubType.CREDIT: "Credit Line",
                AccountSubType.LOAN: "Loan Account",
                AccountSubType.CASH: "Cash Account",
            }

            subtype = random.choice([
                AccountSubType.CHECKING,
                AccountSubType.SAVINGS,
            ])

            currency = random.choice(["GBR", "INR", "USD", "EUR"])
            balance = round(random.uniform(100, 10000), 2)
            
            new_account = Account(
                user_id=user.id,
                account_name=ACCOUNT_NAMES[subtype],
                currency=currency,
                balance=balance,
                type=AccountType.USER,
                subtype=subtype,
            )
            db.add(new_account)
            db.flush() # Get the account.id without committing yet

            # Every real fintech app needs an opening 'CREDIT' entry
            initial_txn = Transaction(
                account_id=new_account.id,
                type=TransactionType.CREDIT, # Use the Enum object here
                amount=balance,
                balance_after=balance, # Audit trail matches account balance
                idempotency_key=str(uuid.uuid4()) # Unique key for the seed record
            )
            db.add(initial_txn)

        db.commit()
        print(f"Successfully seeded {num_records} users, accounts, and matching transactions!")

    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
