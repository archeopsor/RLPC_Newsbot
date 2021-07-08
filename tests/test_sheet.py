from errors.sheets_errors import ClearValuesError, GetSheetError, NoPermissionError, PushDfError
import unittest

from googleapiclient.errors import HttpError
from tools.sheet import Sheet
import settings
import pandas as pd

p4 = Sheet(settings.sheet_p4)
indy = Sheet(settings.sheet_indy)
test = Sheet(settings.test_sheet)
invalid = Sheet('1h2GnudOmd8-86vvOfSPAX5TXFHN5PkflKgl94evhhDs')

class TestSheet(unittest.TestCase):
    def test_get(self):
        self.assertIsNotNone(p4.get("Players!A1:H"))
        self.assertIsNotNone(indy.get("Players!A1:H"))

    def test_no_perms(self):
        self.assertRaises(NoPermissionError, invalid.get, "a1:b")

    def test_get_cache(self):
        p4.get("Players!A1:H")
    
    def test_to_df(self):
        df = p4.to_df("Players!A1:H")
        self.assertEqual(df.columns.to_list(), ['Username', 'Region', 'Platform', 'Sheet MMR', 'Team', 'League', 'Conf', 'Div'])

    def test_invalid_perms_append(self):
        self.assertRaises(NoPermissionError, p4.append, "Major Rosters!A1:B", [['a', 'b']])

    def test_0_update(self):
        self.assertEqual(type(test.update_cell('testing!A4', 20)), dict)
        
    def test_append(self):
        values = [[1, 2, 3, 4], ['a', 'b', 'c', 'd'], [1.0, 1.1, 1.2, 1.3]]
        self.assertEqual(test.append('testing!A1:D3', values)['updates']['updatedCells'], 12)
        
    def test_clear(self):
        self.assertEqual(type(test.clear('testing!A1:D8')), dict)

    def test_clear_error(self):
        self.assertRaises(ClearValuesError, p4.clear, "")

    def test_push_df(self):
        self.assertEqual(type(test.push_df('testing!A1:D', pd.DataFrame({'one': 1, 'two': 2, 'three': 3, 'four': 4}, index=[0]))), dict)

    def test_push_fail(self):
        self.assertRaises(PushDfError, test.push_df, "test!A1:D", pd.DataFrame({'one': 1, 'two': 2, 'three': 3, 'four': 4}, index=[0]), "")

    def test_ensure_recent(self):
        indy.ensure_recent()

if __name__ == '__main__': # pragma: no cover
    unittest.main() 
    test.clear('testing!A1:D')