from shetran.setup import mask
import unittest

class TestClipper(unittest.TestCase):
    outline_path = 'sample_data/44006.zip'
    resolution = 100
    output_path = 'outputs/mask.txt'

    def test_create_mask(self):
        with open(self.outline_path, 'rb') as f:
            outline = bytes(f.read())
        mask.create(outline, self.resolution, self.output_path)

if __name__ == '__main__':
    unittest.main()
