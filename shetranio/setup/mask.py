from osgeo import gdal, ogr
import os
import zipfile
import math
import numpy as np

def create(outline: str, resolution: int, output_path: str) -> None:
    """
    Converts a vector catchment outline to a gridded mask at specified resolution
    Mask output is aligned to coordinates 0 0
    Any grid cells intersected by the geometry are designated as within the domain

    :param outline: path to a zipped shapefile, must contain one feature
    :param resolution: resolution of the output mask in metres
    :param output_path: location to save the created tiff file
    """
    zipped_file = zipfile.ZipFile(outline, 'r')
    shp = [f.filename for f in zipped_file.infolist() if f.filename.endswith('shp')][0]
    for f in zipped_file.infolist():
        gdal.FileFromMemBuffer(os.path.join('/vsimem', f.filename), bytes(zipped_file.read(f.filename)))

    upload = ogr.Open(os.path.join('/vsimem', shp))

    layer = upload.GetLayer()

    feature = layer.GetNextFeature()
    geom = feature.GetGeometryRef()
    minX, maxX, minY, maxY = geom.GetEnvelope()

    minX = math.floor(minX / resolution) * resolution
    maxX = math.ceil(maxX / resolution) * resolution
    minY = math.floor(minY / resolution) * resolution
    maxY = math.ceil(maxY / resolution) * resolution

    width = int((maxX - minX) / resolution)
    height = int((maxY - minY) / resolution)

    driver = gdal.GetDriverByName('GTiff')
    target_ds = driver.Create(output_path+'.tif', width, height, 1, gdal.GDT_Float32)
    target_ds.SetGeoTransform((minX, resolution, 0, maxY, 0, -1*resolution))

    no_data = -9999
    band = target_ds.GetRasterBand(1)
    band.WriteArray(np.full([height, width], no_data))
    band.FlushCache()
    band.SetNoDataValue(no_data)
    del target_ds

    target_ds = gdal.Open(output_path + '.tif', gdal.GA_Update)
    gdal.RasterizeLayer(target_ds, [1], layer, burn_values=[1], options=['ALL_TOUCHED=TRUE'])
    target_ds.FlushCache()

    # Convert to ASCII grid
    driver = gdal.GetDriverByName("AAIGrid")
    driver.CreateCopy(output_path, target_ds, 0)

def extract(mask_path: str, input_path: str, output_path: str, resolution: int) -> None:
    """
    Input data and mask must aligned to the same coordinate grid

    :param mask_path: path to mask file in GDAL recognised format
    :param input_path: path to input data in GDAL recognised format
    :param output_path: path to output data in GDAL recognised format
    :param resolution: resolution of
    """
    mask_file = open(mask_path, "r")

    n_cols_line = mask_file.readline()
    n_cols_list = n_cols_line.rstrip().split()
    n_cols = float(n_cols_list[1])

    n_rows_line = mask_file.readline()
    n_rows_list = n_rows_line.rstrip().split()
    n_rows = float(n_rows_list[1])

    bx_line = mask_file.readline()
    bx_list = bx_line.rstrip().split()
    x_lower_left_corner = float(bx_list[1])

    by_line = mask_file.readline()
    by_list = by_line.rstrip().split()
    y_lower_left_corner = float(by_list[1])

    mask_file.close()
    ds = gdal.Open(input_path)

    start_line_number = ds.RasterYSize - y_lower_left_corner / resolution - n_rows
    start_index_number = x_lower_left_corner / resolution

    gdal.Translate(output_path,
                   ds,
                   srcWin=
                   [
                       start_index_number,
                       start_line_number,
                       n_cols,
                       n_rows
                   ],
                   format='AAIGrid')
