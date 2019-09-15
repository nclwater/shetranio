import h5py
from .dem import Dem
import numpy as np
from datetime import timedelta


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
    def __new__(cls, hdf, variable_name):
        if variable_name in hdf.variable_names.keys():
            return super(Variable, cls).__new__(cls)
        else:
            return None

    def __init__(self, hdf, variable_name):
        self.name = variable_name
        self.hdf = hdf
        self.variable = hdf.file_variables[hdf.variable_names[variable_name]]
        self.values = self.variable['value']
        self.times = self.variable['time']
        self.time_units = self.times.attrs['units'][0].decode("utf-8")
        if self.hdf.start_date:
            self.times = np.array([self.hdf.start_date + timedelta(seconds=time * 60) for time in self.times])
            self.time_units = ''
        self.units = self.values.attrs['units'][0].decode("utf-8")
        self.long_name = '{} ({})'.format(variable_names[self.name], self.units)
        self.is_river = False
        self.is_spatial = True
        try:
            self.hdf.variables.append(self)
        except TypeError:
            pass


class RiverVariable(Variable):
    def __init__(self, hdf, variable_name):
        super().__init__(hdf, variable_name)
        self.is_river = True


class OverlandFlow(RiverVariable):
    def __init__(self, hdf, variable_name):
        super().__init__(hdf, variable_name)

    def get_element(self, element_number):
        return np.abs(self.values[self.hdf.get_element_index(element_number), :, :]).max(axis=0)

    def get_time(self, time_index):
        return np.abs(self.values[:, :, time_index]).max(axis=1)


class SurfaceDepth(RiverVariable):
    def __init__(self, hdf, variable_name):
        super().__init__(hdf, variable_name)

    def get_element(self, element_number):
        return self.values[self.hdf.get_element_index(element_number), :]

    def get_time(self, time_index):
        return np.abs(self.values[:, time_index])


class LandVariable(Variable):
    def __init__(self, hdf, variable_name):
        super().__init__(hdf, variable_name)

    def get_element(self, element_number):
        index = np.where(self.hdf.number.square == element_number)
        return self.values[index[0][0], index[1][0]]

    def get_time(self, time_index):
        numbers = self.hdf.number.square.flatten()
        values = self.values[:, :, time_index].flatten()
        return values[values != -1][np.argsort(numbers[numbers != -1])]


class SoilMoisture(LandVariable):
    def __init__(self, hdf, variable_name):
        super().__init__(hdf, variable_name)

    def get_element(self, element_number, level=0):
        index = np.where(self.hdf.number.square == element_number)
        return self.values[index[0][0], index[1][0], level]

    def get_time(self, time_index, level=0):
        numbers = self.hdf.number.square.flatten()
        values = self.values[:, :, level, time_index].flatten()
        return values[values != -1][np.argsort(numbers[numbers != -1])]


class RainVariable(Variable):
    def __init__(self, hdf, variable_name):
        super().__init__(hdf, variable_name)
        self.is_spatial = False


