from ..hdf import Hdf
from..dem import Dem
import gdal, osr
import numpy as np
from matplotlib import pyplot as plt
import os


def extract_elevation(h5_file, out_dir, dem):
    h5 = Hdf(h5_file)
    dem = Dem(dem)


    max_elevation = h5.surface_elevation.square.max()
    min_elevation = h5.surface_elevation.square[h5.surface_elevation.square!=-1].min()
    scaled_elevations = np.array(h5.sv4_elevation, dtype=float)
    scaled_elevations[scaled_elevations==0] = np.nan


    scaled_elevations /= 256
    scaled_elevations *= (max_elevation-min_elevation)
    scaled_elevations += min_elevation
    cell_size = (dem.x_coordinates.max() - dem.x_coordinates.min()) / scaled_elevations.shape[1]

    plt.imshow(scaled_elevations)
    plt.show()

    driver = gdal.GetDriverByName('GTiff')
    output_path = os.path.join(out_dir, 'elevations.tif')
    ds = driver.Create(output_path, scaled_elevations.shape[1], scaled_elevations.shape[0], 1, gdal.GDT_Float32)
    ds.SetGeoTransform((dem.x_coordinates.min(), cell_size, 0, dem.y_coordinates.max(), 0, -1 * cell_size))


    band = ds.GetRasterBand(1)
    band.WriteArray(scaled_elevations)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(27700)
    ds.SetProjection(srs.ExportToWkt())
    band.FlushCache()

    asc_driver = gdal.GetDriverByName('AAIGrid')
    asc = asc_driver.CreateCopy(os.path.join(out_dir, 'elevations.asc'), ds, 0)
    asc.SetProjection(srs.ExportToWkt())
    asc.FlushCache()


def element_numbers(h5_file, out_dir, dem):
    h5 = Hdf(h5_file)
    dem = Dem(dem)

    numbers = np.array(h5.sv4_numbering, dtype=float)
    numbers[numbers == 0] = np.nan

    cell_size = (dem.x_coordinates.max() - dem.x_coordinates.min()) / numbers.shape[1]

    plt.imshow(numbers)
    plt.show()

    driver = gdal.GetDriverByName('GTiff')
    output_path = os.path.join(out_dir, 'numbers.tif')
    ds = driver.Create(output_path, numbers.shape[1], numbers.shape[0], 1, gdal.GDT_Float32)
    ds.SetGeoTransform((dem.x_coordinates.min(), cell_size, 0, dem.y_coordinates.max(), 0, -1 * cell_size))

    band = ds.GetRasterBand(1)
    band.WriteArray(numbers)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(27700)
    ds.SetProjection(srs.ExportToWkt())
    band.FlushCache()

    asc_driver = gdal.GetDriverByName('AAIGrid')
    asc = asc_driver.CreateCopy(os.path.join(out_dir, 'numbers.asc'), ds, 0)
    asc.SetProjection(srs.ExportToWkt())
    asc.FlushCache()

