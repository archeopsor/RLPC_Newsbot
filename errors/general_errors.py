class LeagueNotFoundError(Exception):
    def __init__(self, team: str, *args: object) -> None:
        self.team = team
        super().__init__(*args)

class InvalidArgumentError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)