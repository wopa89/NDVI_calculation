# -*- coding: utf-8 -*-
"""
Created on Mon Aug 19 11:21:55 2019

@author: Pascal
"""

from satsearch import Search
import rasterio as rio
import matplotlib.pyplot as plt


search = Search(bbox=[8.66744,49.41217,8.68465,49.42278],
               datetime='2018-02-01/2018-02-04',
               property=["eo:cloud_cover<5"])

items = search.items()

item1 = items[0]

item1_band5_url = item1.assets["B5"]["href"]

window = rio.windows.Window(5024, 5024, 1000, 1000)

with rio.open(item1_band5_url) as src:
    #affine = src.transform
    band = src.read(1, window=window)
    
plt.imshow(band)

#Zuerst wird das Raster erstellt mit driver, width, height, count und dtype
#Anschließend wird das Raster gefüllt, Window funktion gibt an, wie das Raster ausgefüllt werden soll
#   In dem Fall soll das Band so groß sein wie das geschriebene Raster
with rio.open('example.tif', 'w', driver='GTiff', width=1000, height=1000, count=1, dtype=band.dtype) as dst:
    dst.write(band, window = rio.windows.Window(0, 0, 1000, 1000), indexes=1)
