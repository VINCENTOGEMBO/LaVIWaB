# -*- coding: utf-8 -*-
"""


@author: VO000003

Test running w Rosa
"""

# GENERATING LAKE EXTENT 

import pandas as pd
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from pyproj import Transformer
from scipy.interpolate import interp1d

#%%
# Load daily lake levels
lake_levels_df = pd.read_csv("C:\DATA\Lake_levels\Lake_Victoria_level_Jun2024.csv")  # Ensure columns: 'date', 'lake_level'

# Open bathymetry raster
bathymetry_tiff = "C:\DATA\Lake V Bathymentry\LakeVictoria_Bathymetry-Reprojected.tif"
basin_topography_tiff = "C:\DATA\Processed\Reprojected_Resampled_DEM.tif"

#%%
with rasterio.open(bathymetry_tiff) as bathy_src, rasterio.open(basin_topography_tiff) as topo_src:
    bathymetry_data = bathy_src.read(1)
    topography_data = topo_src.read(1)
    transform = bathy_src.transform
    pixel_area = bathy_src.res[0] * bathy_src.res[1]  # Resolution of approximately 500m x 500m (e.g., meters^2) - GEBCO global bathymetry: ~470m (~15 arc-seconds)

#%%
# plot bathymetry and topography data

fig, axes = plt.subplots(1,2)
ax=axes[0]
plt1=ax.imshow(bathymetry_data)
fig.colorbar(plt1, ax=ax)

ax=axes[1]
plt2=ax.imshow(topography_data)
fig.colorbar(plt2, ax=ax)

#%%

# put together bathymetry and topography data

# turn zeros in topography (outside of basin), to nan
topography_data[topography_data==0] = 'nan'

min_elevation = np.nanmin(topography_data)

# combine bathymetry and topography data
bath_zeros = np.nan_to_num(bathymetry_data, copy=True,nan=0)
bath_topo = np.subtract(topography_data, bath_zeros)

# test smaller area
#bath_zeros_sel=bath_zeros[365:370,360:365]
#topography_data_sel=topography_data[365:370,360:365]
#bath_topo_sel = topography_data_sel - bath_zeros_sel


#%%

# Create a larger figure with 4 subplots
fig, axes = plt.subplots(1, 4, figsize=(16, 6))  

# Bathymetry
ax = axes[0]
plt1 = ax.imshow(bathymetry_data)
cbar = fig.colorbar(plt1, ax=ax, shrink=0.4) 
ax.set_title("Bathymetry")

# Topography
ax = axes[1]
plt2 = ax.imshow(topography_data, vmin=900, vmax=1200)
cbar = fig.colorbar(plt2, ax=ax, shrink=0.4)
ax.set_title("Topography")

# Topography - Bathymetry
ax = axes[2]
plt3 = ax.imshow(bath_topo, vmin=900, vmax=1200)
cbar = fig.colorbar(plt3, ax=ax, shrink=0.4)
ax.set_title("Topography - Bathymetry")

# Difference Map (bath_topo - topography_data)
ax = axes[3]
plt4 = ax.imshow(bath_topo - topography_data)
cbar = fig.colorbar(plt4, ax=ax, shrink=0.4)
ax.set_title("Difference (Bath_Topo - Topo)")

# Adjust layout for better spacing
plt.tight_layout()
plt.show()


#%%
# Function to calculate lake extent
def calculate_extent(lake_level, bathymetry_data, topography_data):
    water_mask = bathymetry_data <= lake_level
    land_mask = topography_data > lake_level
    water_mask = np.logical_and(water_mask, ~land_mask)
    water_area = np.sum(water_mask) * pixel_area / 1e6  # Convert to km^2
    return water_area

#%%
# Function to calculate lake extent
def calculate_extent_new(lake_level, bathymetry_topography_data):
    water_mask = bathymetry_topography_data <= lake_level
    #land_mask = topography_data > lake_level
    #water_mask = np.logical_and(water_mask, ~land_mask)
    water_area = np.sum(water_mask) * pixel_area / 1e6  # Convert to km^2
    return water_area

# Iterate over daily levels and calculate lake extent
results = []
for index, row in lake_levels_df.iterrows():
    lake_level = row['lake_level']
    water_area_km2 = calculate_extent_new(lake_level, bath_topo)
    results.append({'date': row['date'], 'lake_level': lake_level, 'lake_extent_km2': water_area_km2})

# Save results to CSV
results_df = pd.DataFrame(results)
results_df.to_csv("lake_extent_daily_new.csv", index=False)

print("Lake extent analysis saved to 'lake_extent_daily.csv'")



#%%

# PLOT LAKE LEVELS AND CALCULATED LAKE AREA 


