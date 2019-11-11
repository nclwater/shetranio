import unittest
from shetranio.setup import gear
from datetime import datetime

class TestGear(unittest.TestCase):
    mask_path = 'sample_data/mask.txt'
    data_path = 'sample_data/ceh_gear_rain.nc'
    ts_path = 'outputs/ceh_rain.txt'
    grid_path = 'outputs/ceh_rain_grid.txt'
    start_date = datetime(2015, 1, 1)
    end_date = datetime(2015, 1, 3)


    def test_rain(self):
        gear.extract(self.data_path,
                     'rainfall_amount',
                     self.mask_path,
                     self.start_date,
                     self.end_date,
                     self.grid_path,
                     self.ts_path)

    def test_pet(self):
        gear.extract('sample_data/ceh_gear_pet.nc',
                     'pet',
                     self.mask_path,
                     self.start_date,
                     self.end_date,
                     'outputs/ceh_pet_grid.txt',
                     'outputs/ceh_pet.txt'
                     )

if __name__ == '__main__':
    unittest.main()


