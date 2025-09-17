# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 05:53:38 2024

@author: VO000003
"""


import rasterio
import numpy as np

# Function to calculate the surface area of the lake above a specified depth
def calculate_lake_area(bathymetry_tiff, depth_threshold=0):
    # Open the bathymetry raster data
    with rasterio.open(bathymetry_tiff) as src:
        # Read the bathymetry data into a 2D array (depth values)
        bathymetry_data = src.read(1)
        
        # Get the pixel size (resolution)
        pixel_size_x, pixel_size_y = src.res[0], src.res[1]
        
        # Mask the data to include only areas where depth is above the threshold (i.e., water areas)
        water_area_mask = bathymetry_data >= depth_threshold
        
        # Calculate the number of water pixels
        water_pixels = np.sum(water_area_mask)
        
        # Calculate the area in square meters: Area = (number of pixels) * (pixel area)
        pixel_area = pixel_size_x * pixel_size_y  # in square meters
        water_area_sqm = water_pixels * pixel_area
        
        # Convert square meters to square kilometers (1 km^2 = 1,000,000 m^2)
        water_area_km2 = water_area_sqm / 1e6
        
        return water_area_km2

# Example usage
bathymetry_tiff = "C:\DATA\Lake V Bathymentry\LakeVictoria_Bathymetry-Reprojected.tif"
lake_area = calculate_lake_area(bathymetry_tiff)

print(f"Calculated surface area of Lake Victoria: {lake_area:.2f} km²")

#%%

# Open bathymetry raster
basin_topography_tiff = "C:\DATA\Processed\Reprojected_Resampled_DEM.tif"


#%%%

# same thing but from bathymetry + topography (e.g. in case of flood)

with rasterio.open(bathymetry_tiff) as src:
    # Read the bathymetry data into a 2D array (depth values)
    bathymetry_data = src.read(1)

plt.imshow(bathymetry_data)





#%%
# Lake Victoria Depth-Volume Curve


import rasterio
import numpy as np
import matplotlib.pyplot as plt

# 1. Load Bathymetry Data
file_path = "C:\DATA\Lake V Bathymentry\LakeVictoria_Bathymetry-Reprojected.tif"
with rasterio.open(file_path) as bathy:
    depth_data = bathy.read(1)  # Read the first band (depth values)
    transform = bathy.transform
    pixel_size = transform[0]  # Pixel size in meters (assumes square pixels)

# Replace no-data values with NaN
depth_data[depth_data == bathy.nodata] = np.nan

# 2. Define Depth Bins
bin_size = 1  # Bin thickness in meters
min_depth = np.nanmin(depth_data)  # Minimum depth
max_depth = np.nanmax(depth_data)  # Maximum depth
depth_bins = np.arange(np.floor(min_depth), np.ceil(max_depth) + bin_size, bin_size)

# 3. Calculate Volumes
pixel_area = pixel_size ** 2  # Area of one pixel in square meters
cumulative_volumes = []

for depth in depth_bins:
    # Mask pixels below the current depth
    mask = (depth_data >= depth)
    area_at_depth = np.nansum(mask) * pixel_area  # Sum of areas at this depth
    volume = area_at_depth * bin_size  # Volume = Area * Height (1m bin size)
    cumulative_volumes.append(volume)

# Convert to cumulative volume
cumulative_volumes = np.cumsum(cumulative_volumes)

# 4. Plot Depth vs. Volume
plt.figure(figsize=(10, 6))
plt.plot(cumulative_volumes, depth_bins, marker='o', linestyle='-', color='blue')
plt.gca().invert_yaxis()  # Depth increases downward
plt.title("Lake Victoria Depth-Volume Curve")
plt.xlabel("Cumulative Volume (m³)")
plt.ylabel("Depth (m)")
plt.grid()
plt.show()


#%%

# Depth vs. Surface Area of Lake Victoria

import rasterio
import numpy as np
import matplotlib.pyplot as plt

# 1. Load Bathymetry Data
file_path = "C:\DATA\Lake V Bathymentry\LakeVictoria_Bathymetry-Reprojected.tif"
with rasterio.open(file_path) as bathy:
    depth_data = bathy.read(1)  # Read the first band (depth values)
    transform = bathy.transform
    pixel_size = transform[0]  # Pixel size in meters (assumes square pixels)

# Replace no-data values with NaN
depth_data[depth_data == bathy.nodata] = np.nan

# 2. Define Depth Bins
bin_size = 1  # Bin thickness in meters
min_depth = np.nanmin(depth_data)  # Minimum depth
max_depth = np.nanmax(depth_data)  # Maximum depth
depth_bins = np.arange(np.floor(min_depth), np.ceil(max_depth) + bin_size, bin_size)

# 3. Calculate Surface Area
pixel_area = pixel_size ** 2  # Area of one pixel in square meters
surface_areas = []

for depth in depth_bins:
    # Mask pixels below the current depth bin
    mask = (depth_data >= depth) & (depth_data < depth + bin_size)
    area_at_depth = np.nansum(mask) * pixel_area  # Sum of areas for this depth bin
    surface_areas.append(area_at_depth)

# Convert surface area to square kilometers
surface_areas_km2 = np.array(surface_areas) / 1e6

# 4. Plot Depth vs. Surface Area
plt.figure(figsize=(10, 6))
plt.bar(depth_bins, surface_areas_km2, width=bin_size, color='skyblue', edgecolor='blue', align='center')
plt.gca().invert_xaxis()  # Optional: Invert x-axis to show depths descending
plt.title("Depth vs. Surface Area of Lake Victoria")
plt.xlabel("Depth (m)")
plt.ylabel("Surface Area (km²)")
plt.grid()
plt.show()

#%%

# Surface Area vs. Depth of Lake Victoria Changed Axies 

import rasterio
import numpy as np
import matplotlib.pyplot as plt

# 1. Load Bathymetry Data
file_path = "C:\DATA\Lake V Bathymentry\LakeVictoria_Bathymetry-Reprojected.tif"
with rasterio.open(file_path) as bathy:
    depth_data = bathy.read(1)  # Read the first band (depth values)
    transform = bathy.transform
    pixel_size = transform[0]  # Pixel size in meters (assumes square pixels)

# Replace no-data values with NaN
depth_data[depth_data == bathy.nodata] = np.nan

# 2. Define Depth Bins
bin_size = 1  # Bin thickness in meters
min_depth = np.nanmin(depth_data)  # Minimum depth
max_depth = np.nanmax(depth_data)  # Maximum depth
depth_bins = np.arange(np.floor(min_depth), np.ceil(max_depth) + bin_size, bin_size)

# 3. Calculate Surface Area
pixel_area = pixel_size ** 2  # Area of one pixel in square meters
surface_areas = []

for depth in depth_bins:
    # Mask pixels below the current depth bin
    mask = (depth_data >= depth) & (depth_data < depth + bin_size)
    area_at_depth = np.nansum(mask) * pixel_area  # Sum of areas for this depth bin
    surface_areas.append(area_at_depth)

# Convert surface area to square kilometers
surface_areas_km2 = np.array(surface_areas) / 1e6

# 4. Plot Surface Area vs. Depth
plt.figure(figsize=(10, 6))
plt.plot(surface_areas_km2, depth_bins, color='blue', marker='o', linestyle='-')
plt.gca().invert_yaxis()  # Optional: Invert y-axis to show depths descending
plt.title("Surface Area vs. Depth of Lake Victoria")
plt.xlabel("Surface Area (km²)")
plt.ylabel("Depth (m)")
plt.grid()
plt.show()

#%%

# Depth vs. Volume and Surface Area for Lake Victoria

import rasterio
import numpy as np
import matplotlib.pyplot as plt

# 1. Load Bathymetry Data
file_path = "C:\DATA\Lake V Bathymentry\LakeVictoria_Bathymetry-Reprojected.tif"
with rasterio.open(file_path) as bathy:
    depth_data = bathy.read(1)  # Read the first band (depth values)
    transform = bathy.transform
    pixel_size = transform[0]  # Pixel size in meters (assumes square pixels)

# Replace no-data values with NaN
depth_data[depth_data == bathy.nodata] = np.nan

# 2. Define Depth Bins
bin_size = 1  # Bin thickness in meters
min_depth = np.nanmin(depth_data)  # Minimum depth
max_depth = np.nanmax(depth_data)  # Maximum depth
depth_bins = np.arange(np.floor(min_depth), np.ceil(max_depth) + bin_size, bin_size)

# 3. Calculate Surface Area and Volume
pixel_area = pixel_size ** 2  # Area of one pixel in square meters
surface_areas = []
volumes = []

for depth in depth_bins:
    # Mask pixels below the current depth bin
    mask = (depth_data >= depth) & (depth_data < depth + bin_size)
    surface_area_at_depth = np.nansum(mask) * pixel_area  # Surface area for this depth bin
    volume_at_depth = np.nansum((depth_data >= depth) * (depth_data - depth) * pixel_area)  # Volume at this depth

    surface_areas.append(surface_area_at_depth)
    volumes.append(volume_at_depth)

# Convert surface area to square kilometers and volume to cubic kilometers
surface_areas_km2 = np.array(surface_areas) / 1e6
volumes_km3 = np.cumsum(np.array(volumes)) / 1e9  # Cumulative volume in cubic kilometers

# 4. Plot Combined Graph
fig, ax1 = plt.subplots(figsize=(12, 8))

# Plot Depth vs. Volume
ax1.plot(volumes_km3, depth_bins, color='red', label='Volume')
ax1.set_xlabel("Volume (km³)", color='red')
ax1.tick_params(axis='x', labelcolor='red')

# Invert y-axis for depth
ax1.set_ylabel("Depth (m)")
ax1.invert_yaxis()

# Create second x-axis for surface area
ax2 = ax1.twiny()
ax2.plot(surface_areas_km2, depth_bins, color='blue', label='Surface Area')
ax2.set_xlabel("Surface Area (km²)", color='blue')
ax2.tick_params(axis='x', labelcolor='blue')

# Add grid and title
plt.grid()
plt.title("Depth vs. Volume and Surface Area for Lake Victoria")
plt.show()


#%%

# DEPTH - SURFACE AREA & VOLUME WITH GRID LINES

import rasterio
import numpy as np
import matplotlib.pyplot as plt

# 1. Load Bathymetry Data
file_path = "C:\DATA\Lake V Bathymentry\LakeVictoria_Bathymetry-Reprojected.tif"
with rasterio.open(file_path) as bathy:
    depth_data = bathy.read(1)  # Read the first band (depth values)
    transform = bathy.transform
    pixel_size = transform[0]  # Pixel size in meters (assumes square pixels)

# Replace no-data values with NaN
depth_data[depth_data == bathy.nodata] = np.nan

# 2. Define Depth Bins
bin_size = 1  # Bin thickness in meters
min_depth = np.nanmin(depth_data)  # Minimum depth
max_depth = np.nanmax(depth_data)  # Maximum depth
depth_bins = np.arange(np.floor(min_depth), np.ceil(max_depth) + bin_size, bin_size)

# 3. Calculate Surface Area and Volume
pixel_area = pixel_size ** 2  # Area of one pixel in square meters
surface_areas = []
volumes = []

for depth in depth_bins:
    # Mask pixels below the current depth bin
    mask = (depth_data >= depth) & (depth_data < depth + bin_size)
    surface_area_at_depth = np.nansum(mask) * pixel_area  # Surface area for this depth bin
    volume_at_depth = np.nansum((depth_data >= depth) * (depth_data - depth) * pixel_area)  # Volume at this depth

    surface_areas.append(surface_area_at_depth)
    volumes.append(volume_at_depth)

# Convert surface area to square kilometers and volume to cubic kilometers
surface_areas_km2 = np.array(surface_areas) / 1e6
volumes_km3 = np.cumsum(np.array(volumes)) / 1e9  # Cumulative volume in cubic kilometers

# 4. Plot Combined Graph
fig, ax1 = plt.subplots(figsize=(12, 8))

# Plot Depth vs. Volume
ax1.plot(volumes_km3, depth_bins, color='red', label='Volume')
ax1.set_xlabel("Volume (km³)", color='red')
ax1.tick_params(axis='x', labelcolor='red')

# Invert y-axis for depth
ax1.set_ylabel("Depth (m)")
ax1.invert_yaxis()

# Create second x-axis for surface area
ax2 = ax1.twiny()
ax2.plot(surface_areas_km2, depth_bins, color='blue', label='Surface Area')
ax2.set_xlabel("Surface Area (km²)", color='blue')
ax2.tick_params(axis='x', labelcolor='blue')

# Add grid lines
ax1.grid(visible=True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

# Add title
plt.title("Depth vs. Volume and Surface Area for Lake Victoria")
plt.show()





#%%

# Hypsograph of Lake Victoria

import rasterio
import numpy as np
import matplotlib.pyplot as plt

# 1. Load Bathymetry Data
file_path = "C:\DATA\Lake V Bathymentry\LakeVictoria_Bathymetry-Reprojected.tif"
with rasterio.open(file_path) as bathy:
    depth_data = bathy.read(1)  # Read the first band (depth values)
    transform = bathy.transform
    pixel_size = transform[0]  # Pixel size in meters (assumes square pixels)

# Replace no-data values with NaN
depth_data[depth_data == bathy.nodata] = np.nan

# 2. Define Depth Bins
bin_size = 1  # Bin thickness in meters
min_depth = np.nanmin(depth_data)
max_depth = np.nanmax(depth_data)
depth_bins = np.arange(np.floor(min_depth), np.ceil(max_depth) + bin_size, bin_size)

# 3. Calculate Surface Area and Volume
pixel_area = pixel_size ** 2  # Area of one pixel in square meters
cumulative_surface_area = []
cumulative_volume = []

for depth in depth_bins:
    # Mask pixels below the current depth
    mask = depth_data <= depth
    surface_area = np.nansum(mask) * pixel_area  # Surface area up to this depth
    volume = np.nansum((depth - depth_data) * mask * pixel_area)  # Volume up to this depth
    
    cumulative_surface_area.append(surface_area / 1e6)  # Convert to km²
    cumulative_volume.append(volume / 1e9)  # Convert to km³

# 4. Plot the Hypsograph
fig, ax1 = plt.subplots(figsize=(10, 8))

# Plot Cumulative Surface Area vs. Depth
ax1.plot(cumulative_surface_area, depth_bins, label='Surface Area', color='blue')
ax1.set_xlabel("Cumulative Surface Area (km²)", color='blue')
ax1.tick_params(axis='x', labelcolor='blue')

# Plot Cumulative Volume vs. Depth on the second x-axis
ax2 = ax1.twiny()
ax2.plot(cumulative_volume, depth_bins, label='Volume', color='red')
ax2.set_xlabel("Cumulative Volume (km³)", color='red')
ax2.tick_params(axis='x', labelcolor='red')

# Invert y-axis for depth
ax1.set_ylabel("Depth (m)")
ax1.invert_yaxis()

# Add grid and title
plt.title("Hypsograph of Lake Victoria")
plt.grid()
plt.show()


#%%

# HYPSOGRAPH WITH GRID LINES

import rasterio
import numpy as np
import matplotlib.pyplot as plt

# 1. Load Bathymetry Data
file_path = "C:\DATA\Lake V Bathymentry\LakeVictoria_Bathymetry-Reprojected.tif"
with rasterio.open(file_path) as bathy:
    depth_data = bathy.read(1)  # Read the first band (depth values)
    transform = bathy.transform
    pixel_size = transform[0]  # Pixel size in meters (assumes square pixels)

# Replace no-data values with NaN
depth_data[depth_data == bathy.nodata] = np.nan

# 2. Define Depth Bins
bin_size = 1  # Bin thickness in meters
min_depth = np.nanmin(depth_data)
max_depth = np.nanmax(depth_data)
depth_bins = np.arange(np.floor(min_depth), np.ceil(max_depth) + bin_size, bin_size)

# 3. Calculate Surface Area and Volume
pixel_area = pixel_size ** 2  # Area of one pixel in square meters
cumulative_surface_area = []
cumulative_volume = []

for depth in depth_bins:
    # Mask pixels below the current depth
    mask = depth_data <= depth
    surface_area = np.nansum(mask) * pixel_area  # Surface area up to this depth
    volume = np.nansum((depth - depth_data) * mask * pixel_area)  # Volume up to this depth
    
    cumulative_surface_area.append(surface_area / 1e6)  # Convert to km²
    cumulative_volume.append(volume / 1e9)  # Convert to km³

# 4. Plot the Hypsograph
fig, ax1 = plt.subplots(figsize=(10, 8))

# Plot Cumulative Surface Area vs. Depth
ax1.plot(cumulative_surface_area, depth_bins, label='Surface Area', color='blue')
ax1.set_xlabel("Cumulative Surface Area (km²)", color='blue')
ax1.tick_params(axis='x', labelcolor='blue')

# Plot Cumulative Volume vs. Depth on the second x-axis
ax2 = ax1.twiny()
ax2.plot(cumulative_volume, depth_bins, label='Volume', color='red')
ax2.set_xlabel("Cumulative Volume (km³)", color='red')
ax2.tick_params(axis='x', labelcolor='red')

# Invert y-axis for depth
ax1.set_ylabel("Depth (m)")
ax1.invert_yaxis()

# Add grid and improve layout
ax1.grid(visible=True, which='both', linestyle='--', linewidth=0.5)
ax2.grid(visible=False)  # Ensure no conflicting grids are drawn

# Add major and minor ticks for depth
ax1.set_xticks(np.linspace(0, max(cumulative_surface_area), 10), minor=False)
ax1.set_yticks(np.linspace(min_depth, max_depth, 10), minor=False)
ax1.minorticks_on()

# Add title and legend
plt.title("Hypsograph of Lake Victoria")
plt.show()
