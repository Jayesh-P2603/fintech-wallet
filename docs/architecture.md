```mermaid
graph TD
    %% 1. The Entry Points (Routes)
    WithdrawReq([Withdraw Request]) -->|1. Row Lock| W1
    DepositReq([Deposit Request]) -->|1. Row Lock| W1
    TransferReq([Transfer Request]) -->|1. Deterministic Lock| W1
    TransferReq -->|1. Deterministic Lock| W2

    %% 2. The Intent (Transfers Table)
    subgraph "Event Record (The Why)"
    TransferReq -->|2. Create| TransferTable[(Table: Transfers)]
    end

    %% 3. The State (Accounts Table)
    subgraph "Current Balances (The State)"
    W1[Account: Sender/User]
    W2[Account: Receiver]
    
    W1 -.->|Update| Balance1(New Balance)
    W2 -.->|Update| Balance2(New Balance)
    end

    %% 4. The Ledger (Transactions Table)
    subgraph "Audit Trail (The Evidence)"
    %% Transfer Path
    Txn_Out[Transaction: Transfer Out] -->|Linked via transfer_id| TransferTable
    Txn_In[Transaction: Transfer In] -->|Linked via transfer_id| TransferTable
    
    Txn_Out -->|Belongs to| W1
    Txn_In -->|Belongs to| W2

    %% Deposit/Withdraw Path
    Txn_Dep[Transaction: Deposit] -->|Belongs to| W1
    Txn_With[Transaction: Withdraw] -->|Belongs to| W1
    end

    %% 5. Constraints
    IdemK{Idempotency Key Check}
    WithdrawReq --> IdemK
    DepositReq --> IdemK
    TransferReq --> IdemK
    IdemK -->|If Exists| Return[Return Existing Record]
    ```