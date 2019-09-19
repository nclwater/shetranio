import xml.etree.ElementTree as ET
import os
from . import dem, hdf
from datetime import datetime


class Model:
    def __init__(self, library_file_path):
        self.library = library_file_path
        self.tree = ET.parse(library_file_path)
        self.project_file = self.get('ProjectFile')
        self.catchment_name = self.get('CatchmentName')
        self.mask = self.get_path('MaskFileName')
        self.veg_map = self.get_path('VegMap')
        self.lake_map = self.get_path('LakeMap')
        self.precip_map = self.get_path('PrecipMap')
        self.pe_map = self.get_path('PeMap')
        self.veg_details = self.tree.find('VegetationDetails')
        self.soil_properties = self.tree.find('SoilProperties')
        self.soil_details = self.tree.find('SoilDetails')
        self.initial_conditions = self.get('InitialConditions')
        self.precipitation_time_series = self.get_path('PrecipitationTimeSeriesData')
        self.precipitation_time_step = self.tree.find('PrecipitationTimeStep')
        self.evaporation_time_series = self.get_path('EvaporationTimeSeriesData')
        self.evaporation_time_step = self.tree.find('EvaporationTimeStep')
        self.max_temp_time_series = self.get_path('MaxTempTimeSeriesData')
        self.min_temp_time_series = self.get_path('MinTempTimeSeriesData')
        self.start_day = self.get('StartDay')
        self.start_month = self.get('StartMonth')
        self.start_year = self.get('StartYear')
        self.start_date = datetime(self.start_year, self.start_month, self.start_day)
        self.end_day = self.get('EndDay')
        self.end_month = self.get('EndMonth')
        self.end_year = self.get('EndYear')
        self.end_date = datetime(self.end_year, self.end_month, self.end_day) \
            if self.end_day and self.end_month and self.end_year else None
        self.river_grid_squares_accumulated = self.get('RiverGridSquaresAccumulated')
        self.drop_from_grid_to_channel_depth = self.get('DropFromGridToChannelDepth')
        self.minimum_drop_between_channels = self.get('MinimumDropBetweenChannels')
        self.regular_time_step = self.get('RegularTimestep')
        self.increasing_time_step = self.get('IncreasingTimestep')
        self.simulated_discharge_time_step = self.get('SimulatedDischargeTimestep')
        self.snow_melt_degree_day_factor = self.get('SnowmeltDegreeDayFactor')
        self.snow_melt_degree_day_factor = self.get('SnowmeltDegreeDayFactor')
        self.srid = self.get('SRID')

        self.dem = dem.Dem(self.get_path('DEMMeanFileName'))
        self.h5 = hdf.Hdf(self.path('output_{}_shegraph.h5'.format(self.catchment_name)),
                          model=self)

    def get(self, name):
        value = self.tree.find(name)
        if value is None:
            return
        elif value.text.isdigit():
            return int(value.text)
        else:
            return value.text

    def path(self, name):
        return os.path.join(os.path.dirname(self.library), str(name)) if name is not None else name

    def get_path(self, name):
        return self.path(self.get(name))




