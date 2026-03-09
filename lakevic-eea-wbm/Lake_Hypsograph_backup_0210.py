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
from rasterio.mask import mask
import geopandas as gpd

from rasterio.warp import reproject, Resampling 


#%%


from rasterio.warp import calculate_default_transform, reproject, Resampling


# Input raster
bathymetry_tiff = r"C:\DATA\Lake V Bathymentry\lake_bathymetry.tif"
out_raster = r"C:\DATA\Lake V Bathymentry\lake_bathymetry_UTM.tif"

with rasterio.open(bathymetry_tiff) as src:
    # Choose appropriate UTM zone for Lake Victoria (approx. Zone 36N)
    dst_crs = 'EPSG:32636'  # UTM Zone 36N
    
    transform, width, height = calculate_default_transform(
        src.crs, dst_crs, src.width, src.height, *src.bounds
    )
    
    kwargs = src.meta.copy()
    kwargs.update({
        'crs': dst_crs,
        'transform': transform,
        'width': width,
        'height': height
    })

    # Create the reprojected raster
    with rasterio.open(out_raster, 'w', **kwargs) as dst:
        for i in range(1, src.count + 1):
            reproject(
                source=rasterio.band(src, i),
                destination=rasterio.band(dst, i),
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=dst_crs,
                resampling=Resampling.bilinear
            )

print(f"✅ Bathymetry raster reprojected to UTM: {out_raster}")


#%%

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
bathymetry_tiff = r"C:\DATA\Lake V Bathymentry\lake_bathymetry_UTM.tif"
lake_area = calculate_lake_area(bathymetry_tiff)

print(f"Calculated surface area of Lake Victoria: {lake_area:.2f} km²")






#%%


def calculate_lake_area(bathymetry_tiff):
    with rasterio.open(bathymetry_tiff) as src:
        data = src.read(1)
        res_x, res_y = src.res
        pixel_area = res_x * res_y  # in map units (m² if CRS in meters)

        # Mask out only nodata, not depth
        mask = (data != src.nodata) & (data >= 0)

        lake_pixels = np.sum(mask)
        lake_area_km2 = (lake_pixels * pixel_area) / 1e6
        return lake_area_km2

lake_area = calculate_lake_area(bathymetry_tiff)
print(f"Calculated surface area of Lake Victoria: {lake_area:.2f} km²")


#%%


# Start from here

# Open topography raster
# basin_topography_tiff = "C:\DATA\Processed\Reprojected_Resampled_DEM.tif" (this is reprojected to 500m)

# open the non-reprojected DEM
basin_topography_tiff = "C:\DATA\Lake Basin Topography\LakeVictoriaBasinDEM.tif"
bathymetry_tiff = r"C:\DATA\Lake V Bathymentry\LakeVictoria_BathymetryGEE.tif"


# 1a. Reproject Bathymetry data (500 m) to resolution of Topography data 

# Paths
bathy_file = bathymetry_tiff
basin_file = basin_topography_tiff # DEM
out_file = r"C:\DATA\Lake V Bathymentry\Bathymetry_reprojected_30m_final.tif"



# Open reference (basin_topography_tiff)
with rasterio.open(basin_file) as ref:
    ref_meta = ref.meta.copy()
    ref_crs = ref.crs
    ref_transform = ref.transform
    ref_shape = (ref.height, ref.width)
    

# Open source (bathy_src)
with rasterio.open(bathy_file) as src:
    bathy_data = src.read(1)  # just first band for now
    dst_data = np.empty(ref_shape, dtype=bathy_data.dtype)
    src_meta = src.meta.copy()
  

    # Reproject the bathymetry
    reproject(
        source=bathy_data,
        destination=dst_data,
        src_transform=src.transform,
        src_crs=src.crs,
        dst_transform=ref_transform,
        dst_crs=ref_crs,
        resampling=Resampling.bilinear  # or nearest/cubic depending on your data
    )
  
# set all the zeros to nan to remove area outside of lake that has been added by reprojection
dst_data[dst_data == 0] = np.nan

# Save reprojected raster
ref_meta.update({
    "driver": "GTiff",
    "height": ref_shape[0],
    "width": ref_shape[1],
    "transform": ref_transform,
    "crs": ref_crs,
    "nodata": -9999,
    "dtype": "float32",
    
})

