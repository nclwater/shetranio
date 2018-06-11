import os
import shutil


class Outputs:
    def __init__(self, run):
        self.dem = os.path.join(run.directory, "DEM.txt")
        self.min_dem = os.path.join(run.directory, "MinDEM.txt")
        self.pe = os.path.join(run.directory, "PE.txt")
        self.rain = os.path.join(run.directory, "Rain.txt")
        self.veg = os.path.join(run.directory, "LandCover.txt")
        self.soil = os.path.join(run.directory, "Soil.txt")
        self.lakes = os.path.join(run.directory, "Lakes.txt")
        self.rain_timeseries = os.path.join(run.directory, "RainTimeSeries.csv")
        self.observed_flow = os.path.join(os.path.join(run.directory, "FlowData{}-{}.csv"
                                                       .format(run.start_date.replace("-", "."),
                                                               run.end_date.replace("-", "."))))
        self.mask = os.path.join(run.directory, "Mask.txt")
        self.min_temp_timeseries = os.path.join(run.directory, "MinTempTimeSeries.csv")
        self.max_temp_timeseries = os.path.join(run.directory, "MaxTempTimeSeries.csv")
        self.pe_timeseries = os.path.join(run.directory, "PeTimeSeries.csv")
        self.simulated_discharge = "SimulatedDischarge.txt"


class Inputs:
    def __init__(self, run):
        self.dem = "../Inputs/{0}BngMaps/{0}DtmBng.txt".format(run.resolution)
        self.min_dem = "../Inputs/{0}BngMaps/{0}MinDtmBng.txt".format(run.resolution)
        self.soil = "../Inputs/{0}BngMaps/{0}SoilBng.txt".format(run.resolution)
        self.veg = "../Inputs/{0}BngMaps/{0}LcmBng.txt".format(run.resolution)
        self.pe = "../Inputs/{0}BngMaps/{0}PeRainBng.txt".format(run.resolution)
        self.rain = "../Inputs/{0}BngMaps/{0}PeRainBng.txt".format(run.resolution)
        self.lakes = "../Inputs/1kmBngMaps/lakes1kmBNG.txt"
        if run.upload is None:
            self.mask = "../Inputs/{0}BngMasks/{1}.txt".format(run.resolution, run.gauge_id)
        else:
            self.mask = None


class Run:
    def __init__(
            self,
            gauge_id,
            resolution,
            start_date,
            end_date,
            upload=None
    ):
        """start and end dates must be formatted YYYY-MM-DD and resolution is either '1km', '500m' or '100m'"""
        self.gauge_id = gauge_id
        self.resolution = resolution
        self.start_date = start_date
        self.end_date = end_date
        self.directory = os.path.join('outputs', str(self.gauge_id))

        if os.path.exists(self.directory):
            shutil.rmtree(self.directory)
        os.mkdir(self.directory)

        self.upload = upload
        self.outputs = Outputs(self)
        self.inputs = Inputs(self)
        self.lakes_exist = os.path.exists(self.inputs.lakes)

        resolution_lookup = {'1km': 1000,
                             '500m': 500,
                             '100m': 100}

        self.resolution_in_metres = resolution_lookup[self.resolution]


