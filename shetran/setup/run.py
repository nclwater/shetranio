import os
import shutil


class Outputs:
    def __init__(self, run):
        self.dem = os.path.join(run.path, "DEM.txt")
        self.min_dem = os.path.join(run.path, "MinDEM.txt")
        self.pe = os.path.join(run.path, "PE.txt")
        self.rain = os.path.join(run.path, "Rain.txt")
        self.veg = os.path.join(run.path, "LandCover.txt")
        self.soil = os.path.join(run.path, "Soil.txt")
        self.lakes = os.path.join(run.path, "Lakes.txt")
        self.rain_timeseries = os.path.join(run.path, "RainTimeSeries.csv")
        self.observed_flow = os.path.join(os.path.join(run.path, "FlowData{}-{}.csv"
                                                       .format(run.start_date.replace("-", "."),
                                                               run.end_date.replace("-", "."))))
        self.mask = os.path.join(run.path, "Mask.txt")
        self.min_temp_timeseries = os.path.join(run.path, "MinTempTimeSeries.csv")
        self.max_temp_timeseries = os.path.join(run.path, "MaxTempTimeSeries.csv")
        self.pe_timeseries = os.path.join(run.path, "PeTimeSeries.csv")
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
        if run.boundary is None:
            self.mask = "../Inputs/{0}BngMasks/{1}.txt".format(run.resolution, run.gauge_id)
        else:
            self.mask = None


class Run:
    def __init__(
            self,
            resolution,
            start_date,
            end_date,
            gauge_id=None,
            boundary=None,
            path=None,
            overwrite=True
    ):
        """start and end dates must be formatted YYYY-MM-DD and resolution is either '1km', '500m' or '100m'"""
        self.gauge_id = gauge_id
        self.resolution = resolution
        self.resolution.f = 3
        self.start_date = start_date
        self.end_date = end_date
        self.path = os.path.join('outputs', str(self.gauge_id)) if path is None else path


        if os.path.exists(self.path) and overwrite:
            shutil.rmtree(self.path)
            
        if not os.path.exists(path):
            os.mkdir(path)
            
        self.boundary = boundary
        self.outputs = Outputs(self)
        self.inputs = Inputs(self)
        self.lakes_exist = os.path.exists(self.inputs.lakes)

        resolution_lookup = {'1km': 1000,
                             '500m': 500,
                             '100m': 100}

        self.resolution_in_metres = resolution_lookup[self.resolution]


