class ReplayFailedError(Exception):
    def __init__(self, file_path: str, *args: object) -> None:
        self.file_path = file_path
        super().__init__(*args)