# save the file 
with rasterio.open(out_file, "w", **ref_meta) as dst:
    dst.write(dst_data, 1)
    


#%%
# Plot to check 
plot = plt.imshow(test)
plt.show()

#%%
# Plot to check 
plot = plt.imshow(dst_data)
plt.show()


#%%
# Plot to check 
plot = plt.imshow(dst_data_filled)
plt.show()

#%%


# Plot to check 
plot = plt.imshow(bathy_data)
plt.show()




#%%

# open bathymetry reprojected to 30 m 
bathymetry_tiff =  r"C:\DATA\Lake V Bathymentry\Bathymetry_reprojected_30m_final.tif"

# 1b. Open topography data (30 m) and merge with bathymetry (30 m)

with rasterio.open(bathymetry_tiff) as bathy_src, rasterio.open(basin_topography_tiff) as topo_src:
    bathymetry_data = bathy_src.read(1)
    topography_data = topo_src.read(1)
    bathy_crs = bathy_src.crs
    topo_crs = topo_src.crs
    transform = bathy_src.transform
    res =  bathy_src.res[0]
    pixel_area = bathy_src.res[0] * bathy_src.res[1]  

#%%
# put together bathymetry and topography data
# turn zeros in topography (indicate areas outside of basin), to nan

# Convert to float (allows NaN)
topography_data = topography_data.astype(float)
# Now you can safely replace zeros
topography_data[topography_data == 0] = np.nan
print(f'min elevation, {np.nanmin(topography_data)}')

# combine bathymetry and topography data

# set nan to zero
bath_zeros = np.nan_to_num(bathymetry_data, copy=True,nan=0)


#%%
# subtract one from the other 
bath_topo = np.subtract(topography_data, bath_zeros)


#%%


# Plot to check 
plot = plt.imshow(topography_data)
plt.show()


#%%

plt.imshow(bathymetry_data)
plt.show()

#%%

# Plot Topography - Bathymetry
fig, ax = plt.subplots()
plot = ax.imshow(bath_zeros)
cbar = fig.colorbar(plot, ax=ax, shrink=0.4)
ax.set_title(" Bathymetry")
plt.show()


#%%
# Plot Topography - Bathymetry
fig, ax = plt.subplots()
plot = ax.imshow(bath_topo)
cbar = fig.colorbar(plot, ax=ax, shrink=0.4)
ax.set_title("Topography - Bathymetry")
plt.show()


#%%

# # add back the geographic metadata to this and save as a tiff 


# out_file = r"C:\DATA\Lake V Bathymentry\bathy_topo_final.tif"

# # save the file 
# with rasterio.open(out_file, "w", **ref_meta) as dst:
#     dst.write(bath_topo, 1)
    
    
#%%

depth_data = bathymetry_data


# 2. Define Depth Bins
bin_size = .1  # Bin thickness in meters
min_depth = np.nanmin(depth_data)  # Minimum depth
max_depth = np.nanmax(depth_data)  # Maximum depth
depth_bins = np.arange(np.floor(min_depth), np.ceil(max_depth) + bin_size, bin_size)


#%%


# 3. Calculate Volumes for different depths

# Flatten depth data and drop NaNs
depth_flat = depth_data.ravel()
depth_flat = depth_flat[~np.isnan(depth_flat)]

# Pixel area in km²
pixel_area = 900 

# Define bins
bin_size = 0.1
min_depth = np.floor(np.nanmin(depth_flat))
max_depth = np.ceil(np.nanmax(depth_flat))
depth_bins = np.arange(min_depth, max_depth + bin_size, bin_size)

# Histogram: how many pixels fall into each depth interval
counts, bin_edges = np.histogram(depth_flat, bins=depth_bins)

# Compute cumulative area
areas_at_depth = np.cumsum(counts) * pixel_area

# # Compute cumulative volume
# # Each bin contributes: count * depth_midpoint
# depth_mid = (bin_edges[:-1] + bin_edges[1:]) / 2
# volumes_cumulative = np.cumsum(counts * depth_mid) * pixel_area

# THIS IS NOT CORRECT : To fix volume 

# Convert to arrays with depth labels
areas_at_depth = np.array(areas_at_depth)      # km²
#volumes_at_depth = np.array(volumes_cumulative)  # km³ if depths are meters

#%%

# 5. Depth vs. area

