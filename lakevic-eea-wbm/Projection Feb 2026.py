# -*- coding: utf-8 -*-
"""
Created on Thu Feb 19 17:23:20 2026

@author: VO000003
"""


#%%

import xarray as xr
import os
import glob
import pandas as pd

# ======================================================
# 1. DEFINE YOUR FOLDER
# ======================================================

folder = r
# ======================================================
# 2. GET ALL NETCDF FILES
# ======================================================

files = sorted(glob.glob(os.path.join(folder, "*.nc")))

print(f"Found {len(files)} files")

if len(files) == 0:
    raise ValueError("No NetCDF files found in folder.")

# ======================================================
# 3. OPEN FILES SAFELY
# ======================================================

datasets = []

for f in files:
    try:
        print("Opening:", os.path.basename(f))
        ds = xr.open_dataset(f, decode_times=True)
        datasets.append(ds)
    except Exception as e:
        print("Skipping file due to error:", f)
        print(e)

if len(datasets) == 0:
    raise ValueError("No valid datasets opened.")

# ======================================================
# 4. CONCATENATE ALONG TIME
# ======================================================



ds_merged = xr.concat(datasets, dim="time")

# Sort by time
ds_merged = ds_merged.sortby("time")

# Remove duplicate timestamps (correct method)
import numpy as np
time_values = ds_merged["time"].values
_, index = np.unique(time_values, return_index=True)
ds_merged = ds_merged.isel(time=np.sort(index))

# Ensure correct time slice
ds_merged = ds_merged.sel(time=slice("2015-01-01", "2100-12-31"))

print("Final time range:",
      str(ds_merged.time.min().values),
      "to",
      str(ds_merged.time.max().values))

# ======================================================
# 5. SAVE MERGED FILE
# ======================================================

output_file = os.path.join(folder, "GFDL-ESM4_ssp126_merged_2015_2100.nc")

print("Saving merged file...")
ds_merged.to_netcdf(output_file)

print("✅ Successfully saved:")
print(output_file)


#%%
import xarray as xr
import matplotlib.pyplot as plt
import numpy as np

# =====================================================
# 1. FILE PATHS (UNCHANGED)
# =====================================================

input_files = {
    "20CRv3": r"C:\DATA\0. Data Projection & Attribution\ISIMIP Data 2\ISIMIP3a_Input Data_Climate Forcing_Atmo Forcing_Precipitation\20CRv3_isimip-download-53081cb3893851e5af71671c11a50c7f346e3b6a\20crv3_obsclim_pr_lon30.0to36.0lat-4.0to1.0_daily_1901_2015.nc",
    "20CRv3-ERA5": r"C:\DATA\0. Data Projection & Attribution\ISIMIP Data 2\ISIMIP3a_Input Data_Climate Forcing_Atmo Forcing_Precipitation\20CRv3-ERA5_isimip-download-3f63a01ce0410cb048f3148d245a76120afcbe57\20crv3-era5_obsclim_pr_daily_1901_2024.nc",
    "20CRv3-W5E5": r"C:\DATA\0. Data Projection & Attribution\ISIMIP Data 2\ISIMIP3a_Input Data_Climate Forcing_Atmo Forcing_Precipitation\20CRv3-W5E5_isimip-download-82f71a92ff21e7d7356285bcc8ebc2d32643c29d\20crv3-w5e5_obsclim_pr_daily_1901_2019.nc",
    "GSWP3-W5E5": r"C:\DATA\0. Data Projection & Attribution\ISIMIP Data 2\ISIMIP3a_Input Data_Climate Forcing_Atmo Forcing_Precipitation\GSWP3-W5E5_isimip-download-e0eb602669ff732526c4f52e423cd6a4996344a9\gswp3-w5e5_obsclim_pr_daily_1901_2019.nc"
}

albm_files = {
    "20CRv3": r"C:\DATA\0. Data Projection & Attribution\ISIMIP Data 2\ISIMIP3a_Output Data_Lakes Global_ALBM_Latentheat\isimip-download-83aa3d361e872a496b342d343a124f034bf55121\albm_20crv3_obsclim_2015soc_default_latentheatf_daily_1901_2015.nc",
    "20CRv3-ERA5": r"C:\DATA\0. Data Projection & Attribution\ISIMIP Data 2\ISIMIP3a_Output Data_Lakes Global_ALBM_Latentheat\isimip-download-5aa426fa6f872e9a958b828e0205f32f8ea46e30\albm_20crv3-era5_obsclim_2015soc_default_latentheatf_daily_1901_2019.nc",
    "20CRv3-W5E5": r"C:\DATA\0. Data Projection & Attribution\ISIMIP Data 2\ISIMIP3a_Output Data_Lakes Global_ALBM_Latentheat\isimip-download-2252c42897f9f8e7620ea196d7e534a79d45b0af\albm_20crv3-w5e5_obsclim_2015soc_default_latentheatf_daily_1901_2019.nc",
    "GSWP3-W5E5": r"C:\DATA\0. Data Projection & Attribution\ISIMIP Data 2\ISIMIP3a_Output Data_Lakes Global_ALBM_Latentheat\isimip-download-3b6ad5a710b30c3e8f4505a73d769e63b3b10241\albm_gswp3-w5e5_obsclim_2015soc_default_latentheatf_daily_1901_2019.nc"
}

gotm_files = {
    "20CRv3": r"C:\DATA\0. Data Projection & Attribution\ISIMIP Data 2\ISIMIP3a_Output Data_Lakes Global_GOTM_Latentheat\isimip-download-564f7932506ba70fd961137da3a55a6063f03ab1\gotm_20crv3_obsclim_histsoc_default_latentheat_merged_1901_2015.nc",
    "20CRv3-ERA5": r"C:\DATA\0. Data Projection & Attribution\ISIMIP Data 2\ISIMIP3a_Output Data_Lakes Global_GOTM_Latentheat\isimip-download-fcd43b80507dcd773d3f3602b05496f652d31ca6\gotm_20crv3-era5_obsclim_histsoc_default_latentheatf_merged_1901_2021.nc",
    "GSWP3-W5E5": r"C:\DATA\0. Data Projection & Attribution\ISIMIP Data 2\ISIMIP3a_Output Data_Lakes Global_GOTM_Latentheat\isimip-download-e2f437d74cf6864f2f5fbad1fe8c5fc717b6e318\gotm_gswp3-w5e5_obsclim_histsoc_default_latentheatf_merged_1901_2019.nc"
}

# =====================================================
# 2. ROBUST PROCESSING FUNCTION
# =====================================================

