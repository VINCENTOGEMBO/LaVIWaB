# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 05:53:38 2024

@author: VO000003
"""

import pandas as pd
import rasterio
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.animation as animation


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



#%%
# 1. Load Bathymetry Data
file_path = "C:\DATA\Lake V Bathymentry\LakeVictoria_Bathymetry-Reprojected.tif"
with rasterio.open(file_path) as bathy:
    depth_data = bathy.read(1)  # Read the first band (depth values)
    transform = bathy.transform
    pixel_size = transform[0]  # Pixel size in meters (assumes square pixels)

# Replace no-data values with NaN
depth_data[depth_data == bathy.nodata] = np.nan


#%%

   
# 1b. Open topography data and merge with bathymetry 


with rasterio.open(bathymetry_tiff) as bathy_src, rasterio.open(basin_topography_tiff) as topo_src:
    bathymetry_data = bathy_src.read(1)
    topography_data = topo_src.read(1)
    transform = bathy_src.transform
    pixel_area = bathy_src.res[0] * bathy_src.res[1]  # Resolution of approximately 500m x 500m (e.g., meters^2) - GEBCO global bathymetry: ~470m (~15 arc-seconds)

# put together bathymetry and topography data
# turn zeros in topography (indicate areas outside of basin), to nan
topography_data[topography_data==0] = 'nan'
print(f'min elevation, {np.nanmin(topography_data)}')

# combine bathymetry and topography data
bath_zeros = np.nan_to_num(bathymetry_data, copy=True,nan=0)
bath_topo = np.subtract(topography_data, bath_zeros)

# Plot Topography - Bathymetry
fig, ax = plt.subplots()
plot = ax.imshow(bath_topo)
cbar = fig.colorbar(plot, ax=ax, shrink=0.4)
ax.set_title("Topography - Bathymetry")


#%%


# 2. Define Depth Bins
bin_size = .01  # Bin thickness in meters
min_depth = np.nanmin(depth_data)  # Minimum depth
max_depth = np.nanmax(depth_data)  # Maximum depth
depth_bins = np.arange(np.floor(min_depth), np.ceil(max_depth) + bin_size, bin_size)


#%%


# 3. Calculate Volumes for different depths
pixel_area = pixel_size ** 2  # Area of one pixel in square meters
volumes_at_depth = []
areas_at_depth = []

for depth in depth_bins:
    # Mask pixels below the current depth
    mask = (depth >= (np.nanmax(depth_data) - depth_data) )
    # get area at current depth
    area_at_depth = np.nansum(mask) * pixel_area  # Sum of areas at this depth (number of pixels * pixel area) m2
    # get masked depth
    masked_depth = np.where(mask, depth_data, np.nan)
    # calculate volume as sum of depth, maxed out at the depth of water
    max_depth = np.where(mask, np.minimum(masked_depth, depth), np.nan)
    volume = np.nansum(max_depth)
    # save output
    volumes_at_depth.append(volume)
    areas_at_depth.append(area_at_depth)


#%%

# 4. Plot Depth vs. Volume
plt.figure(figsize=(10, 6))
plt.plot( np.array(volumes_at_depth) / 1e6 , depth_bins, marker='o', linestyle='-', color='blue')
plt.gca().invert_yaxis()  # Depth increases downward
plt.title("Lake Victoria Depth-Volume Curve")
plt.xlabel("Volume (km³)")
plt.ylabel("Depth (m)")
plt.grid()
plt.show()

#%%

# 5. Depth vs. area

plt.figure(figsize=(10, 6))
plt.plot( np.array(areas_at_depth) / 1e6 , depth_bins, marker='o', linestyle='-', color='blue')
plt.gca().invert_yaxis()  # Depth increases downward
plt.title("Lake Victoria Depth-Area Curve")
plt.xlabel("Area (km$^2$)")
plt.ylabel("Depth (m)")
plt.grid()
plt.show()





#%% PART 2 : Add topography as well to extend beyond bathymetry confines 




# 2. Define Depth Bins
bin_size = .01  # Bin thickness in meters
min_depth = np.nanmin(depth_data)  # Minimum depth
max_depth = np.nanmax(depth_data + 17 )  # Maximum depth
depth_bins = np.arange(np.floor(min_depth), np.ceil(max_depth) + bin_size, bin_size)


#%%

# Create a larger figure with 4 subplots
fig, axes = plt.subplots(1, 3, figsize=(16, 6))  

# Bathymetry
ax = axes[0]
plt1 = ax.imshow(bathymetry_data)
cbar = fig.colorbar(plt1, ax=ax, shrink=0.4) 
ax.set_title("Bathymetry")

# Topography
ax = axes[1]
plt2 = ax.imshow(topography_data)
cbar = fig.colorbar(plt2, ax=ax, shrink=0.4)
ax.set_title("Topography")

# Topography - Bathymetry
ax = axes[2]
plt3 = ax.imshow(bath_topo)
cbar = fig.colorbar(plt3, ax=ax, shrink=0.4)
ax.set_title("Topography - Bathymetry")

# Adjust layout for better spacing
plt.tight_layout()
plt.show()


#%%

fig,ax=plt.subplots()
test = np.where(bath_topo<1136, bath_topo, np.nan)
plot = plt.imshow(test)
cbar = fig.colorbar(plot, ax=ax, shrink=0.4)


#%%

max_index = np.unravel_index(np.nanargmax(bathymetry_data), bathymetry_data.shape)
# Get the corresponding bath_topo value
bath_topo_at_max_bathy = bath_topo[max_index]
print(f"Maximum Bathymetry Value: {bathymetry_data[max_index]}")
print(f"Bath_Topo at this location: {bath_topo_at_max_bathy}")

#Maximum Bathymetry Value: 82.76689147949219
#Bath_Topo at this location: 1051.233154296875


#%%


# 3. Calculate Volumes for different depths
pixel_area = pixel_size ** 2  # Area of one pixel in square meters
volumes_at_depth = []
areas_at_depth = []
masks =[]


for depth in depth_bins[-10:]:
    # Mask pixels below the current depth
    mask = (bath_topo <= bath_topo_at_max_bathy + depth )
    # get area at current depth
    area_at_depth = np.nansum(mask) * pixel_area  # Sum of areas at this depth (number of pixels * pixel area) m2
    # get masked depth
    masked_depth = np.where(mask, bath_topo - bath_topo_at_max_bathy , np.nan)
    # calculate volume as sum of depth, maxed out at the depth of water
    max_depth = np.where(mask, np.minimum(masked_depth, depth), np.nan)
    volume = np.nansum(max_depth * pixel_area)
    # save output
    volumes_at_depth.append(volume)
    areas_at_depth.append(area_at_depth)
    # get the mask as a DataArray netcdf
    masks.append(mask)


masks = np.stack(masks)

lakearea_masks_da = xr.DataArray(
    data=np.flip(masks,axis=1),
    dims=["depth","lon","lat"],
    coords=dict(
        depth=depth_bins[-10:],
        lon=np.arange(masks.shape[1]),
        lat=np.arange(masks.shape[2]))

    )


#%%

# 4. Plot Depth vs. Volume
plt.figure(figsize=(10, 6))
plt.plot( np.array(volumes_at_depth)  , depth_bins, marker='o', linestyle='-', color='blue')
plt.gca().invert_yaxis()  # Depth increases downward
plt.title("Lake Victoria Depth-Volume Curve")
plt.xlabel("Volume (m³)")
plt.ylabel("Depth (m)")
plt.grid()
plt.show()

#%%

# 5. Depth vs. area

plt.figure(figsize=(10, 6))

plt.plot( np.array(areas_at_depth) /1e6 , depth_bins, marker='o', linestyle='-', color='blue')
plt.gca().invert_yaxis()  # Depth increases downward
plt.title("Lake Victoria Depth-Area Curve")
plt.xlabel("Area (km$^2$)")
plt.ylabel("Depth (m)")
plt.grid()
plt.show()




#%% Save this

data=np.stack([depth_bins, np.array(areas_at_depth)]).T

#%%
df_area_depth_curve = pd.DataFrame(
    data=data,
    columns= ['depth_m','area_m2']
    )

#df_area_depth_curve.to_csv('/Users/VO000003/OneDrive - Vrije Universiteit Brussel/Ogembo_LVictoria_IWBM/lakevic-eea-wbm/input_data/hypsograph/WBM_depth_area_curve.csv',
#                           index=False)




#Find elevation of 0 depth of lake level 




#%%
import pandas as pd

# make it into a function

# get point where lake has maximum abslute depth
max_index = np.unravel_index(np.nanargmax(bathymetry_data), bathymetry_data.shape)
# Get the corresponding bath_topo value, ie baseline elevation at this point
bath_topo_at_max_bathy = bath_topo[max_index]

def calculate_areas_per_depth_bin(
        depth_bins,
        bath_topo, # bathymetry and topography together 
        bath_topo_at_max_bathy = bath_topo_at_max_bathy,
        pixel_area = pixel_size ** 2 # pixel_size has to be defined 
        ):
    
    volumes_at_depth = []
    areas_at_depth = []

    for depth in depth_bins:
        # Mask pixels below the current depth
        mask = (bath_topo <= bath_topo_at_max_bathy + depth )
        # get area at current depth
        area_at_depth = np.nansum(mask) * pixel_area  # Sum of areas at this depth (number of pixels * pixel area) m2
        # get masked depth
        masked_depth = np.where(mask, bath_topo - bath_topo_at_max_bathy , np.nan)
        # calculate volume as sum of depth*area, maxed out at the depth of water
        max_depth = np.where(mask, np.minimum(masked_depth, depth), np.nan)
        volume = np.nansum(max_depth * pixel_area)
        # save output
        volumes_at_depth.append(volume)
        areas_at_depth.append(area_at_depth)
        
        
    data=np.stack([depth_bins, np.array(areas_at_depth), np.array(volumes_at_depth)]).T
    
    df_area_depth_curve = pd.DataFrame(
        data=data,
        columns= ['depth_m','area_m2', 'vol_m3']
        )
    
    return df_area_depth_curve.set_index('depth_m')




df_area_depth_curve = calculate_areas_per_depth_bin(depth_bins, bath_topo)

#%%

# plot area, volume 


# Create figure and axes
fig, axes = plt.subplots(2, 1, sharex=True, figsize=(10, 8))

# Plot Lake Area
ax = axes[0]
ax.plot(df_area_depth_curve.index + bath_topo_at_max_bathy, df_area_depth_curve['area_m2'] / 1e6, label="Lake Area", color='b')
ax.set_ylabel('Lake Area (km²)')
ax.grid(True)

# Plot Lake Volume
ax = axes[1]
ax.plot(df_area_depth_curve.index + bath_topo_at_max_bathy, df_area_depth_curve['vol_m3'] / 1e9, label="Lake Volume", color='g')
ax.set_ylabel('Lake Volume (km³)')
ax.set_xlabel('Lake Levels (masl)')
ax.grid(True)

# Add title
fig.suptitle('Lake Victoria WB Model: Area & Volume vs Lake Levels')

# Show plot
plt.show()


#%%

#Plotting Lake Area, Volume, Levels with Projection

# Define lake level range for 10m intervals
lake_levels = df_area_depth_curve.index + bath_topo_at_max_bathy
tick_min = np.floor(lake_levels.min() / 10) * 10  # Round down to nearest 10
tick_max = np.ceil(lake_levels.max() / 10) * 10   # Round up to nearest 10
tick_intervals = np.arange(tick_min, tick_max + 10, 10)  # 10m step

# Create figure and axes
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot Lake Area (Left Y-Axis)
ax1.plot(lake_levels, df_area_depth_curve['area_m2'] / 1e6, label="Lake Area", color='b')
ax1.set_xlabel('Lake Levels (masl)')
ax1.set_ylabel('Lake Area (km²)', color='b')
ax1.tick_params(axis='y', labelcolor='b')
ax1.grid(True, linestyle='--')

# Set x-axis ticks to be at 10m intervals
ax1.set_xticks(tick_intervals)

# Create a second y-axis for Lake Volume
ax2 = ax1.twinx()
ax2.plot(lake_levels, df_area_depth_curve['vol_m3'] / 1e9, label="Lake Volume", color='r')
ax2.set_ylabel('Lake Volume (km³)', color='r')
ax2.tick_params(axis='y', labelcolor='r')

# Add title
plt.title('Lake Victoria WB Model: Area & Volume vs Lake Levels')

# Show plot
plt.show()


#%% make function that outputs the masks per each level, area


def calculate_masks_per_depth_bin(
        depth_bins,
        bath_topo, # bathymetry and topography together 
        bath_topo_at_max_bathy = bath_topo_at_max_bathy,
        pixel_area = pixel_size ** 2 # pixel_size has to be defined 
        ):
    

    masks=[]
    for depth in depth_bins:
        # Mask pixels below the current depth
        mask = (bath_topo <= bath_topo_at_max_bathy + depth )
        
        # get the mask as a DataArray netcdf
        masks.append(mask)

    masks = np.stack(masks)

    lakearea_masks_da = xr.DataArray(
        data=np.flip(masks,axis=1),
        dims=["depth","lon","lat"],
        coords=dict(
            depth=depth_bins,
            lon=np.arange(masks.shape[1]),
            lat=np.arange(masks.shape[2]))

        )
    
    return lakearea_masks_da

#%%

# Test

lakearea_masks_da = calculate_masks_per_depth_bin(
        depth_bins,
        bath_topo)

lakearea_masks_da.to_netcdf('lakearea_masks_da.nc')


#%%


lakearea_masks_da.sel(depth=73).plot()
plt.show()
lakearea_masks_da.sel(depth=76).plot()
plt.show()
lakearea_masks_da.sel(depth=79).plot()
plt.show()
lakearea_masks_da.sel(depth=82).plot()
plt.show()
lakearea_masks_da.sel(depth=85).plot()
plt.show()
lakearea_masks_da.sel(depth=88).plot()
plt.show()
lakearea_masks_da.sel(depth=91).plot()
plt.show()

#%%

data_plot = lakearea_masks_da.sel(depth=83.00004, method='nearest')
data_plot.where(data_plot!=0).plot(cmap='Blues', add_colorbar=False)




#%%

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

# Load the NetCDF file
nc_file = r"C:\DATA\Lake Area Mask\lakearea_masks_da.nc"  # Adjust the path
ds = xr.open_dataset(nc_file)

# Print dataset structure to check available variables
print(ds)

# Select the variable inside the dataset (adjust the variable name if needed)
variable_name = list(ds.keys())[0]  # Automatically selects the first variable
data_var = ds[variable_name]  # Extract the DataArray

# Define depths to visualize
depth_levels = [70, 72, 74, 76, 78, 80, 82, 84, 86, 88, 90, 93]

# Plot each depth level
for depth in depth_levels:
    plt.figure(figsize=(8, 6))
    
    # Select data for the current depth
    data_plot = data_var.sel(depth=depth, method='nearest')
    
    # Plot the lake mask
    img = data_plot.where(data_plot != 0).plot(cmap='Blues', add_colorbar=True)

    # Title and labels
    plt.title(f'Lake Victoria Area at Depth = {depth}m', fontsize=12, fontweight='bold')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')

    # Show plot
    plt.show()

    #%%
# CREATE A MOVIE

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Load the NetCDF file
nc_file = r"C:\DATA\Lake Area Mask\lakearea_masks_da.nc"  # Adjust the path
ds = xr.open_dataset(nc_file)

# Select the variable inside the dataset (adjust the variable name if needed)
variable_name = list(ds.keys())[0]  # Automatically selects the first variable
data_var = ds[variable_name]  # Extract the DataArray

# Define depths to visualize
# [70, 72, 74, 76, 78, 80, 81, 82, 83, 83, 84, 86, 88, 90, 93, 88, 84, 80, 76, 72, 70, 76, 78, 80, 81, 82, 83, 83]
depth_levels = lakelevels['water_level'] - bath_topo_at_max_bathy
depth_levels = depth_levels['1984-01-01':'2023-12-31']
# e.g. depth_levels[['2006-10-01','2007-05-05','2020-05-10']]

# could plot only one level per month to make it faster ! e.g. mean monthly level or first of month 

# Create figure
fig, ax = plt.subplots(figsize=(8, 6))

# Function to update each frame
def update(frame):
    ax.clear()

    
    # Select data for the current depth
    depth = depth_levels[frame]
    date = depth_levels.index[frame].date()
    data_plot = data_var.sel(depth=depth, method='nearest')
    
    # Plot the lake mask
    img = data_plot.where(data_plot != 0).plot(ax=ax, cmap='Blues', add_colorbar=False)

    # Set title with changing lake surface area
    #ax.set_title(f'Lake Victoria Area at Depth = {depth}m', fontsize=12, fontweight='bold')
    ax.set_title(f'Lake Victoria Area {date} ({depth + bath_topo_at_max_bathy:.2f}m)', fontsize=12, fontweight='bold') # depth + bath_topo_at_max_bathy (masl)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')

    return img

# Create animation
ani = animation.FuncAnimation(fig, update, frames=len(depth_levels), interval=1)

# Save the animation as an MP4 file
ani.save('lake_area_animation_test3.mp4', writer='ffmpeg', dpi=150)

# Show the animation (optional)
plt.show()



#%%

# Overlay Lake Mask with OpenStreetMap

import rasterio
import numpy as np
import geopandas as gpd
import folium
import matplotlib.pyplot as plt
from rasterio.plot import show
from rasterio.enums import Resampling
from rasterio.warp import reproject
from shapely.geometry import shape
import contextily as ctx
from shapely.ops import unary_union
from rasterio.features import shapes  # Importing the missing function

# Paths to the bathymetry and topography GeoTIFF files
tif_file_bathymetry = r"C:\DATA\Lake V Bathymentry\LakeVictoria_BathymetryGEE.tif"
tif_file_topography = r"C:\DATA\Lake Basin Topography\LakeVictoriaBasinDEM.tif"

# Open the Bathymetry GeoTIFF using rasterio
with rasterio.open(tif_file_bathymetry) as src_bathy:
    bathymetry_data = src_bathy.read(1)  # Read first band (bathymetry data)
    bathymetry_transform = src_bathy.transform
    bathymetry_crs = src_bathy.crs  # CRS of the bathymetry raster

# Open the Topography GeoTIFF using rasterio
with rasterio.open(tif_file_topography) as src_topo:
    topography_data = src_topo.read(1)  # Read first band (topography data)
    topography_transform = src_topo.transform
    topography_crs = src_topo.crs  # CRS of the topography raster

# Plot with OpenStreetMap background for visualization of bathymetry and topography
fig, ax = plt.subplots(figsize=(10, 10))
show(bathymetry_data, transform=bathymetry_transform, ax=ax, cmap='Blues', title="Lake Victoria Bathymetry")
ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

plt.show()

# Interactive Visualization with Folium

# Create an interactive map centered on a default location (Lake Victoria's center)
centroid_lat, centroid_lon = -0.5, 33.0  # Center of Lake Victoria
m = folium.Map(location=[centroid_lat, centroid_lon], zoom_start=8, tiles="OpenStreetMap")

# Add bathymetry layer as an image overlay (optional visualization)
bathymetry_layer = folium.raster_layers.ImageOverlay(
    image=bathymetry_data, 
    bounds=[[bathymetry_transform[5], bathymetry_transform[0]], 
            [bathymetry_transform[5] + bathymetry_data.shape[0] * bathymetry_transform[4], 
             bathymetry_transform[0] + bathymetry_data.shape[1] * bathymetry_transform[1]]],
    opacity=0.5,
    name="Bathymetry"
)
bathymetry_layer.add_to(m)

# Add topography layer as an image overlay (optional visualization)
topography_layer = folium.raster_layers.ImageOverlay(
    image=topography_data, 
    bounds=[[topography_transform[5], topography_transform[0]], 
            [topography_transform[5] + topography_data.shape[0] * topography_transform[4], 
             topography_transform[0] + topography_data.shape[1] * topography_transform[1]]],
    opacity=0.5,
    name="Topography"
)
topography_layer.add_to(m)

# Save the interactive map as an HTML file
m.save("lake_victoria_bathymetry_topography.html")

# Display the folium map
m


#%%

import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject
from pyproj import CRS
import xarray as xr
from rasterio.enums import Resampling
import matplotlib.pyplot as plt

# Load the NetCDF file using xarray
nc_file = r"C:\DATA\Lake Area Mask\lakearea_masks_da.nc"  # Adjust the path
ds = xr.open_dataset(nc_file)

# Select the variable inside the dataset (adjust the variable name if needed)
variable_name = list(ds.keys())[0]  # Automatically selects the first variable
data_var = ds[variable_name]  # Extract the DataArray

# Extract the latitude, longitude, and depth
latitudes = ds['lat'].values
longitudes = ds['lon'].values
depths = ds['depth'].values

# Create a meshgrid from the latitudes and longitudes to form the raster grid
lon_grid, lat_grid = np.meshgrid(longitudes, latitudes)

# Calculate the transform based on the latitude and longitude values
transform = rasterio.transform.from_origin(
    lon_grid.min(),  # Upper left x-coordinate (longitude)
    lat_grid.max(),  # Upper left y-coordinate (latitude)
    lon_grid[1, 0] - lon_grid[0, 0],  # Pixel width (longitude resolution)
    lat_grid[0, 1] - lat_grid[0, 0]   # Pixel height (latitude resolution)
)

# Convert the data array to a 2D array (for example purposes, adjust as necessary)
data = data_var.values

# Convert boolean mask to an integer array (0 for land, 1 for water)
data_int = np.where(data != 0, 1, 0)  # Assuming non-zero values indicate water

# Path to save the reprojected raster
output_file = r"C:\DATA\Reprojected_Lake_Area_Mask.tif"

# Define the target CRS (EPSG:4326 - Latitude/Longitude)
target_crs = CRS.from_epsg(4326)

# Open a temporary file to write the reprojected raster
with rasterio.open(output_file, 'w', driver='GTiff', 
                   height=data_int.shape[0], width=data_int.shape[1], 
                   count=1, dtype='uint8', crs=target_crs, 
                   transform=transform) as dst:

    # Perform the reprojection
    reproject(
        source=data_int,
        destination=rasterio.band(dst, 1),
        src_transform=transform,  # Using the manually defined transform
        src_crs=target_crs,  # Set the source CRS to EPSG:4326
        dst_transform=calculate_default_transform(
            target_crs, target_crs, dst.width, dst.height, lon_grid.min(), lat_grid.max(), lon_grid.max(), lat_grid.min()
        )[0],  # Calculate the appropriate transformation matrix
        dst_crs=target_crs,
        resampling=Resampling.nearest
    )

    print(f"Reprojected raster saved to: {output_file}")

# Show the reprojected file
with rasterio.open(output_file) as src:
    # Plot the reprojected data
    plt.imshow(src.read(1), cmap='Blues')
    plt.title("Reprojected Lake Victoria Mask")
    plt.colorbar()
    plt.show()






