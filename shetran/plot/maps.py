from ..hdf import Hdf
from..dem import Dem
import gdal, osr
import numpy as np
from matplotlib import pyplot as plt
import os


def extract_elevation(h5_file, out_dir, dem):
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    h5 = Hdf(h5_file)
    dem = Dem(dem)

    elevation = np.full(h5.sv4_numbering.shape, np.nan).flatten()
    se = h5.surface_elevation
    n = h5.number
    na = -1

    flat_numbers = h5.sv4_numbering[:].flatten()

    for surface, number in [
        [se.square, n.square],
        [se.north_link, n.north_link],
        [se.east_link, n.east_link],
        [se.south_link, n.south_link],
        [se.west_link, n.west_link]
    ]:

        unique, inverse = np.unique(flat_numbers, return_inverse=True)

        unique_elevations = np.full(unique.shape, np.nan)
        unique_elevations[np.searchsorted(unique, number[number!=na])] = surface[surface!=na]
        all_elevations = unique_elevations[inverse]
        elevation[~np.isnan(all_elevations)] = all_elevations[~np.isnan(all_elevations)]

    elevation = elevation.reshape(h5.sv4_numbering.shape)


    cell_size_factor = h5.sv4_elevation.shape[0]/h5.surface_elevation.square.shape[0]
    cell_size = dem.cell_size / cell_size_factor

    plt.imshow(elevation)
    plt.show()

    driver = gdal.GetDriverByName('GTiff')
    output_path = os.path.join(out_dir, 'elevations.tif')
    ds = driver.Create(output_path, elevation.shape[1], elevation.shape[0], 1, gdal.GDT_Float32)
    ds.SetGeoTransform((dem.x_lower_left - dem.cell_size,
                        cell_size, 0, dem.y_lower_left+cell_size*h5.sv4_elevation.shape[0]-dem.cell_size, 0, -1 * cell_size))


    band = ds.GetRasterBand(1)
    band.WriteArray(elevation)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(27700)
    ds.SetProjection(srs.ExportToWkt())
    band.FlushCache()

    asc_driver = gdal.GetDriverByName('AAIGrid')
    asc = asc_driver.CreateCopy(os.path.join(out_dir, 'elevations.asc'), ds, 0)
    asc.SetProjection(srs.ExportToWkt())
    asc.FlushCache()


def element_numbers(h5_file, out_dir, dem):
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    h5 = Hdf(h5_file)
    dem = Dem(dem)

    numbers = np.array(h5.sv4_numbering, dtype=float)
    numbers[numbers == 0] = np.nan

    cell_size_factor = h5.sv4_elevation.shape[0]/h5.surface_elevation.square.shape[0]

    cell_size = dem.cell_size / cell_size_factor

    plt.imshow(numbers)
    plt.show()

    driver = gdal.GetDriverByName('GTiff')
    output_path = os.path.join(out_dir, 'numbers.tif')
    ds = driver.Create(output_path, numbers.shape[1], numbers.shape[0], 1, gdal.GDT_Float32)
    ds.SetGeoTransform((dem.x_lower_left - dem.cell_size,
                        cell_size, 0, dem.y_lower_left+cell_size*numbers.shape[0]-dem.cell_size, 0, -1 * cell_size))

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