plt.figure(figsize=(10, 6))
plt.plot( np.array(areas_at_depth) / 1e6  , depth_mid, marker='o', linestyle='-', color='blue')
plt.gca().invert_yaxis()  # Depth increases downward
plt.title("Lake Victoria Depth-Area Curve")
plt.xlabel("Area (km$^2$)")
plt.ylabel("Depth (m)")
plt.grid()
plt.show()



#%%

# # 4. Plot Depth vs. Volume
# plt.figure(figsize=(10, 6))
# plt.plot( np.array(volumes_at_depth) / 1e9 , depth_mid, marker='o', linestyle='-', color='blue')
# plt.gca().invert_yaxis()  # Depth increases downward
# plt.title("Lake Victoria Depth-Volume Curve")
# plt.xlabel("Volume (km³)")
# plt.ylabel("Depth (m)")
# plt.grid()
# plt.show()




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

# pixel_size = 30  # meters
# pixel_area = pixel_size ** 2  # 900 m² per pixel

# def calculate_areas_per_depth_bin(
#         depth_bins,
#         bath_topo, # bathymetry and topography together 
#         bath_topo_at_max_bathy = bath_topo_at_max_bathy,
#         pixel_area = pixel_size ** 2 # pixel_size has to be defined 
#         ):
    
#     volumes_at_depth = []
#     areas_at_depth = []

# --------------------------------------------------------------
# Pixel configuration
# --------------------------------------------------------------
pixel_size = 30  # meters
pixel_area = pixel_size ** 2  # 900 m² per pixel


def calculate_areas_per_depth_bin(
        depth_bins,
        bath_topo,  # combined bathymetry + topography array
        bath_topo_at_max_bathy,
        pixel_area=pixel_area
    ):
    """
    Calculate surface area per depth bin.

    Parameters
    ----------
    depth_bins : array-like
        Depth bin edges (e.g. np.arange(-80, 10, 1))
    bath_topo : np.ndarray
        Bathymetry + topography raster (meters)
    bath_topo_at_max_bathy : np.ndarray
        Masked bathymetry at maximum lake extent
    pixel_area : float
        Area of one raster cell in m² (default = 30m × 30m)

    Returns
    -------
    dict
        Depth bin -> area (m²)
    """

    area_per_bin = {}

    for i in range(len(depth_bins) - 1):
        lower = depth_bins[i]
        upper = depth_bins[i + 1]

        mask = (
            (bath_topo_at_max_bathy >= lower) &
            (bath_topo_at_max_bathy < upper)
        )

        area_per_bin[(lower, upper)] = np.sum(mask) * pixel_area

    return area_per_bin


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








