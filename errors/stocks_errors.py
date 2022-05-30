class AccountNotFoundError(Exception):
    def __init__(self, id: str,  *args: object) -> None:
        self.id = id
        super().__init__(*args)

class InsufficientFundsError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)