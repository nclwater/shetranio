from shetranio.setup import mask
import unittest

class TestClipper(unittest.TestCase):
    outline_path = 'sample_data/44006.zip'
    resolution = 1000
    output_path = 'outputs/mask.txt'
    extracted_path = 'outputs/extracted.txt'
    dem_data = 'sample_data/1kmDtmBng.txt'

    def test_create_mask(self):

        mask.create(self.outline_path, self.resolution, self.output_path)

    def test_extract(self):

        mask.extract(self.output_path, self.dem_data, self.extracted_path, 1000)

if __name__ == '__main__':
    unittest.main()
