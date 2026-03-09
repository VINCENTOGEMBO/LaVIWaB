# -*- coding: utf-8 -*-
"""
Created on Mon Nov  3 16:32:40 2025

@author: VO000003
"""



# 1. Import libraries
# --------------------------------------------
import os
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression



#%%
# --------------------------------------------
# 2. Define directory for latent heat evaporation
# --------------------------------------------
data_dir = r"C:\DATA\ISIMIP Data\Latent Heat Evaporation\UKESM1_ISIMIP3bOutputDatalakes_globalalbmukesm1-0-ll\isimip-download-4017f3cf43213469d84b235a63025faeb4c9a427"

# --------------------------------------------
# 3. Load and merge all NetCDF files
# --------------------------------------------
files = sorted([os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".nc")])

if not files:
    raise FileNotFoundError("⚠️ No NetCDF files found in the specified folder.")

# Open all files as one dataset
ds = xr.open_mfdataset(files, combine='by_coords')

# --------------------------------------------
# 4. Inspect variables
# --------------------------------------------
print("Available variables:", list(ds.data_vars))

# Replace 'hfls' below with the correct variable name if different
var_name = 'hfls' if 'hfls' in ds.data_vars else list(ds.data_vars.keys())[0]

# --------------------------------------------
# 5. Process latent heat data
# --------------------------------------------
# Latent heat flux is usually given in W/m²
lh = ds[var_name]
lh_mean = lh.mean(dim=["lat", "lon"])  # spatial mean
lh_df = lh_mean.to_dataframe().reset_index()

# Convert time to datetime
lh_df['time'] = pd.to_datetime(lh_df['time'])

# Annual mean
lh_annual = lh_df.set_index('time').resample('Y').mean()

# --------------------------------------------
# 6. Plot annual time series
# --------------------------------------------
plt.figure(figsize=(12, 6), dpi=150)
plt.plot(lh_annual.index, lh_annual[var_name], color='darkorange', linewidth=2, label='UKESM1-0-LL: Latent Heat Flux')

plt.title("UKESM1-0-LL: Lake Victoria Basin Annual Mean Latent Heat Flux (W/m²)", fontsize=14)
plt.xlabel("Year", fontsize=12)
plt.ylabel("Latent Heat Flux (W/m²)", fontsize=12)
plt.grid(True, alpha=0.4)
plt.legend()
plt.tight_layout()
plt.show()




#%% --------------------------------------------


# --------------------------------------------
# 1. Define paths for multiple scenarios
# --------------------------------------------
base_dir = r"C:\DATA\ISIMIP Data\Latent Heat Evaporation\UKESM1_ISIMIP3bOutputDatalakes_globalalbmukesm1-0-ll"

scenarios = {
    "SSP1-2.6": os.path.join(base_dir, "isimip-download-b2946ac7f91535984f83a62c19ea8d42055abece"),
    "SSP3-7.0": os.path.join(base_dir, "isimip-download-12000d5801776e85b1f57ca0f9e16a85705f5ad8"),  # replace with actual folder
    "SSP5-8.5": os.path.join(base_dir, "isimip-download-4017f3cf43213469d84b235a63025faeb4c9a427"),  # replace with actual folder
}

# --------------------------------------------
# 3. Function to load and process latent heat
# --------------------------------------------
def load_latent_heat(folder, var_name='hfls'):
    files = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".nc")])
    if not files:
        print(f"⚠️ No NetCDF files found in {folder}")
        return None
    
    ds = xr.open_mfdataset(files, combine='by_coords')
    
    # Check variable
    if var_name not in ds.data_vars:
        var_name = list(ds.data_vars.keys())[0]
        print(f"⚠️ Using variable '{var_name}' instead.")
    
    lh = ds[var_name]
    lh_mean = lh.mean(dim=["lat", "lon"])  # spatial mean
    lh_df = lh_mean.to_dataframe().reset_index()
    lh_df['time'] = pd.to_datetime(lh_df['time'])
    lh_annual = lh_df.set_index('time').resample('Y').mean()  # annual mean
    return lh_annual, var_name

# --------------------------------------------
# 4. Load all scenarios
# --------------------------------------------
lh_data = {}
var_names = {}

for scenario, folder in scenarios.items():
    if os.path.exists(folder):
        df, var = load_latent_heat(folder)
        if df is not None:
            lh_data[scenario] = df
            var_names[scenario] = var
    else:
        print(f"⚠️ Folder not found for {scenario}: {folder}")

# --------------------------------------------
# 5. Plot all scenarios together
# --------------------------------------------
plt.figure(figsize=(12, 6), dpi=150)
colors = {"SSP1-2.6": "blue", "SSP3-7.0": "orange", "SSP5-8.5": "red"}

for scenario, df in lh_data.items():
    plt.plot(df.index, df[var_names[scenario]], label=scenario, color=colors[scenario], linewidth=2)

plt.title("Lake Victoria Basin Annual Mean Latent Heat Flux (W/m²) under ISIMIP Models Scenarios", fontsize=14)
plt.xlabel("Year", fontsize=12)
plt.ylabel("Latent Heat Flux (W/m²)", fontsize=12)
plt.grid(True, alpha=0.3)
plt.legend(title="Scenario", fontsize=10)
plt.tight_layout()
plt.show()


#%%



# --------------------------------------------
# 1. Set directory and file pattern
# --------------------------------------------
data_dir = r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\GFDL-ESM_ISIMIP3bInputDataclimateatmospheregfdl-esm4\isimip-download-4ed5ac396cb52c78c4247627c81971e46220bafa"

# --------------------------------------------
# 3. Load and merge all NetCDF files
# --------------------------------------------
files = sorted([os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".nc")])

# Merge all files into one dataset
ds = xr.open_mfdataset(files, combine='by_coords')

# --------------------------------------------
# 4. Inspect the dataset
# --------------------------------------------
print(ds)
print(ds['pr'])  # variable name for precipitation

# --------------------------------------------
# 5. Convert precipitation (kg/m2/s) → mm/day
# --------------------------------------------
pr = ds['pr'] * 86400  # 1 kg/m2/s = 86400 mm/day
pr_mean = pr.mean(dim=["lat", "lon"])  # average over grid
pr_df = pr_mean.to_dataframe().reset_index()

