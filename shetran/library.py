import xml.etree.ElementTree as ET
import os

class Library:
    def __init__(self, path):
        self.path = path
        self.tree = ET.parse(path)
        self.project_file = os.path.join(os.path.dirname(path),self.tree.find('ProjectFile').text)
        self.catchment_name = os.path.join(os.path.dirname(path),self.tree.find('CatchmentName').text)
        self.mask = os.path.join(os.path.dirname(path),self.tree.find('MaskFileName').text)
        self.veg_map = os.path.join(os.path.dirname(path),self.tree.find('VegMap').text)
        self.lake_map = os.path.join(os.path.dirname(path),self.tree.find('LakeMap').text)
        self.precip_map = os.path.join(os.path.dirname(path),self.tree.find('PrecipMap').text)
        self.pe_map = os.path.join(os.path.dirname(path),self.tree.find('PeMap').text)
        self.veg_details = self.tree.find('VegetationDetails')
        self.soil_properties = self.tree.find('SoilProperties')
        self.soil_details = self.tree.find('SoilDetails')
        self.initial_conditions = self.tree.find('InitialConditions').text
        self.precipitation_time_series = \
            os.path.join(os.path.dirname(path),self.tree.find('PrecipitationTimeSeriesData').text)
        self.precipitation_time_step = self.tree.find('PrecipitationTimeStep')
        self.evaporation_time_series = \
            os.path.join(os.path.dirname(path),self.tree.find('EvaporationTimeSeriesData').text)
        self.evaporation_time_step = self.tree.find('EvaporationTimeStep')
        self.max_temp_time_series = \
            os.path.join(os.path.dirname(path), self.tree.find('MaxTempTimeSeriesData').text)
        self.min_temp_time_series = \
            os.path.join(os.path.dirname(path), self.tree.find('MinTempTimeSeriesData').text)
        self.start_day = self.tree.find('StartDay').text
        self.start_month = self.tree.find('StartMonth').text
        self.start_year = self.tree.find('StartYear').text
        self.end_day = self.tree.find('EndDay').text
        self.end_month = self.tree.find('EndMonth').text
        self.end_year = self.tree.find('EndYear').text
        self.river_grid_squares_accumulated = self.tree.find('RiverGridSquaresAccumulated').text
        self.drop_from_grid_to_channel_depth = self.tree.find('DropFromGridToChannelDepth').text
        self.minimum_drop_between_channels = self.tree.find('MinimumDropBetweenChannels').text
        self.regular_time_step = self.tree.find('RegularTimestep').text
        self.increasing_time_step = self.tree.find('IncreasingTimestep').text
        self.simulated_discharge_time_step = self.tree.find('SimulatedDischargeTimestep').text
        self.snow_melt_degree_day_factor = self.tree.find('SnowmeltDegreeDayFactor').text
        self.snow_melt_degree_day_factor = self.tree.find('SnowmeltDegreeDayFactor').text



