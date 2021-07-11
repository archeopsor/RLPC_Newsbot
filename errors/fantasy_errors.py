class FantasyError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class PlayerNotFoundError(Exception):
    def __init__(self, player: str, *args: object) -> None:
        self.player = player
        super().__init__(*args)

class AccountNotFoundError(Exception):
    def __init__(self, discord_id: str, *args: object) -> None:
        self.discord_id = discord_id
        super().__init__(*args)

class TeamFullError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class IllegalPlayerError(Exception):
    def __init__(self, player: str, *args: object) -> None:
        self.player = player
        super().__init__(*args)

class SalaryError(Exception):
    def __init__(self, excess: int, salary_cap: int, player: str, *args: object) -> None:
        self.excess = excess
        self.salary_cap = salary_cap
        self.player = player
        super().__init__(*args)

class AlreadyPickedError(Exception):
    def __init__(self, player: str, *args: object) -> None:
        self.player = player
        super().__init__(*args)

class TimeError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class NoTransactionError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)