fig, axes=plt.subplots(2,1)
results_df.index = results_df['date']
results_df['lake_extent_km2'].plot(ax=axes[0])
results_df['lake_level'].plot(ax=axes[1])


# Set 'date' as index
results_df.set_index('date', inplace=True)

# Create subplots
fig, axes = plt.subplots(2, 1, figsize=(16, 8), sharex=True)

# Plot lake extent (km²)
results_df['lake_extent_km2'].plot(ax=axes[0], color='blue', linewidth=2)
axes[0].set_ylabel("Lake Area (km²)", fontsize=12)
axes[0].set_title("Time Series Lake Victoria Area and Levels", fontsize=14)
axes[0].grid(True)

# Plot lake level (m)
results_df['lake_level'].plot(ax=axes[1], color='green', linewidth=2)
axes[1].set_ylabel("Lake Level (m)", fontsize=12)
axes[1].set_xlabel("Date", fontsize=12)
axes[1].grid(True)

# Improve layout
plt.tight_layout()
plt.show()













#%%

# FROM HERE CHECKS + OLD

























#%%
# CHECKS   CHECKS   CHECKS 

# check baseline of topography data matches baseline of lake level data 



with rasterio.open("C:\DATA\Processed\Reprojected_Resampled_DEM.tif") as src:
    print(src.meta)  # Prints metadata
    print(src.crs)   # Prints coordinate reference system (CRS)
    


# Define transformation (change source/target CRS as needed)
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3855", always_xy=True)

#Convert Lake Level Data to UTM EPSG:32736
#If your lake level data is in latitude/longitude (e.g., EPSG:4326), transform it:

# Define transformation: WGS84 (EPSG:4326) → UTM Zone 36S (EPSG:32736)
transformer = Transformer.from_crs("EPSG:4326", "EPSG:32736", always_xy=True)

# Sample lake level point (longitude, latitude)
lon, lat, elevation = 34.5, -0.2, 1135  # Example point
utm_x, utm_y, utm_elevation = transformer.transform(lon, lat, elevation)

print(f"Converted Coordinates: {utm_x}, {utm_y}, Elevation: {utm_elevation} meters")

#Compare Elevation Ranges
#Extract the minimum and maximum elevations from your topography data:
    
with rasterio.open("C:\DATA\Processed\Reprojected_Resampled_DEM.tif") as src:
    topo_data = src.read(1)  # Read raster band
    min_elevation = np.min(topo_data)
    max_elevation = np.max(topo_data)

print(f"Topography Elevation Range: {min_elevation} - {max_elevation} meters")    #Results:  Topography Elevation Range: 0.0 - 2236.0 meters


#Now compare it with the lake level range from the dataset:

lake_data = pd.read_csv("C:\DATA\Lake_levels\Lake_Victoria_level_Jun2024.csv")  # Replace with actual file
min_lake = lake_data['lake_level'].min()
max_lake = lake_data['lake_level'].max()

print(f"Lake Level Range: {min_lake} - {max_lake} meters")     #Results:  Lake Level Range: 1133.734 - 1136.777 meters


#Extract Water Surface Area
#To ensure you are only working with relevant data, mask the DEM where elevation falls within the lake level range:

# Open DEM
with rasterio.open("C:/DATA/Processed/Reprojected_Resampled_DEM.tif") as src:
    topo_data = src.read(1)
    profile = src.profile  # Save metadata

# Mask areas outside the lake level range
water_mask = (topo_data >= 1133.7) & (topo_data <= 1136.8)
water_area = np.sum(water_mask) * profile["transform"][0]**2  # Convert to square meters

print(f"Estimated Water Surface Area: {water_area/1e6:.2f} km²")  # Convert to km²     #Result: Estimated Water Surface Area: 67114.65 km²

#Check for No-Data Values
#If your DEM contains 0.0 m values that do not correspond to actual elevations, check for no-data:
nodata_value = src.nodata
print(f"No-data Value: {nodata_value}")
topo_data[topo_data == 0] = np.nan  # Set to NaN for proper filtering


# far away pixels that have low elevation but arent't part of lake - ANS: Pixels used in area calculation are only within or immediately adjacent to the lake bathymetry


# if you find timeseries of area check against this 


#%%
# for model part
# solve for volume of lake      ANS: Volume Calculated 
# create a hypsometry curve 
# from volume -> read level and area via hypsometry curve 


# Load the data
file_path = r"C:\DATA\Lake Volume\lake_average_volume.csv"  # Use raw string to avoid escape issues
df = pd.read_csv(file_path)

# Ensure correct column names
df.columns = ["date", "lake_level", "lake_extent_km2", "lake_volume_km3"]

