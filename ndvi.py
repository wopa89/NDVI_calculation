# -*- coding: utf-8 -*-
"""
Created on Mon Aug 19 11:21:55 2019

@author: Pascal
"""

from satsearch import Search
import rasterio as rio
import matplotlib.pyplot as plt
import numpy
import sys

#function for ndvi calculation
def calc_ndvi(nir,red):
    '''Calculate NDVI from integer arrays'''
    nir = nir.astype('f4')
    red = red.astype('f4')
    ndvi = (nir - red) / (nir + red)
    return ndvi

#search and download satellite images
search = Search(bbox=[9.842292,52.868683, 10.336440,52.604698],
               datetime='2018-08-06',
               property=["eo:cloud_cover<5"])
items = search.items()

#Loop through the items list and search for landsat scene
#   as sentinel scenes throws an error message
for item in items:
    item_prop = item.properties["collection"]
    if item_prop.startswith("landsat"):
        item_band4_url = item.assets["B4"]["href"]    #red
        item_band5_url = item.assets["B5"]["href"]    #NIR
        break
    else:
        continue

#Check if landsat scene was found, otherwise stop here
try:
    item_found = item_band4_url[0]
except:
    print("No landsat scene found")
    sys.exit()

#create bounding box and convert geographic coordinates to image coordinates
with rio.open(item_band4_url) as src:
    affine = src.transform
    print(affine)
    xmin = affine[2] + 45000
    xmax = affine[2] + 65000
    ymin = affine[5] - 50000
    ymax = affine[5] - 30000
    col_start, row_start = ~affine * (xmin, ymax)
    col_end, row_end = ~affine * (xmax, ymin)
    print(col_start, row_start)
    print(col_end, row_end)

#create window with image coordinates
with rio.open(item_band4_url) as src:
    band4 = src.read(1, window=((int(row_start), int(row_end)), (int(col_start), int(col_end)) )) #
    
with rio.open(item_band5_url) as src:
    band5 = src.read(1, window=((int(row_start), int(row_end)), (int(col_start), int(col_end)) )) #
    
#allow division by zero
numpy.seterr(divide='ignore', invalid='ignore')

#call function
ndvi = calc_ndvi(band5,band4)

#get x,y pixel size
x = band4.shape[0]
y = band4.shape[1]

localname = 'example.tif'
#Zuerst wird das Raster erstellt mit driver, width, height, count und dtype
#Anschließend wird das Raster gefüllt, Window funktion gibt an, wie das Raster ausgefüllt werden soll
#   In dem Fall soll das Band so groß sein wie das geschriebene Raster
with rio.open(localname, 'w', driver='GTiff', width=x, height=y, count=1, dtype=ndvi.dtype) as dst:
    dst.write(ndvi, window = rio.windows.Window(0,0, x,y), indexes=1)

#reopen and plotting raster
datetime='2018-08-06'
with rio.open(localname) as src:
    print(src.profile)
    ndvi = src.read(1) # read the entire array

plt.imshow(ndvi, cmap='RdYlGn')
plt.colorbar()
plt.title('Overview - Pixel {}'.format(band4.shape))
plt.xlabel('Column #')
plt.ylabel('Row #')