def process_dataset(file_path, var_candidates):

    ds = xr.open_dataset(file_path)

    # Ensure time decoding
    ds["time"] = xr.decode_cf(ds).time

    print("\nProcessing:", file_path)
    print("Time range:", ds.time.min().values, "to", ds.time.max().values)

    # Time slice
    ds = ds.sel(time=slice("1901-01-01", "2015-12-31"))

    # Detect variable automatically
    var_name = None
    for v in var_candidates:
        if v in ds.data_vars:
            var_name = v
            break

    if var_name is None:
        print("⚠ Variable not found. Available:", list(ds.data_vars))
        return None

    data = ds[var_name]

    # Detect coordinates
    lat_name = next((c for c in ["lat", "latitude"] if c in ds.coords), None)
    lon_name = next((c for c in ["lon", "longitude"] if c in ds.coords), None)

    if lat_name and lon_name:

        lat_vals = ds[lat_name].values

        # Handle reversed latitude
        if lat_vals[0] > lat_vals[-1]:
            lat_slice = slice(1, -4)
        else:
            lat_slice = slice(-4, 1)

        data = data.sel({lat_name: lat_slice, lon_name: slice(30, 36)})

        if data.size == 0:
            print("⚠ Spatial selection returned empty array.")
            return None

        data = data.mean(dim=[lat_name, lon_name])

    # Remove all-NaN
    if data.isnull().all():
        print("⚠ Data is all NaN after selection.")
        return None

    # Convert to annual mean
    annual = data.resample(time="1Y").mean()

    return annual


# =====================================================
# 3. LOAD AND PROCESS
# =====================================================

results = {}

for key in input_files:

    print("\n==============================")
    print("Processing:", key)

    pr = process_dataset(input_files[key], ["pr"])
    if pr is not None:
        pr = pr * 86400  # kg m-2 s-1 → mm/day

    albm = process_dataset(albm_files[key], ["latentheatf", "latentheat"])

    results[key] = {}

    if pr is not None:
        results[key]["Input_PR"] = pr

    if albm is not None:
        results[key]["ALBM"] = albm

    if key in gotm_files:
        gotm = process_dataset(gotm_files[key], ["latentheatf", "latentheat"])
        if gotm is not None:
            results[key]["GOTM"] = gotm


# =====================================================
# 4. ENSEMBLE PROCESSING
# =====================================================

def build_ensemble(variable_key):
    """
    Collect same variable across models and compute ensemble stats.
    """
    members = []
    labels = []

    for key in results:
        if variable_key in results[key]:
            members.append(results[key][variable_key])
            labels.append(key)

    if len(members) == 0:
        return None, None, None, None

    # Align time
    aligned = xr.align(*members, join="inner")

    stacked = xr.concat(aligned, dim="model")
    stacked["model"] = labels

    ens_mean = stacked.mean(dim="model")
    ens_std = stacked.std(dim="model")

    return stacked, ens_mean, ens_std, labels


# Build ensembles
pr_stack, pr_mean, pr_std, pr_labels = build_ensemble("Input_PR")
albm_stack, albm_mean, albm_std, albm_labels = build_ensemble("ALBM")
gotm_stack, gotm_mean, gotm_std, gotm_labels = build_ensemble("GOTM")


#=====================================================
# 5. PLOT WITH ENSEMBLE + ENVELOPE
#=====================================================

plt.figure(figsize=(10, 8))

# -----------------------------
# PLOT PRECIPITATION ENSEMBLE
# -----------------------------
if pr_stack is not None:

    # Individual members (faint)
    for i in range(pr_stack.sizes["model"]):
        plt.plot(pr_stack.time,
                 pr_stack.isel(model=i),
                 alpha=0.3,
                 linestyle="--")

    # Ensemble mean
    plt.plot(pr_mean.time,
             pr_mean,
             linewidth=3,
             label="PR Ensemble Mean")

    # Uncertainty envelope ±1 std
    plt.fill_between(pr_mean.time.values,
                     (pr_mean - pr_std).values,
                     (pr_mean + pr_std).values,
                     alpha=0.2)


# -----------------------------
# PLOT ALBM ENSEMBLE
# -----------------------------
if albm_stack is not None:

    for i in range(albm_stack.sizes["model"]):
        plt.plot(albm_stack.time,
                 albm_stack.isel(model=i),
                 alpha=0.3)

    plt.plot(albm_mean.time,
             albm_mean,
             linewidth=3,
             label="ALBM Ensemble Mean")

    plt.fill_between(albm_mean.time.values,
                     (albm_mean - albm_std).values,
                     (albm_mean + albm_std).values,
                     alpha=0.2)


# -----------------------------
# PLOT GOTM ENSEMBLE
# -----------------------------
if gotm_stack is not None:

    for i in range(gotm_stack.sizes["model"]):
        plt.plot(gotm_stack.time,
                 gotm_stack.isel(model=i),
                 alpha=0.3)

    plt.plot(gotm_mean.time,
             gotm_mean,
             linewidth=3,
             label="GOTM Ensemble Mean")

    plt.fill_between(gotm_mean.time.values,
                     (gotm_mean - gotm_std).values,
                     (gotm_mean + gotm_std).values,
                     alpha=0.2)


# -----------------------------
# FINAL FIGURE SETTINGS
# -----------------------------
plt.title("Lake Victoria ISIMIP3a Ensemble Mean + Uncertainty (1901–2015)")
plt.xlabel("Year")
plt.ylabel("Flux / Precipitation")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()


#%%




import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import os

# =====================================================
# 1. DEFINE MODELS AND SCENARIOS
# =====================================================

models = ["GFDL-ESM4", "IPSL-CM6A-LR", "MPI-ESM1-2-HR",
          "MRI-ESM2-0", "UKESM1-0-LL"]

scenarios = {
    "ssp126": "2.6",
    "ssp370": "7.0",
    "ssp585": "8.5"
}

base_input = r"C:\DATA\0. Data Projection & Attribution\ISIMIP Data 2\ISIMIP3b_Input Data_Climate Forcing_Atmo Forcing_Precipitation"
base_albm = r"C:\DATA\0. Data Projection & Attribution\ISIMIP Data 2\ISIMIP3b_Output Data_Lakes Global_ALBM_Latentheat"
base_gotm = r"C:\DATA\0. Data Projection & Attribution\ISIMIP Data 2\ISIMIP3b_Output Data_Lakes Global_GOTM_Latentheat"

# =====================================================
# 2. FUNCTION TO LOAD & AREA AVERAGE
# =====================================================

def load_annual_mean(file_path, varname=None):

    ds = xr.open_dataset(file_path)

    # If variable name not provided, take first data variable
    if varname is None:
        varname = list(ds.data_vars.keys())[0]

    da = ds[varname]

    # Area mean (Lake Victoria domain already subset)
    if "lat" in da.dims and "lon" in da.dims:
        da = da.mean(dim=["lat", "lon"])

    # Convert to annual mean
    da_annual = da.resample(time="1Y").mean()

    return da_annual


# =====================================================
# 3. COLLECT DATA
# =====================================================

results = {}

