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
search1 = Search(bbox=[9.842292,52.868683, 10.336440,52.604698],
               datetime='2018-08-06',
               property=["eo:cloud_cover<5"])
items1 = search1.items()
search2 = Search(bbox=[9.842292,52.868683, 10.336440,52.604698],
               datetime='2013-08-24',
               property=["eo:cloud_cover<5"])
items2 = search2.items()

#Loop through the items list and search for landsat scene
#   as sentinel scenes throws an error message
for item in items1:
    item_prop = item.properties["collection"]
    if item_prop.startswith("landsat"):
        item1_band4_url = item.assets["B4"]["href"]    #red
        item1_band5_url = item.assets["B5"]["href"]    #NIR
        break
    else:
        continue
for item in items2:
    item_prop = item.properties["collection"]
    if item_prop.startswith("landsat"):
        item2_band4_url = item.assets["B4"]["href"]    #red
        item2_band5_url = item.assets["B5"]["href"]    #NIR
        break
    else:
        continue

#Check if landsat scene was found, otherwise stop here
try:
    item1_found = item1_band4_url[0]
    item2_found = item2_band4_url[0]
except:
    print("No landsat scene found")
    sys.exit()

#hier kommt funktion für tiling

#create bounding box and convert geographic coordinates to image coordinates
with rio.open(item1_band4_url) as src:
    affine1 = src.transform
    print(affine1)
    xmin1 = affine1[2] + 45000
    xmax1 = affine1[2] + 65000
    ymin1 = affine1[5] - 50000
    ymax1 = affine1[5] - 30000
    col_start1, row_start1 = ~affine1 * (xmin1, ymax1)
    col_end1, row_end1 = ~affine1 * (xmax1, ymin1)
#create bounding box and convert geographic coordinates to image coordinates
with rio.open(item2_band4_url) as src:
    affine2 = src.transform
    print(affine2)
    xmin2 = affine1[2] + 45000
    xmax2 = affine1[2] + 65000
    ymin2 = affine1[5] - 50000
    ymax2 = affine1[5] - 30000
    col_start2, row_start2 = ~affine2 * (xmin2, ymax2)
    col_end2, row_end2 = ~affine2 * (xmax2, ymin2)

#create window with image coordinates
with rio.open(item1_band4_url) as src:
    item1_band4 = src.read(1, window=((int(row_start1), int(row_end1)), (int(col_start1), int(col_end1)) )) #
with rio.open(item1_band5_url) as src:
    item1_band5 = src.read(1, window=((int(row_start1), int(row_end1)), (int(col_start1), int(col_end1)) )) #
#create window with image coordinates
with rio.open(item2_band4_url) as src:
    item2_band4 = src.read(1, window=((int(row_start2), int(row_end2)), (int(col_start2), int(col_end2)) )) #
with rio.open(item2_band5_url) as src:
    item2_band5 = src.read(1, window=((int(row_start2), int(row_end2)), (int(col_start2), int(col_end2)) ))

    
#allow division by zero
numpy.seterr(divide='ignore', invalid='ignore')

#call function
ndvi1 = calc_ndvi(item1_band5,item1_band4)
ndvi2 = calc_ndvi(item2_band5,item2_band4)

#calculate difference
ndvi = ndvi1 - ndvi2

#plot rasters
fig, axes = plt.subplots(1,3, figsize=(14,6), sharex=True, sharey=True)
date1 = '2018-08-06'
date2 = '2013-08-24'

#plot ndvi date1
plt.sca(axes[0])
plt.imshow(ndvi2, cmap='RdYlGn', vmin=-1, vmax=1)
plt.colorbar(shrink=0.5)
plt.title('NDVI {}'.format(date2))
plt.xlabel('Column #')
plt.ylabel('Row #')

#plot ndvi date2
plt.sca(axes[1])
plt.imshow(ndvi1, cmap='RdYlGn', vmin=-1, vmax=1)
plt.colorbar(shrink=0.5)
plt.title('NDVI {}'.format(date1))

#plot difference
plt.sca(axes[2])
plt.imshow(ndvi, cmap='bwr', vmin=-1, vmax=1)
plt.colorbar(shrink=0.5)
plt.title('Diff ({} - {})'.format(date1, date2))

#write raster
#get x,y pixel size
x = item1_band4.shape[0]
y = item1_band4.shape[1]

localname = 'example.tif'
#Zuerst wird das Raster erstellt mit driver, width, height, count und dtype
#Anschließend wird das Raster gefüllt, Window funktion gibt an, wie das Raster ausgefüllt werden soll
#   In dem Fall soll das Band so groß sein wie das geschriebene Raster
with rio.open(localname, 'w', driver='GTiff', width=x, height=y, count=1, dtype=ndvi.dtype) as dst:
    dst.write(ndvi, window = rio.windows.Window(0,0, x,y), indexes=1)
