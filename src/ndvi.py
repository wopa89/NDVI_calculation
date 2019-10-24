# -*- coding: utf-8 -*-
"""
Created on Mon Aug 19 11:21:55 2019

@author: Pascal
"""

from satsearch import Search
from itertools import product
from rasterio import warp
import numpy as np
import rasterio as rio
import sys
from time import time

#Function for tiles calculation
def calc_tiles(raster, tile_x, tile_y):
    """This function creates rasterio windows for a raster band 
    with the pixel size of tile_x x tile_y
    Parameter: Raster band, tile width in meter, tile height in meter,
    Returns: Rasterio window"""
    
    #get coordinates of upper left corner
    x_upper_left = raster.transform[2]
    y_upper_left = raster.transform[5]
    #calculate width and height based on tile_x and tile_y
    x,y = x_upper_left + tile_x, y_upper_left - tile_y
    height, width = raster.index(x,y)
    
    #get cols and rows of raster band
    ncols, nrows = raster.meta['width'], raster.meta['height']
    #create offsets for window processing
    subsets = product(range(0, ncols, width), range(0, nrows, height))
    #create bounding_window to fill missing windows
    bounding_window = rio.windows.Window(col_off=0, row_off=0, width=ncols, height=nrows)
    
    #create windows
    for col_off, row_off in subsets:
        #yield windows with the given parameters
        window = rio.windows.Window(col_off=col_off, row_off=row_off, 
                                    width=width, height=height).intersection(bounding_window)
        yield window

#Function for writing ndvi calculated rasters
def tiled_writing(red, nir, output):
    """This function writes ndvi calculated rasterfiles based on the tiled windows
    Parameter: Red band, near-infrared band, output raster
    Return: NDVI calculated raster"""
    
    #open datasets
    src_red = rio.open(red)
    src_nir = rio.open(nir)
           
    #define raster properies and update datatype
    meta = src_red.meta.copy()
    meta.update({'dtype':'float32'}) # meta is a dictionary
    outfile = output
    #open outfile in writing mode with the properties of defined raster band
    with rio.open(outfile, 'w', **meta) as dst:
        #iterate over blocks of the bands, calculate ndvi for each block 
        #   and put the blocks back together
        for window in calc_tiles(src_red, tile_size_x, tile_size_y):
            red_block = src_red.read(window=window, masked=True)
            nir_block = src_nir.read(window=window, masked=True)
            #cast ndarrays to Float32 type
            red = red_block.astype('f4')
            nir = nir_block.astype('f4')
            #allow division by zero
            np.seterr(divide='ignore', invalid='ignore')
            #calculate ndvi and write raster
            ndvi = (nir - red) / (nir + red)
            dst.write(ndvi, window=window)

    #close dataset
    src_red.close()
    src_nir.close()
    return outfile

#Function for calculating the difference of two rasters
def calc_difference(ndvi_tile1, ndvi_tile2, output):
    """This function calculates the difference of two rasters
    Parameter: Two ndvi calculated rasters, output raster"""
    
    #open dataset and get Affine transformation and bounding properties 
    with rio.open(ndvi1) as src1:
        meta = src1.meta.copy()
        transform = src1.meta["transform"]
        x = meta['width']
        y = meta['height']
        band1 = src1.read()
    
    #open dataset    
    with rio.open(ndvi2) as src2:
        #read the band as ndarray with the same dimension of src1
        band2 = src2.read(out_shape=(src1.height, src1.width), 
                               resampling=rio.enums.Resampling.bilinear)
        #create destination for reprojection of src2
        dst_crs = {'init': 'EPSG:32632'}
        proj_band2 = np.empty(src1.shape, dtype=np.float32)
        #reproject the src2 to match src1
        warp.reproject(band2, destination=proj_band2, src_transform=src2.transform, src_crs=src2.crs, 
                       dst_transform=transform, dst_crs=dst_crs)                        
    
    #calculate difference between reprojected band2 and band1
    difference = np.subtract(proj_band2, band1)
    #create outfile
    outfile = output
    #write outfile with the properties and resolution of src1
    with rio.open(outfile, 'w', **meta) as dst:
        dst.write(difference, window=rio.windows.Window(col_off=0, row_off=0, width=x, height=y))

    return outfile

#Check who many input arguments the user has given
if len(sys.argv) < 11:
    print("Usage: python ndvi.py output_ndvi1.tif output_ndvi2.tif output_difference.tif longitude latitude longitude latitude YYYY-MM-DD YYYY-MM-DD meters meters")
    sys.exit(1)

#check the user input arguments
try:
    ndvi1_output = str(sys.argv[1])
    ndvi2_output = str(sys.argv[2])
    end_output   = str(sys.argv[3])
except ValueError:
    print("Output must be string values")
    sys.exit(1)

try:
    lat_left   = float(sys.argv[4])
    long_left  = float(sys.argv[5])
    lat_right  = float(sys.argv[6])
    long_right = float(sys.argv[7])
except ValueError:
    print("Coordinates must be float values")
    sys.exit(1)

try:
    date1 = str(sys.argv[8])
    date2 = str(sys.argv[9])
except ValueError:
    print("Dates must be string! Usage: YYYY-MM-DD")
    sys.exit(1)

try:
    tile_size_x = int(sys.argv[10])
    tile_size_y = int(sys.argv[11])
except:
    print("Tile size must be integer values!")
    sys.exit(1)

#check how much time the process took
time_start = time()

#search and download satellite images
search1 = Search(bbox=[str(long_left),str(lat_left), str(long_right),str(lat_right)],
               datetime=date1,
               property=["eo:cloud_cover<5"])
items1 = search1.items()
search2 = Search(bbox=[str(long_left),str(lat_left), str(long_right),str(lat_right)],
               datetime=date2,
               property=["eo:cloud_cover<5"])
items2 = search2.items()

#Loop through the items list and search for landsat scene
#   as sentinel scenes throws an error message
for item in items1:
    item_prop = item.properties["collection"]
    if item_prop.startswith("landsat"):
        item1_band4_url = item.assets["B4"]["href"]    #red
        item1_band5_url = item.assets["B5"]["href"]    #NIR
        i1 = item
        break
    else:
        continue
for item in items2:
    item_prop = item.properties["collection"]
    if item_prop.startswith("landsat"):
        item2_band4_url = item.assets["B4"]["href"]    #red
        item2_band5_url = item.assets["B5"]["href"]    #NIR
        i2 = item
        break
    else:
        continue

#Check if landsat scene was found, otherwise stop here
try:
    item1_found = item1_band4_url[0]
    item2_found = item2_band4_url[0]
except:
    print("No landsat scene found")
    sys.exit(1)

#run tiled_writing function for first landsat scene
ndvi1 = tiled_writing(item1_band4_url, item1_band5_url, ndvi1_output)
print("Calculated NDVI for scene %s." % (i1))
#run tiled_writing function for second landsat scene
ndvi2 = tiled_writing(item2_band4_url, item2_band5_url, ndvi2_output)
print("Calculated NDVI for scene %s." % (i2))

#run calc_difference function for first and second output
calc_difference(ndvi1, ndvi2, end_output)
print("Calculated difference between scene %s and scene %s!" % (i2,i1))

#check how much time the process took
time_end = time()
print('Process took %i seconds' % (time_end-time_start))

print("Calculation done!")
