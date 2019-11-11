from shetranio import Model
import unittest
import os


sample_data = os.path.join(os.path.dirname(__file__), 'sample_data')


def path(s):
    return os.path.join(sample_data, s)


class TestHdf(unittest.TestCase):

    def test_model(self):
        self.assertIsInstance(Model(path('Wansbeck_at_Mitford_Library_File.xml')), Model)