# --------------------------------------------
# 6. (Optional) Resample to monthly or annual mean
# --------------------------------------------
pr_df['time'] = pd.to_datetime(pr_df['time'])
pr_monthly = pr_df.set_index('time').resample('M').mean()
pr_annual = pr_df.set_index('time').resample('Y').mean()

# --------------------------------------------
# 7. Plot
# --------------------------------------------
plt.figure(figsize=(12,6), dpi=150)
plt.plot(pr_annual.index, pr_annual['pr'], color='royalblue', linewidth=2, label='GFDL-ESM4 SSP3-7.0')
plt.title("GFDL-ESM4: Annual Mean Precipitation (SSP3-7.0 Scenario)", fontsize=14)
plt.xlabel("Year", fontsize=12)
plt.ylabel("Precipitation (mm/day)", fontsize=12)
plt.grid(True, alpha=0.4)
plt.legend()
plt.tight_layout()
plt.show()




#%%


# --------------------------------------------
# 1. Set directory and file pattern
# --------------------------------------------
data_dir = r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\GFDL-ESM_ISIMIP3bInputDataclimateatmospheregfdl-esm4\isimip-download-4ed5ac396cb52c78c4247627c81971e46220bafa"

# --------------------------------------------
# 3. Load and merge all NetCDF files
# --------------------------------------------
files = sorted([os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".nc")])

# Merge all files into one dataset
ds = xr.open_mfdataset(files, combine='by_coords')

# --------------------------------------------
# 4. Inspect the dataset
# --------------------------------------------
print(ds)
print(ds['pr'])  # variable name for precipitation

# --------------------------------------------
# 5. Convert precipitation (kg/m2/s) → mm/day
# --------------------------------------------
pr = ds['pr'] * 86400  # 1 kg/m2/s = 86400 mm/day
pr_mean = pr.mean(dim=["lat", "lon"])  # average over grid
pr_df = pr_mean.to_dataframe().reset_index()

# --------------------------------------------
# 6. (Optional) Resample to monthly or annual mean
# --------------------------------------------
pr_df['time'] = pd.to_datetime(pr_df['time'])
pr_monthly = pr_df.set_index('time').resample('M').mean()
pr_annual = pr_df.set_index('time').resample('Y').mean()

# --------------------------------------------
# 7. Plot
# --------------------------------------------
plt.figure(figsize=(12,6), dpi=150)
plt.plot(pr_annual.index, pr_annual['pr'], color='royalblue', linewidth=2, label='GFDL-ESM4 SSP3-7.0')
plt.title("GFDL-ESM4: Annual Mean Precipitation (SSP3-7.0 Scenario)", fontsize=14)
plt.xlabel("Year", fontsize=12)
plt.ylabel("Precipitation (mm/day)", fontsize=12)
plt.grid(True, alpha=0.4)
plt.legend()
plt.tight_layout()
plt.show()


#%%



# -------------------------------------------------
# 1. Define paths for the three scenarios
# -------------------------------------------------
base_dir = r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\GFDL-ESM_ISIMIP3bInputDataclimateatmospheregfdl-esm4"

scenarios = {
    "SSP1-2.6": os.path.join(base_dir, "C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\GFDL-ESM_ISIMIP3bInputDataclimateatmospheregfdl-esm4\isimip-download-b417c0cdec2fd86b1a30303857526d43121e8397"),  # update with exact folder name
    "SSP3-7.0": os.path.join(base_dir, "C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\GFDL-ESM_ISIMIP3bInputDataclimateatmospheregfdl-esm4\isimip-download-4ed5ac396cb52c78c4247627c81971e46220bafa"),
    "SSP5-8.5": os.path.join(base_dir, "C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\GFDL-ESM_ISIMIP3bInputDataclimateatmospheregfdl-esm4\isimip-download-31b33464e44cbaccef70bef9abe5c91be6c9b047"),
}

# -------------------------------------------------
# 3. Function to load and process precipitation
# -------------------------------------------------
def load_precip(folder):
    files = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".nc")])
    ds = xr.open_mfdataset(files, combine='by_coords')
    pr = ds['pr'] * 86400  # convert kg/m2/s to mm/day
    pr_mean = pr.mean(dim=["lat", "lon"])  # basin-average
    pr_df = pr_mean.to_dataframe().reset_index()
    pr_df['time'] = pd.to_datetime(pr_df['time'])
    pr_annual = pr_df.set_index('time').resample('Y').mean()
    return pr_annual

# -------------------------------------------------
# 4. Load each scenario and store data
# -------------------------------------------------
data = {}
for scenario, folder in scenarios.items():
    if os.path.exists(folder):
        data[scenario] = load_precip(folder)
    else:
        print(f"⚠️ Folder not found for {scenario}: {folder}")

# -------------------------------------------------
# 5. Plot all scenarios together
# -------------------------------------------------
plt.figure(figsize=(12, 6), dpi=150)
colors = {"SSP1-2.6": "green", "SSP3-7.0": "orange", "SSP5-8.5": "red"}

for scenario, df in data.items():
    plt.plot(df.index, df['pr'], label=scenario, color=colors[scenario], linewidth=2)

plt.title("GFDL-ESM4: Lake Victoria Basin Annual Mean Precipitation under ISIMIP Scenarios (1980–2100)", fontsize=14)
plt.xlabel("Year", fontsize=12)
plt.ylabel("Precipitation (mm/day)", fontsize=12)
plt.grid(True, alpha=0.3)
plt.legend(title="Scenario", fontsize=10)
plt.tight_layout()
plt.show()



#%%


# -------------------------------------------------
# 1. Define base directory and model list
# -------------------------------------------------
base_dir = r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection"

