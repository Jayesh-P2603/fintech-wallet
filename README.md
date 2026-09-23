# Fintech Wallet Backend

A backend service for a digital wallet system, built with a focus on financial data integrity, safe concurrent access, and auditability — the same core concerns you'd find in a real payments or ledger system.

Built with **Python**, **FastAPI**, and **SQLAlchemy**.

## What it does

- User signup and login with JWT-based authentication
- Create wallet accounts per user (per currency)
- Deposit and withdraw funds
- Transfer funds between accounts
- View paginated transaction history per account

## Architecture & design decisions

This project intentionally avoids the "just mutate a balance column" approach in favor of patterns used in real financial systems.

### Double-entry ledger
Every deposit, withdrawal, and transfer is recorded as an immutable `Transaction` row, in addition to updating the account's `balance`. Transfers create two linked transaction rows (a debit on the sender, a credit on the receiver) tied together via a `Transfer` record.

**Why not just update the balance directly?** A single mutable balance gives you no audit trail and no way to reconstruct how an account reached its current state. The ledger of transactions makes every balance change traceable, replayable, and verifiable after the fact — essential for anything handling real money.

### Optimistic concurrency control
Accounts have a `version` column. Balance updates are conditioned on the version matching what was read (`UPDATE ... WHERE id = ? AND version = ?`). If no rows are affected, the update is retried against a freshly re-fetched account.

**Why optimistic over pessimistic locking?** Wallet operations (deposits, withdrawals) are typically low-contention — the same account isn't usually being hit by concurrent writers most of the time. Optimistic concurrency avoids holding row locks and blocking other transactions, and only pays a retry cost on the rare occasion of an actual conflict. Pessimistic locking (`SELECT ... FOR UPDATE`) would be more appropriate if concurrent writes to the same account were the common case.

### Idempotency keys
Deposit, withdrawal, and transfer requests carry a client-supplied `idempotency_key`. If the same key is submitted again (e.g. due to a client retry after a timeout), the original result is returned instead of double-processing the operation.

**Why this matters:** network retries are a fact of life. Without idempotency, a client retrying a timed-out deposit request could cause a double credit. This is standard practice in real payment APIs (Stripe, for example, works the same way).

### Cursor-based pagination
Transaction history is paginated using a cursor (the last-seen transaction ID) rather than offset-based pagination.

**Why cursor over offset?** Offset pagination (`LIMIT/OFFSET`) degrades in performance on large tables and produces inconsistent results if rows are inserted between page requests. Cursor pagination stays performant and stable as the transaction table grows into the thousands or millions of rows.

### Authentication & authorization
- **Authentication** (verifying *who* is calling) is handled via JWT bearer tokens, checked in a FastAPI dependency (`get_current_user`) at the route level.
- **Authorization** (verifying the caller *owns* the resource they're acting on) is enforced in the service layer, right where the account is fetched — not in the route. This ensures an authenticated user can't act on another user's account just by changing an ID in the request.
- Passwords are hashed with **bcrypt** via `passlib`, never stored or compared in plaintext.

**Known tradeoff:** JWTs are stateless, so a token can't be revoked before it expires. Short expiry windows mitigate this; a refresh-token flow or a token blocklist would be the next step for production use.

## Tech stack

| Layer | Choice |
|---|---|
| API framework | FastAPI |
| ORM | SQLAlchemy |
| Auth | JWT (`python-jose`) + bcrypt (`passlib`) |
| Validation | Pydantic |
| Database | SQLite (dev) / swappable for PostgreSQL |

## Project structure

```
app/
├── models/          # SQLAlchemy ORM models (Account, Transaction, Transfer, User)
├── schemas/         # Pydantic request/response schemas
├── services/        # Business logic (AccountService, TransferService, UserService)
├── routers/         # FastAPI route handlers
├── core/            # Security utilities, auth dependencies
└── db/              # Database session/engine setup
```

## Getting started

### 1. Clone and set up a virtual environment
```bash
git clone https://github.com/Jayesh-P2603/fintech-wallet.git
cd <project-folder>
python -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Create a `.env` file in the project root:
```dotenv
JWT_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
```

### 4. Run the app
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

## Example flow

```
POST /users/signup        → create a user + default wallet account
POST /auth/login          → get a JWT access token
POST /accounts/{id}/deposit    (with Bearer token)
POST /accounts/{id}/withdraw   (with Bearer token)
POST /transfers                (with Bearer token)
GET  /accounts/{id}/history?cursor=...&limit=...
```

## Known limitations / next steps

Being upfront about these — they reflect deliberate scoping decisions, not oversights:

- **No token revocation.** JWTs are stateless; a compromised token remains valid until it expires. A refresh-token pattern or blocklist would address this.
- **No database migrations tool yet.** Schema changes currently require manual intervention; adopting Alembic would make schema evolution versioned and reversible.
- **No rate limiting.** Would be needed before any public deployment, particularly on auth endpoints.
- **Single-currency transfers only.** No FX conversion between accounts of different currencies.
- **No automated concurrency test suite.** Optimistic concurrency logic has been reasoned through and manually tested; a load test (e.g. with `asyncio` or Locust) would give stronger confidence under real contention.

## License

MIT
