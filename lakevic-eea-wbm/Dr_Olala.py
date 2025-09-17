# -*- coding: utf-8 -*-
"""
Created on Fri Feb 14 11:17:00 2025

@author: VO000003
"""



#%%
# LAKE VICTORIA KENYAN PORTION SHAPEFILE

import geopandas as gpd
import matplotlib.pyplot as plt

# Load the shapefiles
kenya = gpd.read_file(r"C:\DATA\Dr. Olala Shapefile\kenya_Kenya_Country_Boundary_MAPOG\kenya_Kenya_Country_Boundary.shp")
lake_victoria_basin = gpd.read_file(r"C:\DATA\Dr. Olala Shapefile\Shapefile_final\LakeVictoria.shp")

# Ensure both shapefiles use the same CRS
if kenya.crs != lake_victoria_basin.crs:
    lake_victoria_basin = lake_victoria_basin.to_crs(kenya.crs)

# Perform the clipping operation
lake_victoria_kenya = gpd.overlay(lake_victoria_basin, kenya, how="intersection")

# Save the clipped shapefile
lake_victoria_kenya.to_file("lake_victoria_kenya.shp")

# Plot the results
fig, ax = plt.subplots(figsize=(10, 8))  # Enlarged figure size

# Plot Kenya boundary
kenya.plot(ax=ax, color="none", edgecolor="black", linewidth=1, label="Kenya Boundary")

# Plot entire Lake Victoria Basin
lake_victoria_basin.plot(ax=ax, color="lightblue", edgecolor="blue", alpha=0.5, label="Lake Victoria Basin")

# Plot clipped portion (Kenya side of the lake)
lake_victoria_kenya.plot(ax=ax, color="cyan", edgecolor="darkblue", linewidth=1.2, label="Lake Victoria (Kenyan Side)")

# Add title and labels
ax.set_title("Lake Victoria in Kenya", fontsize=14)
ax.set_xlabel("Longitude", fontsize=12)
ax.set_ylabel("Latitude", fontsize=12)

# Add grid and legend
ax.grid(True, linestyle="--", alpha=0.6)
ax.legend()

# Show the map
plt.show()

#%%


# Load the shapefiles
kenya = gpd.read_file(r"C:\DATA\Dr. Olala Shapefile\kenya_Kenya_Country_Boundary_MAPOG\kenya_Kenya_Country_Boundary.shp")
lake_victoria_basin = gpd.read_file(r"C:\DATA\Dr. Olala Shapefile\lv_basin_shape file\lv_basin.shp")

# Ensure both shapefiles use the same CRS
if kenya.crs != lake_victoria_basin.crs:
    lake_victoria_basin = lake_victoria_basin.to_crs(kenya.crs)

# Perform the clipping operation
lake_victoria_kenya = gpd.overlay(lake_victoria_basin, kenya, how="intersection")

# Save the clipped shapefile
lake_victoria_kenya.to_file("lake_victoria_basin_kenya.shp")

# Plot the results
fig, ax = plt.subplots(figsize=(10, 8))  # Enlarged figure size

# Plot Kenya boundary
kenya.plot(ax=ax, color="none", edgecolor="black", linewidth=1, label="Kenya Boundary")

# Plot entire Lake Victoria Basin
lake_victoria_basin.plot(ax=ax, color="lightblue", edgecolor="blue", alpha=0.5, label="Lake Victoria Basin")

# Plot clipped portion (Kenya side of the lake)
lake_victoria_kenya.plot(ax=ax, color="cyan", edgecolor="darkblue", linewidth=1.2, label="Lake Victoria (Kenyan Side)")

# Add title and labels
ax.set_title("Lake Victoria Basin in Kenya", fontsize=14)
ax.set_xlabel("Longitude", fontsize=12)
ax.set_ylabel("Latitude", fontsize=12)

# Add grid and legend
ax.grid(True, linestyle="--", alpha=0.6)
ax.legend()

# Show the map
plt.show()


#%%

import os
print(os.getcwd())

#%%



import ee

# Initialize Google Earth Engine
ee.Initialize()

# Load the shapefile (must be uploaded to GEE Assets)
kenya_lvb = ee.FeatureCollection("C:\DATA\Dr. Olala Shapefile\LV_basin_kenya\lake_victoria_basin_kenya.shp")

# Select the "occurrence" band (Percentage of time water was detected)
image = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence").clip(kenya_lvb)

# Export clipped image
task = ee.batch.Export.image.toDrive(
    image=image,
    description="LakeVictoria_WaterOccurrence",
    folder="GEE_Exports",
    fileNamePrefix="LakeVictoria_Occurrence",
    scale=30,
    region=kenya_lvb.geometry().bounds(),
    fileFormat="GeoTIFF"
)

task.start()
print("Export task started. Check Google Drive for the TIFF file.")


# Function to get water satellite images for specific date
def get_landsat_image(sensor, year, month):
    dataset = ee.ImageCollection(sensor) \
        .filterBounds(kenya_lvb) \
        .filterDate(f"{year}-{month}-01", f"{year}-{month}-28") \
        .median()  # Take median composite to reduce cloud effects
    return dataset.clip(kenya_lvb)

# Landsat 8 (2020) and Landsat 5 (2006)
landsat_2020 = get_landsat_image("LANDSAT/LC08/C02/T1_TOA", 2020, 6)
landsat_2006 = get_landsat_image("LANDSAT/LT05/C02/T1_TOA", 2006, 10)

# Export Landsat 8 (June 2020)
task_2020 = ee.batch.Export.image.toDrive(
    image=landsat_2020,
    description="LakeVictoria_Landsat_June2020",
    folder="GEE_Exports",
    fileNamePrefix="LakeVictoria_Landsat_June2020",
    scale=30,
    region=kenya_lvb.geometry().bounds(),
    fileFormat="GeoTIFF"
)
task_2020.start()

