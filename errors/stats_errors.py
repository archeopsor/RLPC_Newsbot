class PRSheetError(Exception):
    def __init__(self, league: str, *args: object) -> None:
        self.league = league
        super().__init__(*args)

class FindMeError(Exception):
    def __init__(self, discord_id: str, *args: object) -> None:
        self.discord_id = discord_id
        super().__init__(*args)

class InvalidStatError(Exception):
    def __init__(self, stat, *args: object) -> None:
        self.stat = stat
        super().__init__(*args)

class StatSheetError(Exception):
    def __init__(self, range: str, *args: object) -> None:
        self.range = range
        super().__init__(*args)

class StatsError(Exception):
    def __init__(self, player: str, stat: str, *args: object) -> None:
        self.player = player
        self.stat = stat
        super().__init__(*args)

class FindPlayersError(Exception):
    def __init__(self, league: str, stat: str, *args: object) -> None:
        self.league = league
        self.stat = stat
        super().__init__(*args)

class InvalidDayError(Exception):
    def __init__(self, day: int, *args: object) -> None:
        self.day = day
        super().__init__(*args)

class GDStatsSheetError(Exception):
    def __init__(self, day: int, *args: object) -> None:
        self.day = day
        super().__init__(*args)

class PlayerNotFoundError(Exception):
    def __init__(self, player: str, day: int, *args: object) -> None:
        self.player = player
        self.day = day
        super().__init__(*args)