# -*- coding: utf-8 -*-
"""
Lake Victoria Hypsograph Generator
Creates area-volume-level relationship plot from bathymetry and topography data

Author: V. Ogembo
Created: December 2025
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import rasterio
from rasterio.warp import reproject, Resampling
import seaborn as sns

# ===============================================================
# CONFIGURATION
# ===============================================================

# Input files
BATHYMETRY_FILE = r"C:\DATA\Lake V Bathymentry\LakeVictoria_BathymetryGEE.tif"
TOPOGRAPHY_FILE = r"C:\DATA\Lake Basin Topography\LakeVictoriaBasinDEM.tif"

# Output
OUTPUT_DIR = r"C:\DATA\Lake V Bathymentry"
HYPSOGRAPH_CSV = r"C:\Users\VO000003\OneDrive - Vrije Universiteit Brussel\Ogembo_LVictoria_IWBM\lakevic-eea-wbm\input_data\hypsograph\WBM_depth_area_curve.csv"

# Depth bin configuration
BIN_SIZE = 0.1  # meters
PIXEL_SIZE = 30  # meters (DEM resolution)
PIXEL_AREA = PIXEL_SIZE ** 2  # m² per pixel

# Plotting style
sns.set_style("whitegrid")
plt.rcParams.update({
    'figure.dpi': 150,
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 14
})

# ===============================================================
# STEP 1: LOAD AND ALIGN DATA
# ===============================================================

def load_and_align_data(bathy_file, topo_file):
    """
    Load bathymetry and topography, reproject bathymetry to match topography
    """
    print("Loading and aligning bathymetry and topography...")
    
    # Load topography (reference)
    with rasterio.open(topo_file) as topo_src:
        topography_data = topo_src.read(1).astype(float)
        ref_transform = topo_src.transform
        ref_crs = topo_src.crs
        ref_shape = topography_data.shape
        pixel_size = topo_src.res[0]
    
    # Load and reproject bathymetry
    with rasterio.open(bathy_file) as bathy_src:
        bathy_data = bathy_src.read(1)
        
        # Create empty array for reprojected data
        bathy_reprojected = np.empty(ref_shape, dtype=float)
        
        # Reproject bathymetry to match topography
        reproject(
            source=bathy_data,
            destination=bathy_reprojected,
            src_transform=bathy_src.transform,
            src_crs=bathy_src.crs,
            dst_transform=ref_transform,
            dst_crs=ref_crs,
            resampling=Resampling.bilinear
        )
    
    # Clean data
    bathy_reprojected[bathy_reprojected == 0] = np.nan  # Remove areas outside lake
    topography_data[topography_data == 0] = np.nan  # Remove areas outside basin
    
    print(f"✓ Data loaded and aligned")
    print(f"  Grid size: {ref_shape}")
    print(f"  Pixel size: {pixel_size} m")
    
    return bathy_reprojected, topography_data, pixel_size


# ===============================================================
# STEP 2: MERGE BATHYMETRY AND TOPOGRAPHY
# ===============================================================

def merge_bathy_topo(bathymetry, topography):
    """
    Combine bathymetry (negative depths) and topography (elevations)
    into a single elevation surface
    """
    print("\nMerging bathymetry and topography...")
    
    # Convert bathymetry NaN to 0 for subtraction
    bathy_zeros = np.nan_to_num(bathymetry, nan=0)
    
    # Subtract bathymetry from topography
    # (topography is elevation above sea level, bathymetry is depth below lake surface)
    combined = topography - bathy_zeros
    
    # Find the baseline elevation (deepest point)
    max_bathy_idx = np.unravel_index(np.nanargmax(bathymetry), bathymetry.shape)
    baseline_elevation = combined[max_bathy_idx]
    
    print(f"✓ Data merged")
    print(f"  Deepest point: {bathymetry[max_bathy_idx]:.2f} m depth")
    print(f"  Baseline elevation: {baseline_elevation:.2f} m a.s.l.")
    
    return combined, baseline_elevation


# ===============================================================
# STEP 3: CALCULATE HYPSOGRAPH
# ===============================================================

def calculate_hypsograph(combined_elevation, baseline_elev, bin_size, pixel_area):
    """
    Calculate area and volume for each depth/elevation bin
    """
    print("\nCalculating hypsographic curve...")
    
    # Define depth bins relative to baseline
    max_depth = np.nanmax(combined_elevation - baseline_elev)
    min_depth = np.nanmin(combined_elevation - baseline_elev)
    
    depth_bins = np.arange(np.floor(min_depth), np.ceil(max_depth) + bin_size, bin_size)
    
    areas = []
    volumes = []
    
    for depth in depth_bins:
        # Mask all pixels below this water level
        mask = (combined_elevation <= baseline_elev + depth)
        
        # Calculate area
        area = np.nansum(mask) * pixel_area  # m²
        
        # Calculate volume
        # For each pixel, depth is limited by either actual depth or water level
        pixel_depths = np.where(
            mask,
            np.minimum(combined_elevation - baseline_elev, depth),
            np.nan
        )
        volume = np.nansum(pixel_depths) * pixel_area  # m³
        
        areas.append(area)
        volumes.append(volume)
    
    # Create DataFrame
    df = pd.DataFrame({
        'depth_m': depth_bins,
        'area_m2': areas,
        'vol_m3': volumes
    })
    
    # Add lake levels (elevation a.s.l.)
    df['level_masl'] = df['depth_m'] + baseline_elev
    
    print(f"✓ Hypsograph calculated")
    print(f"  Depth range: {min_depth:.2f} to {max_depth:.2f} m")
    print(f"  Level range: {df['level_masl'].min():.2f} to {df['level_masl'].max():.2f} m a.s.l.")
    
    return df


# ===============================================================
# STEP 4: PLOT HYPSOGRAPH
# ===============================================================

def plot_hypsograph(df, savepath=None):
    """
    Create publication-quality hypsograph plot
    Lake Level (x) vs Area (left y) and Volume (right y)
    """
    print("\nCreating hypsograph plot...")
    
    fig, ax1 = plt.subplots(figsize=(12, 7))
    
    # Plot Lake Area (Left Y-Axis)
    color_area = '#1976D2'  # Blue
    ax1.plot(df['level_masl'], df['area_m2'] / 1e6, 
            color=color_area, linewidth=2.5, label='Lake Area')
    ax1.set_xlabel('Lake Level (m a.s.l.)', fontsize=13, fontweight='bold')
    ax1.set_ylabel('Lake Area (km²)', fontsize=13, fontweight='bold', color=color_area)
    ax1.tick_params(axis='y', labelcolor=color_area, labelsize=11)
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Set x-axis ticks at 10m intervals
    level_min = np.floor(df['level_masl'].min() / 10) * 10
    level_max = np.ceil(df['level_masl'].max() / 10) * 10
    tick_intervals = np.arange(level_min, level_max + 10, 10)
    ax1.set_xticks(tick_intervals)
    
    # Plot Lake Volume (Right Y-Axis)
    ax2 = ax1.twinx()
    color_volume = '#D32F2F'  # Red
    ax2.plot(df['level_masl'], df['vol_m3'] / 1e9, 
            color=color_volume, linewidth=2.5, label='Lake Volume')
    ax2.set_ylabel('Lake Volume (km³)', fontsize=13, fontweight='bold', color=color_volume)
    ax2.tick_params(axis='y', labelcolor=color_volume, labelsize=11)
    
    # Add title
    plt.title('Lake Victoria Hypsographic Curve\nArea and Volume vs. Lake Level', 
             fontsize=15, fontweight='bold', pad=20)
    
    # Add legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, 
              loc='upper left', fontsize=11, frameon=True, shadow=True)
    
    plt.tight_layout()
    
    if savepath:
        plt.savefig(savepath, dpi=300, bbox_inches='tight')
        print(f"✓ Saved plot: {savepath}")
    
    plt.show()
    
    return fig


# ===============================================================
# STEP 5: SAVE HYPSOGRAPH DATA
# ===============================================================

def save_hypsograph_csv(df, filepath):
    """
    Save hypsograph data to CSV for use in water balance model
    """
    # Select relevant columns for model
    df_output = df[['depth_m', 'area_m2', 'vol_m3']].copy()
    df_output = df_output.set_index('depth_m')
    
    df_output.to_csv(filepath)
    print(f"\n✓ Saved hypsograph CSV: {filepath}")
    
    # Print summary statistics
    print("\nHypsograph Summary:")
    print(f"  At depth 0 m:")
    print(f"    Area: {df_output.iloc[0]['area_m2']/1e6:.1f} km²")
    print(f"    Volume: {df_output.iloc[0]['vol_m3']/1e9:.1f} km³")
    
    max_idx = df_output.index.max()
    print(f"  At maximum depth ({max_idx:.1f} m):")
    print(f"    Area: {df_output.loc[max_idx]['area_m2']/1e6:.1f} km²")
    print(f"    Volume: {df_output.loc[max_idx]['vol_m3']/1e9:.1f} km³")


# ===============================================================
# MAIN EXECUTION
# ===============================================================

def main():
    """
    Main execution function
    """
    print("="*70)
    print("LAKE VICTORIA HYPSOGRAPH GENERATOR")
    print("="*70)
    
    # Step 1: Load and align data
    bathymetry, topography, pixel_size = load_and_align_data(
        BATHYMETRY_FILE, 
        TOPOGRAPHY_FILE
    )
    
    # Step 2: Merge bathymetry and topography
    combined, baseline = merge_bathy_topo(bathymetry, topography)
    
    # Step 3: Calculate hypsograph
    pixel_area = pixel_size ** 2
    df_hypsograph = calculate_hypsograph(
        combined, 
        baseline, 
        BIN_SIZE, 
        pixel_area
    )
    
    # Step 4: Plot hypsograph
    plot_path = OUTPUT_DIR + r"\Lake_Victoria_Hypsograph.png"
    plot_hypsograph(df_hypsograph, plot_path)
    
    # Step 5: Save CSV
    save_hypsograph_csv(df_hypsograph, HYPSOGRAPH_CSV)
    
    print("\n" + "="*70)
    print("✅ HYPSOGRAPH GENERATION COMPLETE")
    print("="*70)
    
    return df_hypsograph


if __name__ == "__main__":
    df = main()










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






