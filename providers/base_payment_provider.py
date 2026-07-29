import abc

class BasePaymentProvider(abc.ABC):
    @abc.abstractmethod
    def get_wallet_balance(self, wallet_id: str) -> float:
        """Retrieves current USDC balance for the wallet."""
        pass

    @abc.abstractmethod
    def execute_payment(self, wallet_id: str, destination_address: str, amount: float) -> str:
        """Executes USDC payment transfer and returns a unique transaction hash/confirmation ID."""
        pass

    @abc.abstractmethod
    def provider_name(self) -> str:
        """Returns the provider unique label."""
        pass
