# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 09:39:37 2024

@author: VO000003
"""

# WATER EXTENT OVER TIME 2006 - 2020

import rasterio
import numpy as np
import matplotlib.pyplot as plt
import imageio
import os

# Define file paths for images corresponding to the specified dates
image_files = {
    "April 2006": "path_to_image/April2006.tif",
    "May 2009": "path_to_image/May2009.tif",
    "May 2012": "path_to_image/May2012.tif",
    "May 2015": "path_to_image/May2015.tif",
    "May 2018": "path_to_image/May2018.tif",
    "May 2020": "path_to_image/May2020.tif",
}

# Create a temporary directory for frames
os.makedirs("frames", exist_ok=True)

# Generate frames for the movie
frames = []
for date, file_path in image_files.items():
    with rasterio.open(file_path) as src:
        water_extent = src.read(1)  # Read the first band (water extent)
        water_extent[water_extent == src.nodata] = np.nan  # Replace nodata with NaN

    # Plot the water extent
    plt.figure(figsize=(10, 8))
    plt.imshow(water_extent, cmap="Blues", interpolation="none")
    plt.title(f"Lake Victoria Water Extent - {date}")
    plt.colorbar(label="Water Extent")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.grid()
    
    # Save the frame
    frame_path = f"frames/{date.replace(' ', '_')}.png"
    plt.savefig(frame_path)
    frames.append(frame_path)
    plt.close()

# Create a movie from the frames
movie_path = "LakeVictoria_WaterExtent_Movie.mp4"
with imageio.get_writer(movie_path, fps=2) as writer:
    for frame in frames:
        image = imageio.imread(frame)
        writer.append_data(image)

# Clean up the frames (optional)
for frame in frames:
    os.remove(frame)

print(f"Movie created: {movie_path}")
