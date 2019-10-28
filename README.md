# NDVI_calculation
This repository features a Python script that calculates the NDVI of an automatically downloaded satellite image at two different points in time.

## Dependencies
-Version: Python 3.7.4<br/>
-Installation: conda create -n name_of_environment python=3 numpy rasterio satsearch

## Usage
python ndvi.py output_ndvi1.tif output_ndvi2.tif output_difference.tif latitude longitude latitude longitude YYYY-MM-DD YYYY-MM-DD meters meters
###### Example
python ndvi.py ndvi1.tif ndvi2.tif difference.tif 52.868683 9.842292 52.604698 10.336440 2013-08-24 2018-08-06 1000 1000