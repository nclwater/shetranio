import operator
from osgeo import gdal, ogr
import os
import zipfile
import math
import shutil
import io

def create_mask(run):
    # Raster image to clip
    # Needs to be aligned to same coordinates as DEM / other data

    zip = zipfile.ZipFile(io.BytesIO(run.upload), 'r')
    shp = [f.filename for f in zip.infolist() if f.filename.endswith('shp')][0]
    for f in zip.infolist():
        gdal.FileFromMemBuffer(os.path.join('/vsimem', f.filename), bytes(zip.read(f.filename)))
    upload = ogr.Open(os.path.join('/vsimem', shp))

    layer = upload.GetLayer()

    feature = layer.GetNextFeature()
    geom = feature.GetGeometryRef()
    minX, maxX, minY, maxY = geom.GetEnvelope()

    minX = math.floor(minX / run.resolution_in_metres)*run.resolution_in_metres
    maxX = math.ceil(maxX / run.resolution_in_metres)*run.resolution_in_metres
    minY = math.floor(minY / run.resolution_in_metres) * run.resolution_in_metres
    maxY = math.ceil(maxY / run.resolution_in_metres) * run.resolution_in_metres

    x_res = int((maxX - minX) / run.resolution_in_metres)
    y_res = int((maxY - minY) / run.resolution_in_metres)

    # source_layer = data.GetLayer()
    driver = gdal.GetDriverByName('GTiff')
    target_ds = driver.Create(run.outputs.mask+'.tif', x_res, y_res, 1, gdal.GDT_Float32)
    target_ds.SetGeoTransform((minX, run.resolution_in_metres, 0, maxY, 0, -1*run.resolution_in_metres))

    NoData_value = -9999
    import numpy as np
    band = target_ds.GetRasterBand(1)
    band.WriteArray(np.full([y_res, x_res], NoData_value))
    band.FlushCache()
    band.SetNoDataValue(NoData_value)
    del target_ds
    target_ds = gdal.Open(run.outputs.mask + '.tif', gdal.GA_Update)
    gdal.RasterizeLayer(target_ds, [1], layer, burn_values=[1], options=['ALL_TOUCHED=TRUE'])
    target_ds.FlushCache()

    format = "AAIGrid"
    driver = gdal.GetDriverByName(format)

    # Output to new format
    driver.CreateCopy(run.outputs.mask, target_ds, 0)
