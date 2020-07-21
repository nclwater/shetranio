from shetranio import Model
import unittest
import os


sample_data = os.path.join(os.path.dirname(__file__), 'sample_data')


def path(s):
    return os.path.join(sample_data, s)


wansbeck = Model(path('Wansbeck_at_Mitford_Library_File.xml'))


class TestModel(unittest.TestCase):

    def test_model(self):
        self.assertIsInstance(wansbeck, Model)

    def test_get_element(self):
        wansbeck.hdf.overland_flow.get_element(1)

    def test_get_element_by_location(self):
        wansbeck.hdf.ph_depth.get_element_by_location(wansbeck.dem, 398465, 586505)

    def test_get_contaminant_concentration(self):
        model = Model(path("coledale-contaminant-good3-test/LibraryFile.xml"))
        print(model.hdf.contaminant_concentration_land)
        print(model.hdf.contaminant_concentration_rivers)