models = {
    "GFDL-ESM4": "GFDL-ESM_ISIMIP3bInputDataclimateatmospheregfdl-esm4",
    "IPSL-CM6A-LR": "IPSL-CM6A_ISIMIP3bInputDataclimateatmosphereipsl-cm6a-lr",
    "MPI-ESM1-2-HR": "MPI-ESM_ISIMIP3bInputDataclimateatmospherempi-esm1-2-hr",
    "MRI-ESM2-0": "MRI-ESM2_ISIMIP3bInputDataclimateatmospheremri-esm2-0",
    "UKESM1-0-LL": "UKESM1_ISIMIP3bInputDataclimateatmosphereukesm1-0"
}

# -------------------------------------------------
# 3. Define scenarios and mapping to your actual folders
# -------------------------------------------------
scenarios = ["SSP1-2.6", "SSP3-7.0", "SSP5-8.5"]

scenario_map = {
    "SSP1-2.6": "isimip-download-b417c0cdec2fd86b1a30303857526d43121e8397",
    "SSP3-7.0": "isimip-download-4ed5ac396cb52c78c4247627c81971e46220bafa",
    "SSP5-8.5": "isimip-download-31b33464e44cbaccef70bef9abe5c91be6c9b047"
}

# -------------------------------------------------
# 4. Function to load and process precipitation
# -------------------------------------------------
def load_precip_data(model_folder, scenario):
    if scenario not in scenario_map:
        print(f"⚠️ No mapping found for {scenario}")
        return None
    
    folder_path = os.path.join(model_folder, scenario_map[scenario])
    if not os.path.exists(folder_path):
        print(f"⚠️ Missing folder: {os.path.basename(model_folder)} - {scenario}")
        return None
    
    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".nc")]
    if not files:
        print(f"⚠️ No NetCDF files found in {folder_path}")
        return None

    ds = xr.open_mfdataset(files, combine='by_coords')
    var_name = 'pr' if 'pr' in ds.data_vars else list(ds.data_vars.keys())[0]
    pr = ds[var_name] * 86400  # convert from kg/m2/s to mm/day
    pr_mean = pr.mean(dim=["lat", "lon"])
    df = pr_mean.to_dataframe().reset_index()
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time').resample('YE').mean()
    return df

# -------------------------------------------------
# 5. Loop through all scenarios and models
# -------------------------------------------------
scenario_results = {}

for scenario in scenarios:
    model_dfs = []
    for model_name, model_folder in models.items():
        model_path = os.path.join(base_dir, model_folder)
        data = load_precip_data(model_path, scenario)
        if data is not None:
            model_dfs.append(data.rename(columns={"pr": model_name}))
    
    # Combine models for this scenario
    if model_dfs:
        combined = pd.concat(model_dfs, axis=1)
        scenario_results[scenario] = combined
    else:
        print(f"⚠️ No data available for scenario {scenario}")

# -------------------------------------------------
# 6. Plot multi-model mean with uncertainty shading
# -------------------------------------------------
plt.figure(figsize=(12, 6), dpi=150)
colors = {"SSP1-2.6": "green", "SSP3-7.0": "orange", "SSP5-8.5": "red"}

for scenario, df in scenario_results.items():
    ensemble_mean = df.mean(axis=1)
    ensemble_min = df.min(axis=1)
    ensemble_max = df.max(axis=1)
    
    plt.plot(ensemble_mean.index, ensemble_mean, color=colors[scenario],
             linewidth=2, label=f"{scenario} (mean of {len(df.columns)} models)")
    plt.fill_between(ensemble_mean.index, ensemble_min, ensemble_max,
                     color=colors[scenario], alpha=0.2)

plt.title("ISIMIP3b Multi-Model Annual Mean Precipitation\nLake Victoria Basin (1980–2100)", fontsize=14)
plt.xlabel("Year", fontsize=12)
plt.ylabel("Precipitation (mm/day)", fontsize=12)
plt.legend(fontsize=10, title="Scenario")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()





#%% --------------------------------------------
# COMBINE BOTH PRECIPITATION AND LATENT HEAT FLUX IN ONE PLOT

# 1. Define paths for precipitation and latent heat scenarios
# --------------------------------------------
precip_base = r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\GFDL-ESM_ISIMIP3bInputDataclimateatmospheregfdl-esm4"
lh_base = r"C:\DATA\ISIMIP Data\Latent Heat Evaporation\UKESM1_ISIMIP3bOutputDatalakes_globalalbmukesm1-0-ll"

scenarios = {
    "SSP1-2.6": {"pr": os.path.join(precip_base, "isimip-download-b417c0cdec2fd86b1a30303857526d43121e8397"),
                 "lh": os.path.join(lh_base, "isimip-download-b2946ac7f91535984f83a62c19ea8d42055abece")},
    "SSP3-7.0": {"pr": os.path.join(precip_base, "isimip-download-4ed5ac396cb52c78c4247627c81971e46220bafa"),
                 "lh": os.path.join(lh_base, "isimip-download-12000d5801776e85b1f57ca0f9e16a85705f5ad8")},
    "SSP5-8.5": {"pr": os.path.join(precip_base, "isimip-download-31b33464e44cbaccef70bef9abe5c91be6c9b047"),
                 "lh": os.path.join(lh_base, "isimip-download-4017f3cf43213469d84b235a63025faeb4c9a427")}
}

# --------------------------------------------
# 3. Function to load and process precipitation
# --------------------------------------------
def load_precip(folder):
    files = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".nc")])
    ds = xr.open_mfdataset(files, combine='by_coords')
    pr = ds['pr'] * 86400  # kg/m2/s -> mm/day
    pr_mean = pr.mean(dim=["lat", "lon"])
    df = pr_mean.to_dataframe().reset_index()
    df['time'] = pd.to_datetime(df['time'])
    df_annual = df.set_index('time').resample('Y').mean()
    return df_annual

# --------------------------------------------
# 4. Function to load and process latent heat
# --------------------------------------------
def load_latent_heat(folder, var_name='hfls'):
    files = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".nc")])
    ds = xr.open_mfdataset(files, combine='by_coords')
    
    if var_name not in ds.data_vars:
        var_name = list(ds.data_vars.keys())[0]
    
    lh = ds[var_name].mean(dim=["lat", "lon"])
    df = lh.to_dataframe().reset_index()
    df['time'] = pd.to_datetime(df['time'])
    df_annual = df.set_index('time').resample('Y').mean()
    
    # ✅ Convert from W/m² → mm/day (1 W/m² = 86400 / 2.45e6 mm/day)
    lambda_evap = 2.45e6  # J/kg
    df_annual[var_name] = df_annual[var_name] * (86400 / lambda_evap)
    
    return df_annual, var_name

