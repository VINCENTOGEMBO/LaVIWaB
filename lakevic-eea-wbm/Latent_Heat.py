# -*- coding: utf-8 -*-


import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import os

# Step 1: Define the directory where the NetCDF files are stored
data_directory = r"C:\DATA\Temperature\ALBM_Model"  # Adjust to your directory

# Step 2: List all the NetCDF files
file_list = [f for f in os.listdir(data_directory) if f.endswith('.nc')]

# Step 3: Initialize lists to store temperature and time data
temperature_data = []
time_data = []

# Step 4: Loop through the files, load them, and append the temperature data
for file in file_list:
    file_path = os.path.join(data_directory, file)
    dataset = xr.open_dataset(file_path, chunks={'time': 365})  # Use Dask to chunk the data
    
    # Using the correct variable name 'latentheatf' as per your dataset
    temperature = dataset['latentheatf']  # Correct variable name
    time = dataset['time']  # Assuming 'time' is the time variable

    # Add the temperature data to the list
    temperature_data.append(temperature)

# Step 5: Concatenate the temperature data along the time dimension using Dask
temperature_combined = xr.concat(temperature_data, dim='time')

# Step 6: Define the time bins (1901-2019) as datetime64
time_bins = np.arange(1901, 2020, 10)  # Years from 1901 to 2019 with a step of 10
time_bins = np.array([np.datetime64(f'{year}-01-01') for year in time_bins])  # Convert to datetime64

# Step 7: Perform the groupby_bins operation based on the time dimension
temperature_10yr = temperature_combined.groupby_bins('time', time_bins).mean()

# Step 8: Plot the temperature data for each 10-year interval
plt.figure(figsize=(10, 6))
for i in range(len(temperature_10yr)):
    plt.plot(temperature_10yr[i].time.values, temperature_10yr[i].values, label=f'{time_bins[i].astype("datetime64[Y]").astype(str)}-{time_bins[i+1].astype("datetime64[Y]").astype(str)}')

plt.xlabel('Year')
plt.ylabel('Temperature (°C)')  # Adjust units if needed
plt.title('ALBM ISIMIP Temperature Over 10-Year Intervals (1901-2019)')
plt.legend()
plt.grid(True)
plt.show()


#%%

import xarray as xr
import matplotlib.pyplot as plt

# Step 1: Define the file path for the specific decade (e.g., 1901-1910)
file_path = r"C:\DATA\Temperature\ALBM_Model\albm_gswp3-w5e5_obsclim_2015soc_default_latentheatf_global_daily_2011_2019.nc"  # Adjust to your file path

# Step 2: Load the NetCDF data for that specific decade
dataset = xr.open_dataset(file_path)

# Step 3: Check the structure of the dataset
print(dataset)

# Step 4: Extract the relevant variable, for example, 'latentheatf' (adjust if necessary)
temperature = dataset['latentheatf']  # Adjust this variable name as per your dataset

# Step 5: Plot the temperature data
# We can plot a time slice (e.g., mean temperature over the decade)

plt.figure(figsize=(10, 6))
temperature.mean(dim=['lat', 'lon']).plot()  # Averaging over latitude and longitude
plt.xlabel('Time (Year)')
plt.ylabel('Average Temperature (°C)')  # Adjust units if necessary
plt.title('Average Temperature Over the Decade 2011-2019')
plt.grid(True)
plt.show()

#%%

"C:\DATA\Temperature\GOTM_Model\gotm_gswp3-w5e5_obsclim_histsoc_default_latentheatf_global_daily_2011_2019.nc"

import xarray as xr
import matplotlib.pyplot as plt

# Step 1: Define the file path for the specific decade (e.g., 1901-1910)
file_path = r"C:\DATA\Temperature\GOTM_Model\gotm_gswp3-w5e5_obsclim_histsoc_default_latentheatf_global_daily_2011_2019.nc"  # Adjust to your file path

# Step 2: Load the NetCDF data for that specific decade
dataset = xr.open_dataset(file_path)

# Step 3: Check the structure of the dataset
print(dataset)

# Step 4: Extract the relevant variable, for example, 'latentheatf' (adjust if necessary)
temperature = dataset['latentheatf']  # Adjust this variable name as per your dataset

# Step 5: Plot the temperature data
# We can plot a time slice (e.g., mean temperature over the decade)

plt.figure(figsize=(10, 6))
temperature.mean(dim=['lat', 'lon']).plot()  # Averaging over latitude and longitude
plt.xlabel('Time (Year)')
plt.ylabel('Average Temperature (°C)')  # Adjust units if necessary
plt.title('Average Temperature Over the Decade 2011-2019')
plt.grid(True)
plt.show()

