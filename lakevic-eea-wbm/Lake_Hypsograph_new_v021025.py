# -*- coding: utf-8 -*-
"""
Created on Thu Oct  2 15:29:58 2025

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
import matplotlib as mpl
mpl.rcParams.update(mpl.rcParamsDefault)


#%%

# Start from here

# Open topography raster

# open the non-reprojected DEM
basin_topography_tiff = "C:\DATA\Lake Basin Topography\LakeVictoriaBasinDEM.tif"
bathymetry_tiff = r"C:\DATA\Lake V Bathymentry\LakeVictoria_BathymetryGEE.tif"


#%%
# 1a. Reproject Bathymetry data (500 m) to resolution of Topography data (30 m ) and save

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
# 1b. Open topography data (30 m) and merge with bathymetry (30 m)


# open bathymetry reprojected to 30 m 
bathymetry_tiff =  r"C:\DATA\Lake V Bathymentry\Bathymetry_reprojected_30m_final.tif"


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


# set nan to zero
bath_zeros = np.nan_to_num(bathymetry_data, copy=True,nan=0)


#%%
# subtract one from the other to combine bathymetry and topography data

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

# add geographic metadata to this and save as a tiff  - can use this for plotting and movies and stuff 

# out_file = r"C:\DATA\Lake V Bathymentry\bathy_topo_final.tif"

# # save the file 
# with rasterio.open(out_file, "w", **ref_meta) as dst:
#     dst.write(bath_topo, 1)
    
    
#%%

depth_data = bathymetry_data


# # 2. Define Depth Bins
# bin_size = .1  # Bin thickness in meters
# min_depth = np.nanmin(depth_data)  # Minimum depth
# max_depth = np.nanmax(depth_data)  # Maximum depth
# depth_bins = np.arange(np.floor(min_depth), np.ceil(max_depth) + bin_size, bin_size)


#%%


# 3. Calculate Areas and Volumes for different depths

# Flatten depth data and drop NaNs
depth_flat = depth_data.ravel()
depth_flat = depth_flat[~np.isnan(depth_flat)]

# Pixel area in km²
pixel_area = 900 

# Define bins
bin_size = 0.01
min_depth = np.floor(np.nanmin(depth_flat))
max_depth = np.ceil(np.nanmax(depth_flat))
depth_bins = np.arange(min_depth, max_depth + bin_size, bin_size)

# Histogram: how many pixels fall into each depth interval
counts, bin_edges = np.histogram(depth_flat, bins=depth_bins)

# Compute cumulative area
areas_at_depth = np.cumsum(counts) * pixel_area

# # Compute cumulative volume
# # Each bin contributes: count * depth_midpoint
depth_mid = (bin_edges[:-1] + bin_edges[1:]) / 2
# volumes_cumulative = np.cumsum(counts * depth_mid) * pixel_area

# THIS IS NOT CORRECT : To fix volume 

# Convert to arrays with depth labels
areas_at_depth = np.array(areas_at_depth)      # km²
#volumes_at_depth = np.array(volumes_cumulative)  # km³ if depths are meters

#%%

plt.hist(depth_flat, bins=30)
plt.show()


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

# Calculate area also with topography 


topo_data = topography_data
topo_flat = topography_data.ravel()
topo_flat = topo_flat[~np.isnan(topo_flat)]

min_topo = np.nanmin(topo_flat)

#%%
# Find the index of the minimum value in bathy_data
min_index = np.nanargmin(bathymetry_data)

# Get the corresponding value in topography_data
corresponding_value = topography_data.flat[min_index]

print("Value in topography_data at minimum of bathy_data:", corresponding_value)

#%%
filtered_topo = topo_flat[topo_flat >= corresponding_value] # 1143
filtered_topo = filtered_topo - corresponding_value

topo_adjusted = filtered_topo + max_depth

topo_adjusted_filtered = topo_adjusted[topo_adjusted <= 90]

#%%

bath_topo_flat = np.concatenate((depth_flat, topo_adjusted_filtered))

#%%


plt.hist(bath_topo_flat, bins=40)
plt.show()


#%%

plt.hist(depth_flat, bins=40)
plt.show()


#%%

plt.hist(filtered_topo, bins=40)
plt.show()


#%%

plt.hist(topo_flat, bins=40)
plt.show()

#%%

plt.imshow(topography_data)
plt.show()

#%%
masked_data = np.ma.masked_where(topography_data >= 1100, topography_data)

plt.imshow(masked_data)  # choose a colormap
plt.colorbar()
plt.show()

#%%


#%%

# 3. Calculate Areas and Volumes for different depths



# Pixel area in km²
pixel_area = 900 

# Define bins
bin_size = 0.005
min_depth = np.floor(np.nanmin(bath_topo_flat))
max_depth = np.ceil(np.nanmax(bath_topo_flat))
depth_bins = np.arange(min_depth, max_depth + bin_size, bin_size)

# Histogram: how many pixels fall into each depth interval
counts, bin_edges = np.histogram(bath_topo_flat, bins=depth_bins)

# Compute cumulative area
areas_at_depth = np.cumsum(counts) * pixel_area

# # Compute cumulative volume
# # Each bin contributes: count * depth_midpoint
depth_mid = (bin_edges[:-1] + bin_edges[1:]) / 2
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


df_area_depth_curve.set_index('depth_m').plot()
plt.show()



#%%

data=np.stack([depth_mid, np.array(areas_at_depth)]).T

df_area_depth_curve = pd.DataFrame(
    data=data,
    columns= ['depth_m','area_m2']
    )

#df_area_depth_curve.to_csv('/Users/VO000003/OneDrive - Vrije Universiteit Brussel/Ogembo_LVictoria_IWBM/lakevic-eea-wbm/input_data/hypsograph/WBM_depth_area_curve_v0210_01cm.csv',index=False)


