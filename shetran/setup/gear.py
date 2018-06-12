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
            mask_path: str,
            start_date: datetime,
            end_date: datetime,
            grid_path: str,
            ts_path: str) -> None:

    mask = gdal.Open(mask_path)

    x_min, x_res, x_skew, y_max, y_skew, y_res = mask.GetGeoTransform()

    ncols = mask.RasterXSize
    nrows = mask.RasterYSize

    x_max = x_min + (ncols * x_res)
    y_min = y_max + (nrows * y_res)
    no_data = mask.GetRasterBand(1).GetNoDataValue()

    mask_x = np.arange(x_min, x_max + x_res, x_res)
    mask_y = np.arange(y_min, y_max + x_res, x_res)

    mask_y_idx, mask_x_idx = np.where(mask.ReadAsArray()!=no_data)

    mask_y_coords = mask_y[mask_y_idx]
    mask_x_coords = mask_x[mask_x_idx]

    nearest = lambda a, v: a[(np.abs(a - v)).argmin()]

    ds = nc.Dataset(data_path)

    ds_x = ds.variables['x'][:]
    ds_y = ds.variables['y'][:]

    data_y_coords = [nearest(ds_y, y_val) for y_val in mask_y_coords]
    data_x_coords = [nearest(ds_x, x_val) for x_val in mask_x_coords]

    data_y_mask = np.isin(ds_y, data_y_coords)
    data_x_mask = np.isin(ds_x, data_x_coords)


    values = ds.variables['rainfall_amount'][:3, data_y_mask, data_x_mask]

    y_vals = np.unique(data_y_coords).astype(int)
    x_vals = np.unique(data_x_coords).astype(int)

    output = np.full((ncols, nrows), no_data).astype(int)

    series = []

    for i in range(len(mask_x_coords)):

        data_y = data_y_coords[i]
        data_x = data_x_coords[i]
        x = mask_x_coords[i]
        y = mask_y_coords[i]
        vals = values[:, np.where(y_vals==data_y)[0][0],np.where(x_vals==data_x)[0][0]]
        series.append(vals)
        output[np.where(mask_y==y), np.where(mask_x==x)] = i+1

    driver = gdal.GetDriverByName("GTiff")
    grid = driver.CreateCopy(grid_path, mask, 0)
    grid.GetRasterBand(1).WriteArray(output)
    print(grid.ReadAsArray().astype(int))

    driver = gdal.GetDriverByName("AAIGrid")
    driver.CreateCopy(grid_path, grid, 0)

    with open(ts_path, 'w') as f:
        f.write(','.join(np.arange(1, len(series)+1).astype(str))+'\n')
        for i in range(len(series[0])):
            f.write(','.join([str(cell_series[i]) for cell_series in series])+'\n')
