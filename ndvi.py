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

#search and download satellite images
search = Search(bbox=[11.264539,48.041888, 11.378214,47.804930],
               datetime='2018-02-01/2018-03-04',
               property=["eo:cloud_cover<5"])

items = search.items()

for item in items:
    print(item)

#Check if image was found, otherwise stop here
try:
    item1 = items[2]
except:
    print("No image found")
    sys.exit()

item1_band4_url = item1.assets["B4"]["href"]    #red
item1_band5_url = item1.assets["B5"]["href"]    #NIR


#hier kommt funktion für tiling

window = rio.windows.Window(3000, 5000, 1000, 1000)

with rio.open(item1_band4_url) as src:
    #affine = src.transform
    band4 = src.read(1, window=window)
    affine = src.transform

with rio.open(item1_band5_url) as src:
    #affine = src.transform
    band5 = src.read(1, window=window)

# Allow division by zero
numpy.seterr(divide='ignore', invalid='ignore')

# Calculate NDVI
ndvi = (band5.astype(float) - band4.astype(float)) / (band5 + band4)
    
plt.imshow(ndvi)



#Zuerst wird das Raster erstellt mit driver, width, height, count und dtype
#Anschließend wird das Raster gefüllt, Window funktion gibt an, wie das Raster ausgefüllt werden soll
#   In dem Fall soll das Band so groß sein wie das geschriebene Raster
with rio.open('example.tif', 'w', driver='GTiff', width=1000, height=1000, count=1, dtype=ndvi.dtype) as dst:
    dst.write(ndvi, window = rio.windows.Window(0, 0, 1000, 1000), indexes=1)
