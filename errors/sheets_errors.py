class SheetsError(Exception):
    """Base class for Sheets exceptions"""
    def __init__(self, message: str, sheet_id: str):
        self.sheet_id = sheet_id
        self.message = message
        super().__init__(self.message)


class GetSheetError(SheetsError):
    
    def __init__(self, message: str, sheet_id: str, sheet_range: str):
        self.message = message
        self.sheet_id = sheet_id
        self.sheet_range = sheet_range
        super().__init__(sheet_id, message)


class SheetToDfError(SheetsError):

    def __init__(self, message: str, sheet_id: str, sheet_range: str):
        self.message = message
        self.sheet_id = sheet_id
        self.sheet_range = sheet_range
        super().__init__(message, sheet_id)

class UpdateCellError(SheetsError):

    def __init__(self, message: str, sheet_id: str, cell: str):
        self.message = message
        self.sheet_id = sheet_id
        self.cell = cell
        super().__init__(message, sheet_id)