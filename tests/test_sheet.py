import unittest
from tools.sheet import Sheet
import settings

p4 = Sheet(settings.sheet_p4)
indy = Sheet(settings.sheet_indy)
test = Sheet(settings.test_sheet)

class TestSheet(unittest.TestCase):
    def test_get(self):
        self.assertIsNotNone(p4.get("Players!A1:H"))
        self.assertIsNotNone(indy.get("Players!A1:H"))
    
    def test_to_df(self):
        df = p4.to_df("Players!A1:H")
        self.assertEqual(df.columns.to_list(), ['Username', 'Region', 'Platform', 'Sheet MMR', 'Team', 'League', 'Conf', 'Div'])

    def test_0_update(self):
        self.assertEqual(type(test.update_cell('Sheet1!A4', 20)), dict)
        
    def test_append(self):
        values = [[1, 2, 3, 4], ['a', 'b', 'c', 'd'], [1.0, 1.1, 1.2, 1.3]]
        self.assertEqual(test.append('Sheet1!A1:D3', values)['updates']['updatedCells'], 12)
        
    def test_clear(self):
        self.assertEqual(type(test.clear('Sheet1!A1:D4')), dict)

if __name__ == '__main__':
    unittest.main()