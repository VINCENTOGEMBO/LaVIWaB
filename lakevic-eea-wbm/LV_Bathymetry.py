# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 12:07:23 2024

@author: VO000003
"""


#%%

import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

# Open the NetCDF file with xarray
ds = xr.open_dataset("C:\DATA\clipped_bathymetry_lake_victoria.nc")

# Inspect the dataset structure
print(ds)

# Check if the dataset contains coordinates or grids
print(ds.coords)  # Check available coordinate names

# Assuming 'elevation' exists and coordinates are automatically recognized
if 'lat' in ds.coords and 'lon' in ds.coords:
    lat = ds.coords['lat']
    lon = ds.coords['lon']
    depth = ds['elevation']  # Or another variable name for bathymetry

    # Create the plot
    fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()})
    ax.set_extent([31, 35, -3, 1])  # Approximate coordinates for Lake Victoria

    # Plot the bathymetric data
    contour = ax.contourf(lon, lat, depth, levels=30, cmap='Purples')

    # Add coastlines and other features
    ax.coastlines()
    ax.set_title('Lake Victoria Bathymetry (Plan View)')

    # Add colorbar for depth
    fig.colorbar(contour, ax=ax, orientation='horizontal', label='Depth (m)')

    plt.show()
else:
    print("Coordinates or bathymetric data not found!")


#%%

import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

# Load the NetCDF file using xarray
file_path = r"C:\DATA\clipped_bathymetry_lake_victoria.nc"
ds = xr.open_dataset(file_path)

# Inspect the dataset to verify latitude, longitude, and bathymetry variables
print(ds)

# Extract latitude, longitude, and bathymetric data
lat = ds.coords['latitude']  # Latitude values
lon = ds.coords['longitude']  # Longitude values
depth = ds['depth']  # Bathymetric data (depth)

# Create the plot with larger figure size
fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()}, figsize=(12, 10))  # Adjust figsize here
ax.set_extent([31, 35, -3, 1])  # Approximate coordinates for Lake Victoria

# Plot the bathymetric data
contour = ax.contourf(lon, lat, depth, levels=30, cmap='Purples')

# Add coastlines and other features
ax.coastlines()
ax.set_title('Lake Victoria Bathymetry (Plan View)')

# Add colorbar for depth
fig.colorbar(contour, ax=ax, orientation='horizontal', label='Depth (m)')

# Show the plot
plt.show()




#%%
# LAKE VICTORIA BATHYMETRIC CROSS-SECTIONAL VIEW

import xarray as xr
import matplotlib.pyplot as plt
import numpy as np  # For numerical operations

# Load the NetCDF file using xarray
file_path = r"C:\DATA\clipped_bathymetry_lake_victoria.nc"
ds = xr.open_dataset(file_path)

# Inspect the dataset to verify latitude, longitude, and bathymetry variables
print(ds)

# Extract latitude, longitude, and bathymetric data
lat = ds.coords['latitude']  # Latitude values
lon = ds.coords['longitude']  # Longitude values
depth = ds['depth']  # Bathymetric data (depth)

# Extract depth data across all latitudes
# We'll take depth data for each latitude, averaged over all longitudes (across the entire lake surface)
#depth_across_latitudes = depth.mean(dim='longitude')  # Mean depth across all longitudes for each latitude

# Plot the cross-sectional depth profile across all latitudes
plt.figure(figsize=(12, 6))
plt.plot(lat, depth, label='Average Depth Across Latitudes', color='b')

# Customize the plot
plt.title('Cross-Sectional Depth Profile Across Lake Victoria')
plt.xlabel('Latitude (°)')
plt.ylabel('Depth (m)')
plt.grid(True)
plt.legend()
plt.tight_layout()

# Show the plot
plt.show()


#%%

#CROSS SECTION VIW 2

import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

# Load the NetCDF file using xarray
file_path = r"C:\DATA\clipped_bathymetry_lake_victoria.nc"
ds = xr.open_dataset(file_path)

# Inspect the dataset to verify latitude, longitude, and bathymetry variables
print(ds)

# Extract latitude, longitude, and bathymetric data
lat = ds.coords['latitude']  # Latitude values
lon = ds.coords['longitude']  # Longitude values
depth = ds['depth']  # Bathymetric data (depth)

# Create the plot with a Cartopy map
fig, ax = plt.subplots(figsize=(12, 8), subplot_kw={'projection': ccrs.PlateCarree()})

# Set map extent for Lake Victoria region
ax.set_extent([31, 35, -3, 1])  # Approximate coordinates for Lake Victoria

# Plot the bathymetric data using contour lines
contour = ax.contour(lon, lat, depth, levels=20, cmap='Purples', linewidths=1)

# Add coastlines and other features
ax.coastlines()
ax.set_title('Gridded Bathymetric Depth View with Contour Lines')

# Add a colorbar for depth
fig.colorbar(contour, ax=ax, orientation='horizontal', label='Depth (m)')

# Show the plot
plt.tight_layout()
plt.show()



#%%

# ENLARGED VISUALIZATION 

import netCDF4 as nc
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

# Load the bathymetry data
file_path = "C:\DATA\clipped_bathymetry_lake_victoria.nc"  # Replace with your file path
dataset = nc.Dataset(file_path)

# Extract latitude, longitude, and depth
lat = dataset.variables['lat'][:]  # Latitude values
lon = dataset.variables['lon'][:]  # Longitude values
depth = dataset.variables['elevation'][:]  # Bathymetry data (depth/elevation)

# Set up the figure and axis with a larger size
fig, ax = plt.subplots(figsize=(12, 10), subplot_kw={'projection': ccrs.PlateCarree()})

# Zoom into the Lake Victoria region (extent in longitude and latitude)
ax.set_extent([31, 35, -3, 1], crs=ccrs.PlateCarree())  # Lake Victoria bounding box

# Plot the bathymetric data with more contour levels
contour = ax.contourf(lon, lat, depth, levels=50, cmap='Reds')  # Increased levels for detail

# Add coastlines with higher resolution
ax.coastlines(resolution='10m')  # High resolution for more detail around the lake
ax.set_title('Lake Victoria Bathymetry Plan View', fontsize=16)

# Add color bar for depth visualization
cbar = fig.colorbar(contour, ax=ax, orientation='horizontal', pad=0.05, aspect=50)
cbar.set_label('Depth (m)', fontsize=12)

# Show the enlarged plot
plt.show()


#%%

# 1. Load the Bathymetry Data
import netCDF4 as nc
import numpy as np
import rasterio
from rasterio.transform import from_origin
import matplotlib.pyplot as plt

# Load the bathymetry data
file_path = "C:\DATA\clipped_bathymetry_lake_victoria.nc"  # Replace with your file path
dataset = nc.Dataset(file_path)

# Extract variables (latitude, longitude, and depth)
lat = dataset.variables['lat'][:]  # Latitude values
lon = dataset.variables['lon'][:]  # Longitude values
depth = dataset.variables['elevation'][:]  # Bathymetry data (depth/elevation)

# Reshape lat/lon to create a 2D meshgrid (if needed for the data)
lon2d, lat2d = np.meshgrid(lon, lat)


# 2. Load External Raster Data (ASTER GDEM V3 or Pekel)

import rasterio

# Load external raster data (ASTER GDEM or Pekel) at 30m resolution
raster_path = "C:\DATA\LakeVictoria_WaterOccurrence.tif"  # Replace with your file path
raster = rasterio.open(raster_path)

# Get raster metadata
raster_meta = raster.meta
print(raster_meta)  # Check the coordinate system, dimensions, resolution, etc.

# Read raster data
raster_data = raster.read(1)  # Reading the first band (elevation)


# 3. Align the Bathymetry Data to the Raster’s Grid (Resample to 30m x 30m Resolution)

from rasterio.warp import reproject, Resampling

# Define the output array with the same shape as the raster dataset
bathymetry_resampled = np.empty_like(raster_data)

# Reproject bathymetry data to match the external raster's grid (30m resolution)
transform = raster.transform
reproject(
    source=depth,
    destination=bathymetry_resampled,
    src_transform=from_origin(lon.min(), lat.max(), lon[1] - lon[0], lat[1] - lat[0]),
    src_crs='EPSG:4326',  # Assuming WGS84 for the bathymetry data
    dst_transform=transform,
    dst_crs=raster.crs,
    resampling=Resampling.bilinear  # Bilinear interpolation for resampling
)


# 4. Create the “Lake Extent” Variable

# Create a mask for lake extent (assuming bathymetry values below zero represent water)
lake_extent = np.where(bathymetry_resampled < 0, 1, 0)  # 1 = Lake, 0 = Non-lake

# Plot the lake extent
plt.imshow(lake_extent, cmap='Blues')
plt.title('Lake Victoria Extent (aligned with ASTER/Pekel)')
plt.colorbar(label='Lake/Non-Lake')
plt.show()


# 5. Save the Aligned and Resampled Bathymetry Data

# Define output path for the aligned bathymetry data
output_path = 'aligned_bathymetry.tif'

# Update the metadata for the new raster file
new_meta = raster.meta.copy()
new_meta.update({
    "dtype": 'float32',  # Update data type
    "count": 1,          # One band for bathymetry
    "compress": 'lzw'    # Compression option
})

# Write the aligned bathymetry data to a new GeoTIFF file
with rasterio.open(output_path, 'w', **new_meta) as dst:
    dst.write(bathymetry_resampled, 1)
    

# Assuming your raster data is already loaded as a NumPy array, for example:
# lake_extent_data = np.load('lake_extent.npy')  # Example for loading

# For this example, I'll assume the array is lake_extent_data
lake_extent_data = np.random.random((15000, 15000)) * 0.1  # Simulated data, replace with actual data

# Create a figure with larger size
fig, ax = plt.subplots(figsize=(10, 8))

# Plot the data with enhanced color contrast
cax = ax.imshow(lake_extent_data, cmap='Blues', vmin=-0.1, vmax=0.1)

# Add a color bar with more descriptive labels
cbar = fig.colorbar(cax, ax=ax, orientation='vertical', shrink=0.8)
cbar.set_label('Lake/Non-Lake Classification')

# Set title with more description
ax.set_title('Lake Victoria Extent (Aligned with ASTER/Pekel) - 30m Resolution')

# Add axis labels (replace with actual coordinate values if known)
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')

# Optionally, overlay a shapefile of Lake Victoria’s boundary for context (requires geopandas or rasterio)
# from geopandas import read_file
# shape = read_file('lake_victoria_shapefile.shp')  # Example of loading shapefile
# shape.boundary.plot(ax=ax, color='red')  # Add lake boundary

# Display the plot
plt.show()