# Export Landsat 5 (October 2006)
task_2006 = ee.batch.Export.image.toDrive(
    image=landsat_2006,
    description="LakeVictoria_Landsat_October2006",
    folder="GEE_Exports",
    fileNamePrefix="LakeVictoria_Landsat_October2006",
    scale=30,
    region=kenya_lvb.geometry().bounds(),
    fileFormat="GeoTIFF"
)
task_2006.start()

print("Export tasks started. Check Google Drive for the TIFF files.")


#%%

import rasterio
import numpy as np
import matplotlib.pyplot as plt

# Load the TIFF file
tiff_file = "C:\DATA\Dr. Olala Shapefile\Water_October_2006_Kenya_LVB.tif"  # Update with your actual file path

with rasterio.open(tiff_file) as src:
    water_data = src.read(1)  # Read the first band
    extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]  # Get extent

# Replace nodata values with NaN for better visualization
water_data = np.where(water_data == src.nodata, np.nan, water_data)

# Plot the water occurrence TIFF
plt.figure(figsize=(10, 8))
plt.imshow(water_data, cmap="Blues", extent=extent)
plt.colorbar(label="Water Occurrence (%)")
plt.title("Water Occurrence - October 2006")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.grid(False)
plt.show()


#%%

import rasterio
import numpy as np
import matplotlib.pyplot as plt

# Define file paths for the two images
tiff_2020 = "C:\DATA\Dr. Olala Shapefile\Water_June_2020_Kenya_LVB.tif"
tiff_2006 = "C:\DATA\Dr. Olala Shapefile\Water_October_2006_Kenya_LVB.tif"

# Read the June 2020 water occurrence image
with rasterio.open(tiff_2020) as src_2020:
    water_2020 = src_2020.read(1)
    extent = [src_2020.bounds.left, src_2020.bounds.right, src_2020.bounds.bottom, src_2020.bounds.top]

# Read the October 2006 water occurrence image
with rasterio.open(tiff_2006) as src_2006:
    water_2006 = src_2006.read(1)

# Ensure both images have the same dimensions
if water_2020.shape != water_2006.shape:
    raise ValueError("Images do not have the same dimensions. Consider resampling.")

# Replace NoData values with NaN for better computation
water_2020 = np.where(water_2020 == src_2020.nodata, np.nan, water_2020)
water_2006 = np.where(water_2006 == src_2006.nodata, np.nan, water_2006)

# Compute the difference (increase/decrease in water occurrence)
water_difference = water_2020 - water_2006

# Plot the difference map
plt.figure(figsize=(10, 8))
plt.imshow(water_difference, cmap="RdBu", extent=extent)
plt.colorbar(label="Change in Water Occurrence (%)")
plt.title("Change in Water Occurrence (June 2020 - October 2006)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.grid(False)
plt.show()

#%%

import rasterio
import numpy as np
from rasterio.warp import calculate_default_transform, reproject, Resampling

# Function to reproject raster to a common CRS
def reproject_raster(input_raster, output_raster, target_crs):
    with rasterio.open(input_raster) as src:
        # Get the transform and metadata for the target CRS
        transform, width, height = calculate_default_transform(
            src.crs, target_crs, src.width, src.height, *src.bounds)
        
        # Update metadata for the reprojected raster
        metadata = src.meta.copy()
        metadata.update({
            'crs': target_crs,
            'transform': transform,
            'width': width,
            'height': height
        })
        
        # Write the reprojected data to the output file
        with rasterio.open(output_raster, 'w', **metadata) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=target_crs,
                    resampling=Resampling.nearest)

# Function to calculate the water area in square meters
def calculate_water_area(raster_file, water_threshold):
    with rasterio.open(raster_file) as src:
        # Read the raster data as a numpy array
        water_data = src.read(1)
        
        # Apply a mask based on the water threshold (e.g., water values above a certain threshold)
        water_mask = water_data > water_threshold
        
        # Calculate the area of water in square meters
        pixel_area = src.res[0] * src.res[1]  # Resolution of the raster (in meters)
        water_area = np.sum(water_mask) * pixel_area
        
    return water_area

# Define the file paths for the two TIFF images
tiff_june_2020 = "C:\DATA\Dr. Olala Shapefile\Water_June_2020_Kenya_LVB.tif"  # Path to the June 2020 TIFF file
tiff_october_2006 = "C:\DATA\Dr. Olala Shapefile\Water_October_2006_Kenya_LVB.tif"  # Path to the October 2006 TIFF file

# Define the output file paths for the reprojected TIFF images
reprojected_june_2020 = 'reprojected_june_2020_water.tif'
reprojected_october_2006 = 'reprojected_october_2006_water.tif'

# Define the target CRS (for example, EPSG:4326, WGS 84)
target_crs = 'EPSG:4326'

# Reproject the rasters to the same CRS
reproject_raster(tiff_june_2020, reprojected_june_2020, target_crs)
reproject_raster(tiff_october_2006, reprojected_october_2006, target_crs)

# Define the water threshold based on the raster's pixel values (adjust this based on your data)
water_threshold = 0.5  # Assuming water values are represented by values greater than 0.5

# Calculate the water areas for both dates
water_area_june_2020 = calculate_water_area(reprojected_june_2020, water_threshold)
water_area_october_2006 = calculate_water_area(reprojected_october_2006, water_threshold)

# Calculate the difference in the water areas
area_difference = water_area_june_2020 - water_area_october_2006

print(f"Water area in June 2020: {water_area_june_2020:.2f} m²")
print(f"Water area in October 2006: {water_area_october_2006:.2f} m²")
print(f"Difference in water area: {area_difference:.2f} m²")




















