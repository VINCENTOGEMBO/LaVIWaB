# -*- coding: utf-8 -*-
"""
Created on Wed Nov 20 12:34:58 2024

@author: VO000003
"""


#%%

import os
import numpy as np
import rasterio
from rasterio.enums import Resampling
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from tempfile import gettempdir

# Define file paths using raw strings or forward slashes
temp_dir = r"C:\Users\VO000003\Documents\Temporary files"  # Replace with your folder
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

aligned_bathymetry_file = os.path.join(temp_dir, "aligned_bathymetry.tif")
submerged_mask_file = os.path.join(temp_dir, "submerged_mask.tif")

# Function to resample raster data to match a reference raster
def resample_raster(input_raster, output_raster, reference_raster):
    with rasterio.open(input_raster) as src, rasterio.open(reference_raster) as ref:
        transform, width, height = ref.transform, ref.width, ref.height
        profile = src.profile
        profile.update({
            'crs': ref.crs,
            'transform': transform,
            'width': width,
            'height': height
        })

        # Resample the data
        data = src.read(
            out_shape=(src.count, height, width),
            resampling=Resampling.bilinear
        )
        data = np.where(data < 0, data, 0)  # Keep only negative values (submerged areas)

        # Write the aligned bathymetry raster
        with rasterio.open(output_raster, 'w', **profile) as dst:
            dst.write(data)

# Replace with your actual file paths
bathymetry_file = r"C:\DATA\Lake V Bathymentry\LakeVictoria_BathymetryGEE.tif"  # Replace with your bathymetry file
water_occurrence_file = r"C:\DATA\Water Occurance LV\LakeVictoria_WaterOccurrence.tif"  # Replace with your Pekel water occurrence file

# Process resampling
try:
    resample_raster(bathymetry_file, aligned_bathymetry_file, water_occurrence_file)
except Exception as e:
    print(f"Error during resampling: {e}")
    raise

# Create submerged mask based on aligned bathymetry
def create_submerged_mask(bathymetry_file, output_file):
    with rasterio.open(bathymetry_file) as bathy:
        bathy_data = bathy.read(1)
        submerged_mask = np.where(bathy_data < 0, 1, 0)  # Submerged = 1, Non-submerged = 0

        profile = bathy.profile
        profile.update(dtype=rasterio.uint8, count=1)

        with rasterio.open(output_file, 'w', **profile) as dst:
            dst.write(submerged_mask.astype(rasterio.uint8), 1)

try:
    create_submerged_mask(aligned_bathymetry_file, submerged_mask_file)
except Exception as e:
    print(f"Error creating submerged mask: {e}")
    raise

# Plot maps of water occurrence and submerged areas
def plot_maps(water_occurrence_file, submerged_mask_file):
    with rasterio.open(water_occurrence_file) as wo, rasterio.open(submerged_mask_file) as sm:
        wo_data = wo.read(1)
        sm_data = sm.read(1)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 8))
        cbar_ax1 = fig.add_axes([0.92, 0.55, 0.02, 0.35])
        cbar_ax2 = fig.add_axes([0.92, 0.1, 0.02, 0.35])

        im1 = ax1.imshow(wo_data, cmap='Blues', extent=wo.bounds, vmin=0, vmax=100)
        ax1.set_title("Pekel Water Extent")
        ax1.set_xlabel("Longitude")
        ax1.set_ylabel("Latitude")
        fig.colorbar(im1, cax=cbar_ax1, label="Water Extent (%)")

        im2 = ax2.imshow(sm_data, cmap='Blues', extent=sm.bounds, vmin=0, vmax=1)
        ax2.set_title("Submerged Areas (Bathymetry)")
        ax2.set_xlabel("Longitude")
        ax2.set_ylabel("Latitude")
        fig.colorbar(im2, cax=cbar_ax2, label="Submerged (1=Yes, 0=No)")

        plt.tight_layout(rect=[0, 0, 0.9, 1])
        plt.show()

plot_maps(water_occurrence_file, submerged_mask_file)

# Create a movie showing submerged areas over time
def create_movie(bathymetry_file, output_movie):
    with rasterio.open(bathymetry_file) as src:
        data = src.read(1)
        fig, ax = plt.subplots(figsize=(8, 8))

        def update(frame):
            ax.clear()
            ax.imshow(data, cmap='Blues', vmin=0, vmax=1)
            ax.set_title(f"Submerged Areas Frame {frame}")

        ani = animation.FuncAnimation(fig, update, frames=10, repeat=True)
        ani.save(output_movie, writer='ffmpeg')

output_movie = os.path.join(temp_dir, "submerged_areas_movie.mp4")
try:
    create_movie(submerged_mask_file, output_movie)
    print(f"Movie saved at: {output_movie}")
except Exception as e:
    print(f"Error creating movie: {e}")