class Hdf:
    def __init__(self, path, start_date=None):
        self.path = path
        self.start_date = start_date
        self.file = h5py.File(path, 'r', driver='core')
        self.catchment_maps = self.file['CATCHMENT_MAPS']
        self.sv4_elevation = self.catchment_maps['SV4_elevation'][:]
        self.palette1 = self.catchment_maps['palette1']
        self.catchment_spreadsheets = self.file['CATCHMENT_SPREADSHEETS']
        self.sv4_numbering = self.catchment_spreadsheets['SV4_numbering'][:]
        self.element_numbers = np.unique(self.sv4_numbering)[1:]
        self.constants = self.file['CONSTANTS']
        self.centroid = Constant(self.constants['centroid'])
        self.grid_dxy = self.constants['grid_dxy']
        self.number = Constant(self.constants['number'])
        self.land_elements = np.unique(self.number.square)[1:]
        self.river_elements = self.element_numbers[:min(self.land_elements) - 1]
        self.r_span = Constant(self.constants['r_span'])
        self.soil_type = Constant(self.constants['soil_typ'])
        self.spatial1 = Constant(self.constants['spatial1'])
        self.surface_elevation = Constant(self.constants['surf_elv'])
        self.vertical_thickness = Constant(self.constants['vert_thk'])

        self.file_variables = self.file['VARIABLES']
        self.variable_names = dict([(k.split(' ')[-1], k) for k in self.file_variables.keys()])
        self.variables = []
        self.net_rain = RainVariable(self, 'net_rain')
        self.potential_evapotranspiration = LandVariable(self, 'pot_evap')
        self.transpiration = LandVariable(self, 'trnsp')
        self.surface_evaporation = LandVariable(self, 'srf_evap')
        self.evaporation_from_interception = LandVariable(self, 'int_evap')
        self.drainage_from_interception = LandVariable(self, 'drainage')
        self.canopy_storage = LandVariable(self, 'can_stor')
        self.vertical_flows = LandVariable(self, 'v_flow')
        self.snow_depth = LandVariable(self, 'snow_dep')
        self.ph_depth = LandVariable(self, 'ph_depth')
        self.overland_flow = OverlandFlow(self, 'ovr_flow')
        self.surface_depth = SurfaceDepth(self, 'srf_dep')
        self.surface_water_potential = LandVariable(self, 'psi')
        self.soil_moisture = SoilMoisture(self, 'theta')
        self.total_sediment_depth = LandVariable(self, 's_t_dp')
        self.surface_erosion_rate = LandVariable(self, 's_v_er')
        self.sediment_discharge_rate = LandVariable(self, 's_dis')
        self.mass_balance_error = LandVariable(self, 'bal_err')
        self.snow_depth = LandVariable(self, 'snow_dep')
        self.variables = tuple(self.variables)


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

    def get_element_index(self, element_number):
        return self.element_numbers.tolist().index(element_number)

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

        dem = Dem(dem)

        features = []

        geoms = Geometries(self, dem, srs)

        for n in self.element_numbers:


            properties = {}

            if self.overland_flow:
                properties['overland_flow'] = {
                    'values':(np.absolute(self.overland_flow.values[n-1,:,:]).max(axis=0).astype(np.float64).tolist()
                              if n-1<self.overland_flow.values.shape[0] else [])
                         }
            if self.ph_depth:
                properties['ph_depth'] = {
                    'values':self.ph_depth.values[:][self.number.square==n].flatten().tolist()
                }

            if self.surface_depth:
                properties['surface_depth'] = {
                    'values':(self.surface_depth.values[n-1,:].astype(np.float64).tolist()
                              if n-1<self.overland_flow.values.shape[0] else [])
                         }

            if self.canopy_storage:
                properties['canopy_storage'] = {
                    'values':self.canopy_storage.values[:][self.number.square==n].flatten().tolist()
                }
            if self.soil_moisture:
                properties['theta'] = {
                    'values': self.soil_moisture.values[:, :, 0, 1:][self.number.square == n].flatten().tolist()
                }

            properties['dem'] = {
                'value': float(self.sv4_elevation[self.sv4_numbering == n][0])
            }

            properties['number'] = int(n)


            features.append({
                'type': 'Feature',
                'geometry': geoms.__next__(),
                'properties': properties
            })

        # unique, inverse = np.unique(numbers, return_inverse=True)


        variables = []

        if self.ph_depth:
            variables.append(
                {
                'name': 'ph_depth',
                'longName':'Phreatic Depth (m)',
                'max': self.ph_depth.values[:][self.ph_depth.values[:] != -1].astype(np.float64).max(),
                'min': self.ph_depth.values[:][self.ph_depth.values[:] != -1].astype(np.float64).min(),
                'times': self.ph_depth.times[:].tolist()
                })

        if self.overland_flow:
            variables.append(
                {
                'name': 'overland_flow',
                'longName':'Overland Flow (cumecs)',
                'max': np.absolute(self.overland_flow.values[:].astype(np.float64)).max(),
                'min': np.absolute(self.overland_flow.values[:].astype(np.float64)).min(),
                'times':self.overland_flow.times[:].tolist()
                })
        if self.canopy_storage:
            variables.append(
                {
                'name': 'canopy_storage',
                'longName':'Canopy Storage (mm)',
                'max': self.canopy_storage.values[:][self.canopy_storage.values[:] != -1].astype(np.float64).max(),
                'min': self.canopy_storage.values[:][self.canopy_storage.values[:] != -1].astype(np.float64).min(),
                'times': self.canopy_storage.times[:].tolist()
                })
        if self.surface_depth:
            variables.append(
                {
                    'name': 'surface_depth',
                    'longName': 'Surface Depth (m)',
                    'max': self.surface_depth.values[:].astype(np.float64).max(),
                    'min': self.surface_depth.values[:].astype(np.float64).min(),
                    'times': self.surface_depth.times[:].tolist()
                }
            )
        if self.soil_moisture:
            variables.append(
                {
                    'name': 'theta',
                    'longName': 'Soil Moisture (m3/m3)',
                    'max': (self.soil_moisture.values[:, :, 0, 1:][self.soil_moisture.values[:, :, 0, 1:] != -1].astype(np.float64).max()
                        if len(self.soil_moisture.values[:, :, 0, 1:][self.soil_moisture.values[:, :, 0, 1:] != -1]) > 0 else None),
                    'min': (self.soil_moisture.values[:, :, 0, 1:][self.soil_moisture.values[:, :, 0, 1:] != -1].astype(np.float64).min()
                        if len(self.soil_moisture.values[:, :, 0, 1:][self.soil_moisture.values[:, :, 0, 1:] != -1]) > 0 else None),
                    'times': self.soil_moisture.times[1:].tolist()
                }
            )


        return {
            'geom':
                    {
                        'type':'FeatureCollection',
                        'features':features
                    },
            'variables':variables
        }