for scenario, folder_code in scenarios.items():

    results[scenario] = {"pr": [], "albm": [], "gotm": []}

    for model in models:

        try:
            # ---- INPUT PR ----
            input_path = os.path.join(
                base_input, model,
                f"{folder_code}_*",
            )

            # Manually adjust filename pattern if needed
            input_file = [f for f in
                          xr.backends.common.glob(os.path.join(base_input,
                          model, f"{folder_code}*", "*merged_2015_2100.nc"))][0]

            pr = load_annual_mean(input_file)
            results[scenario]["pr"].append(pr)

        except:
            print(f"Missing PR for {model} {scenario}")

        try:
            # ---- ALBM ----
            albm_file = [f for f in
                         xr.backends.common.glob(os.path.join(base_albm,
                         model, f"{folder_code}*", "*merged_2015_2100.nc"))][0]

            albm = load_annual_mean(albm_file)
            results[scenario]["albm"].append(albm)

        except:
            print(f"Missing ALBM for {model} {scenario}")

        # GOTM short path names → user may need manual mapping
        # If paths differ strongly, adjust this section manually


# =====================================================
# 4. PLOTTING
# =====================================================

fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

variables = ["pr", "albm", "gotm"]
titles = ["Precipitation (Input)",
          "ALBM Latent Heat",
          "GOTM Latent Heat"]

for i, var in enumerate(variables):

    ax = axes[i]

    for scenario in scenarios:

        members = results[scenario][var]

        if len(members) == 0:
            continue

        # Align time
        aligned = xr.align(*members, join="inner")
        stack = xr.concat(aligned, dim="model")

        # Plot individual models
        for m in range(stack.sizes["model"]):
            ax.plot(stack.time,
                    stack.isel(model=m),
                    alpha=0.25)

        # Ensemble mean
        ens_mean = stack.mean(dim="model")
        ax.plot(ens_mean.time,
                ens_mean,
                linewidth=3,
                label=f"{scenario} Ensemble")

    ax.set_title(titles[i])
    ax.grid(True)
    ax.legend()

plt.xlabel("Year")
plt.suptitle("Lake Victoria ISIMIP3b Projections (2015–2100)")
plt.tight_layout()
plt.show()


#%%


# -*- coding: utf-8 -*-
"""
ISIMIP Multi-Model Analysis for Lake Victoria
Analyzes precipitation (input) and latent heat (output) projections
across 5 GCMs and 3 SSP scenarios

Author: V. Ogembo
Created: December 2025
"""

import os
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

# ===============================================================
# CONFIGURATION
# ===============================================================

BASE_DIR = r"C:\DATA\0. Data Projection & Attribution\ISIMIP Data 2"
OUTPUT_DIR = r"C:\GLIWaB\outputs\ISIMIP\MultiModel_Analysis"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "figures"), exist_ok=True)

# Models to analyze
MODELS = ["GFDL-ESM4", "IPSL-CM6A-LR", "MPI-ESM1-2-HR", "MRI-ESM2-0", "UKESM1-0-LL"]

# Scenarios
SCENARIOS = ["ssp126", "ssp370", "ssp585"]

# Official IPCC colors
COLORS = {
    "ssp126": "#1e9583",  # Teal
    "ssp370": "#f69320",  # Orange
    "ssp585": "#980002"   # Dark Red
}

# Model colors (for multi-model plots)
MODEL_COLORS = {
    "GFDL-ESM4": "#1f77b4",
    "IPSL-CM6A-LR": "#ff7f0e",
    "MPI-ESM1-2-HR": "#2ca02c",
    "MRI-ESM2-0": "#d62728",
    "UKESM1-0-LL": "#9467bd"
}

# Plotting style
sns.set_style("whitegrid")
plt.rcParams.update({
    'figure.dpi': 150,
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 13,
    'legend.fontsize': 9
})

# ===============================================================
# FILE PATH CONSTRUCTION
# ===============================================================

def construct_precipitation_path(model, scenario):
    """Build precipitation file path"""
    scenario_folders = {
        "ssp126": "2.6",
        "ssp370": "7.0",
        "ssp585": "8.5"
    }
    
    folder_map = {
        "GFDL-ESM4": {
            "ssp126": "bc7035bc9cad19f9563f30f48ad0068f86edb1c1",
            "ssp370": "dc8de8af0043f26bb6fbed378926d2086f7ab1e9",
            "ssp585": "8196eb8252b82fe130e9e8adea50ffe427816dfa"
        }
        # Add others if you have the exact folder IDs
    }
    
    model_lower = model.lower().replace("-", "-")
    scenario_num = scenario_folders[scenario]
    
    base_path = os.path.join(
        BASE_DIR,
        "ISIMIP3b_Input Data_Climate Forcing_Atmo Forcing_Precipitation",
        model
    )
    
    # Try to find the scenario folder
    if os.path.exists(base_path):
        for folder in os.listdir(base_path):
            if folder.startswith(scenario_num):
                nc_files = [f for f in os.listdir(os.path.join(base_path, folder)) if f.endswith('.nc')]
                if nc_files:
                    return os.path.join(base_path, folder, nc_files[0])
    
    return None


def construct_albm_path(model, scenario):
    """Build ALBM latent heat file path"""
    scenario_folders = {
        "ssp126": "2.6",
        "ssp370": "7.0",
        "ssp585": "8.5"
    }
    
    scenario_num = scenario_folders[scenario]
    
    base_path = os.path.join(
        BASE_DIR,
        "ISIMIP3b_Output Data_Lakes Global_ALBM_Latentheat",
        model
    )
    
    if os.path.exists(base_path):
        for folder in os.listdir(base_path):
            if folder.startswith(scenario_num):
                nc_files = [f for f in os.listdir(os.path.join(base_path, folder)) if f.endswith('.nc')]
                if nc_files:
                    return os.path.join(base_path, folder, nc_files[0])
    
    return None


# ===============================================================
# DATA LOADING
# ===============================================================

def load_climate_data(filepath, variable, conversion_factor):
    """
    Load and process climate data from NetCDF
    
    Args:
        filepath: Path to NetCDF file
        variable: Variable name ('pr' or 'hfls')
        conversion_factor: Multiply factor for unit conversion
    
    Returns:
        pandas Series with daily basin-mean values
    """
    if not filepath or not os.path.exists(filepath):
        return None
    
    try:
        ds = xr.open_dataset(filepath)
        
        # Auto-detect variable name
        if variable not in ds.data_vars:
            variable = list(ds.data_vars)[0]
        
        # Spatial mean
        data = ds[variable].mean(dim=['lat', 'lon']) * conversion_factor
        
        # Convert to Series
        series = data.to_pandas()
        series.index = pd.to_datetime(series.index)
        
        ds.close()
        return series
        
    except Exception as e:
        print(f"Error loading {os.path.basename(filepath)}: {e}")
        return None


def load_all_data(models, scenarios, variable_type='precipitation'):
    """
    Load data for all models and scenarios
    
    Args:
        models: List of model names
        scenarios: List of scenario names
        variable_type: 'precipitation' or 'albm' or 'gotm'
    
    Returns:
        Nested dictionary: {scenario: {model: Series}}
    """
    data = {sc: {} for sc in scenarios}
    
    for scenario in scenarios:
        print(f"\nLoading {variable_type} for {scenario.upper()}:")
        
        for model in models:
            # Get file path
            if variable_type == 'precipitation':
                filepath = construct_precipitation_path(model, scenario)
                var = 'pr'
                factor = 86400  # kg/m²/s to mm/day
            elif variable_type == 'albm':
                filepath = construct_albm_path(model, scenario)
                var = 'hfls'
                factor = 86400 / 2.45e6  # W/m² to mm/day
            
            # Load data
            series = load_climate_data(filepath, var, factor)
            
            if series is not None:
                data[scenario][model] = series
                print(f"  ✓ {model}: {len(series)} days")
            else:
                print(f"  ✗ {model}: Not found")
    
    return data


