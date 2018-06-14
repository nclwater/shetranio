import subprocess
import os
from datetime import datetime
import netCDF4 as nc
import gdal
import numpy as np


def download_ceh_gear(username, password, output_directory=None, start=1890, end=2016):
    base_url = "https://catalogue.ceh.ac.uk/datastore/eidchub/33604ea0-c238-4488-813d-0ad9ab7c51ca/GB/daily/"

    for year in range(start, end):

        filename = "CEH_GEAR_daily_GB_{}.nc".format(year)

        url = base_url + filename

        if output_directory is not None:
            output_file = os.path.join(output_directory, filename)
        else:
            output_file = filename

        subprocess.call(["curl", "--user", "{}:{}".format(username, password),  url, "-o", output_file])


def extract(data_path: str,
            variable: str,
            mask_path: str,
            start_date: datetime,
            end_date: datetime,
            grid_path: str,
            ts_path: str) -> None:

    mask = gdal.Open(mask_path)

    x_min, x_res, x_skew, y_max, y_skew, y_res = mask.GetGeoTransform()

    mask_width = mask.RasterXSize
    mask_height = mask.RasterYSize

    x_max = x_min + (mask_width * x_res)
    y_min = y_max + (mask_height * y_res)
    no_data = mask.GetRasterBand(1).GetNoDataValue()

    mask_x = np.arange(x_min, x_max + x_res, x_res)
    mask_y = np.arange(y_min, y_max + x_res, x_res)

    mask_y_idx, mask_x_idx = np.where(mask.ReadAsArray()!=no_data)

    mask_y_selected = mask_y[mask_y_idx]
    mask_x_selected = mask_x[mask_x_idx]

    nearest = lambda a, v: a[(np.abs(a - v)).argmin()]

    ds = nc.Dataset(data_path)

    data_x = ds.variables['x'][:]
    data_y = ds.variables['y'][:]

    data_y_selected = [nearest(data_y, y_val) for y_val in mask_y_selected]
    data_x_selected = [nearest(data_x, x_val) for x_val in mask_x_selected]

    data_y_mask = np.isin(data_y, data_y_selected)
    data_x_mask = np.isin(data_x, data_x_selected)

    time = ds.variables['time']

    dates = nc.num2date(time[:], time.units, time.calendar)
    dates_mask = (dates>=start_date)&(dates<=end_date)

    values = ds.variables[variable][dates_mask, data_y_mask, data_x_mask]

    data_unique_x = np.unique(data_y_selected).astype(int)
    data_unique_y = np.unique(data_x_selected).astype(int)

    output = np.full((mask_height, mask_width), no_data).astype(int)

    series = []
    cells = {}
    number = 1

    for i in range(len(mask_x_selected)):

        data_y = data_y_selected[i]
        data_x = data_x_selected[i]
        x = mask_x_selected[i]
        y = mask_y_selected[i]

        if (data_x, data_y) not in cells:
            series.append( values[:, np.where(data_unique_x == data_y)[0][0], np.where(data_unique_y == data_x)[0][0]])
            cells[(data_x, data_y)] = number
            number += 1

        output[np.where(mask_y==y), np.where(mask_x==x)] = cells[(data_x, data_y)]

    driver = gdal.GetDriverByName("GTiff")
    tif_path = grid_path + '.tif'
    grid = driver.CreateCopy(tif_path, mask, 0)
    grid.GetRasterBand(1).WriteArray(output)
    print(grid.ReadAsArray().astype(int))

    driver = gdal.GetDriverByName("AAIGrid")
    driver.CreateCopy(grid_path, grid, 0)

    with open(ts_path, 'w') as f:
        f.write(','.join(np.arange(1, len(series)+1).astype(str))+'\n')
        for i in range(len(series[0])):
            f.write(','.join([str(cell_series[i]) for cell_series in series])+'\n')