class Geometries:
    def __init__(self, hdf, dem, srs=None):
        from osgeo import osr

        self.hdf = hdf
        self.dem = dem
        if srs is None:
            srs = 'EPSG:27700'
            print('SRID not specified, setting to {}'.format(srs))

        assert ':' in srs, 'SRID must be formatted like EPSG:27700'

        authority, code = srs.split(':')
        source = osr.SpatialReference()

        if authority == 'EPSG':
            source.ImportFromEPSG(int(code))
        else:
            raise Exception('Only EPSG coordinate systems are currently supported')

        target = osr.SpatialReference()
        target.ImportFromEPSG(4326)

        self.transform = osr.CoordinateTransformation(source, target)

        n = hdf.sv4_numbering

        self.indices = np.indices(n.shape)

        cell_size_factor = hdf.sv4_elevation.shape[0] / hdf.surface_elevation.square.shape[0]

        self.cell_size = dem.cell_size / cell_size_factor

        self.current = 0

        _, self.index = np.unique(n.flatten(), return_index=True)
        _, self.reverse_index = np.unique(n.flatten()[::-1], return_index=True)

        self.y = (self.indices[0] * self.cell_size + dem.y_lower_left - dem.cell_size)[::-1]
        self.x = self.indices[1] * self.cell_size + dem.x_lower_left - dem.cell_size

        self.ymax = self.y.flatten()[::-1][self.reverse_index][1:]
        self.ymin = self.y.flatten()[self.index][1:]

        self.xmax = self.x.flatten()[::-1][self.reverse_index][1:]
        self.xmin = self.x.flatten()[self.index][1:]

    def __len__(self):
        return len(self.ymax)

    def __iter__(self):
        return self

    def __next__(self):
        from osgeo import ogr
        if self.current > len(self) - 1:
            raise StopIteration
        else:
            y1 = self.ymin[self.current]
            x1 = self.xmin[self.current]
            y2 = self.ymax[self.current]
            x2 = self.xmax[self.current]

            point = ogr.CreateGeometryFromWkt("POINT ({} {})".format(x1, y1))
            point.Transform(self.transform)

            x1 = point.GetX()
            y1 = point.GetY()

            point = ogr.CreateGeometryFromWkt("POINT ({} {})".format(x2, y2))
            point.Transform(self.transform)

            x2 = point.GetX()
            y2 = point.GetY()

            self.current += 1

            return {
                'type': 'Polygon',
                'coordinates': [[[x1, y1], [x1, y2], [x2, y2], [x2, y1], [x1, y1]]]
            }

variable_names = {
    'net_rain': 'Net Rain',
    'trnsp': 'Transpiration',
    'pot_evap': 'Potential Evapotranspiration',
    'srf_evap': 'Surface Evaporation',
    'int_evap': 'Evaporation from Interception',
    'drainage': 'Drainage from Interception',
    'can_stor': 'Canopy Storage',
    'v_flow': 'Vertical Flows',
    'snow_dep': 'Snow Depth',
    'ph_depth': 'Phreatic Depth',
    'ovr_flow': 'Overland Flow',
    'srf_dep': 'Surface Depth',
    'psi': 'Surface Water Potential',
    'theta': 'Soil Moisture',
    's_t_dp': 'Total Sediment Depth',
    's_v_er': 'Surface Erosion Rate',
    's_dis': 'Sediment Discharge Rate',
    'bal_err': 'Mass Balance Error'
}