# --------------------------------------------
# 5. Load all scenarios
# --------------------------------------------
precip_data = {}
lh_data = {}
var_names_lh = {}

for scenario, paths in scenarios.items():
    if os.path.exists(paths['pr']):
        precip_data[scenario] = load_precip(paths['pr'])
    else:
        print(f"⚠️ Precipitation folder not found: {paths['pr']}")
    
    if os.path.exists(paths['lh']):
        df, var = load_latent_heat(paths['lh'])
        lh_data[scenario] = df
        var_names_lh[scenario] = var
    else:
        print(f"⚠️ Latent heat folder not found: {paths['lh']}")

# --------------------------------------------
# 6. Plot precipitation and latent heat on same figure
# --------------------------------------------
plt.figure(figsize=(12, 6), dpi=150)

# Colors: separate schemes for precip (solid) and latent heat (dotted)
precip_colors = {"SSP1-2.6": "green", "SSP3-7.0": "orange", "SSP5-8.5": "red"}
lh_colors = {"SSP1-2.6": "blue", "SSP3-7.0": "deeppink", "SSP5-8.5": "black"}

for scenario in scenarios.keys():
    # Plot precipitation
    if scenario in precip_data:
        plt.plot(precip_data[scenario].index,
                 precip_data[scenario]['pr'],
                 label=f"{scenario} Precipitation",
                 color=precip_colors[scenario],
                 linestyle='-',
                 linewidth=2)
    # Plot latent heat
    if scenario in lh_data:
        plt.plot(lh_data[scenario].index,
                 lh_data[scenario][var_names_lh[scenario]],
                 label=f"{scenario} Latent Heat",
                 color=lh_colors[scenario],
                 linestyle='--',
                 linewidth=2)

# --------------------------------------------
# 7. Final figure formatting
# --------------------------------------------
plt.title("Lake Victoria Basin Annual Mean Precipitation and Latent Heat Flux (mm/day)", fontsize=14)
plt.xlabel("Year", fontsize=12)
plt.ylabel("Flux (mm/day)", fontsize=12)
plt.grid(True, alpha=0.3)
plt.legend(title="Scenario / Variable", fontsize=10)
plt.tight_layout()
plt.show()





#%% --------------------------------------------
# COMBINED PRECIPITATION & LATENT HEAT FLUX PLOTS BY SCENARIO
# --------------------------------------------

# 1. Define data paths
# --------------------------------------------
precip_base = r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\GFDL-ESM_ISIMIP3bInputDataclimateatmospheregfdl-esm4"
lh_base = r"C:\DATA\ISIMIP Data\Latent Heat Evaporation\UKESM1_ISIMIP3bOutputDatalakes_globalalbmukesm1-0-ll"

scenarios = {
    "SSP1-2.6": {"pr": os.path.join(precip_base, "isimip-download-b417c0cdec2fd86b1a30303857526d43121e8397"),
                 "lh": os.path.join(lh_base, "isimip-download-b2946ac7f91535984f83a62c19ea8d42055abece")},
    "SSP3-7.0": {"pr": os.path.join(precip_base, "isimip-download-4ed5ac396cb52c78c4247627c81971e46220bafa"),
                 "lh": os.path.join(lh_base, "isimip-download-12000d5801776e85b1f57ca0f9e16a85705f5ad8")},
    "SSP5-8.5": {"pr": os.path.join(precip_base, "isimip-download-31b33464e44cbaccef70bef9abe5c91be6c9b047"),
                 "lh": os.path.join(lh_base, "isimip-download-4017f3cf43213469d84b235a63025faeb4c9a427")}
}

# --------------------------------------------
# 2. Functions to load datasets
# --------------------------------------------
def load_precip(folder):
    files = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".nc")])
    ds = xr.open_mfdataset(files, combine='by_coords')
    pr = ds['pr'] * 86400  # kg/m2/s -> mm/day
    pr_mean = pr.mean(dim=["lat", "lon"])
    df = pr_mean.to_dataframe().reset_index()
    df['time'] = pd.to_datetime(df['time'])
    return df.set_index('time').resample('Y').mean()

def load_latent_heat(folder, var_name='hfls'):
    files = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".nc")])
    ds = xr.open_mfdataset(files, combine='by_coords')
    if var_name not in ds.data_vars:
        var_name = list(ds.data_vars.keys())[0]
    lh = ds[var_name].mean(dim=["lat", "lon"])
    df = lh.to_dataframe().reset_index()
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time').resample('Y').mean()
    df[var_name] = df[var_name] * (86400 / 2.45e6)  # W/m² -> mm/day
    return df, var_name

# --------------------------------------------
# 3. Load all scenarios
# --------------------------------------------
precip_data, lh_data, var_names_lh = {}, {}, {}

for scenario, paths in scenarios.items():
    if os.path.exists(paths['pr']):
        precip_data[scenario] = load_precip(paths['pr'])
    else:
        print(f"⚠️ Missing precipitation data: {paths['pr']}")
    if os.path.exists(paths['lh']):
        df, var = load_latent_heat(paths['lh'])
        lh_data[scenario] = df
        var_names_lh[scenario] = var
    else:
        print(f"⚠️ Missing latent heat data: {paths['lh']}")

# --------------------------------------------
# 4. Plot: 3 subplots for 3 SSP scenarios
# --------------------------------------------
fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True, dpi=150)
fig.suptitle("Lake Victoria Basin Annual Mean Precipitation and Latent Heat Flux (mm/day)", fontsize=14)

# Color settings
precip_colors = {"SSP1-2.6": "green", "SSP3-7.0": "orange", "SSP5-8.5": "red"}
lh_colors = {"SSP1-2.6": "blue", "SSP3-7.0": "deeppink", "SSP5-8.5": "black"}

