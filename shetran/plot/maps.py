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

    elevation = np.full(h5.sv4_numbering.shape, np.nan)
    se = h5.surface_elevation
    n = h5.number
    na = -1


    for surface, number in [
        [se.square, n.square],
        [se.north_bank, n.north_bank],
        [se.east_bank, n.east_bank],
        [se.south_bank, n.south_bank],
        [se.west_bank, n.west_bank],
        [se.north_link, n.north_link],
        [se.east_link, n.east_link],
        [se.south_link, n.south_link],
        [se.west_link, n.west_link]
    ]:
        for idx, elev in enumerate(surface[surface != na]):
            elevation[h5.sv4_numbering[:] == number[number != na][idx]] = elev

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
    print(numbers.shape)
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