# ===============================================================
# PLOTTING FUNCTIONS
# ===============================================================

def plot_multi_model_ensemble(data_dict, variable_name, ylabel, savepath):
    """
    Plot multi-model ensemble with individual models and mean
    """
    fig, axes = plt.subplots(3, 1, figsize=(16, 12), sharex=True)
    
    for idx, scenario in enumerate(SCENARIOS):
        ax = axes[idx]
        
        if scenario not in data_dict or not data_dict[scenario]:
            continue
        
        model_series = []
        
        # Plot individual models
        for model, series in data_dict[scenario].items():
            # Resample to annual
            annual = series.resample('YE').mean()
            ax.plot(annual.index, annual, 
                   color=MODEL_COLORS.get(model, 'gray'),
                   linewidth=1.5, alpha=0.6,
                   label=model)
            model_series.append(annual)
        
        # Plot ensemble mean
        if model_series:
            ensemble_df = pd.concat(model_series, axis=1)
            ensemble_mean = ensemble_df.mean(axis=1)
            ensemble_std = ensemble_df.std(axis=1)
            
            ax.plot(ensemble_mean.index, ensemble_mean,
                   color=COLORS[scenario], linewidth=3,
                   label='Ensemble Mean', zorder=10)
            
            # Uncertainty band
            ax.fill_between(ensemble_mean.index,
                           ensemble_mean - ensemble_std,
                           ensemble_mean + ensemble_std,
                           color=COLORS[scenario], alpha=0.2)
        
        # Formatting
        ax.set_ylabel(ylabel, fontsize=11, fontweight='bold')
        ax.set_title(f"({chr(97+idx)}) {scenario.upper()}", 
                    fontsize=12, fontweight='bold', loc='left')
        ax.legend(fontsize=8, ncol=3, loc='best')
        ax.grid(True, alpha=0.3)
    
    axes[-1].set_xlabel('Year', fontsize=12, fontweight='bold')
    
    fig.suptitle(f'Lake Victoria Basin: {variable_name} Multi-Model Projections',
                fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(savepath, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"✅ Saved: {savepath}")


def plot_scenario_comparison(data_dict, variable_name, ylabel, savepath):
    """
    Compare scenarios with ensemble means only
    """
    fig, ax = plt.subplots(figsize=(14, 7))
    
    for scenario in SCENARIOS:
        if scenario not in data_dict or not data_dict[scenario]:
            continue
        
        # Calculate ensemble mean
        model_series = []
        for series in data_dict[scenario].values():
            annual = series.resample('YE').mean()
            model_series.append(annual)
        
        if model_series:
            ensemble_df = pd.concat(model_series, axis=1)
            mean = ensemble_df.mean(axis=1)
            std = ensemble_df.std(axis=1)
            
            # Plot mean
            ax.plot(mean.index, mean,
                   color=COLORS[scenario], linewidth=3,
                   label=f'{scenario.upper()} ({len(model_series)} models)')
            
            # Uncertainty
            ax.fill_between(mean.index, mean - std, mean + std,
                           color=COLORS[scenario], alpha=0.25)
    
    ax.set_xlabel('Year', fontsize=13, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=13, fontweight='bold')
    ax.set_title(f'Lake Victoria Basin: {variable_name} Ensemble Comparison',
                fontsize=15, fontweight='bold')
    ax.legend(fontsize=11, loc='best', frameon=True, shadow=True)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(savepath, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"✅ Saved: {savepath}")


def plot_model_comparison_grid(data_dict, variable_name, ylabel, savepath):
    """
    Grid plot showing each model across scenarios
    """
    # Find all models that have data
    all_models = set()
    for scenario_data in data_dict.values():
        all_models.update(scenario_data.keys())
    all_models = sorted(all_models)
    
    n_models = len(all_models)
    fig, axes = plt.subplots(n_models, 1, figsize=(14, 3*n_models), sharex=True)
    
    if n_models == 1:
        axes = [axes]
    
    for idx, model in enumerate(all_models):
        ax = axes[idx]
        
        for scenario in SCENARIOS:
            if scenario in data_dict and model in data_dict[scenario]:
                series = data_dict[scenario][model]
                annual = series.resample('YE').mean()
                
                ax.plot(annual.index, annual,
                       color=COLORS[scenario], linewidth=2,
                       label=scenario.upper())
        
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(f'{model}', fontsize=11, fontweight='bold', loc='left')
        ax.legend(fontsize=9, loc='best')
        ax.grid(True, alpha=0.3)
    
    axes[-1].set_xlabel('Year', fontsize=12, fontweight='bold')
    
    fig.suptitle(f'Lake Victoria Basin: {variable_name} by Model',
                fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(savepath, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"✅ Saved: {savepath}")


def plot_climatology_comparison(data_dict, variable_name, ylabel, savepath):
    """
    Monthly climatology (2050-2100) comparison
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 5), sharey=True)
    
    for idx, scenario in enumerate(SCENARIOS):
        ax = axes[idx]
        
        if scenario not in data_dict or not data_dict[scenario]:
            continue
        
        for model, series in data_dict[scenario].items():
            # Filter to 2050-2100
            future = series[series.index.year >= 2050]
            
            # Monthly climatology
            monthly = future.groupby(future.index.month).mean()
            
            ax.plot(range(1, 13), monthly.values,
                   marker='o', linewidth=2, label=model,
                   color=MODEL_COLORS.get(model, 'gray'))
        
        # Formatting
        ax.set_xlabel('Month', fontsize=11, fontweight='bold')
        if idx == 0:
            ax.set_ylabel(ylabel, fontsize=11, fontweight='bold')
        ax.set_title(f'{scenario.upper()}', fontsize=12, fontweight='bold')
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(['J','F','M','A','M','J','J','A','S','O','N','D'])
        ax.legend(fontsize=8, loc='best')
        ax.grid(True, alpha=0.3)
    
    fig.suptitle(f'Lake Victoria Basin: {variable_name} Climatology (2015-2100)',
                fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(savepath, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"✅ Saved: {savepath}")


# ===============================================================
# STATISTICS
# ===============================================================

def print_statistics(data_dict, variable_name):
    """Print comprehensive statistics"""
    print("\n" + "="*80)
    print(f"{variable_name.upper()} STATISTICS")
    print("="*80)
    
    for scenario in SCENARIOS:
        if scenario not in data_dict or not data_dict[scenario]:
            continue
        
        print(f"\n{scenario.upper()}:")
        
        for model, series in data_dict[scenario].items():
            annual = series.resample('YE').mean()
            
            # Period statistics
            early = annual[annual.index.year <= 2050].mean()
            late = annual[annual.index.year > 2050].mean()
            change = late - early
            
            print(f"  {model}:")
            print(f"    2015-2050: {early:.2f}")
            print(f"    2051-2100: {late:.2f}")
            print(f"    Change: {change:+.2f} ({change/early*100:+.1f}%)")
    
    print("\n" + "="*80)


# ===============================================================
# MAIN EXECUTION
# ===============================================================

def main():
    """Main analysis workflow"""
    print("="*80)
    print("ISIMIP MULTI-MODEL CLIMATE ANALYSIS")
    print("="*80)
    
    fig_dir = os.path.join(OUTPUT_DIR, "figures")
    
    # ==================== PRECIPITATION ====================
    print("\n" + "="*80)
    print("ANALYZING PRECIPITATION")
    print("="*80)
    
    pr_data = load_all_data(MODELS, SCENARIOS, 'precipitation')
    
    if any(pr_data.values()):
        plot_multi_model_ensemble(
            pr_data, "Precipitation", "Precipitation (mm/day)",
            os.path.join(fig_dir, "01_Precipitation_MultiModel.png")
        )
        
        plot_scenario_comparison(
            pr_data, "Precipitation", "Precipitation (mm/day)",
            os.path.join(fig_dir, "02_Precipitation_Scenarios.png")
        )
        
        plot_model_comparison_grid(
            pr_data, "Precipitation", "Precipitation (mm/day)",
            os.path.join(fig_dir, "03_Precipitation_ByModel.png")
        )
        
        plot_climatology_comparison(
            pr_data, "Precipitation", "Precipitation (mm/day)",
            os.path.join(fig_dir, "04_Precipitation_Climatology.png")
        )
        
        print_statistics(pr_data, "Precipitation")
    
    # ==================== LATENT HEAT (ALBM) ====================
    print("\n" + "="*80)
    print("ANALYZING LATENT HEAT (ALBM)")
    print("="*80)
    
    lh_data = load_all_data(MODELS, SCENARIOS, 'albm')
    
    if any(lh_data.values()):
        plot_multi_model_ensemble(
            lh_data, "Evaporation (Latent Heat)", "Evaporation (mm/day)",
            os.path.join(fig_dir, "05_Evaporation_MultiModel.png")
        )
        
        plot_scenario_comparison(
            lh_data, "Evaporation (Latent Heat)", "Evaporation (mm/day)",
            os.path.join(fig_dir, "06_Evaporation_Scenarios.png")
        )
        
        plot_model_comparison_grid(
            lh_data, "Evaporation (Latent Heat)", "Evaporation (mm/day)",
            os.path.join(fig_dir, "07_Evaporation_ByModel.png")
        )
        
        plot_climatology_comparison(
            lh_data, "Evaporation (Latent Heat)", "Evaporation (mm/day)",
            os.path.join(fig_dir, "08_Evaporation_Climatology.png")
        )
        
        print_statistics(lh_data, "Evaporation")
    
    print("\n" + "="*80)
    print(f"✅ ANALYSIS COMPLETE - Figures saved in: {fig_dir}")
    print("="*80)


if __name__ == "__main__":
    main()
    


#%%

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import xarray as xr
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# PUBLICATION STYLE SETTINGS
# ============================================================
plt.rcParams.update({
    'font.family':        'DejaVu Sans',
    'font.size':          14,
    'axes.titlesize':     16,
    'axes.labelsize':     15,
    'xtick.labelsize':    13,
    'ytick.labelsize':    13,
    'legend.fontsize':    13,
    'legend.title_fontsize': 13,
    'axes.linewidth':     1.4,
    'xtick.major.width':  1.2,
    'ytick.major.width':  1.2,
    'xtick.minor.width':  0.8,
    'ytick.minor.width':  0.8,
    'xtick.major.size':   6,
    'ytick.major.size':   6,
    'xtick.minor.size':   3,
    'ytick.minor.size':   3,
    'figure.dpi':         150,
    'savefig.dpi':        300,
    'savefig.bbox':       'tight',
    'savefig.facecolor':  'white',
    'axes.spines.top':    False,
    'axes.spines.right':  False,
})

# ============================================================
# CONFIGURATION
# ============================================================
LAT_MIN, LAT_MAX = -3.0,  0.5
LON_MIN, LON_MAX = 31.5, 35.0

MODELS      = ['GFDL-ESM4', 'IPSL-CM6A-LR', 'MPI-ESM1-2-HR', 'MRI-ESM2-0', 'UKESM1-0-LL']
MODEL_DIRS  = ['GFDL-ESM4', 'IPSL',          'MPI',            'MRI',         'UKESM1']

SCENARIOS        = ['ssp126', 'ssp370', 'ssp585']
SCENARIO_LABELS  = {'ssp126': 'SSP1-2.6', 'ssp370': 'SSP3-7.0', 'ssp585': 'SSP5-8.5'}
SCENARIO_COLORS  = {'ssp126': '#1e9583',  'ssp370': '#f69320',   'ssp585': '#980002'}
SCENARIO_FOLDERS = {'ssp126': '2.6',      'ssp370': '7.0',       'ssp585': '8.5'}

BASE = r"C:\DATA\0. Data Projection & Attribution\ISIMIP Data 2"

C_PRECIP  = '#2166ac'
C_EVAP    = '#d6604d'
C_NET     = '#4d4d4d'
C_STORAGE = '#6a3d9a'
C_SURPLUS = '#1a9641'
C_DEFICIT = '#b2182b'
C_ROLL    = '#111111'

EVAP_MODELS = {'ALBM': 'albm', 'GOTM': 'gotm'}

# ============================================================
# PATH FINDERS
# ============================================================

def find_nc_in_scenario_subfolder(base_folder, scenario):
    base_p = Path(base_folder)
    if not base_p.exists():
        return None
    prefix = SCENARIO_FOLDERS[scenario]
    for sub in sorted(base_p.iterdir()):
        if sub.is_dir() and sub.name.startswith(prefix):
            nc_files = sorted(sub.glob("*.nc"))
            if nc_files:
                return str(nc_files[0])
    return None

def get_precip_path(model_dir, scenario):
    folder = os.path.join(BASE,
        "ISIMIP3b_Input Data_Climate Forcing_Atmo Forcing_Precipitation",
        model_dir)
    return find_nc_in_scenario_subfolder(folder, scenario)

def get_evap_path(output_type, model_dir, scenario):
    folder = os.path.join(BASE,
        f"ISIMIP3b_Output Data_Lakes Global_{output_type}_Latentheat",
        model_dir)
    return find_nc_in_scenario_subfolder(folder, scenario)

# ============================================================
# DATA EXTRACTION
# ============================================================

def extract_lake_victoria(filepath, var_hint=None):
    if filepath is None or not os.path.exists(filepath):
        return None
    try:
        ds  = xr.open_dataset(filepath, engine='netcdf4')
        dvs = [v for v in ds.data_vars if ds[v].ndim >= 2]
        if not dvs:
            return None

        var = dvs[0]
        if var_hint:
            for v in dvs:
                if var_hint.lower() in v.lower():
                    var = v; break

        da    = ds[var]
        units = da.attrs.get('units', 'unknown')

        rename = {}
        for d in da.dims:
            if d.lower() in ('latitude','lat'):  rename[d] = 'lat'
            if d.lower() in ('longitude','lon'): rename[d] = 'lon'
        if rename: da = da.rename(rename)

        if 'lat' in da.dims and 'lon' in da.dims:
            lat_asc = float(da['lat'][0]) < float(da['lat'][-1])
            lat_slc = slice(LAT_MIN,LAT_MAX) if lat_asc else slice(LAT_MAX,LAT_MIN)
            da = da.sel(lat=lat_slc, lon=slice(LON_MIN, LON_MAX))

        sp = [d for d in ['lat','lon'] if d in da.dims]
        da = da.mean(dim=sp)

        u = units.replace(' ','').lower()
        if 'kgm-2s-1' in u or ('kg' in u and 's-1' in u):
            da = da * 86400; units = 'mm/day'
        elif u in ('wm-2','w/m2','wm**-2'):
            da = da / 2.45e6 * 86400; units = 'mm/day'

        da_mon = da.resample(time='1MS').mean()
        t_mon  = (da_mon['time'].dt.year.values
                  + (da_mon['time'].dt.month.values - 1) / 12.0)
        v_mon  = da_mon.values.astype(float)

        da_ann = da.resample(time='1Y').mean()
        years  = da_ann['time'].dt.year.values
        v_ann  = da_ann.values.astype(float)

        ds.close()
        return {'annual': (years, v_ann),
                'monthly': (t_mon, v_mon),
                'units': units}
    except Exception as e:
        print(f"  ✗ {os.path.basename(filepath or '')}: {e}")
        return None

# ============================================================
# ENSEMBLE HELPERS
# ============================================================

def ensemble_stats(result_list, key='annual'):
    valid = [r[key] for r in result_list if r is not None]
    if not valid: return None
    common_t = sorted(set.intersection(*[set(np.round(t,4)) for t,_ in valid]))
    if not common_t: return None
    common_t = np.array(common_t)
    arr = []
    for t,v in valid:
        mask = np.isin(np.round(t,4), common_t)
        arr.append(v[mask])
    arr = np.array(arr)
    return common_t, arr.mean(0), arr.min(0), arr.max(0), arr

def net_balance_stats(st_pr, st_ev):
    if st_pr is None or st_ev is None: return None
    t_pr, m_pr, mn_pr, mx_pr, a_pr = st_pr
    t_ev, m_ev, mn_ev, mx_ev, a_ev = st_ev
    common = np.intersect1d(np.round(t_pr,4), np.round(t_ev,4))
    if common.size == 0: return None
    idx_pr = np.isin(np.round(t_pr,4), common)
    idx_ev = np.isin(np.round(t_ev,4), common)
    if a_pr.shape[0] == a_ev.shape[0]:
        net_members = a_pr[:,idx_pr] - a_ev[:,idx_ev]
    else:
        net_members = (m_pr[idx_pr] - m_ev[idx_ev])[np.newaxis,:]
    net_mean = m_pr[idx_pr] - m_ev[idx_ev]
    return common, net_mean, net_members.min(0), net_members.max(0), net_members

def cumulative_storage(net_stats):
    if net_stats is None: return None
    t, mean, mn, mx, members = net_stats
    return (t,
            np.cumsum(mean),
            np.cumsum(members, axis=1).min(0),
            np.cumsum(members, axis=1).max(0))

# ============================================================
# LOAD DATA
# ============================================================

print("=" * 65)
print("Loading Lake Victoria ISIMIP3b data …")
print("=" * 65)

store = {
    'precip': {sc: [] for sc in SCENARIOS},
    'albm':   {sc: [] for sc in SCENARIOS},
    'gotm':   {sc: [] for sc in SCENARIOS},
}

for model, mdir in zip(MODELS, MODEL_DIRS):
    print(f"\n▶  {model}")
    for sc in SCENARIOS:
        lbl = SCENARIO_LABELS[sc]
        fp = get_precip_path(mdir, sc)
        r  = extract_lake_victoria(fp, var_hint='pr')
        store['precip'][sc].append(r)
        print(f"   Precip  {lbl}: {'✓' if r else '✗'}")

        fp = get_evap_path('ALBM', mdir, sc)
        r  = extract_lake_victoria(fp)
        store['albm'][sc].append(r)
        print(f"   ALBM    {lbl}: {'✓' if r else '✗'}")

        fp = get_evap_path('GOTM', mdir, sc)
        r  = extract_lake_victoria(fp)
        store['gotm'][sc].append(r)
        print(f"   GOTM    {lbl}: {'✓' if r else '✗'}")

# Pre-compute stats
all_stats = {}
for em_label, em_key in EVAP_MODELS.items():
    all_stats[em_label] = {}
    for sc in SCENARIOS:
        st_pr_ann  = ensemble_stats(store['precip'][sc], 'annual')
        st_ev_ann  = ensemble_stats(store[em_key  ][sc], 'annual')
        st_pr_mon  = ensemble_stats(store['precip'][sc], 'monthly')
        st_ev_mon  = ensemble_stats(store[em_key  ][sc], 'monthly')
        net_ann    = net_balance_stats(st_pr_ann, st_ev_ann)
        net_mon    = net_balance_stats(st_pr_mon, st_ev_mon)
        cum_ann    = cumulative_storage(net_ann)
        all_stats[em_label][sc] = {
            'pr_ann':  st_pr_ann, 'ev_ann':  st_ev_ann,
            'pr_mon':  st_pr_mon, 'ev_mon':  st_ev_mon,
            'net_ann': net_ann,   'net_mon':  net_mon,
            'cum_ann': cum_ann,
        }

# ============================================================
# SHARED HELPERS
# ============================================================

def shade(ax, t, mn, mx, color, alpha=0.18):
    ax.fill_between(t, mn, mx, color=color, alpha=alpha, linewidth=0)

def style_ax(ax, xlabel='Year', ylabel='', xlim=(2015,2100)):
    ax.set_xlim(xlim)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(10))
    ax.xaxis.set_minor_locator(mticker.MultipleLocator(5))
    ax.set_xlabel(xlabel, fontsize=15, labelpad=8)
    ax.set_ylabel(ylabel, fontsize=15, labelpad=8)
    ax.tick_params(axis='both', which='major', labelsize=13, length=6, width=1.2)
    ax.tick_params(axis='both', which='minor', labelsize=10, length=3, width=0.8)
    ax.grid(True, which='major', alpha=0.3, linestyle='--', linewidth=0.7)
    ax.grid(True, which='minor', alpha=0.12, linestyle=':', linewidth=0.4)
    ax.axhline(0, color='#555555', linewidth=1.0, alpha=0.6, zorder=2)
    ax.set_facecolor('#fafafa')

def scenario_tag(ax, sc_label, sc_color):
    """Bold scenario badge top-left."""
    ax.text(0.02, 0.96, sc_label,
            transform=ax.transAxes,
            fontsize=15, fontweight='bold', color='white',
            va='top', ha='left', zorder=10,
            bbox=dict(boxstyle='round,pad=0.35', facecolor=sc_color,
                      edgecolor='none', alpha=0.92))

def watermark(ax, text='Lake Victoria  |  ISIMIP3b', alpha=0.10):
    ax.text(0.98, 0.02, text, transform=ax.transAxes,
            fontsize=10, color='gray', alpha=alpha,
            ha='right', va='bottom', style='italic')

def save_fig(fig, fname):
    fig.savefig(fname, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"  ✓  Saved: {fname}")
    plt.close(fig)

# ============================================================
# FIGURE FACTORY
# ============================================================

for em_label, em_key in EVAP_MODELS.items():
    EM = em_label      # short alias
    S  = all_stats[EM]

    # ----------------------------------------------------------
    # FIG 1  –  Annual P & E  (3 panels, one per scenario)
    # ----------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(20, 6), sharey=False)
    fig.suptitle(
        f'Lake Victoria – Annual Precipitation (P) & Evaporation (E)\n'
        f'ISIMIP3b Projections 2015–2100  |  Evaporation model: {EM}  |  5-model ensemble',
        fontsize=16, fontweight='bold', y=1.02
    )

    for col, sc in enumerate(SCENARIOS):
        ax = axes[col]
        ax2 = ax.twinx()
        s = S[sc]

        if s['pr_ann']:
            t,m,mn,mx,_ = s['pr_ann']
            shade(ax, t, mn, mx, C_PRECIP, 0.18)
            ax.plot(t, m, color=C_PRECIP, lw=2.2, label='Precipitation (P)', zorder=4)
            ax.axhline(np.nanmean(m), color=C_PRECIP, lw=1.0, ls=':', alpha=0.6)

        if s['ev_ann']:
            t,m,mn,mx,_ = s['ev_ann']
            shade(ax, t, mn, mx, C_EVAP, 0.18)
            ax.plot(t, m, color=C_EVAP, lw=2.2, ls='--', label=f'Evaporation {EM} (E)', zorder=4)
            ax.axhline(np.nanmean(m), color=C_EVAP, lw=1.0, ls=':', alpha=0.6)

        if s['net_ann']:
            t,m,mn,mx,_ = s['net_ann']
            shade(ax2, t, mn, mx, C_NET, 0.12)
            ax2.plot(t, m, color=C_NET, lw=1.6, ls=':', label='P − E', zorder=3)
            ax2.set_ylabel('P − E  (mm day⁻¹)', fontsize=14,
                           color=C_NET, labelpad=8)
            ax2.tick_params(axis='y', labelcolor=C_NET, labelsize=13)
            ax2.spines['right'].set_visible(True)
            ax2.spines['right'].set_color(C_NET)

        style_ax(ax, ylabel='P  &  E  (mm day⁻¹)' if col==0 else '')
        scenario_tag(ax, SCENARIO_LABELS[sc], SCENARIO_COLORS[sc])
        watermark(ax)
        ax.spines['right'].set_visible(False)

        if col == 0:
            h1,l1 = ax.get_legend_handles_labels()
            h2,l2 = ax2.get_legend_handles_labels()
            ax.legend(h1+h2, l1+l2, fontsize=12, loc='upper left',
                      framealpha=0.9, edgecolor='#cccccc')

    plt.tight_layout()
    save_fig(fig, f'Fig1_{EM}_Annual_P_and_E.png')

    # ----------------------------------------------------------
    # FIG 2  –  Monthly P & E  (3 panels)
    # ----------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(20, 6), sharey=True)
    fig.suptitle(
        f'Lake Victoria – Monthly Precipitation (P) & Evaporation (E)\n'
        f'ISIMIP3b Projections 2015–2100  |  Evaporation model: {EM}  |  5-model ensemble',
        fontsize=16, fontweight='bold', y=1.02
    )

    for col, sc in enumerate(SCENARIOS):
        ax = axes[col]
        s = S[sc]

        if s['pr_mon']:
            t,m,mn,mx,_ = s['pr_mon']
            shade(ax, t, mn, mx, C_PRECIP, 0.15)
            ax.plot(t, m, color=C_PRECIP, lw=1.5, label='Precipitation (P)', zorder=4)

        if s['ev_mon']:
            t,m,mn,mx,_ = s['ev_mon']
            shade(ax, t, mn, mx, C_EVAP, 0.15)
            ax.plot(t, m, color=C_EVAP, lw=1.5, ls='--', label=f'Evaporation {EM} (E)', zorder=4)

        style_ax(ax, ylabel='P  &  E  (mm day⁻¹)' if col==0 else '')
        scenario_tag(ax, SCENARIO_LABELS[sc], SCENARIO_COLORS[sc])
        watermark(ax)

        if col == 0:
            ax.legend(fontsize=12, loc='upper left', framealpha=0.9, edgecolor='#cccccc')

    plt.tight_layout()
    save_fig(fig, f'Fig2_{EM}_Monthly_P_and_E.png')

    # ----------------------------------------------------------
    # FIG 3  –  Annual P−E bar chart  (3 panels)
    # ----------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(20, 6), sharey=False)
    fig.suptitle(
        f'Lake Victoria – Annual Water Balance  (P − E)\n'
        f'ISIMIP3b Projections 2015–2100  |  Evaporation model: {EM}  |  5-model ensemble',
        fontsize=16, fontweight='bold', y=1.02
    )

    for col, sc in enumerate(SCENARIOS):
        ax = axes[col]
        s = S[sc]

        if s['net_ann']:
            t,m,mn,mx,_ = s['net_ann']
            shade(ax, t, mn, mx, '#888888', 0.15)

            pos = np.where(m >= 0, m, 0)
            neg = np.where(m <  0, m, 0)
            ax.bar(t, pos, width=0.75, color=C_SURPLUS, alpha=0.80,
                   label='Surplus  (P > E)', zorder=3)
            ax.bar(t, neg, width=0.75, color=C_DEFICIT, alpha=0.80,
                   label='Deficit  (P < E)', zorder=3)

            if len(m) >= 10:
                roll   = np.convolve(m, np.ones(10)/10, mode='valid')
                t_roll = t[9:]
                ax.plot(t_roll, roll, color=C_ROLL, lw=2.2,
                        label='10-yr rolling mean', zorder=5)

            ylims = ax.get_ylim()
            ax.fill_between([2015,2100],[0,0],[max(ylims[1],0.1)]*2,
                            color=C_SURPLUS, alpha=0.05, zorder=0)
            ax.fill_between([2015,2100],[min(ylims[0],-0.1)]*2,[0,0],
                            color=C_DEFICIT, alpha=0.05, zorder=0)
            ax.text(0.02, 0.97, 'SURPLUS', transform=ax.transAxes,
                    fontsize=12, color=C_SURPLUS, fontweight='bold',
                    va='top', alpha=0.75)
            ax.text(0.02, 0.03, 'DEFICIT', transform=ax.transAxes,
                    fontsize=12, color=C_DEFICIT, fontweight='bold',
                    va='bottom', alpha=0.75)

        style_ax(ax, ylabel='P − E  (mm day⁻¹)' if col==0 else '')
        scenario_tag(ax, SCENARIO_LABELS[sc], SCENARIO_COLORS[sc])
        watermark(ax)

        if col == 0:
            ax.legend(fontsize=12, loc='upper right', framealpha=0.9, edgecolor='#cccccc')

    plt.tight_layout()
    save_fig(fig, f'Fig3_{EM}_Annual_WaterBalance_Bars.png')

    # ----------------------------------------------------------
    # FIG 4  –  Cumulative storage ΔS  (3 panels)
    # ----------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(20, 6), sharey=False)
    fig.suptitle(
        f'Lake Victoria – Cumulative Water Storage  ΔS = Σ(P − E)\n'
        f'ISIMIP3b Projections 2015–2100  |  Evaporation model: {EM}  |  5-model ensemble',
        fontsize=16, fontweight='bold', y=1.02
    )

    for col, sc in enumerate(SCENARIOS):
        ax = axes[col]
        s = S[sc]

        if s['cum_ann']:
            t, cum_mean, cum_min, cum_max = s['cum_ann']
            shade(ax, t, cum_min, cum_max, C_STORAGE, 0.20)
            ax.plot(t, cum_mean, color=C_STORAGE, lw=2.5,
                    label='Cumulative ΔS = Σ(P − E)', zorder=4)

            ax.fill_between(t, 0, cum_mean,
                            where=cum_mean >= 0,
                            color=C_SURPLUS, alpha=0.22, zorder=1,
                            label='Storage gain')
            ax.fill_between(t, 0, cum_mean,
                            where=cum_mean <  0,
                            color=C_DEFICIT, alpha=0.22, zorder=1,
                            label='Storage loss')

            final = cum_mean[-1]
            ax.annotate(
                f'End ΔS: {final:+.0f} mm',
                xy=(t[-1], final),
                xytext=(-55, 18 if final > 0 else -28),
                textcoords='offset points',
                fontsize=12, color=C_STORAGE, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color=C_STORAGE,
                                lw=1.4, connectionstyle='arc3,rad=0.2')
            )

        style_ax(ax,
                 ylabel='Cumulative  ΔS  (mm)' if col==0 else '')
        scenario_tag(ax, SCENARIO_LABELS[sc], SCENARIO_COLORS[sc])
        watermark(ax)

        if col == 0:
            ax.legend(fontsize=12, loc='upper left', framealpha=0.9, edgecolor='#cccccc')

    plt.tight_layout()
    save_fig(fig, f'Fig4_{EM}_Cumulative_Storage.png')

    # ----------------------------------------------------------
    # FIG 5  –  All-scenario overlay  (single wide panel)
    # ----------------------------------------------------------
    fig, ax = plt.subplots(figsize=(16, 7))
    fig.suptitle(
        f'Lake Victoria – Annual Water Balance  (P − E)  |  All Scenarios\n'
        f'ISIMIP3b Projections 2015–2100  |  Evaporation model: {EM}  |  5-model ensemble',
        fontsize=16, fontweight='bold', y=1.02
    )

    for sc in SCENARIOS:
        s   = S[sc]
        col = SCENARIO_COLORS[sc]
        lbl = SCENARIO_LABELS[sc]

        if s['net_ann']:
            t,m,mn,mx,_ = s['net_ann']
            shade(ax, t, mn, mx, col, 0.15)
            ax.plot(t, m, color=col, lw=2.5,
                    label=f"{lbl}  (period mean = {np.nanmean(m):.2f} mm day⁻¹)",
                    zorder=4)

            # 10-yr rolling mean
            if len(m) >= 10:
                roll   = np.convolve(m, np.ones(10)/10, mode='valid')
                t_roll = t[9:]
                ax.plot(t_roll, roll, color=col, lw=1.2, ls='--',
                        alpha=0.70, zorder=5)

    ax.fill_between([2015,2100],[0,0],
                    [ax.get_ylim()[1] if ax.get_ylim()[1]>0 else 2]*2,
                    color=C_SURPLUS, alpha=0.05, zorder=0)
    ax.fill_between([2015,2100],
                    [ax.get_ylim()[0] if ax.get_ylim()[0]<0 else -2]*2,
                    [0,0], color=C_DEFICIT, alpha=0.05, zorder=0)

    ax.text(0.01, 0.97, 'SURPLUS  (P > E)', transform=ax.transAxes,
            fontsize=12, color=C_SURPLUS, fontweight='bold',
            va='top', alpha=0.80)
    ax.text(0.01, 0.03, 'DEFICIT  (P < E)', transform=ax.transAxes,
            fontsize=12, color=C_DEFICIT, fontweight='bold',
            va='bottom', alpha=0.80)

    style_ax(ax, ylabel='P − E  (mm day⁻¹)')
    watermark(ax)
    ax.legend(fontsize=13, loc='upper right',
              framealpha=0.92, edgecolor='#cccccc',
              title='Solid = ensemble mean  |  dashed = 10-yr rolling mean\nShading = 5-model spread',
              title_fontsize=11)

    plt.tight_layout()
    save_fig(fig, f'Fig5_{EM}_AllScenarios_WaterBalance.png')

    # ----------------------------------------------------------
    # FIG 6  –  All-scenario cumulative ΔS overlay
    # ----------------------------------------------------------
    fig, ax = plt.subplots(figsize=(16, 7))
    fig.suptitle(
        f'Lake Victoria – Cumulative Storage Change  ΔS  |  All Scenarios\n'
        f'ISIMIP3b Projections 2015–2100  |  Evaporation model: {EM}  |  5-model ensemble',
        fontsize=16, fontweight='bold', y=1.02
    )

    for sc in SCENARIOS:
        s   = S[sc]
        col = SCENARIO_COLORS[sc]
        lbl = SCENARIO_LABELS[sc]

        if s['cum_ann']:
            t, cum_mean, cum_min, cum_max = s['cum_ann']
            shade(ax, t, cum_min, cum_max, col, 0.15)
            ax.plot(t, cum_mean, color=col, lw=2.5,
                    label=f"{lbl}  (end ΔS = {cum_mean[-1]:+.0f} mm)",
                    zorder=4)

            ax.annotate(f'{cum_mean[-1]:+.0f} mm',
                        xy=(t[-1], cum_mean[-1]),
                        xytext=(5, 0), textcoords='offset points',
                        fontsize=12, color=col, fontweight='bold', va='center')

    style_ax(ax, ylabel='Cumulative  ΔS  (mm)')
    watermark(ax)
    ax.legend(fontsize=13, loc='upper left',
              framealpha=0.92, edgecolor='#cccccc',
              title='Shading = 5-model spread',
              title_fontsize=11)

    plt.tight_layout()
    save_fig(fig, f'Fig6_{EM}_AllScenarios_CumulativeStorage.png')

print("\n" + "="*65)
print(f"✓  All figures saved  ({2 * 6} files total, ALBM + GOTM)")
print("="*65)

