import h5py
from .dem import Dem
import numpy as np

class Constant:
    def __init__(self, array):
        self.square = array[:, :, 0]
        self.north_bank = array[:, :, 1]
        self.east_bank = array[:, :, 2]
        self.south_bank = array[:, :, 3]
        self.west_bank = array[:, :, 4]
        self.north_link = array[:, :, 5]
        self.east_link = array[:, :, 6]
        self.south_link = array[:, :, 7]
        self.west_link = array[:, :, 8]

    def get_link(self,direction):
        if direction == 'n':
            return self.north_link
        elif direction == 'e':
            return self.east_link
        elif direction == 's':
            return self.south_link
        elif direction == 'w':
            return self.west_link
        else:
            raise Exception('Please specify a direction from [n,e,s,w]')


class Hdf:
    def __init__(self, path):
        self.path = path
        self.file = h5py.File(path, 'r')
        self.catchment_maps = self.file['CATCHMENT_MAPS']
        self.sv4_elevation = self.catchment_maps['SV4_elevation']
        self.palette1 = self.catchment_maps['palette1']
        self.catchment_spreadsheets = self.file['CATCHMENT_SPREADSHEETS']
        self.sv4_numbering = self.catchment_spreadsheets['SV4_numbering']
        self.constants = self.file['CONSTANTS']
        self.centroid = Constant(self.constants['centroid'])
        self.grid_dxy = self.constants['grid_dxy']
        self.number = Constant(self.constants['number'])
        self.r_span = Constant(self.constants['r_span'])
        self.soil_type = Constant(self.constants['soil_typ'])
        self.spatial1 = Constant(self.constants['spatial1'])
        self.surface_elevation = Constant(self.constants['surf_elv'])
        self.vertical_thickness = Constant(self.constants['vert_thk'])
        self.variables = self.file['VARIABLES']
        self.net_rain = self.variables['  1 net_rain']
        self.net_rain_value = self.net_rain['value']
        self.net_rain_time = self.net_rain['time']
        self.ph_depth = self.variables['  2 ph_depth']
        self.ph_depth_value = self.ph_depth['value']
        self.ph_depth_time = self.ph_depth['time']
        self.theta = self.variables['  3 theta']
        self.theta_value = self.theta['value']
        self.theta_time = self.theta['time']
        self.overland_flow = self.variables['  4 ovr_flow']
        self.overland_flow_value = self.overland_flow['value']
        self.overland_flow_time = self.overland_flow['time']
        self.surface_depth = self.variables['  5 srf_dep']
        self.surface_depth_value = self.surface_depth['value']
        self.surface_depth_flow_time = self.surface_depth['time']
        self.snow_depth = self.variables['  6 snow_dep']
        self.snow_depth_value = self.snow_depth['value']
        self.snow_depth_flow_time = self.snow_depth['time']

    def get_element_number(self, dem_file, location):
        d = Dem(dem_file)

        # x_coordinates = np.array([d.x_lower_left+i*d.cell_size for i in range(d.number_of_columns)])
        # y_coordinates = np.array([d.y_lower_left+i*d.cell_size for i in range(d.number_of_rows)])
        #
        # x_location = x_coordinates[np.abs(x_coordinates-location[0]) ==np.min(np.abs(x_coordinates-location[0]))]
        # y_location = y_coordinates[np.abs(y_coordinates-location[1]) ==np.min(np.abs(y_coordinates-location[1]))]
        #
        # x_index = int(np.where(x_coordinates==x_location)[0])
        # y_index = int(np.where(y_coordinates==y_location)[0])

        x_index, y_index = d.get_index(location[0], location[1])



        return self.number.square[y_index,x_index]


    def get_channel_link_number(self, dem_file, location, direction):
        """Returns north-south and east-west channel link numbers"""
        assert direction in ['n', 'e', 's', 'w'], 'Please specify a direction from [n, e, s, w]'
        d = Dem(dem_file)

        # x_coordinates = np.array([d.x_lower_left + i * d.cell_size for i in range(d.number_of_columns)])
        # y_coordinates = np.array([d.y_lower_left + i * d.cell_size for i in range(d.number_of_rows)])
        #
        # x_location = x_coordinates[np.abs(x_coordinates - location[0]) == np.min(np.abs(x_coordinates - location[0]))]
        # y_location = y_coordinates[np.abs(y_coordinates - location[1]) == np.min(np.abs(y_coordinates - location[1]))]
        #
        # x_index = int(np.where(x_coordinates == x_location)[0])
        # y_index = int(np.where(y_coordinates == y_location)[0])

        x_index, y_index = d.get_index(location[0], location[1])

        if direction=='n':
            return self.number.north_link[y_index, x_index]
        elif direction=='e':
            return self.number.east_link[y_index,x_index]
        elif direction=='s':
            return self.number.south_link[y_index,x_index]
        elif direction=='w':
            return self.number.west_link[y_index, x_index]


    def get_channel_link_location(self, dem_file, element_number):
        d = Dem(dem_file)

        if element_number in self.number.north_link:
            index = np.where(self.number.north_link == element_number)
        elif element_number in self.number.east_link:
            index = np.where(self.number.east_link == element_number)
        elif element_number in self.number.south_link:
            index = np.where(self.number.south_link == element_number)
        elif element_number in self.number.west_link:
            index = np.where(self.number.west_link == element_number)
        else:
            index = None
        assert index, 'Element number is not a channel link'

        # x_coordinates = np.array([d.x_lower_left+i*d.cell_size for i in range(d.number_of_columns)])
        # y_coordinates = np.array([d.y_lower_left+i*d.cell_size for i in range(d.number_of_rows)])

        x_location = d.x_coordinates[int(index[1])]
        y_location = d.y_coordinates[int(index[0])]

        return x_location,y_location

    def get_element_location(self, dem_file, element_number):
        d = Dem(dem_file)

        index = np.where(self.number.square == element_number)

        x_location = d.x_coordinates[int(index[1])]
        y_location = d.y_coordinates[int(index[0])]

        return x_location, y_location

