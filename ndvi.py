# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 14:46:43 2019

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

#hier kommt funktion für tiling


#read the red and nir band 
with rio.open(item_band4_url) as src:
    oviews = src.overviews(1) # list of overviews from biggest to smallest
    oview = oviews[1]  # Use second-highest resolution overview
    band4 = src.read(1, out_shape=(1, int(src.height // oview), int(src.width // oview)))

with rio.open(item_band5_url) as src:
    oviews = src.overviews(1) # list of overviews from biggest to smallest
    oview = oviews[1]  # Use second-highest resolution overview
    band5 = src.read(1, out_shape=(1, int(src.height // oview), int(src.width // oview)))

#allow division by zero
numpy.seterr(divide='ignore', invalid='ignore')

#call function
ndvi = calc_ndvi(band5,band4)

#write raster
localname = 'example.tif'
#modify the original metadata to fit the subsampled overview
with rio.open(item_band5_url) as src:
    profile = src.profile.copy()

    aff = src.transform
    newaff = rio.Affine(aff.a * oview, aff.b, aff.c, aff.d, aff.e * oview, aff.f)
    profile.update({
            'dtype': 'float32',
            'height': ndvi.shape[0],
            'width': ndvi.shape[1],
            'transform': newaff})  

    with rio.open(localname, 'w', **profile) as dst:
        dst.write_band(1, ndvi)

#reopen and plotting raster
datetime='2018-08-06'
with rio.open(localname) as src:
    print(src.profile)
    ndvi = src.read(1) # read the entire array

plt.imshow(ndvi, cmap='RdYlGn')
plt.colorbar()
plt.title('NDVI {}'.format(datetime))
plt.xlabel('Column #')
plt.ylabel('Row #')