for i, scenario in enumerate(scenarios.keys()):
    ax = axes[i]

    # Precipitation line (solid)
    if scenario in precip_data:
        ax.plot(precip_data[scenario].index,
                precip_data[scenario]['pr'],
                color=precip_colors[scenario],
                linestyle='-',
                linewidth=2,
                label="Precipitation")

    # Latent heat line (dotted)
    if scenario in lh_data:
        var = var_names_lh[scenario]
        ax.plot(lh_data[scenario].index,
                lh_data[scenario][var],
                color=lh_colors[scenario],
                linestyle='--',
                linewidth=2,
                label="Latent Heat Flux")

    ax.set_title(scenario, fontsize=12, loc='left', fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_ylabel("Flux (mm/day)", fontsize=11)
    ax.legend(fontsize=9)

# Common x-axis label
axes[-1].set_xlabel("Year", fontsize=12)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.show()






#%% --------------------------------------------
# COMBINED PRECIPITATION & LATENT HEAT FLUX PLOTS BY SCENARIO WITH TRENDLINES
# --------------------------------------------
# --------------------------------------------
# 1. Define data paths
# --------------------------------------------
precip_base = r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\GFDL-ESM_ISIMIP3bInputDataclimateatmospheregfdl-esm4"
lh_base = r"C:\DATA\ISIMIP Data\Latent Heat Evaporation\UKESM1_ISIMIP3bOutputDatalakes_globalalbmukesm1-0-ll"

scenarios = {
    "SSP1-2.6": {"pr": os.path.join(precip_base, "isimip-download-b417c0cdec2fd86b1a30303857526d43121e8397"),
                 "lh": os.path.join(lh_base, "isimip-download-b2946ac7f91535984f83a62c19ea8d42055abece")},
    "SSP3-7.0": {"pr": os.path.join(precip_base, "isimip-download-4ed5ac396cb52c78c4247627c81971e46220bafa"),
                 "lh": os.path.join(lh_base, "isimip-download-12000d5801776e85b1f57ca0f9e16a85705f5ad8")},
    "SSP5-8.5": {"pr": os.path.join(precip_base, "isimip-download-31b33464e44cbaccef70bef9abe5c91be6c9b047"),
                 "lh": os.path.join(lh_base, "isimip-download-4017f3cf43213469d84b235a63025faeb4c9a427")}
}

# --------------------------------------------
# 2. Functions to load datasets
# --------------------------------------------
def load_precip(folder):
    files = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".nc")])
    ds = xr.open_mfdataset(files, combine='by_coords')
    pr = ds['pr'] * 86400  # kg/m2/s -> mm/day
    pr_mean = pr.mean(dim=["lat", "lon"])
    df = pr_mean.to_dataframe().reset_index()
    df['time'] = pd.to_datetime(df['time'])
    return df.set_index('time').resample('Y').mean()

def load_latent_heat(folder, var_name='hfls'):
    files = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".nc")])
    ds = xr.open_mfdataset(files, combine='by_coords')
    if var_name not in ds.data_vars:
        var_name = list(ds.data_vars.keys())[0]
    lh = ds[var_name].mean(dim=["lat", "lon"])
    df = lh.to_dataframe().reset_index()
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time').resample('Y').mean()
    df[var_name] = df[var_name] * (86400 / 2.45e6)  # W/m² -> mm/day
    return df, var_name

# --------------------------------------------
# 3. Load all scenarios
# --------------------------------------------
precip_data, lh_data, var_names_lh = {}, {}, {}

for scenario, paths in scenarios.items():
    if os.path.exists(paths['pr']):
        precip_data[scenario] = load_precip(paths['pr'])
    else:
        print(f"⚠️ Missing precipitation data: {paths['pr']}")
    if os.path.exists(paths['lh']):
        df, var = load_latent_heat(paths['lh'])
        lh_data[scenario] = df
        var_names_lh[scenario] = var
    else:
        print(f"⚠️ Missing latent heat data: {paths['lh']}")

# --------------------------------------------
# 4. Plot: 3 subplots for 3 SSP scenarios + trendlines
# --------------------------------------------
fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True, dpi=150)
fig.suptitle("Lake Victoria Basin Annual Mean Precipitation and Latent Heat Flux (mm/day)", fontsize=14)

# Color settings
precip_colors = {"SSP1-2.6": "green", "SSP3-7.0": "orange", "SSP5-8.5": "red"}
lh_colors = {"SSP1-2.6": "blue", "SSP3-7.0": "deeppink", "SSP5-8.5": "black"}

for i, scenario in enumerate(scenarios.keys()):
    ax = axes[i]

    # Precipitation line (solid)
    if scenario in precip_data:
        df_pr = precip_data[scenario].copy()
        years = df_pr.index.year
        y_pr = df_pr['pr'].values
        ax.plot(df_pr.index, y_pr, color=precip_colors[scenario], linestyle='-', linewidth=2, label="Precipitation")

        # Trendline for precipitation
        z_pr = np.polyfit(years, y_pr, 1)
        trend_pr = np.poly1d(z_pr)
        ax.plot(df_pr.index, trend_pr(years), color=precip_colors[scenario], linestyle=':', linewidth=1.5,
                label="Precip. Trend")

    # Latent heat line (dashed)
    if scenario in lh_data:
        var = var_names_lh[scenario]
        df_lh = lh_data[scenario].copy()
        years = df_lh.index.year
        y_lh = df_lh[var].values
        ax.plot(df_lh.index, y_lh, color=lh_colors[scenario], linestyle='--', linewidth=2, label="Latent Heat Flux")

        # Trendline for latent heat
        z_lh = np.polyfit(years, y_lh, 1)
        trend_lh = np.poly1d(z_lh)
        ax.plot(df_lh.index, trend_lh(years), color=lh_colors[scenario], linestyle='-.', linewidth=1.5,
                label="LHF Trend")

    ax.set_title(scenario, fontsize=12, loc='left', fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_ylabel("Flux (mm/day)", fontsize=11)
    ax.legend(fontsize=8, loc="upper left")

# Common x-axis label
axes[-1].set_xlabel("Year", fontsize=12)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.show()


#%%

# HISTORICAL PLOTS


# -*- coding: utf-8 -*-
"""
Plot historical-only ISIMIP files (e.g., precipitation, latent heat)
@author: VO000003
"""

# --------------------------------------------
# 1. Define base directory and variable
# --------------------------------------------
data_dir = r"C:\DATA\ISIMIP Data\Latent Heat Evaporation\UKESM1_ISIMIP3bOutputDatalakes_globalalbmukesm1-0-ll\isimip-download-ad7fd1a6b887910d2620518d540854bb0b19494b"
var_name = 'hfls'   # or 'pr' for precipitation

# --------------------------------------------
# 2. Filter only *historical* files
# --------------------------------------------
all_files = sorted([os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".nc")])
hist_files = [f for f in all_files if "historical" in f.lower()]

