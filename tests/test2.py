from shetran.plot import maps
import os
data_path = os.path.join(os.path.dirname(__file__), 'sample_data')
output_path = os.path.join(os.path.dirname(__file__), 'outputs')
h5_file = os.path.join(data_path, 'output_Wansbeck_at_Mitford_shegraph.h5')
dem_file = os.path.join(data_path, 'Wansbeck_at_Mitford_Dem.txt')

maps.extract_elevation(h5_file, output_path, dem_file)

maps.element_numbers(h5_file, output_path, dem_file)