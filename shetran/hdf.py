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

class Variable:
    def __init__(self, variable):
        self.values = variable['value']
        self.times = variable['time']

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
        self.net_rain = self.lookup_variable('net_rain')
        self.potential_evapotranspiration = self.lookup_variable('pot_evap')
        self.transpiration = self.lookup_variable('trnsp')
        self.surface_evaporation = self.lookup_variable('srf_evap')
        self.evaporation_from_interception = self.lookup_variable('int_evap')
        self.drainage_from_interception = self.lookup_variable('drainage')
        self.canopy_storage = self.lookup_variable('can_stor')
        self.vertical_flows = self.lookup_variable('v_flow')
        self.snow_depth = self.lookup_variable('snow_dep')
        self.ph_depth = self.lookup_variable('ph_depth')
        self.overland_flow = self.lookup_variable('ovr_flow')
        self.surface_depth = self.lookup_variable('srf_dep')
        self.surface_water_potential = self.lookup_variable('psi')
        self.theta = self.lookup_variable('theta')
        self.total_sediment_depth = self.lookup_variable('s_t_dp')
        self.surface_erosion_rate = self.lookup_variable('s_v_er')
        self.sediment_discharge_rate = self.lookup_variable('s_dis')
        self.mass_balance_error = self.lookup_variable('bal_err')



        self.snow_depth = self.lookup_variable('snow_dep')

    def lookup_variable(self, var):
        variables = dict([(k.split(' ')[-1], k) for k in self.variables.keys()])
        if var in variables.keys():
            return Variable(self.variables[variables[var]])
        else:
            return None

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

    def to_json(self):

        d = {}

        for key in self.__dict__.keys():

            attr = self.__dict__[key]

            if type(attr) == Constant:
                d[key] = {}
                for constant_key in attr.__dict__.keys():
                    constant_attr = attr.__dict__[constant_key]
                    d[key][constant_key] = constant_attr.tolist()

            elif type(attr) == Variable:
                d[key] = {}
                d[key]['values'] = attr.values[:].tolist()
                d[key]['times'] = attr.times[:].tolist()

        return d

    def to_geom(self, dem, srs=27700):
        from osgeo import ogr
        from osgeo import osr
        dem = Dem(dem)

        source = osr.SpatialReference()
        source.ImportFromEPSG(srs)

        target = osr.SpatialReference()
        target.ImportFromEPSG(4326)

        transform = osr.CoordinateTransformation(source, target)

        numbers = self.sv4_numbering[:]

        indices = np.indices(numbers.shape)
        result = []
        for n in np.unique(numbers):
            a = indices[:, numbers == n]
            y1 = (numbers.shape[0]-a.min(axis=1)[0]) * dem.cell_size + dem.x_lower_left
            x1 = a.min(axis=1)[1] * dem.cell_size + dem.y_lower_left
            y2 = (numbers.shape[0]-a.max(axis=1)[0]) * dem.cell_size + dem.x_lower_left
            x2 = a.max(axis=1)[1] * dem.cell_size + dem.y_lower_left

            point = ogr.CreateGeometryFromWkt("POINT ({} {})".format(x1, y1))
            point.Transform(transform)

            x1 = point.GetX()
            y1 = point.GetY()

            point = ogr.CreateGeometryFromWkt("POINT ({} {})".format(x2, y2))
            point.Transform(transform)

            x2 = point.GetX()
            y2 = point.GetY()


            result.append([[x1, y1], [x1, y2], [x2, y2], [x2, y1], [x1, y1]])

        # unique, inverse = np.unique(numbers, return_inverse=True)

        return {'geoms':result}