if not hist_files:
    raise FileNotFoundError("⚠️ No historical NetCDF files found in this folder.")

print(f"Found {len(hist_files)} historical files.")

# --------------------------------------------
# 3. Load and process dataset
# --------------------------------------------
ds = xr.open_mfdataset(hist_files, combine='by_coords')

if var_name not in ds.data_vars:
    var_name = list(ds.data_vars.keys())[0]
    print(f"⚠️ Variable not found, using {var_name}")

da = ds[var_name]

# Convert variable units if needed
if var_name == 'pr':       # Precipitation kg/m2/s -> mm/day
    da = da * 86400
elif var_name == 'hfls':   # Latent heat W/m² -> mm/day
    da = da * (86400 / 2.45e6)

# --------------------------------------------
# 4. Compute spatial & annual mean
# --------------------------------------------
da_mean = da.mean(dim=["lat", "lon"])
df = da_mean.to_dataframe().reset_index()
df['time'] = pd.to_datetime(df['time'])
df = df.set_index('time').resample('Y').mean()

# --------------------------------------------
# 5. Plot
# --------------------------------------------
plt.figure(figsize=(12,6), dpi=150)
plt.plot(df.index, df[var_name], color='teal', linewidth=2)

plt.title(f"Historical Annual Mean {var_name.upper()} (Lake Victoria Basin)", fontsize=14)
plt.xlabel("Year", fontsize=12)
plt.ylabel("Flux (mm/day)" if var_name in ['pr','hfls'] else var_name, fontsize=12)
plt.grid(True, alpha=0.4)
plt.tight_layout()
plt.show()



#%% --------------------------------------------
# LATENT HEAT FLUX: UKESM1 & MRI-ESM2 COMBINED (Historical + SSPs)
# -------------------------------------------

# --------------------------------------------
# 1. Define directories
# --------------------------------------------
lh_base = r"C:\DATA\ISIMIP Data\Latent Heat Evaporation"

models = {
    "UKESM1-0-LL": {
        "historical": r"C:\DATA\ISIMIP Data\Latent Heat Evaporation\UKESM1_ISIMIP3bOutputDatalakes_globalalbmukesm1-0-ll\isimip-download-ad7fd1a6b887910d2620518d540854bb0b19494b",
        "ssp126": r"C:\DATA\ISIMIP Data\Latent Heat Evaporation\UKESM1_ISIMIP3bOutputDatalakes_globalalbmukesm1-0-ll\isimip-download-b2946ac7f91535984f83a62c19ea8d42055abece",
        "ssp370": r"C:\DATA\ISIMIP Data\Latent Heat Evaporation\UKESM1_ISIMIP3bOutputDatalakes_globalalbmukesm1-0-ll\isimip-download-12000d5801776e85b1f57ca0f9e16a85705f5ad8",
        "ssp585": r"C:\DATA\ISIMIP Data\Latent Heat Evaporation\UKESM1_ISIMIP3bOutputDatalakes_globalalbmukesm1-0-ll\isimip-download-4017f3cf43213469d84b235a63025faeb4c9a427",
    },
    "MRI-ESM2-0": {
        "historical": r"C:\DATA\ISIMIP Data\Latent Heat Evaporation\MRI-ESM2_ISIMIP3bOutputDatalakes_globalalbmmri-esm2-0\isimip-download-9a2396c1806c480742e4cae805f3645c5d5872a4",
        "ssp126": r"C:\DATA\ISIMIP Data\Latent Heat Evaporation\MRI-ESM2_ISIMIP3bOutputDatalakes_globalalbmmri-esm2-0\isimip-download-20836a746848f505bb5e960bc1c41e6ac63ef662",
        "ssp370": r"C:\DATA\ISIMIP Data\Latent Heat Evaporation\MRI-ESM2_ISIMIP3bOutputDatalakes_globalalbmmri-esm2-0\isimip-download-04807dc6b94473db3e82c54b14c77a008ae272e7",
        "ssp585": r"C:\DATA\ISIMIP Data\Latent Heat Evaporation\MRI-ESM2_ISIMIP3bOutputDatalakes_globalalbmmri-esm2-0\isimip-download-2c0c9c92bc11651472fc08d4857036b4e7a5736c",
    }
}

# --------------------------------------------
# 2. Helper function to load & process latent heat
# --------------------------------------------
def load_latent_heat(folder, var_name='hfls'):
    files = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".nc")])
    if not files:
        print(f"⚠️ No NetCDF files found in {folder}")
        return None
    ds = xr.open_mfdataset(files, combine='by_coords')
    if var_name not in ds.data_vars:
        var_name = list(ds.data_vars.keys())[0]
    lh = ds[var_name].mean(dim=["lat", "lon"])
    df = lh.to_dataframe().reset_index()
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time').resample('Y').mean()
    # Convert W/m² → mm/day (1 W/m² ≈ 0.035 mm/day)
    df[var_name] = df[var_name] * (86400 / 2.45e6)
    return df.rename(columns={var_name: 'latent_heat'})

# --------------------------------------------
# 3. Load all datasets
# --------------------------------------------
lh_data = {}
for model, paths in models.items():
    lh_data[model] = {}
    for scenario, path in paths.items():
        if os.path.exists(path):
            lh_data[model][scenario] = load_latent_heat(path)
        else:
            print(f"⚠️ Missing data for {model} - {scenario}")

