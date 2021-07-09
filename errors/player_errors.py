class TeamNotFoundError(Exception):
    def __init__(self, team: str, *args: object) -> None:
        self.team = team
        super().__init__(*args)

class NoLogoError(Exception):
    def __init__(self, team: str, *args: object) -> None:
        self.team = team
        super().__init__(*args)