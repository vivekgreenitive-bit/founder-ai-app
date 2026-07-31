import time
import uuid
from typing import Optional
from providers.base_payment_provider import BasePaymentProvider

class CoinbasePaymentProvider(BasePaymentProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def get_wallet_balance(self, wallet_id: str) -> float:
        time.sleep(0.1)
        return 8.50  # 8.50 ETH balance simulation

    def execute_payment(self, wallet_id: str, destination_address: str, amount: float) -> str:
        time.sleep(0.2)
        return f"cb_tx_{uuid.uuid4().hex[:16]}"

    def provider_name(self) -> str:
        return "coinbase"