#%%

import xarray as xr
import matplotlib.pyplot as plt

# Define file paths
file_path_albm = r"C:\DATA\Temperature\ALBM_Model\albm_gswp3-w5e5_obsclim_2015soc_default_latentheatf_global_daily_2011_2019.nc"
file_path_gotm = r"C:\DATA\Temperature\GOTM_Model\gotm_gswp3-w5e5_obsclim_histsoc_default_latentheatf_global_daily_2011_2019.nc"

# Load NetCDF datasets
dataset_albm = xr.open_dataset(file_path_albm, engine="netcdf4")
dataset_gotm = xr.open_dataset(file_path_gotm, engine="netcdf4")

# Print available variables to check correct temperature variable
print("ALBM Dataset Variables:", list(dataset_albm.variables.keys()))
print("GOTM Dataset Variables:", list(dataset_gotm.variables.keys()))

# Identify temperature variable (replace 'latentheatf' with correct variable if needed)
temperature_var = 'latentheatf'  # Update if necessary

# Extract temperature data
temperature_albm = dataset_albm[temperature_var]
temperature_gotm = dataset_gotm[temperature_var]

# Convert Kelvin to Celsius if needed
if 'units' in temperature_albm.attrs and temperature_albm.units in ['K', 'kelvin']:
    temperature_albm = temperature_albm - 273.15
    print("Converted ALBM temperature from Kelvin to Celsius.")

if 'units' in temperature_gotm.attrs and temperature_gotm.units in ['K', 'kelvin']:
    temperature_gotm = temperature_gotm - 273.15
    print("Converted GOTM temperature from Kelvin to Celsius.")

# Extract time variable
time_albm = dataset_albm['time']
time_gotm = dataset_gotm['time']

# Compute mean temperature over Lake Victoria
temp_mean_albm = temperature_albm.mean(dim=['lat', 'lon'])
temp_mean_gotm = temperature_gotm.mean(dim=['lat', 'lon'])

fig, ax = plt.subplots(figsize=(10,5)) 

# Plot both datasets for comparison
plt.figure(figsize=(12, 6))
plt.plot(time_albm, temp_mean_albm, label="ALBM Model", color='blue', linestyle='dashed')
plt.plot(time_gotm, temp_mean_gotm, label="GOTM Model", color='red', linestyle='solid')

# Labels and title
plt.xlabel('Time (Year)')
plt.ylabel('Average Temperature (°C)')  # Adjust units if necessary
plt.title('Comparison of ALBM Model vs. GOTM Model for Lake Victoria Basin (2011-2019)')
plt.legend()
plt.grid(True)

# Show the plot
plt.show()



#%%

import xarray as xr
import matplotlib.pyplot as plt

# Define file paths for ALBM and GOTM model data (adjust paths if necessary)
file_paths_albm = [
    r"C:\DATA\Temperature\ALBM_Model\albm_gswp3-w5e5_obsclim_2015soc_default_latentheatf_global_daily_1981_1990.nc",
    r"C:\DATA\Temperature\ALBM_Model\albm_gswp3-w5e5_obsclim_2015soc_default_latentheatf_global_daily_1991_2000.nc",
    r"C:\DATA\Temperature\ALBM_Model\albm_gswp3-w5e5_obsclim_2015soc_default_latentheatf_global_daily_2001_2010.nc",
    r"C:\DATA\Temperature\ALBM_Model\albm_gswp3-w5e5_obsclim_2015soc_default_latentheatf_global_daily_2011_2019.nc"
]

file_paths_gotm = [
    r"C:\DATA\Temperature\GOTM_Model\gotm_gswp3-w5e5_obsclim_histsoc_default_latentheatf_global_daily_1981_1990.nc",
    r"C:\DATA\Temperature\GOTM_Model\gotm_gswp3-w5e5_obsclim_histsoc_default_latentheatf_global_daily_1991_2000.nc",
    r"C:\DATA\Temperature\GOTM_Model\gotm_gswp3-w5e5_obsclim_histsoc_default_latentheatf_global_daily_2001_2010.nc",
    r"C:\DATA\Temperature\GOTM_Model\gotm_gswp3-w5e5_obsclim_histsoc_default_latentheatf_global_daily_2011_2019.nc"
]

# Load and merge ALBM files
datasets_albm = [xr.open_dataset(file, engine="netcdf4") for file in file_paths_albm]
dataset_albm = xr.concat(datasets_albm, dim="time")  # Merge along the time dimension

