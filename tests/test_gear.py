import unittest
from shetran.setup import gear
from datetime import datetime

class TestGear(unittest.TestCase):
    mask_path = 'sample_data/mask.txt'
    data_path = '/Users/fergus/downloads/CEH_GEAR_daily_GB_2015.nc'
    ts_path = 'outputs/ceh_rain.txt'
    grid_path = 'outputs/ceh_rain_grid.txt'
    start_date = datetime(2015, 1, 1)
    end_date = datetime(2015, 1, 3)


    def test_rain(self):
        gear.extract(self.data_path,
                     self.mask_path,
                     self.start_date,
                     self.end_date,
                     self.grid_path,
                     self.ts_path)

if __name__ == '__main__':
    unittest.main()


