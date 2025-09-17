# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 09:41:14 2024

@author: VO000003
"""

import netCDF4 as nc
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs


file_path = "C:\DATA\gebco_2024_n2.0_s-7.0_w29.0_e37.0.nc"  # Replace with your file path
dataset = nc.Dataset(file_path)

# View available variables
print(dataset.variables)


fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()})
ax.set_extent([31, 35, -3, 1])  # Approximate coordinates for Lake Victoria

# Plot the bathymetric data
contour = ax.contourf(lon, lat, depth, levels=30, cmap='Blues')

# Add coastlines and other features
ax.coastlines()
ax.set_title('Lake Victoria Bathymetry (Plan View)')

# Add colorbar for depth
fig.colorbar(contour, ax=ax, orientation='horizontal', label='Depth (m)')

plt.show()


import numpy as np

# Define a transect line (longitude and latitude)
transect_lon = np.linspace(31, 35, 100)  # From west to east across Lake Victoria
transect_lat = np.linspace(-1, 1, 100)

# Interpolate depth along the transect
transect_depth = np.interp(transect_lon, lon, depth.mean(axis=0))  # Example interpolation

# Plot cross-section (depth profile)
plt.figure()
plt.plot(transect_lon, transect_depth)
plt.title('Cross-Section of Lake Victoria')
plt.xlabel('Longitude')
plt.ylabel('Depth (m)')
plt.gca().invert_yaxis()  # Invert y-axis (depth increases downward)
plt.grid(True)
plt.show()
