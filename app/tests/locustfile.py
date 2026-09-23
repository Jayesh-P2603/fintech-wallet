import uuid
from locust import HttpUser, task, between
import random

class WebsiteUser(HttpUser):
    host = "http://127.0.0.1:8000"
    wait_time = between(0.1, 0.5 )
    
    @task
    def test_multiple_deposits(self):
        
        account_id = random.randint(1, 1000)
        payload = {
            "amount": 10.0,
            "idempotency_key": str(uuid.uuid4())
        }

        self.client.post(f"/accounts/{account_id}/deposit", json=payload, name="/accounts/[account_id]/deposit")

    @task
    def test_multiple_withdraws(self):

        account_id = random.randint(1, 1000)
        payload = {
            "amount": 1.0,
            "idempotency_key": str(uuid.uuid4())
        }

        self.client.post(f"/accounts/{account_id}/withdraw", json=payload, name="/accounts/[account_id]/withdraw")

    @task
    def test_multiple_transfers(self):

        sender_id = random.randint(1, 1000)
        receiver_account_id = random.randint(1, 1000)
        
        while receiver_account_id == sender_id:
            receiver_account_id = random.randint(1, 1000)
        payload = {
            "receiver_account_id": receiver_account_id,
            "amount": 1.0,
            "idempotency_key": str(uuid.uuid4())
        }

        self.client.post(
            f"/accounts/{sender_id}/transfer",
            json=payload,
            name="/accounts/[id]/transfer"
        )