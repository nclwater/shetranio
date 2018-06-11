from osgeo import gdal, ogr
import os
import zipfile
import math
import numpy as np

def create(outline: str, resolution: int, output_path: str) -> None:
    """
    Converts a vector catchment outline to a gridded mask at specified resolution
    Needs to be aligned to same coordinates as DEM / other data

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

    minX = math.floor(minX / resolution)*resolution
    maxX = math.ceil(maxX / resolution)*resolution
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