# --------------------------------------------
# 4. Plot combined data
# --------------------------------------------
colors = {"ssp126": "blue", "ssp370": "green", "ssp585": "red"}
linestyles = {"UKESM1-0-LL": "-", "MRI-ESM2-0": "--"}

plt.figure(figsize=(12, 6), dpi=150)
plt.title("Lake Victoria Basin: Evaporation Latent Heat Flux (mm/day)", fontsize=14)

for scenario, color in colors.items():
    scenario_series = []
    for model, style in linestyles.items():
        df_hist = lh_data[model].get("historical")
        df_future = lh_data[model].get(scenario)
        if df_hist is not None and df_future is not None:
            df_combined = pd.concat([df_hist, df_future])
            plt.plot(df_combined.index, df_combined["latent_heat"], color=color, linestyle=style, linewidth=2,
                     label=f"{model} {scenario.upper()}")
            scenario_series.append(df_combined["latent_heat"])
    
    # Ensemble mean and trendline
    if scenario_series:
        ensemble = pd.concat(scenario_series, axis=1).mean(axis=1)
        plt.plot(ensemble.index, ensemble, color=color, linewidth=3, linestyle=':',
                 label=f"{scenario.upper()} Mean")
        x = np.arange(len(ensemble)).reshape(-1, 1)
        y = ensemble.values.reshape(-1, 1)
        trend = LinearRegression().fit(x, y).predict(x)
        plt.plot(ensemble.index, trend, color=color, linestyle='--', alpha=0.6)

plt.xlabel("Year", fontsize=12)
plt.ylabel("Evaporation - Latent Heat Flux (mm/day)", fontsize=12)
plt.legend(fontsize=9, ncol=2)
plt.grid(alpha=0.3)
plt.tight_layout()

# Save figure
plt.savefig("latent_heat_UKESM1_MRI_combined.png", dpi=300, bbox_inches="tight")
plt.show()

print("✅ Figure saved as 'latent_heat_UKESM1_MRI_combined.png'")








#%%


#%%


#%%

# PRECIPITATION    PRECIPITATION     PRECIPITATION

# ---------------------------------------------------------------
# PRECIPITATION: Historical Data for 5 ISIMIP Models
# ---------------------------------------------------------------


# ---------------------------------------------------------------
# 1. Define directories
# ---------------------------------------------------------------
pr_base = r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection"

models = {
    "GFDL-ESM4": r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\GFDL-ESM_ISIMIP3bInputDataclimateatmospheregfdl-esm4\isimip-download-e1b404e0599f538004c023bdc0951e4adf98af85",
    "IPSL-CM6A-LR": r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\IPSL-CM6A_ISIMIP3bInputDataclimateatmosphereipsl-cm6a-lr\isimip-download-e1b404e0599f538004c023bdc0951e4adf98af85",
    "MPI-ESM1-2-HR": r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\MPI-ESM_ISIMIP3bInputDataclimateatmospherempi-esm1-2-hr\isimip-download-8bb7aabb00a990ad45cdbce5b5bd0dfaca8e538f",
    "MRI-ESM2-0": r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\MRI-ESM2_ ISIMIP3bInputDataclimateatmospheremri-esm2-0\isimip-download-48a679cc8ae16f71cdd5e221430368c224ad7743",
    "UKESM1-0-LL": r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\UKESM1_ISIMIP3bInputDataclimateatmosphereukesm1-0\isimip-download-efff9895cf494be2138e5e510188440794bdff0c"
}

# ---------------------------------------------------------------
# 2. Helper function to load and process precipitation
# ---------------------------------------------------------------
def load_precipitation(folder, var_name='pr'):
    files = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".nc")])
    if not files:
        print(f"⚠️ No NetCDF files found in {folder}")
        return None
    
    ds = xr.open_mfdataset(files, combine='by_coords')
    if var_name not in ds.data_vars:
        var_name = list(ds.data_vars.keys())[0]
    
    pr = ds[var_name].mean(dim=["lat", "lon"])
    df = pr.to_dataframe().reset_index()
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time').resample('Y').sum()  # Convert to annual total
    # Convert from kg/m²/s → mm/year (1 kg/m²/s = 86400 mm/day)
    df[var_name] = df[var_name] * 86400
    return df.rename(columns={var_name: 'precipitation_mm_day'})

# ---------------------------------------------------------------
# 3. Load all model datasets
# ---------------------------------------------------------------
pr_data = {}
for model, path in models.items():
    if os.path.exists(path):
        pr_data[model] = load_precipitation(path)
    else:
        print(f"⚠️ Missing data for {model}")

# ---------------------------------------------------------------
# 4. Plot combined data
# ---------------------------------------------------------------
plt.figure(figsize=(12, 6), dpi=150)
plt.title("Lake Victoria Basin: Historical Precipitation (mm/day)", fontsize=14)

for model, df in pr_data.items():
    if df is not None:
        plt.plot(df.index, df["precipitation_mm_day"], linewidth=2, label=model)

# Ensemble mean and trendline
ensemble = pd.concat([df["precipitation_mm_day"] for df in pr_data.values() if df is not None], axis=1).mean(axis=1)
plt.plot(ensemble.index, ensemble, color="black", linewidth=3, linestyle='--', label="Ensemble Mean")

# Linear trend on ensemble mean
x = np.arange(len(ensemble)).reshape(-1, 1)
y = ensemble.values.reshape(-1, 1)
trend = LinearRegression().fit(x, y).predict(x)
plt.plot(ensemble.index, trend, color="gray", linestyle=":", alpha=0.7, label="Trendline")

plt.xlabel("Year", fontsize=12)
plt.ylabel("Annual Precipitation (mm/day)", fontsize=12)
plt.legend(fontsize=9, ncol=2)
plt.grid(alpha=0.3)
plt.tight_layout()

# Save figure
plt.savefig("precipitation_5models_historical.png", dpi=300, bbox_inches="tight")
plt.show()

print("✅ Figure saved as 'precipitation_5models_historical.png'")



#%%



# ===============================================================
# COMBINED PRECIPITATION PLOT: Historical + Projections (5 Models)
# Lake Victoria Basin – ISIMIP3b
# ===============================================================


