# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 06:58:18 2024

@author: V.Ogembo
"""


#%%

#Interpolate Lake Bathymetry and DEM

import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np
import os

# === File paths ===
bathymetry_tif = r"C:\DATA\Lake V Bathymentry\LakeVictoria_BathymetryGEE.tif"
dem_tif = r"C:\DATA\Lake Basin Topography\LakeVictoriaBasinDEM.tif"
output_merged_tif = r"C:\DATA\Lake V Bathymentry\Merged_Elevation_30m.tif"

# === Step 1: Read DEM (Target Resolution) ===
with rasterio.open(dem_tif) as dem_src:
    dem_data = dem_src.read(1)
    dem_meta = dem_src.meta.copy()
    dem_transform = dem_src.transform
    dem_crs = dem_src.crs
    dem_bounds = dem_src.bounds

# === Step 2: Resample Bathymetry to Match DEM ===
with rasterio.open(bathymetry_tif) as bathy_src:
    bathy_data = bathy_src.read(1)
    bathy_transform = bathy_src.transform
    bathy_crs = bathy_src.crs

    # Create array for resampled bathymetry
    bathy_resampled = np.empty_like(dem_data, dtype=np.float32)

    # Reproject and resample bathymetry to 30m
    reproject(
        source=bathy_data,
        destination=bathy_resampled,
        src_transform=bathy_transform,
        src_crs=bathy_crs,
        dst_transform=dem_transform,
        dst_crs=dem_crs,
        resampling=Resampling.bilinear
    )

# === Step 3: Merge — Use Bathymetry where available (e.g., bathy < 0 or valid) ===
# Assuming NoData in bathymetry is negative or a specific value
merged_elevation = np.where(~np.isnan(bathy_resampled), bathy_resampled, dem_data)

# Optional: Set NoData where both are invalid
merged_elevation[np.isnan(merged_elevation)] = -9999

# === Step 4: Save Merged Raster ===
dem_meta.update({
    "dtype": "float32",
    "nodata": -9999
})

with rasterio.open(output_merged_tif, 'w', **dem_meta) as dst:
    dst.write(merged_elevation, 1)

print(f"Merged elevation raster saved to: {output_merged_tif}")



#%%

# LAKE VICTORIA PLAN VIEW 

import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# Path to your bathymetry GeoTIFF file
tif_file = "C:\DATA\Lake V Bathymentry\LakeVictoria_BathymetryGEE.tif"

# Open the GeoTIFF file
with rasterio.open(tif_file) as src:
    # Read the raster data
    bathymetry = src.read(1)  # Read the first band
    # Mask invalid data (e.g., NaN or no-data values)
    bathymetry = np.ma.masked_where(bathymetry == src.nodata, bathymetry)

    # Extract spatial metadata
    extent = (src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top)

# Plot the bathymetry
plt.figure(figsize=(12, 10))
plt.imshow(
    bathymetry,
    cmap="viridis",  # Use a perceptual colormap for better depth visualization
    extent=extent,
    origin="upper",
)
plt.colorbar(label="Depth (m)")  # Add a color bar


# Add grid lines
plt.grid(visible=True, linestyle="--", color="gray", alpha=0.7)

# Label the axes
plt.title("Bathymetric Plan View of Lake Victoria")
plt.xlabel("Longitude")
plt.ylabel("Latitude")

# Ensure the aspect ratio is correct
plt.gca().set_aspect('equal', adjustable='box')

# Add major ticks for grid lines
plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))

# Show the plot
plt.show()


#%%

# CROSS SECTION VIEW WITH SHADED WATER VOLUMES

import rasterio
import numpy as np
import matplotlib.pyplot as plt
from rasterio.sample import sample_gen
from shapely.geometry import LineString

# Path to your bathymetry GeoTIFF file
tif_file = r"C:\DATA\Lake V Bathymentry\LakeVictoria_BathymetryGEE.tif"

# Define the cross-section line (coordinates in the same CRS as the raster)
start_point = (31.6, -0.98)  # Example start point (Longitude, Latitude)
end_point = (34.19092, -0.98)  # Example end point (Longitude, Latitude)

# Generate line coordinates for sampling
line = LineString([start_point, end_point])
num_points = 500  # Number of points to sample along the line
line_coords = np.linspace(start_point, end_point, num_points)  # Longitudes and Latitudes

# Extract the longitude values for the x-axis
longitudes = [coord[0] for coord in line_coords]

# Open the GeoTIFF file and extract depth values along the line
with rasterio.open(tif_file) as src:
    # Sample the raster data along the line
    depth_values = list(
        sample_gen(src, [(coord[0], coord[1]) for coord in line_coords])
    )
    depth_values = [val[0] if val[0] != src.nodata else np.nan for val in depth_values]

# Invert depth values (surface = 0, bottom = negative depth)
depth_values = np.array(depth_values)  # Convert to numpy array
depth_values = -depth_values  # Invert values

# Plot the inverted cross-section with longitude as x-axis
plt.figure(figsize=(12, 6))
plt.plot(longitudes, depth_values, label="Profile with Lake Water Column (Latitude -0.98°)", color="blue")
plt.fill_between(longitudes, depth_values, 0, where=(depth_values < 0), color="blue", alpha=0.3)  # Shade the water area

# Customize the plot
plt.title("Bathymetric Cross-Section Profile of Lake Victoria")
plt.xlabel("Longitude (°)")
plt.ylabel("Depth (m)")
plt.grid(visible=True, linestyle="--", alpha=0.5)
plt.axhline(y=0, color="black", linewidth=0.8, linestyle="--")  # Highlight lake surface
plt.legend()
plt.show()


#%%

# BATHYMETRIC AND TOPOGRAPHIC PROFILE OF LAKE VICTORIA

import rasterio
import numpy as np
import matplotlib.pyplot as plt
from rasterio.sample import sample_gen
from shapely.geometry import LineString

# Paths to the bathymetry and topography GeoTIFF files
tif_file_bathymetry = r"C:\DATA\Lake V Bathymentry\LakeVictoria_BathymetryGEE.tif"
tif_file_topography = r"C:\DATA\Lake Basin Topography\LakeVictoria_Topography.tif"

# Define the cross-section line (coordinates in the same CRS as the rasters)
start_point = (31.6, -0.98)  # Example start point (Longitude, Latitude)
end_point = (34.2, -0.98)   # Example end point (Longitude, Latitude)

# Generate line coordinates for sampling
num_points = 500  # Number of points to sample along the line
line_coords = np.linspace(start_point, end_point, num_points)  # Generate line sample points
longitudes = [coord[0] for coord in line_coords]  # Extract longitudes for x-axis

# Function to extract data along the cross-section line
def extract_profile(tif_file, line_coords):
    with rasterio.open(tif_file) as src:
        values = list(
            sample_gen(src, [(coord[0], coord[1]) for coord in line_coords])
        )
        values = [val[0] if val[0] != src.nodata else np.nan for val in values]
    return np.array(values)

# Extract bathymetry and topography data
bathymetry_values = extract_profile(tif_file_bathymetry, line_coords)
topography_values = extract_profile(tif_file_topography, line_coords)

# Combine bathymetry and topography into a uniform elevation scale
lake_surface_elevation = 1134  # Lake Victoria surface elevation above sea level (m)
bathymetry_values = lake_surface_elevation - bathymetry_values  # Convert depth to elevation
combined_values = np.where(bathymetry_values < lake_surface_elevation, bathymetry_values, topography_values)

# Plot the bathymetry and topography
plt.figure(figsize=(12, 6))
plt.plot(longitudes, combined_values, label="Lake Victoria Profile - along Lat -0.98", color="black")
plt.fill_between(
    longitudes, combined_values, lake_surface_elevation,
    where=(combined_values < lake_surface_elevation), color="blue", alpha=0.4, label="Water Column"
)
plt.fill_between(
    longitudes, lake_surface_elevation, combined_values,
    where=(combined_values > lake_surface_elevation), color="green", alpha=0.3, label="Land Elevation"
)

# Customize the plot
plt.title("Bathymetric and Topographic Profile of Lake Victoria and Basin")
plt.axhline(y=lake_surface_elevation, color="black", linestyle="--", linewidth=0.8, label="Lake Surface Level")
plt.xlabel("Longitude (°)")
plt.ylabel("Elevation (m)")
plt.grid(visible=True, linestyle="--", alpha=0.5)
plt.legend()
plt.show()


#%%
 # SEAMLESS TRANSITION 
 
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from rasterio.sample import sample_gen

# Paths to the bathymetry and topography GeoTIFF files
tif_file_bathymetry = r"C:\DATA\Lake V Bathymentry\LakeVictoria_BathymetryGEE.tif"
tif_file_topography = r"C:\DATA\Lake Basin Topography\LakeVictoriaBasinDEM.tif"

# Define the cross-section line (coordinates in the same CRS as the rasters)
start_point = (31.25, -0.98)  # Example start point (Longitude, Latitude)
end_point = (34.45, -0.98)   # Example end point (Longitude, Latitude)

# Generate line coordinates for sampling
num_points = 500  # Number of points to sample along the line
line_coords = np.linspace(start_point, end_point, num_points)  # Generate line sample points
longitudes = [coord[0] for coord in line_coords]  # Extract longitudes for x-axis

# Function to extract data along the cross-section line
def extract_profile(tif_file, line_coords):
    with rasterio.open(tif_file) as src:
        values = list(
            sample_gen(src, [(coord[0], coord[1]) for coord in line_coords])
        )
        values = [val[0] if val[0] != src.nodata else np.nan for val in values]
    return np.array(values)

# Extract bathymetry and topography data
bathymetry_values = extract_profile(tif_file_bathymetry, line_coords)
topography_values = extract_profile(tif_file_topography, line_coords)

# Combine bathymetry and topography into a uniform elevation scale
lake_surface_elevation = 1134  # Lake Victoria surface elevation above sea level (m)
bathymetry_values = lake_surface_elevation - bathymetry_values  # Convert depth to elevation

# Identify transition point (where bathymetry ends and topography begins)
transition_point = np.argmax(bathymetry_values > lake_surface_elevation)

# Create a transition zone: 5% of the profile length around the transition point
transition_zone_size = int(0.05 * len(longitudes))  # 5% of total length for the transition zone
start_transition = max(0, transition_point - transition_zone_size)  # Avoid going out of bounds
end_transition = min(len(longitudes), transition_point + transition_zone_size)

# Interpolate smoothly between bathymetry and topography
if transition_point > 0 and start_transition < end_transition:
    # Generate a linear transition
    transition_values = np.linspace(
        bathymetry_values[start_transition], topography_values[end_transition - 1],
        end_transition - start_transition
    )
    combined_values = np.copy(bathymetry_values)
    combined_values[start_transition:end_transition] = transition_values
    combined_values[end_transition:] = topography_values[end_transition:]
else:
    # Directly combine without transition if no overlap
    combined_values = np.where(
        bathymetry_values < lake_surface_elevation, bathymetry_values, topography_values
    )

# Plot the bathymetry and topography
plt.figure(figsize=(12, 6))
plt.plot(longitudes, combined_values, label="Lake Victoria Profile", color="black")
plt.fill_between(
    longitudes, combined_values, lake_surface_elevation,
    where=(combined_values < lake_surface_elevation), color="blue", alpha=0.4, label="Water Column"
)
plt.fill_between(
    longitudes, lake_surface_elevation, combined_values,
    where=(combined_values > lake_surface_elevation), color="green", alpha=0.3, label="Land Elevation"
)

# Customize the plot
plt.title("Lake Victoria Extent")
plt.axhline(y=lake_surface_elevation, color="black", linestyle="--", linewidth=0.8, label="Lake Surface Level")
plt.xlabel("Longitude (°)")
plt.ylabel("Elevation (m)")
plt.grid(visible=True, linestyle="--", alpha=0.5)
plt.legend()
plt.show()

#%%

# CROSS-SECTION PROFILE WITH BATHYMETRY AND TOPOGRAPHY

import rasterio
import numpy as np
import matplotlib.pyplot as plt
from rasterio.sample import sample_gen

# Paths to the bathymetry and topography GeoTIFF files
tif_file_bathymetry = r"C:\DATA\Lake V Bathymentry\LakeVictoria_BathymetryGEE.tif"
tif_file_topography = r"C:\DATA\Lake Basin Topography\LakeVictoriaBasinDEM.tif"

# Define the cross-section line (coordinates in the same CRS as the rasters)
start_point = (31.6, -1.0)  # Example start point (Longitude, Latitude)
end_point = (34.3, -1.0)   # Example end point (Longitude, Latitude)

# Generate line coordinates for sampling
num_points = 500  # Number of points to sample along the line
line_coords = np.linspace(start_point, end_point, num_points)  # Generate line sample points
longitudes = [coord[0] for coord in line_coords]  # Extract longitudes for x-axis

# Function to extract data along the cross-section line
def extract_profile(tif_file, line_coords):
    with rasterio.open(tif_file) as src:
        values = list(
            sample_gen(src, [(coord[0], coord[1]) for coord in line_coords])
        )
        values = [val[0] if val[0] != src.nodata else np.nan for val in values]
    return np.array(values)

# Extract bathymetry and topography data
bathymetry_values = extract_profile(tif_file_bathymetry, line_coords)
topography_values = extract_profile(tif_file_topography, line_coords)

# Combine bathymetry and topography into a uniform elevation scale
lake_surface_elevation = 1134  # Lake Victoria surface elevation above sea level (m)
bathymetry_values = lake_surface_elevation - bathymetry_values  # Convert depth to elevation

# Identify transition point (where bathymetry ends and topography begins)
transition_point = np.argmax(bathymetry_values > lake_surface_elevation)

# Create a transition zone: 5% of the profile length around the transition point
transition_zone_size = int(0.05 * len(longitudes))  # 5% of total length for the transition zone
start_transition = max(0, transition_point - transition_zone_size)  # Avoid going out of bounds
end_transition = min(len(longitudes), transition_point + transition_zone_size)

# Interpolate smoothly between bathymetry and topography
if transition_point > 0 and start_transition < end_transition:
    # Generate a linear transition
    transition_values = np.linspace(
        bathymetry_values[start_transition], topography_values[end_transition - 1],
        end_transition - start_transition
    )
    combined_values = np.copy(bathymetry_values)
    combined_values[start_transition:end_transition] = transition_values
    combined_values[end_transition:] = topography_values[end_transition:]
else:
    # Directly combine without transition if no overlap
    combined_values = np.where(
        bathymetry_values < lake_surface_elevation, bathymetry_values, topography_values
    )

# Plot the bathymetry and topography
plt.figure(figsize=(12, 6))
plt.plot(longitudes, combined_values, label="Lake Victoria Profile Along Lat -1.0°", color="black")
plt.fill_between(
    longitudes, combined_values, lake_surface_elevation,
    where=(combined_values < lake_surface_elevation), color="blue", alpha=0.4, label="Water Column"
)
plt.fill_between(
    longitudes, lake_surface_elevation, combined_values,
    where=(combined_values > lake_surface_elevation), color="green", alpha=0.3, label="Land Elevation"
)

# Customize the plot
plt.title("Lake Victoria Extent")
plt.axhline(y=lake_surface_elevation, color="black", linestyle="--", linewidth=0.8, label="Lake Surface Level")
plt.xlabel("Longitude (°)")
plt.ylabel("Elevation (m)")
plt.grid(visible=True, linestyle="--", alpha=0.5)
plt.legend()
plt.show()

#%%

# ALIGNING WITH PEKEL RESOLUTION PROFILE WITH TOPOGRAPHY

import rasterio
import numpy as np
import matplotlib.pyplot as plt
from rasterio.sample import sample_gen
from rasterio.warp import transform
from shapely.geometry import LineString

# Paths to the bathymetry and topography GeoTIFF files
tif_file_bathymetry = r"C:\DATA\Lake V Bathymentry\LakeVictoria_BathymetryGEE.tif"
tif_file_topography = r"C:\DATA\Lake Basin Topography\LakeVictoriaBasinDEM.tif"

# Define the cross-section line (coordinates in the same CRS as the rasters)
start_point = (31.6, -1.0)  # Example start point (Longitude, Latitude)
end_point = (34.3, -1.0)   # Example end point (Longitude, Latitude)

# Generate line coordinates for sampling, considering 30m resolution
num_points = 500  # Number of points to sample along the line
line_coords = np.linspace(start_point, end_point, num_points)  # Generate line sample points
longitudes = [coord[0] for coord in line_coords]  # Extract longitudes for x-axis
latitudes = [coord[1] for coord in line_coords]   # Extract latitudes for y-axis

# Function to extract data along the cross-section line at a given resolution
def extract_profile(tif_file, line_coords):
    with rasterio.open(tif_file) as src:
        # Calculate the sample points based on the resolution (30m)
        values = list(
            sample_gen(src, [(coord[0], coord[1]) for coord in line_coords])
        )
        # Replace no data values with NaN
        values = [val[0] if val[0] != src.nodata else np.nan for val in values]
    return np.array(values)

# Extract bathymetry and topography data
bathymetry_values = extract_profile(tif_file_bathymetry, line_coords)
topography_values = extract_profile(tif_file_topography, line_coords)

# Combine bathymetry and topography into a uniform elevation scale
lake_surface_elevation = 1134  # Lake Victoria surface elevation above sea level (m)
bathymetry_values = lake_surface_elevation - bathymetry_values  # Convert depth to elevation

# Identify transition point (where bathymetry ends and topography begins)
transition_point = np.argmax(bathymetry_values > lake_surface_elevation)

# Create a transition zone: 5% of the profile length around the transition point
transition_zone_size = int(0.05 * len(longitudes))  # 5% of total length for the transition zone
start_transition = max(0, transition_point - transition_zone_size)  # Avoid going out of bounds
end_transition = min(len(longitudes), transition_point + transition_zone_size)

# Interpolate smoothly between bathymetry and topography
if transition_point > 0 and start_transition < end_transition:
    # Generate a linear transition
    transition_values = np.linspace(
        bathymetry_values[start_transition], topography_values[end_transition - 1],
        end_transition - start_transition
    )
    combined_values = np.copy(bathymetry_values)
    combined_values[start_transition:end_transition] = transition_values
    combined_values[end_transition:] = topography_values[end_transition:]
else:
    # Directly combine without transition if no overlap
    combined_values = np.where(
        bathymetry_values < lake_surface_elevation, bathymetry_values, topography_values
    )

# Plot the bathymetry and topography
plt.figure(figsize=(12, 6), dpi=300)
plt.plot(longitudes, combined_values, label="Lake Victoria Profile Along Lat -1.0°", color="black")
plt.fill_between(
    longitudes, combined_values, lake_surface_elevation,
    where=(combined_values < lake_surface_elevation), color="blue", alpha=0.4, label="Water Column"
)
plt.fill_between(
    longitudes, lake_surface_elevation, combined_values,
    where=(combined_values > lake_surface_elevation), color="green", alpha=0.3, label="Land Elevation"
)

# Customize the plot
plt.title("Lake Victoria Extent")
plt.axhline(y=lake_surface_elevation, color="black", linestyle="--", linewidth=0.8, label="Lake Surface Level")
plt.xlabel("Longitude (°)")
plt.ylabel("Elevation (m)")
plt.grid(visible=True, linestyle="--", alpha=0.5)
plt.legend()
plt.show()


#%%

# CREATING A MOVIE 

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

# Define lake surface elevations and corresponding dates
lake_surface_data = {
    1135: "Feb 2018",
    1136: "Dec 2019",
    1137: "April 2020",
    1138: "June 2020"
}

# Repeat the elevation list for dry periods
lake_surface_elevations = [1135, 1136, 1137, 1138, 1138, 1137, 1136, 1135, 1135, 1136, 1137, 1138, 1137, 1136, 1135, 1135, 1136, 1137, 1138]

# Read the bathymetry and topography data
def read_raster(tif_file):
    with rasterio.open(tif_file) as src:
        data = src.read(1)  # Read the first band (elevation data)
        transform = src.transform
        nodata = src.nodata
    return data, transform, nodata

bathymetry_data, bathymetry_transform, bathymetry_nodata = read_raster(tif_file_bathymetry)
topography_data, topography_transform, topography_nodata = read_raster(tif_file_topography)

# Resample topography data to match bathymetry resolution
def resample_raster(src_data, src_transform, src_crs, target_shape, target_transform):
    """Resample raster data to match the target resolution."""
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

# Resample topography data to match bathymetry's spatial resolution
topography_resampled = resample_raster(
    topography_data, topography_transform, 'EPSG:4326',
    bathymetry_data.shape, bathymetry_transform
)

# Create a video file
output_folder = r"C:\TEMP\LakeVictoria"
os.makedirs(output_folder, exist_ok=True)  # Ensure the output folder exists
video_filename = os.path.join(output_folder, 'lake_victoria_dry_period.avi')
fourcc = cv2.VideoWriter_fourcc(*'XVID')
frame_size = (800, 800)  # Square frames for better visualization
video = cv2.VideoWriter(video_filename, fourcc, 1, frame_size)  # 1 fps, 800x800 resolution

# Loop through each surface elevation and plot the submerged area
for surface_elevation in lake_surface_elevations:
    # Fetch the corresponding date
    date_label = lake_surface_data.get(surface_elevation, "Unknown Date")
    print(f"Processing elevation: {surface_elevation} m - {date_label}")

    # Determine submerged areas
    submerged_bathymetry = bathymetry_data > (surface_elevation - 0.5)
    submerged_topography = topography_resampled < surface_elevation
    combined_submerged = np.logical_or(submerged_bathymetry, submerged_topography)

    # Create a mask for submerged areas
    masked_combined = np.where(combined_submerged, 1, 0)

    # Plot the data
    plt.figure(figsize=(10, 10))
    plt.title(f"Lake Victoria Water Extent at {surface_elevation}m - {date_label}", fontsize=14)
    
    # Use terrain colors for the base map
    plt.imshow(topography_resampled, extent=(0, 1, 0, 1), cmap='terrain', alpha=0.7)
    
    # Overlay only the submerged area in blue (not the whole map)
    plt.imshow(
        masked_combined,
        extent=(0, 1, 0, 1),
        cmap='Blues',  # Submerged area in blue
        alpha=0.6,  # Adjust alpha for better visibility
        interpolation='none',
    )

    plt.xlabel("Longitude (°)")
    plt.ylabel("Latitude (°)")
    plt.colorbar(label="Submerged Areas (1=Submerged, 0=Land)")
    plt.grid(True, linestyle='--', alpha=0.5)

    # Save the frame
    temp_image_path = os.path.join(output_folder, 'temp_frame.png')
    plt.tight_layout()
    plt.savefig(temp_image_path, dpi=150)
    plt.close()

    # Read the frame and add to the video
    img = cv2.imread(temp_image_path)
    img_resized = cv2.resize(img, frame_size)
    video.write(img_resized)

# Highlight the area submerged at elevation 1142 and exposed at 1135 in red
submerged_at_1142 = bathymetry_data > (1142 - 0.5)
submerged_at_1135 = bathymetry_data > (1135 - 0.5)
exposed_at_1135 = np.logical_and(submerged_at_1142, np.logical_not(submerged_at_1135))

plt.figure(figsize=(10, 10))
plt.title("Area Submerged at 1142m and Exposed at 1135m (Highlighted in Red)", fontsize=14)

# Use terrain colors for the base map
plt.imshow(topography_resampled, extent=(0, 1, 0, 1), cmap='terrain', alpha=0.7)

# Overlay the specific area submerged at 1142 but exposed at 1135 in red
plt.imshow(
    exposed_at_1135,
    extent=(0, 1, 0, 1),
    cmap='Reds',
    alpha=0.6,
    interpolation='none',
)

# Save the frame with the highlighted red area
temp_image_path = os.path.join(output_folder, 'temp_frame_final.png')
plt.tight_layout()
plt.savefig(temp_image_path, dpi=150)
plt.close()

# Read the final frame and add to the video
img = cv2.imread(temp_image_path)
img_resized = cv2.resize(img, frame_size)
video.write(img_resized)

# Release the video writer
video.release()
print(f"Video has been saved successfully: {video_filename}")


#%%

# MAPPING LAKE EXTENT SUBMERGED BETWEEN 1138M AND 1135M

import rasterio
import numpy as np
import matplotlib.pyplot as plt
from rasterio.warp import reproject, Resampling

# Paths to the bathymetry and topography GeoTIFF files
tif_file_bathymetry = r"C:\DATA\Lake V Bathymentry\LakeVictoria_BathymetryGEE.tif"
tif_file_topography = r"C:\DATA\Lake Basin Topography\LakeVictoriaBasinDEM.tif"

# Read the raster data
def read_raster(tif_file):
    with rasterio.open(tif_file) as src:
        data = src.read(1)  # Read the first band (elevation data)
        transform = src.transform
        bounds = src.bounds
        crs = src.crs
        nodata = src.nodata
    return data, transform, bounds, crs, nodata

bathymetry_data, bathymetry_transform, bathymetry_bounds, bathymetry_crs, bathymetry_nodata = read_raster(tif_file_bathymetry)
topography_data, topography_transform, topography_bounds, topography_crs, topography_nodata = read_raster(tif_file_topography)

# Resample topography data to match bathymetry resolution
def resample_raster(src_data, src_transform, src_crs, target_shape, target_transform, target_crs):
    resampled_data = np.empty(target_shape, dtype=np.float32)
    reproject(
        src_data, resampled_data,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=target_transform,
        dst_crs=target_crs,
        resampling=Resampling.nearest
    )
    return resampled_data

topography_resampled = resample_raster(
    topography_data, topography_transform, topography_crs,
    bathymetry_data.shape, bathymetry_transform, bathymetry_crs
)

# Identify water at 1135m and transition areas
def calculate_areas(topography, bathymetry, elevation_high, elevation_low):
    water_at_low = topography < elevation_low  # Water at elevation 1135m
    submerged_at_high = topography < elevation_high  # Water at elevation 1142m
    transition_strip = np.logical_and(submerged_at_high, ~water_at_low)  # Exposed between 1142m and 1135m
    return water_at_low, transition_strip

elevation_high = 1145
elevation_low = 1134.3
water_at_low, transition_strip = calculate_areas(
    topography_resampled, bathymetry_data, elevation_high, elevation_low
)

# Generate a static map showing water and the transition strip
fig, ax = plt.subplots(figsize=(12, 10), dpi=300)
plt.title("Lake Victoria Flood Prone Areas", fontsize=20)

# Base map: Topography
plt.imshow(topography_resampled, extent=(bathymetry_bounds.left, bathymetry_bounds.right,
                                         bathymetry_bounds.bottom, bathymetry_bounds.top),
           cmap='terrain', alpha=0.7)

# Overlay water area at 1135m in blue
plt.imshow(np.where(water_at_low, 1, np.nan), extent=(bathymetry_bounds.left, bathymetry_bounds.right,
                                                     bathymetry_bounds.bottom, bathymetry_bounds.top),
           cmap='Blues', alpha=0.6, label='Water at 1135m')

# Overlay transition strip in maroon
plt.imshow(np.where(transition_strip, 1, np.nan), extent=(bathymetry_bounds.left, bathymetry_bounds.right,
                                                          bathymetry_bounds.bottom, bathymetry_bounds.top),
           cmap='Reds', alpha=0.8, label='Transition Strip')

# Labels and Color Bar
plt.colorbar(label="Elevation (m)")
plt.xlabel("Longitude (°)")
plt.ylabel("Latitude (°)")
plt.grid(alpha=0.5, linestyle='--')
plt.tight_layout()

# Save the map as an image
output_map_path = r"C:\TEMP\LakeVictoria_1135m_water_transition_strip.png"
plt.savefig(output_map_path, dpi=300)
plt.show()

print(f"Map saved successfully: {output_map_path}")