# Load and merge GOTM files
datasets_gotm = [xr.open_dataset(file, engine="netcdf4") for file in file_paths_gotm]
dataset_gotm = xr.concat(datasets_gotm, dim="time")  # Merge along the time dimension

# Print available variables to check correct temperature variable
print("ALBM Dataset Variables:", list(dataset_albm.variables.keys()))
print("GOTM Dataset Variables:", list(dataset_gotm.variables.keys()))

# Identify temperature variable (replace 'latentheatf' with correct variable if needed)
temperature_var = 'latentheatf'  # Update if necessary

# Extract temperature data
temperature_albm = dataset_albm[temperature_var]
temperature_gotm = dataset_gotm[temperature_var]

# Convert Kelvin to Celsius if needed
if 'units' in temperature_albm.attrs and temperature_albm.units in ['K', 'kelvin']:
    temperature_albm = temperature_albm - 273.15
    print("Converted ALBM temperature from Kelvin to Celsius.")

if 'units' in temperature_gotm.attrs and temperature_gotm.units in ['K', 'kelvin']:
    temperature_gotm = temperature_gotm - 273.15
    print("Converted GOTM temperature from Kelvin to Celsius.")

# Extract time variable
time_albm = dataset_albm['time']
time_gotm = dataset_gotm['time']

# Compute mean temperature over Lake Victoria
temp_mean_albm = temperature_albm.mean(dim=['lat', 'lon'])
temp_mean_gotm = temperature_gotm.mean(dim=['lat', 'lon'])

# Plot both datasets for comparison
plt.figure(figsize=(12, 6))
plt.plot(time_albm, temp_mean_albm, label="ALBM Model", color='blue', linestyle='dashed')
plt.plot(time_gotm, temp_mean_gotm, label="GOTM Model", color='red', linestyle='solid')

# Labels and title
plt.xlabel('Time (Year)')
plt.ylabel('Average Temperature (°C)')  # Adjust units if necessary
plt.title('Comparison of ALBM vs. GOTM Model Latent Heat for Lake Victoria (1981-2019)')
plt.legend()
plt.grid(True)

# Show the plot
plt.show()


#%%

#Convert to Evaporation Temperatures 

import xarray as xr
import matplotlib.pyplot as plt

# Enable dask to load data lazily
datasets_albm = [xr.open_dataset(file, engine="netcdf4", chunks={'time': 100}) for file in file_paths_albm]
datasets_gotm = [xr.open_dataset(file, engine="netcdf4", chunks={'time': 100}) for file in file_paths_gotm]

# Concatenate datasets along time axis
dataset_albm = xr.concat(datasets_albm, dim="time")
dataset_gotm = xr.concat(datasets_gotm, dim="time")

# Identify latent heat variable
latent_heat_var = 'latentheatf'  # Update if necessary

# Extract latent heat data
latent_heat_albm = dataset_albm[latent_heat_var]
latent_heat_gotm = dataset_gotm[latent_heat_var]

# Convert latent heat to temperature
c_p = 1860  # Specific heat capacity of water vapor (J/kg·K)
T0 = 273.15  # Reference temperature in Kelvin

temperature_albm = T0 + (latent_heat_albm / c_p)
temperature_gotm = T0 + (latent_heat_gotm / c_p)

# Convert from Kelvin to Celsius
temperature_albm = temperature_albm - 273.15
temperature_gotm = temperature_gotm - 273.15

# Compute mean temperature over Lake Victoria lazily
temp_mean_albm = temperature_albm.mean(dim=['lat', 'lon'])
temp_mean_gotm = temperature_gotm.mean(dim=['lat', 'lon'])

# Compute actual values before plotting
temp_mean_albm = temp_mean_albm.compute()
temp_mean_gotm = temp_mean_gotm.compute()

# Extract time variable
time_albm = dataset_albm['time']
time_gotm = dataset_gotm['time']

# Plot both datasets for comparison
plt.figure(figsize=(12, 6))
plt.plot(time_albm, temp_mean_albm, label="ALBM Model", color='blue', linestyle='dashed')
plt.plot(time_gotm, temp_mean_gotm, label="GOTM Model", color='red', linestyle='solid')

# Labels and title
plt.xlabel('Time (Year)')
plt.ylabel('Evaporation Temperature (°C)')
plt.title('Comparison of ALBM vs. GOTM Model Evaporation Temperature (1981-2019)')
plt.legend()
plt.grid(True)

# Show the plot
plt.show()