# Convert Date column to datetime format
df["Date"] = pd.to_datetime(df["date"], errors="coerce")

# Convert numerical columns to float (force conversion to handle non-numeric issues)
numeric_cols = ["lake_level", "lake_extent_km2", "lake_volume_km3"]
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

# Drop rows with NaN (caused by non-convertible values)
df = df.dropna()

# Check for duplicates in lake_volume_km3
if df["lake_volume_km3"].duplicated().any():
    print("Duplicate values found in lake_volume_km3. Aggregating...")
    df = df.groupby("lake_volume_km3", as_index=False)[["lake_level", "lake_extent_km2"]].mean()  # Aggregate only numeric columns

# Sort data by Lake Level (ascending order)
df = df.sort_values(by="lake_level")

# Fit Hypsometry Curves
# Interpolation function for Volume -> Level
volume_to_level = interp1d(df["lake_volume_km3"], df["lake_level"], kind="cubic", fill_value="extrapolate")

# Interpolation function for Volume -> Area
volume_to_area = interp1d(df["lake_volume_km3"], df["lake_extent_km2"], kind="cubic", fill_value="extrapolate")

# Generate values for plotting
volume_range = np.linspace(df["lake_volume_km3"].min(), df["lake_volume_km3"].max(), 500)
predicted_levels = volume_to_level(volume_range)
predicted_areas = volume_to_area(volume_range)

# Plot the Hypsometry Curve
plt.figure(figsize=(10, 5))
plt.plot(predicted_levels, volume_range, label="Lake Victoria Volume vs Lake Level", color="b")
plt.xlabel("Lake Level (m)")
plt.ylabel("Lake Volume (km³)")
plt.title("Hypsometry Curve: Lake Victoria Volume vs Lake Level")
plt.legend()
plt.grid(True)
plt.show()

plt.figure(figsize=(10, 5))
plt.plot(predicted_levels, predicted_areas, label="Lake Victoria Area vs Lake Level", color="g")
plt.xlabel("Lake Level (m)")
plt.ylabel("Lake Area (km²)")
plt.title("Hypsometry Curve: Lake Victoria Area vs Lake Level")
plt.legend()
plt.grid(True)
plt.show()

# Create the figure and axis
fig, ax1 = plt.subplots(figsize=(10, 5))

# Plot Lake Area on the left y-axis
ax1.plot(predicted_levels, predicted_areas, label="Lake Area vs Level", color="g", linewidth=2)
ax1.set_xlabel("Lake Level (m)")
ax1.set_ylabel("Lake Area (km²)", color="g")
ax1.tick_params(axis="y", labelcolor="g")

# Create a second y-axis for Lake Volume
ax2 = ax1.twinx()
ax2.plot(predicted_levels, volume_range, label="Lake Volume vs Level", color="b", linewidth=2)
ax2.set_ylabel("Lake Volume (km³)", color="b")
ax2.tick_params(axis="y", labelcolor="b")

# Add grid lines
ax1.grid(which='major', linestyle='--', linewidth=0.75, alpha=0.7)  # Major grid lines
ax1.grid(which='minor', linestyle=':', linewidth=0.5, alpha=0.5)  # Minor grid lines
ax1.minorticks_on()  # Enable minor ticks

# Title and legend
plt.title("Hypsometry Curve: Lake Victoria Area & Volume vs Water Level")
fig.tight_layout()
plt.show()





#%%


import pandas as pd

# Load lake level data
lake_level = pd.read_csv(r"C:\DATA\Lake_levels\Lake_Victoria_level_Jun2024.csv")

# Load lake area data
lake_area = pd.read_csv(r"C:\DATA\Lake Extent csv 1993-2023\lake_extent_daily_1948_2024.csv")

# Convert 'date' column to datetime format
lake_level["date"] = pd.to_datetime(lake_level["date"])
lake_area["date"] = pd.to_datetime(lake_area["date"])

# Drop duplicate 'lake_level' column from lake_area before merging
lake_area = lake_area.drop(columns=["lake_level"])  

# Merge datasets on 'date'
lake_data = pd.merge(lake_level, lake_area, on="date", how="inner")

# Sort by lake level
lake_data = lake_data.sort_values(by="lake_level")

# Display sample
print(lake_data.head())

#%%

# VOLUME CALCULATION

# Load lake level data
lake_level = pd.read_csv(r"C:/DATA/Lake_levels/Lake_Victoria_level_Jun2024.csv")
lake_level["date"] = pd.to_datetime(lake_level["date"])

# Load lake area data
lake_area = pd.read_csv(r"C:\DATA\Lake Extent csv 1993-2023\lake_extent_daily_1948_2024_new.csv")
lake_area["date"] = pd.to_datetime(lake_area["date"])