# ---------------------------------------------------------------
# 1. Define base directories
# ---------------------------------------------------------------
base_dir = r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection"

# Historical model folders
historical_paths = {
    "GFDL-ESM4": r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\GFDL-ESM_ISIMIP3bInputDataclimateatmospheregfdl-esm4\isimip-download-e1b404e0599f538004c023bdc0951e4adf98af85",
    "IPSL-CM6A-LR": r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\IPSL-CM6A_ISIMIP3bInputDataclimateatmosphereipsl-cm6a-lr\isimip-download-e1b404e0599f538004c023bdc0951e4adf98af85",
    "MPI-ESM1-2-HR": r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\MPI-ESM_ISIMIP3bInputDataclimateatmospherempi-esm1-2-hr\isimip-download-8bb7aabb00a990ad45cdbce5b5bd0dfaca8e538f",
    "MRI-ESM2-0": r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\MRI-ESM2_ ISIMIP3bInputDataclimateatmospheremri-esm2-0\isimip-download-48a679cc8ae16f71cdd5e221430368c224ad7743",
    "UKESM1-0-LL": r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\UKESM1_ISIMIP3bInputDataclimateatmosphereukesm1-0\isimip-download-efff9895cf494be2138e5e510188440794bdff0c"
}

# Projection model folders
projection_models = {
    "GFDL-ESM4": "GFDL-ESM_ISIMIP3bInputDataclimateatmospheregfdl-esm4",
    "IPSL-CM6A-LR": "IPSL-CM6A_ISIMIP3bInputDataclimateatmosphereipsl-cm6a-lr",
    "MPI-ESM1-2-HR": "MPI-ESM_ISIMIP3bInputDataclimateatmospherempi-esm1-2-hr",
    "MRI-ESM2-0": "MRI-ESM2_ISIMIP3bInputDataclimateatmospheremri-esm2-0",
    "UKESM1-0-LL": "UKESM1_ISIMIP3bInputDataclimateatmosphereukesm1-0"
}

scenarios = ["SSP1-2.6", "SSP3-7.0", "SSP5-8.5"]
scenario_map = {
    "SSP1-2.6": "isimip-download-b417c0cdec2fd86b1a30303857526d43121e8397",
    "SSP3-7.0": "isimip-download-4ed5ac396cb52c78c4247627c81971e46220bafa",
    "SSP5-8.5": "isimip-download-31b33464e44cbaccef70bef9abe5c91be6c9b047"
}

# ---------------------------------------------------------------
# 2. Helper function – load precipitation and aggregate annually
# ---------------------------------------------------------------
def load_precip(folder, var_name='pr'):
    files = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".nc")])
    if not files:
        print(f"⚠️ No NetCDF files found in {folder}")
        return None
    ds = xr.open_mfdataset(files, combine='by_coords')
    if var_name not in ds.data_vars:
        var_name = list(ds.data_vars.keys())[0]
    pr = ds[var_name] * 86400  # Convert from kg/m²/s → mm/day
    df = pr.mean(dim=["lat", "lon"]).to_dataframe().reset_index()
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index("time").resample("Y").mean()
    return df.rename(columns={var_name: "precipitation_mm_day"})

# ---------------------------------------------------------------
# 3. Load historical data
# ---------------------------------------------------------------
hist_data = {}
for model, path in historical_paths.items():
    if os.path.exists(path):
        hist_data[model] = load_precip(path)
    else:
        print(f"⚠️ Missing historical data for {model}")

# ---------------------------------------------------------------
# 4. Load projection data
# ---------------------------------------------------------------
proj_data = {sc: {} for sc in scenarios}

for scenario in scenarios:
    for model, subpath in projection_models.items():
        folder_path = os.path.join(base_dir, subpath, scenario_map[scenario])
        if os.path.exists(folder_path):
            proj_data[scenario][model] = load_precip(folder_path)
        else:
            print(f"⚠️ Missing projection data for {model} - {scenario}")

# ---------------------------------------------------------------
# 5. Plot all data together
# ---------------------------------------------------------------
plt.figure(figsize=(13, 7), dpi=150)
plt.title("Lake Victoria Basin: Multi-Model Precipitation (Historical + SSPs)", fontsize=14)

# --- Historical ensemble mean ---
hist_ensemble = pd.concat([df["precipitation_mm_day"] for df in hist_data.values() if df is not None], axis=1).mean(axis=1)
plt.plot(hist_ensemble.index, hist_ensemble, color="black", linewidth=3, label="Historical Ensemble Mean (5 models)")

# --- Future projections ensemble ---
colors = {"SSP1-2.6": "green", "SSP3-7.0": "orange", "SSP5-8.5": "red"}

for scenario in scenarios:
    scenario_dfs = [df["precipitation_mm_day"] for df in proj_data[scenario].values() if df is not None]
    if scenario_dfs:
        ensemble = pd.concat(scenario_dfs, axis=1).mean(axis=1)
        min_vals = pd.concat(scenario_dfs, axis=1).min(axis=1)
        max_vals = pd.concat(scenario_dfs, axis=1).max(axis=1)

        plt.plot(ensemble.index, ensemble, color=colors[scenario], linewidth=2.5, label=f"{scenario} Mean")
        plt.fill_between(ensemble.index, min_vals, max_vals, color=colors[scenario], alpha=0.2)

# --- Trendline for historical ensemble ---
x = np.arange(len(hist_ensemble)).reshape(-1, 1)
y = hist_ensemble.values.reshape(-1, 1)
trend = LinearRegression().fit(x, y).predict(x)
plt.plot(hist_ensemble.index, trend, color="gray", linestyle=":", label="Historical Trend")

plt.xlabel("Year", fontsize=12)
plt.ylabel("Mean Precipitation (mm/day)", fontsize=12)
plt.legend(fontsize=9, ncol=2)
plt.grid(alpha=0.3)
plt.tight_layout()

# Save figure
plt.savefig("precipitation_combined_hist_proj.png", dpi=300, bbox_inches="tight")
plt.show()

print("✅ Combined figure saved as 'precipitation_combined_hist_proj.png'")



