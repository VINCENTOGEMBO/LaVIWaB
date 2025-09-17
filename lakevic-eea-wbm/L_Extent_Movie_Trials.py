# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 15:24:37 2024

@author: VO000003
"""

#STRIP OF SUBMERGED AREA BETWEEN 1136.777M AND 1135.333M

import rasterio
import numpy as np

with rasterio.open("C:\DATA\Lake Basin Topography\LakeVictoriaBasinDEM.tif") as dem:
    dem_data = dem.read(1)
    submerged_1136 = (dem_data <= 1136.777).astype(int)
    submerged_1135 = (dem_data <= 1135.333).astype(int)
    exposed_strip = submerged_1136 - submerged_1135  # Areas submerged only at 1142m

    # Save the exposed strip as a new raster

    with rasterio.open(r"C:\DATA\Lake Basin Topography\exposed_strip.tif", 'w', **dem.meta) as out:
        out.write(exposed_strip, 1)


#%%

# AREA OF THE SUBMERGED STRIP

import matplotlib.pyplot as plt
import rasterio
import numpy as np

# Open the DEM raster
with rasterio.open(r"C:\DATA\Lake Basin Topography\LakeVictoriaBasinDEM.tif") as dem:
    dem_data = dem.read(1)
    # Get geographic bounds for axis labels (min/max longitudes and latitudes)
    lon_min, lat_min, lon_max, lat_max = dem.bounds

    # Determine pixel size (in meters)
    pixel_width, pixel_height = dem.meta['transform'][0], dem.meta['transform'][4]

    # Calculate submerged areas for the range between 1136.777m and 1135.333m
    submerged_1136 = (dem_data <= 1136.777).astype(int)
    submerged_1135 = (dem_data <= 1135.333).astype(int)
    water_between_1136_1135 = submerged_1136 - submerged_1135  # Areas submerged only between 1136m and 1135m

    # Create a colored DEM where water between 1136.777 and 1135.333 is blue
    dem_colored = np.zeros((dem_data.shape[0], dem_data.shape[1], 3), dtype=np.uint8)  # RGB image

    # Set the areas with water between 1136.777 and 1135.333 to blue
    dem_colored[water_between_1136_1135 == 1] = [0, 0, 255]  # Blue for water between 1136 and 1135

    # Retain original DEM colors for land areas (not submerged)
    dem_colored[water_between_1136_1135 == 0] = plt.cm.terrain(dem_data[water_between_1136_1135 == 0] / np.max(dem_data))[:, :3] * 255

    # Calculate the number of pixels in the water area between the two elevations
    water_pixels = np.sum(water_between_1136_1135)

    # Calculate the area in square meters
    area_m2 = water_pixels * abs(pixel_width) * abs(pixel_height)

    # Convert area from square meters to square kilometers
    area_km2 = area_m2 / 1e6  # 1 km^2 = 1e6 m^2

    print(f"Area of water between elevation 1136.777m and 1135.333m: {area_km2} square kilometers")

# Visualize the colored DEM and the water area between the two elevations
plt.figure(figsize=(12, 6))

# Plot the colored DEM data with Longitudes and Latitudes
plt.subplot(1, 2, 1)
plt.imshow(dem_colored)
plt.title("Lake Victoria Extent with Water Area Between 1136.777m and 1135.333m")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.colorbar(plt.cm.ScalarMappable(cmap='terrain', norm=plt.Normalize(vmin=np.min(dem_data), vmax=np.max(dem_data))), label="Elevation (m)")

# Plot Water Area Between 1136.777m and 1135.333m
plt.subplot(1, 2, 2)
plt.imshow(water_between_1136_1135, cmap='Blues')
plt.title("Water Area Between Elevation 1136.777m and 1135.333m")
plt.xlabel("Longitude")
plt.ylabel("Latitude")

plt.show()

#%%

import matplotlib.pyplot as plt
import rasterio
import numpy as np

# Open the DEM raster
with rasterio.open(r"C:\DATA\Lake Basin Topography\LakeVictoriaBasinDEM.tif") as dem:
    dem_data = dem.read(1)
    # Get geographic bounds for axis labels (min/max longitudes and latitudes)
    lon_min, lat_min, lon_max, lat_max = dem.bounds

    # Determine pixel size (in meters)
    pixel_width, pixel_height = dem.meta['transform'][0], dem.meta['transform'][4]

    # Calculate submerged areas
    submerged_1136 = (dem_data <= 1136.777).astype(int)
    submerged_1135 = (dem_data <= 1135.333).astype(int)
    exposed_strip = submerged_1136 - submerged_1135  # Areas submerged only at 1136m but not 1135m

    # Create a colored DEM where water at 1135.333 is blue
    dem_colored = np.zeros((dem_data.shape[0], dem_data.shape[1], 3), dtype=np.uint8)  # RGB image

    # Set the areas with water (<= 1135.333) to blue
    dem_colored[submerged_1135 == 1] = [0, 0, 255]  # Blue for water

    # Retain original DEM colors for land areas (not submerged)
    dem_colored[submerged_1135 == 0] = plt.cm.terrain(dem_data[submerged_1135 == 0] / np.max(dem_data))[:, :3] * 255

    # Calculate the number of pixels in the exposed strip
    exposed_pixels = np.sum(exposed_strip)

    # Calculate the area in square meters
    area_m2 = exposed_pixels * abs(pixel_width) * abs(pixel_height)

    # Convert area from square meters to square kilometers
    area_km2 = area_m2 / 1e6  # 1 km^2 = 1e6 m^2

    print(f"Area of the exposed strip: {area_km2} square kilometers")

# Visualize the colored DEM and the exposed strip
plt.figure(figsize=(12, 6))

# Plot the colored DEM data with Longitudes and Latitudes
plt.subplot(1, 2, 1)
plt.imshow(dem_colored)
plt.title("Lake Victoria Extent with Exposed Strip")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.colorbar(plt.cm.ScalarMappable(cmap='terrain', norm=plt.Normalize(vmin=np.min(dem_data), vmax=np.max(dem_data))), label="Elevation (m)")

# Plot Exposed Strip
plt.subplot(1, 2, 2)
plt.imshow(exposed_strip, cmap='binary')
plt.title("Exposed Strip Between Elevation 1136.777m and 1135.333m")
plt.xlabel("Longitude")
plt.ylabel("Latitude")

plt.show()





#%%


import rasterio
import numpy as np
import matplotlib.pyplot as plt
import cv2
import os
from rasterio.enums import Resampling
from rasterio.warp import reproject

# Paths to the bathymetry and topography GeoTIFF files
tif_file_bathymetry = r"C:\DATA\Lake V Bathymentry\LakeVictoria_BathymetryGEE.tif"
tif_file_topography = r"C:\DATA\Lake Basin Topography\LakeVictoriaBasinDEM.tif"

# Define a range of lake surface elevations for the dry period (simulated)
lake_surface_elevations = [1130, 1132, 1134, 1136, 1138, 1140, 1142, 1142, 1140, 1138, 1136, 1134, 1132, 1130]

# Read the bathymetry and topography data
def read_raster(tif_file):
    with rasterio.open(tif_file) as src:
        data = src.read(1)  # Read the first band (elevation data)
        transform = src.transform
        bounds = src.bounds
        nodata = src.nodata
        crs = src.crs
    return data, transform, bounds, nodata, crs

bathymetry_data, bathymetry_transform, bathymetry_bounds, bathymetry_nodata, bathymetry_crs = read_raster(tif_file_bathymetry)
topography_data, topography_transform, topography_bounds, topography_nodata, topography_crs = read_raster(tif_file_topography)

# Resample topography data to match bathymetry resolution
def resample_raster(src_data, src_transform, src_crs, target_shape, target_transform):
    """Resample raster data to match the target resolution"""
    resampled_data = np.empty(target_shape, dtype=np.float32)
    reproject(
        src_data, resampled_data,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=target_transform,
        dst_crs=src_crs,
        resampling=Resampling.nearest
    )
    return resampled_data

# Resample topography data to bathymetry's spatial resolution
topography_resampled = resample_raster(
    topography_data, topography_transform, topography_crs,
    bathymetry_data.shape, bathymetry_transform
)

# Create a video file
output_folder = r"C:\TEMP\LakeVictoria"
os.makedirs(output_folder, exist_ok=True)  # Ensure the output folder exists
video_filename = os.path.join(output_folder, 'lake_victoria_dry_period.avi')
fourcc = cv2.VideoWriter_fourcc(*'XVID')
frame_size = (800, 800)
video = cv2.VideoWriter(video_filename, fourcc, 1, frame_size)  # 1 fps

# Loop through each surface elevation and plot submerged areas
for i, surface_elevation in enumerate(lake_surface_elevations):
    print(f"Processing elevation: {surface_elevation} m")

    # Determine submerged areas
    submerged_bathymetry = bathymetry_data <= surface_elevation
    submerged_topography = topography_resampled <= surface_elevation
    combined_submerged = np.logical_or(submerged_bathymetry, submerged_topography)

    # Create a mask for submerged areas
    masked_combined = np.where(combined_submerged, 1, 0)

    # Plot the data
    plt.figure(figsize=(10, 10))
    plt.title(f"Lake Victoria Water Extent (Elevation: {surface_elevation} m)", fontsize=14)
    plt.imshow(topography_resampled, extent=(bathymetry_bounds.left, bathymetry_bounds.right,
                                             bathymetry_bounds.bottom, bathymetry_bounds.top),
               cmap='terrain', alpha=0.7)
    plt.imshow(
        masked_combined,
        extent=(bathymetry_bounds.left, bathymetry_bounds.right,
                bathymetry_bounds.bottom, bathymetry_bounds.top),
        cmap='Blues', alpha=0.5, interpolation='none'
    )
    plt.xlabel("Longitude (°)")
    plt.ylabel("Latitude (°)")
    plt.colorbar(label="Submerged Areas (1=Submerged, 0=Land)")
    plt.grid(True, linestyle='--', alpha=0.5)

    # Save the frame
    temp_image_path = os.path.join(output_folder, f'temp_frame_{i}.png')
    plt.tight_layout()
    plt.savefig(temp_image_path, dpi=150)
    plt.close()

    # Read the frame and add to the video
    img = cv2.imread(temp_image_path)
    img_resized = cv2.resize(img, frame_size)
    video.write(img_resized)

# Release the video writer
video.release()
print(f"Video has been saved successfully: {video_filename}")


