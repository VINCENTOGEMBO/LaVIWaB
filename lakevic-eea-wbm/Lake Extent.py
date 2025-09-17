# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 15:51:10 2024

@author: VO000003
"""

#%%

import rasterio
import matplotlib.pyplot as plt

# File path to the Lake Victoria extent raster
lake_extent_path = "C:\DATA\Lake Extent GEE\LakeVictoria_MaxWaterExtent.tif"  # Replace with your actual file path

# Load the Lake Extent GeoTIFF
with rasterio.open(lake_extent_path) as lake_extent:
    extent_data = lake_extent.read(1)  # Read the first band
    extent_transform = lake_extent.transform
    extent_crs = lake_extent.crs

# Plot the Lake Extent
plt.figure(figsize=(10, 8))
plt.imshow(extent_data, cmap='Blues', interpolation='none')  # Blue color for water extent
plt.colorbar(label="Extent (1 = Water, 0 = Non-Water)")
plt.title("Lake Victoria Water Extent")
plt.xlabel("Longitude")
plt.ylabel("Latitude")

# Add gridlines with coordinates
plt.grid(color='gray', linestyle='--', linewidth=0.5)
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)
plt.show()


#%%
#SAMPLE 1


import rasterio
from rasterio.enums import Resampling
import numpy as np
import matplotlib.pyplot as plt

# File paths
bathymetry_path = "C:\DATA\Lake V Bathymentry\LakeVictoria_BathymetryGEE.tif"  # Input bathymetry GeoTIFF file
reference_raster_path = "C:\DATA\Lake Extent GEE\LakeVictoria_MaxWaterExtent.tif"  # External raster for alignment (e.g., Pekel or ASTER)
resampled_bathymetry_path = "aligned_bathymetry_30m.tif"  # Output aligned bathymetry file
lake_extent_path = "lake_extent.tif"  # Output lake extent file

# 1. Load the reference raster (30m x 30m resolution)
with rasterio.open(reference_raster_path) as ref_raster:
    ref_transform = ref_raster.transform
    ref_crs = ref_raster.crs
    ref_shape = ref_raster.shape  # (height, width)

# 2. Load the bathymetry data
with rasterio.open(bathymetry_path) as bathy:
    bathy_data = bathy.read(1)  # Read the first band
    bathy_transform = bathy.transform
    bathy_crs = bathy.crs

# 3. Resample the bathymetry data to match the reference raster
resampled_bathymetry = np.empty(ref_shape, dtype=np.float32)  # Prepare output array
with rasterio.open(bathymetry_path) as bathy:
    rasterio.warp.reproject(
        source=bathy.read(1),
        destination=resampled_bathymetry,
        src_transform=bathy_transform,
        src_crs=bathy_crs,
        dst_transform=ref_transform,
        dst_crs=ref_crs,
        resampling=Resampling.bilinear,  # Bilinear interpolation
    )

# 4. Create the "Lake Extent" variable
# Negative bathymetry values represent the lake area
lake_extent = np.where(resampled_bathymetry < 0, 1, 0)  # 1 = Lake, 0 = Non-lake

# 5. Save the aligned bathymetry data
aligned_meta = {
    "driver": "GTiff",
    "height": ref_shape[0],
    "width": ref_shape[1],
    "count": 1,
    "dtype": "float32",
    "crs": ref_crs,
    "transform": ref_transform,
    "compress": "lzw",
}
with rasterio.open(resampled_bathymetry_path, "w", **aligned_meta) as dest:
    dest.write(resampled_bathymetry, 1)

# 6. Save the Lake Extent raster
extent_meta = aligned_meta.copy()
extent_meta["dtype"] = "uint8"  # Lake extent as integer mask
with rasterio.open(lake_extent_path, "w", **extent_meta) as dest:
    dest.write(lake_extent.astype("uint8"), 1)

# 7. Plot the Lake Extent
plt.figure(figsize=(10, 8))
plt.imshow(lake_extent, cmap="Blues", interpolation="none")
plt.title("Lake Victoria Extent")
plt.colorbar(label="Lake Extent (1=Water, 0=Non-Water)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.grid(color="gray", linestyle="--", linewidth=0.5)
plt.show()

print(np.unique(lake_extent))

plt.imshow(resampled_bathymetry, cmap="viridis")
plt.colorbar(label="Depth (m)")
plt.title("Resampled Bathymetry")
plt.show()



#%%

# SAMPLE 2

import numpy as np
import rasterio
import matplotlib.pyplot as plt
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
import os

# Step 1: Load the Bathymetry Data
bathymetry_file = "C:\DATA\Lake V Bathymentry\LakeVictoria_BathymetryGEE.tif"  # Update with the correct path
with rasterio.open(bathymetry_file) as src:
    bathymetry_data = src.read(1)  # Read the first band (bathymetry data)
    bathymetry_transform = src.transform  # Transformation information
    bathymetry_crs = src.crs  # Coordinate reference system

# Step 2: Resample Bathymetry Data to 30m x 30m Resolution
# Load reference raster (e.g., ASTER or Pekel) with a 30m resolution
reference_raster = "C:\DATA\Lake Extent GEE\LakeVictoria_MaxWaterExtent.tif"  # Update with the reference raster file path
with rasterio.open(reference_raster) as ref_src:
    reference_transform = ref_src.transform
    reference_crs = ref_src.crs
    reference_width = ref_src.width
    reference_height = ref_src.height
    reference_data = ref_src.read(1)

# Define new empty array for resampled bathymetry data
resampled_bathymetry = np.empty((reference_height, reference_width), dtype=np.float32)

# Perform resampling to match reference raster's grid and resolution (30m x 30m)
reproject(
    source=bathymetry_data,
    destination=resampled_bathymetry,
    src_transform=bathymetry_transform,
    src_crs=bathymetry_crs,
    dst_transform=reference_transform,
    dst_crs=reference_crs,
    resampling=Resampling.bilinear  # Bilinear interpolation for smoother resampling
)

# Step 3: Create the "Lake Extent" Variable
# Let's assume depths < 0 represent water, so create a mask for lake extent
lake_extent = np.where(resampled_bathymetry < 0, 1, 0)  # 1 = water, 0 = non-water

# Step 4: Plot the Results (Lake Victoria Extent)
plt.figure(figsize=(10, 8))
plt.imshow(lake_extent, cmap='Blues', vmin=0, vmax=1)  # Blue for water, white for non-water
plt.colorbar(label='Lake Extent (1 = Water, 0 = Non-Water)')
plt.title('Lake Victoria Water Extent')
plt.xlabel('Longitude')
plt.ylabel('Latitude')

# Add gridlines for better reference
plt.grid(which='both', color='gray', linestyle='--', linewidth=0.5)

plt.show()

# Optional: Save the water extent map as a new GeoTIFF
output_path = '/path/to/output/lake_victoria_extent.tif'  # Update with desired output path
with rasterio.open(output_path, 'w', driver='GTiff', 
                   count=1, dtype='uint8', 
                   crs=reference_crs, transform=reference_transform, 
                   width=reference_width, height=reference_height) as dst:
    dst.write(lake_extent, 1)



# Define output path (ensure it's a valid path on your system)
output_path = r'C:\valid\directory\lake_victoria_extent.tif'  # Update with actual valid path

# Ensure the directory exists, or create it
output_dir = os.path.dirname(output_path)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)  # Create the directory if it doesn't exist

# Saving the water extent map as a new GeoTIFF
with rasterio.open(output_path, 'w', driver='GTiff', 
                   count=1, dtype='uint8', 
                   crs=reference_crs, transform=reference_transform, 
                   width=reference_width, height=reference_height) as dst:
    dst.write(lake_extent, 1)