# Load bathymetry data (DEM)
with rasterio.open(r"C:/DATA/Processed/Reprojected_Resampled_DEM.tif") as src:
    bathymetry = src.read(1)  # Read elevation data
    bathymetry[bathymetry == src.nodata] = np.nan  # Replace NoData values

# Merge lake level & area datasets
lake_data = pd.merge(lake_level, lake_area, on="date", how="inner")

# Get lake bed elevation (min bathymetry)
lake_bed_elevation = np.nanmin(bathymetry)  # Lowest lake bed elevation

# Compute Water Depth = Lake Level - Lake Bed Elevation
lake_data["water_depth"] = lake_data["lake_level"] - lake_bed_elevation

# Compute Volume (km³)
lake_data["volume_km3"] = (lake_data["lake_extent_km2"] * lake_data["water_depth"]) / 1000  # Convert m³ to km³

# Save results
lake_data.to_csv("Lake_Victoria_Volume.csv", index=False)
print("Lake volume data saved to 'Lake_Victoria_Volume.csv'.")

# Display sample results
print(lake_data[["date", "lake_level", "lake_extent_km2", "water_depth", "volume_km3"]].head())



#%%
# PLOTTING VOLUME, AREA AND LEVELS
import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file
df = pd.read_csv("C:\DATA\Lake Volume\lake_average_volume.csv")

# Convert 'date' column to datetime
df['date'] = pd.to_datetime(df['date'])

# Extract year from the 'date' column for plotting
df['year'] = df['date'].dt.year

# Plotting
plt.figure(figsize=(12, 8))

# Plot Volume vs Year
plt.subplot(3, 1, 1)  # 3 rows, 1 column, 1st plot
plt.plot(df['year'], df['lake_volume_km3'], label='Lake Volume (km³)', color='b')
plt.xlabel('Year')
plt.ylabel('Lake Volume (km³)')
plt.title('Lake Volume Over Time')
plt.grid(True)
plt.legend()

# Plot Lake Level vs Year
plt.subplot(3, 1, 2)  # 3 rows, 1 column, 2nd plot
plt.plot(df['year'], df['lake_level'], label='Lake Level (m)', color='g')
plt.xlabel('Year')
plt.ylabel('Lake Level (m)')
plt.title('Lake Level Over Time')
plt.grid(True)
plt.legend()

# Plot Lake Extent vs Year
plt.subplot(3, 1, 3)  # 3 rows, 1 column, 3rd plot
plt.plot(df['year'], df['lake_extent_km2'], label='Lake Extent (km²)', color='r')
plt.xlabel('Year')
plt.ylabel('Lake Extent (km²)')
plt.title('Lake Extent Over Time')
plt.grid(True)
plt.legend()

# Adjust layout to avoid overlap
plt.tight_layout()

# Show the plots
plt.show()


#%%
#PLOTTING VOLUME LAKE LEVEL AND LAKE AREA

#  Load the CSV file
df = pd.read_csv("C:/DATA/Lake Volume/lake_average_volume.csv")

# Convert 'date' column to datetime format
df['date'] = pd.to_datetime(df['date'])

#  Apply a rolling average (Optional: Adjust window size for smoothness)
df['lake_volume_km3_smooth'] = df['lake_volume_km3'].rolling(window=30, min_periods=1).mean()
df['lake_level_smooth'] = df['lake_level'].rolling(window=30, min_periods=1).mean()
df['lake_extent_km2_smooth'] = df['lake_extent_km2'].rolling(window=30, min_periods=1).mean()

#  Plot setup
plt.figure(figsize=(12, 10))

# Plot Lake Volume Over Time
plt.subplot(3, 1, 1)
plt.plot(df['date'], df['lake_volume_km3_smooth'], label='Lake Volume (km³)', color='b', linewidth=2)
plt.xlabel('Year')
plt.ylabel('Lake Volume (km³)')
plt.title('Lake Victoria Volume Over Time')
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()

# Plot Lake Level Over Time
plt.subplot(3, 1, 2)
plt.plot(df['date'], df['lake_level_smooth'], label='Lake Level (m)', color='g', linewidth=2)
plt.xlabel('Year')
plt.ylabel('Lake Level (m)')
plt.title('Lake Victoria Level Over Time')
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()

# Plot Lake Extent Over Time
plt.subplot(3, 1, 3)
plt.plot(df['date'], df['lake_extent_km2_smooth'], label='Lake Extent (km²)', color='r', linewidth=2)
plt.xlabel('Year')
plt.ylabel('Lake Area (km²)')
plt.title('Lake Victoria Area Over Time')
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()

# Adjust layout for better visibility
plt.tight_layout()

# Show the plots
plt.show()


