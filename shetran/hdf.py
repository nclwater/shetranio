import h5py
import dem
import numpy as np
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
        self.centroid = self.constants['centroid']
        self.grid_dxy = self.constants['grid_dxy']
        self.number = self.constants['number']
        self.r_span = self.constants['r_span']
        self.soil_type = self.constants['soil_typ']
        self.spatial1 = self.constants['spatial1']
        self.surface_elevation = self.constants['surf_elv']
        self.vertical_thickness = self.constants['vert_thk']
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
        d = dem.Dem(dem_file)

        x_coordinates = np.array([d.x_lower_left+i*d.cell_size for i in range(d.number_of_columns)])
        y_coordinates = np.array([d.y_lower_left+i*d.cell_size for i in range(d.number_of_rows)])

        x_location = x_coordinates[np.abs(x_coordinates-location[0]) ==np.min(np.abs(x_coordinates-location[0]))]
        y_location = y_coordinates[np.abs(y_coordinates-location[1]) ==np.min(np.abs(y_coordinates-location[1]))]

        x_index = int(np.where(x_coordinates==x_location)[0])
        y_index = int(np.where(y_coordinates==y_location)[0])
        return self.number[y_index,x_index,0]


    def get_element_location(self, dem_file, element_number):
        d = dem.Dem(dem_file)

        index = np.where(self.number[:, :, 0] == element_number)


        x_coordinates = np.array([d.x_lower_left+i*d.cell_size for i in range(d.number_of_columns)])
        y_coordinates = np.array([d.y_lower_left+i*d.cell_size for i in range(d.number_of_rows)])

        x_location = x_coordinates[int(index[1])]
        y_location = y_coordinates[int(index[0])]

        return x_location,y_location

