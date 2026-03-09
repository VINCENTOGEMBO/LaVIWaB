# -*- coding: utf-8 -*-
"""
Lake Victoria Basin: ISIMIP Climate Data Analysis


Author: V. Ogembo
Created: Nov 2025
"""

import os
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")
import sys
import json
from datetime import datetime
import warnings
from scipy.integrate import cumtrapz
warnings.filterwarnings("ignore")

#%%

# Set plots style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 150
plt.rcParams['font.size'] = 14
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['axes.titlesize'] = 18
plt.rcParams['legend.fontsize'] = 12
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14

# ===============================================================
# CONFIGURATION
# ===============================================================

BASE_DIR = r"C:\DATA\ISIMIP Data"
OUTPUT_DIR = r"C:\GLIWaB\outputs\ISIMIP\climate_figures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Define color scheme
COLORS = {
    "SSP1-2.6": "#4FC3F7",   # Light Blue
    "SSP3-7.0": "#F57C00",  # Orange
    "SSP5-8.5": "#C62828",  # Red
    "historical": "#424242"  # Dark gray
}

SCENARIOS = ["SSP1-2.6", "SSP3-7.0", "SSP5-8.5"]

# Precipitation model paths
PRECIP_MODELS = {
    "GFDL-ESM4": {
        "base": os.path.join(BASE_DIR, "Precipitation_Hist+Projection", "GFDL-ESM_ISIMIP3bInputDataclimateatmospheregfdl-esm4"),
        "historical": "isimip-download-e1b404e0599f538004c023bdc0951e4adf98af85",
        "SSP1-2.6": "isimip-download-b417c0cdec2fd86b1a30303857526d43121e8397",
        "SSP3-7.0": "isimip-download-4ed5ac396cb52c78c4247627c81971e46220bafa",
        "SSP5-8.5": "isimip-download-31b33464e44cbaccef70bef9abe5c91be6c9b047"
    },
    "IPSL-CM6A-LR": {
        "base": os.path.join(BASE_DIR, "Precipitation_Hist+Projection", "IPSL-CM6A_ISIMIP3bInputDataclimateatmosphereipsl-cm6a-lr"),
        "historical": "isimip-download-e1b404e0599f538004c023bdc0951e4adf98af85"
    },
    "MPI-ESM1-2-HR": {
        "base": os.path.join(BASE_DIR, "Precipitation_Hist+Projection", "MPI-ESM_ISIMIP3bInputDataclimateatmospherempi-esm1-2-hr"),
        "historical": "isimip-download-8bb7aabb00a990ad45cdbce5b5bd0dfaca8e538f"
    },
    "MRI-ESM2-0": {
        "base": os.path.join(BASE_DIR, "Precipitation_Hist+Projection", "MRI-ESM2_ ISIMIP3bInputDataclimateatmospheremri-esm2-0"),
        "historical": "isimip-download-48a679cc8ae16f71cdd5e221430368c224ad7743"
    },
    "UKESM1-0-LL": {
        "base": os.path.join(BASE_DIR, "Precipitation_Hist+Projection", "UKESM1_ISIMIP3bInputDataclimateatmosphereukesm1-0"),
        "historical": "isimip-download-efff9895cf494be2138e5e510188440794bdff0c"
    }
}

# Evaporation model paths
EVAP_MODELS = {
    "UKESM1-0-LL": {
        "base": os.path.join(BASE_DIR, "Latent Heat Evaporation", "UKESM1_ISIMIP3bOutputDatalakes_globalalbmukesm1-0-ll"),
        "historical": "isimip-download-ad7fd1a6b887910d2620518d540854bb0b19494b",
        "SSP1-2.6": "isimip-download-b2946ac7f91535984f83a62c19ea8d42055abece",
        "SSP3-7.0": "isimip-download-12000d5801776e85b1f57ca0f9e16a85705f5ad8",
        "SSP5-8.5": "isimip-download-4017f3cf43213469d84b235a63025faeb4c9a427"
    },
    "MRI-ESM2-0": {
        "base": os.path.join(BASE_DIR, "Latent Heat Evaporation", "MRI-ESM2_ISIMIP3bOutputDatalakes_globalalbmmri-esm2-0"),
        "historical": "isimip-download-9a2396c1806c480742e4cae805f3645c5d5872a4",
        "SSP1-2.6": "isimip-download-20836a746848f505bb5e960bc1c41e6ac63ef662",
        "SSP3-7.0": "isimip-download-04807dc6b94473db3e82c54b14c77a008ae272e7",
        "SSP5-8.5": "isimip-download-2c0c9c92bc11651472fc08d4857036b4e7a5736c"
    }
}

# ===============================================================
# DATA LOADING FUNCTIONS
# ===============================================================

def load_climate_variable(folder, var_name, conversion_factor=1.0):
    """
    Generic function to load and process climate variables.
    
    Args:
        folder: Directory containing NetCDF files
        var_name: Variable name to extract
        conversion_factor: Multiplier for unit conversion
    
    Returns:
        DataFrame with annual mean values
    """
    files = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".nc")])
    
    if not files:
        print(f"⚠️ No NetCDF files in {os.path.basename(folder)}")
        return None
    
    try:
        ds = xr.open_mfdataset(files, combine='by_coords')
        
        # Auto-detect variable if not found
        if var_name not in ds.data_vars:
            var_name = list(ds.data_vars.keys())[0]
        
        # Spatial mean
        data = ds[var_name].mean(dim=["lat", "lon"])
        
        # Convert to DataFrame
        df = data.to_dataframe().reset_index()
        df['time'] = pd.to_datetime(df['time'])
        
        # Annual mean
        df_annual = df.set_index('time').resample('YE').mean()
        
        # Apply conversion
        df_annual[var_name] = df_annual[var_name] * conversion_factor
        
        ds.close()
        return df_annual.rename(columns={var_name: 'value'})
    
    except Exception as e:
        print(f"⚠️ Error loading {os.path.basename(folder)}: {e}")
        return None


def load_precipitation(folder):
    """Load precipitation data (kg/m²/s → mm/day)"""
    return load_climate_variable(folder, 'pr', conversion_factor=86400)


def load_evaporation(folder):
    """Load latent heat flux (W/m² → mm/day)"""
    return load_climate_variable(folder, 'hfls', conversion_factor=86400/2.45e6)


def load_model_ensemble(models_dict, scenario, load_func):
    """
    Load data from multiple models for a given scenario.
    
    Returns:
        DataFrame with each model as a column
    """
    model_data = {}
    
    for model_name, paths in models_dict.items():
        if scenario not in paths:
            continue
        
        folder_path = os.path.join(paths["base"], paths[scenario])
        
        if not os.path.exists(folder_path):
            print(f"⚠️ Missing {scenario} for {model_name}")
            continue
        
        df = load_func(folder_path)
        if df is not None:
            model_data[model_name] = df['value']
    
    if not model_data:
        return None
    
    return pd.DataFrame(model_data)


# ===============================================================
# PLOTTING FUNCTIONS
# ===============================================================

def plot_multi_model_ensemble(data_dict, variable_name, ylabel, filename):
    """
    Create publication-ready multi-model ensemble plot.
    
    Args:
        data_dict: Dictionary with scenario names as keys, DataFrames as values
        variable_name: Name for plot title
        ylabel: Y-axis label
        filename: Output filename
    """
    fig, ax = plt.subplots(figsize=(14, 7))
    
    for scenario in ["historical"] + SCENARIOS:
        if scenario not in data_dict:
            continue
        
        df = data_dict[scenario]
        
        # Calculate ensemble statistics
        ensemble_mean = df.mean(axis=1)
        ensemble_std = df.std(axis=1)
        
        # Plot mean line
        color = COLORS.get(scenario, "gray")
        label = scenario if scenario != "historical" else "Historical (Multi-model)"
        
        ax.plot(ensemble_mean.index, ensemble_mean, 
                color=color, linewidth=2.5, label=label, alpha=0.9)
        
        # Add uncertainty band (±1 std)
        ax.fill_between(ensemble_mean.index, 
                        ensemble_mean - ensemble_std, 
                        ensemble_mean + ensemble_std,
                        color=color, alpha=0.15)
        
        # Add trend line for projections
        # if scenario != "historical":
        #     years = ensemble_mean.index.year
        #     z = np.polyfit(years, ensemble_mean.values, 1)
        #     trend = np.poly1d(z)
        #     ax.plot(ensemble_mean.index, trend(years), 
        #            color=color, linestyle='--', linewidth=1.5, alpha=0.6)
    
    ax.set_title(f"Lake Victoria Basin: {variable_name} Projections (ISIMIP3b)", 
                fontsize=18, fontweight='bold', pad=15)
    ax.set_xlabel("Year", fontsize=14, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=14, fontweight='bold')
    ax.legend(fontsize=12, loc='best', frameon=True, shadow=True)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    savepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(savepath, dpi=100, bbox_inches="tight")
    plt.show()
    print(f"✅ Saved: {savepath}")

def plot_multi_model_ensemble(data_dict, variable_name, ylabel, filename):
    """
    Create publication-ready multi-model ensemble plot with
    scenario-specific uncertainty shading.
    """
    fig, ax = plt.subplots(figsize=(14, 7))

    # Order: historical, then SSPs
    scenarios_order = ["historical"] + SCENARIOS

    for scenario in scenarios_order:
        if scenario not in data_dict or data_dict[scenario] is None:
            continue

        df = data_dict[scenario]

        # Ensemble statistics
        ensemble_mean = df.mean(axis=1)
        ensemble_std = df.std(axis=1)

        # Plot mean line
        color = COLORS.get(scenario, "gray")
        label = scenario if scenario != "historical" else "Historical (Multi-model)"

        ax.plot(
            ensemble_mean.index, ensemble_mean,
            color=color, linewidth=2.4, alpha=0.9, label=label
        )

        # ---------- NEW: Uncertainty shading (±1 std) ----------
        ax.fill_between(
            ensemble_mean.index,
            ensemble_mean - ensemble_std,
            ensemble_mean + ensemble_std,
            color=color,
            alpha=0.22,          # slightly stronger shading for clarity
            edgecolor=None
        )
        # --------------------------------------------------------

        # Add trend line only for projections
        # if scenario != "historical":
        #     years = ensemble_mean.index.year
        #     z = np.polyfit(years, ensemble_mean.values, 1)
        #     trend = np.poly1d(z)
        #     ax.plot(
        #         ensemble_mean.index, trend(years),
        #         color=color, linestyle='--',
        #         linewidth=1.5, alpha=0.6
        #     )

    # Title and labels
    ax.set_title(
        f"Lake Victoria Basin: {variable_name} Projections (ISIMIP3b)",
        fontsize=18, fontweight='bold', pad=15
    )
    ax.set_xlabel("Year", fontsize=14, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=14, fontweight='bold')
    ax.legend(fontsize=12, loc='best', frameon=True, shadow=False)
    ax.grid(True, alpha=0.3, linestyle='--')

    # Save and show
    plt.tight_layout()
    savepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(savepath, dpi=100, bbox_inches="tight")
    plt.show()
    print(f"✅ Saved: {savepath}")

def plot_precipitation_evaporation_combined(precip_data, evap_data, filename):
    """
    Create combined P-E plot showing water balance changes.
    """
    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
    fig.suptitle("Lake Victoria Basin: Water Balance Components (ISIMIP3b)", 
                 fontsize=15, fontweight='bold')
    
    for i, scenario in enumerate(SCENARIOS):
        ax = axes[i]
        
        # Get data
        pr_df = precip_data.get(scenario)
        ev_df = evap_data.get(scenario)
        
        if pr_df is None or ev_df is None:
            continue
        
        # Calculate means
        pr_mean = pr_df.mean(axis=1)
        ev_mean = ev_df.mean(axis=1)
        net = pr_mean - ev_mean
        
        color = COLORS[scenario]
        
        # Plot P and E
        ax.plot(pr_mean.index, pr_mean, color='blue', linewidth=2, 
               label='Precipitation', linestyle='-')
        ax.plot(ev_mean.index, ev_mean, color='red', linewidth=2, 
               label='Evaporation', linestyle='--')
        ax.plot(net.index, net, color=color, linewidth=2.5, 
               label='Net (P - E)', linestyle='-', alpha=0.8)
        
        # Add zero line
        ax.axhline(0, color='black', linestyle=':', linewidth=1, alpha=0.5)
        
        # Trend for Net
        years = net.index.year
        z = np.polyfit(years, net.values, 1)
        trend = np.poly1d(z)
        trend_label = f"Net Trend: {z[0]:.4f} mm/day/year"
        ax.plot(net.index, trend(years), color=color, linestyle=':', 
               linewidth=1.5, alpha=0.7, label=trend_label)
        
        ax.set_title(f"{scenario}", fontsize=18, loc='left', fontweight='bold')
        ax.set_ylabel("Flux (mm/day)", fontsize=14, fontweight='bold')
        ax.legend(fontsize=12, loc='best')
        ax.grid(True, alpha=0.3)
    
    axes[-1].set_xlabel("Year", fontsize=14, fontweight='bold')
    
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    savepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(savepath, dpi=100, bbox_inches="tight")
    plt.show()
    print(f"✅ Saved: {savepath}")


def plot_summary_statistics(precip_data, evap_data, filename):
    """
    Create summary bar plot comparing periods and scenarios.
    """
    scenarios_to_plot = SCENARIOS
    periods = {
        "2020-2050": (2020, 2050),
        "2050-2100": (2050, 2100)
    }
    
    results = []
    
    for scenario in scenarios_to_plot:
        pr_df = precip_data.get(scenario)
        ev_df = evap_data.get(scenario)
        
        if pr_df is None or ev_df is None:
            continue
        
        pr_mean = pr_df.mean(axis=1)
        ev_mean = ev_df.mean(axis=1)
        net = pr_mean - ev_mean
        
        for period_name, (start, end) in periods.items():
            period_data = net[(net.index.year >= start) & (net.index.year <= end)]
            if len(period_data) > 0:
                results.append({
                    'Scenario': scenario,
                    'Period': period_name,
                    'Net P-E (mm/day)': period_data.mean()
                })
    
    df_results = pd.DataFrame(results)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(periods))
    width = 0.25
    
    for i, scenario in enumerate(scenarios_to_plot):
        scenario_data = df_results[df_results['Scenario'] == scenario]
        values = [scenario_data[scenario_data['Period'] == p]['Net P-E (mm/day)'].values[0] 
                 if len(scenario_data[scenario_data['Period'] == p]) > 0 else 0 
                 for p in periods.keys()]
        
        ax.bar(x + i*width, values, width, label=scenario, 
              color=COLORS[scenario], alpha=0.8)
    
    ax.set_xlabel('Time Period', fontsize=14, fontweight='bold')
    ax.set_ylabel('Mean Net Water Balance (mm/day)', fontsize=14, fontweight='bold')
    ax.set_title('Lake Victoria Basin: Future Water Balance Summary', 
                fontsize=18, fontweight='bold')
    ax.set_xticks(x + width)
    ax.set_xticklabels(periods.keys())
    ax.legend(fontsize=12)
    ax.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    savepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(savepath, dpi=100, bbox_inches="tight")
    plt.show()
    print(f"✅ Saved: {savepath}")


# ===============================================================
# MAIN EXECUTION
# ===============================================================

def main():
    print("="*70)
    print("Lake Victoria Basin: ISIMIP Climate Data Analysis")
    print("="*70)
    
    # ---------------------------------------------------------------
    # 1. Load Precipitation Data
    # ---------------------------------------------------------------
    print("\n📊 Loading precipitation data...")
    precip_data = {}
    
    precip_data["historical"] = load_model_ensemble(PRECIP_MODELS, "historical", load_precipitation)
    
    for scenario in SCENARIOS:
        precip_data[scenario] = load_model_ensemble(PRECIP_MODELS, scenario, load_precipitation)
    
    # ---------------------------------------------------------------
    # 2. Load Evaporation Data
    # ---------------------------------------------------------------
    print("\n📊 Loading evaporation data...")
    evap_data = {}
    
    evap_data["historical"] = load_model_ensemble(EVAP_MODELS, "historical", load_evaporation)
    
    for scenario in SCENARIOS:
        evap_data[scenario] = load_model_ensemble(EVAP_MODELS, scenario, load_evaporation)
    
    # ---------------------------------------------------------------
    # 3. Generate Publication Plots
    # ---------------------------------------------------------------
    print("\n📈 Creating plots...")
    
    # Plot 1: Precipitation ensemble
    plot_multi_model_ensemble(
        precip_data, 
        "Precipitation", 
        "Precipitation (mm/day)",
        "01_precipitation_ensemble.png"
    )
    
    # Plot 2: Evaporation ensemble
    plot_multi_model_ensemble(
        evap_data, 
        "Evaporation (Latent Heat Flux)", 
        "Evaporation (mm/day)",
        "02_evaporation_ensemble.png"
    )
    
    # Plot 3: Combined P-E by scenario
    plot_precipitation_evaporation_combined(
        precip_data,
        evap_data,
        "03_water_balance_by_scenario.png"
    )
    
    # Plot 4: Summary statistics
    plot_summary_statistics(
        precip_data,
        evap_data,
        "04_summary_statistics.png"
    )
    
    print("\n" + "="*70)
    print(f"✅ All figures saved to: {OUTPUT_DIR}")
    print("="*70)


if __name__ == "__main__":
    main()





#%%
# -*- coding: utf-8 -*-
"""

Run Lake Victoria WBM future projections (ISIMIP ensembles) in LaVIWaB Model
Produces CSV outputs for each scenario with ensemble mean and uncertainty


"""



# --------------------------------------------------------------
# 1. CONFIGURATION AND PATHS
# --------------------------------------------------------------
PROJECT_DIR = os.path.dirname(__file__)
DEFAULT_CONFIG_PATH = os.path.join(PROJECT_DIR, "settings_isimip.json")

cfg = {
    "lake_name": "Lake Victoria",
    "simulation_period": {"historical_start": 1985, "historical_end": 2023, "future_end": 2100},
    "input_data": {
        "precipitation": {
            "path": r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection",
            "variable": "pr",
            "models": ["GFDL-ESM4"],
            "scenarios": ["ssp126", "ssp370", "ssp585"]
        },
        "evaporation": {
            "path": r"C:\DATA\ISIMIP Data\Latent Heat Evaporation",
            "variable": "hfls",
            "models": ["UKESM1-0-LL"],
            "scenarios": ["ssp126", "ssp370", "ssp585"]
        }
    },
    "lake_geometry": {
        "area_elevation_curve": r"C:\Users\VO000003\OneDrive - Vrije Universiteit Brussel\Ogembo_LVictoria_IWBM\lakevic-eea-wbm\input_data\hypsograph\WBM_depth_area_curve.csv"
    },
    "output": {"directory": r"C:\GLIWaB\outputs\ISIMIP"}
}

# Scenario directory mapping
cfg["input_data"]["precipitation"]["scenarios_paths"] = {
    "ssp126": r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\GFDL-ESM_ISIMIP3bInputDataclimateatmospheregfdl-esm4\isimip-download-b417c0cdec2fd86b1a30303857526d43121e8397",
    "ssp370": r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\GFDL-ESM_ISIMIP3bInputDataclimateatmospheregfdl-esm4\isimip-download-4ed5ac396cb52c78c4247627c81971e46220bafa",
    "ssp585": r"C:\DATA\ISIMIP Data\Precipitation_Hist+Projection\GFDL-ESM_ISIMIP3bInputDataclimateatmospheregfdl-esm4\isimip-download-31b33464e44cbaccef70bef9abe5c91be6c9b047"
}
cfg["input_data"]["evaporation"]["scenarios_paths"] = {
    "ssp126": r"C:\DATA\ISIMIP Data\Latent Heat Evaporation\UKESM1_ISIMIP3bOutputDatalakes_globalalbmukesm1-0-ll\isimip-download-b2946ac7f91535984f83a62c19ea8d42055abece",
    "ssp370": r"C:\DATA\ISIMIP Data\Latent Heat Evaporation\UKESM1_ISIMIP3bOutputDatalakes_globalalbmukesm1-0-ll\isimip-download-12000d5801776e85b1f57ca0f9e16a85705f5ad8",
    "ssp585": r"C:\DATA\ISIMIP Data\Latent Heat Evaporation\UKESM1_ISIMIP3bOutputDatalakes_globalalbmukesm1-0-ll\isimip-download-4017f3cf43213469d84b235a63025faeb4c9a427"
}


OUT_DIR = cfg["output"]["directory"]
os.makedirs(OUT_DIR, exist_ok=True)

# --------------------------------------------------------------
# 2. IMPORT LOCAL MODULES
# --------------------------------------------------------------
sys.path.append(PROJECT_DIR)
try:
    import WBM_inicon as inicon
    import WBM_inigeom as inigeom
    print("Imported local WBM helper modules (WBM_inicon, WBM_inigeom).")
except Exception:
    class _inicon:
        sec_per_day = 86400
    class _inigeom:
        elev_lakebottom = 1115.0
        A_lake = 6.7e10
    inicon = _inicon()
    inigeom = _inigeom()
    print("WBM helper modules not found; using fallback constants.")

# --------------------------------------------------------------
# 3. LOAD HYPSOGRAPH
# --------------------------------------------------------------
print("Loading hypsographic curve...")
hypsograph_path = cfg["lake_geometry"]["area_elevation_curve"]
hypsograph = pd.read_csv(hypsograph_path)
hypsograph = hypsograph.sort_values("depth_m")
hypsograph["vol_m3"] = cumtrapz(hypsograph["area_m2"], hypsograph["depth_m"], initial=0)
hypsograph = hypsograph.set_index("depth_m")
print(f"✓ Hypsograph loaded with {len(hypsograph)} rows.")

# Get valid depth range
MIN_DEPTH = hypsograph.index.min()
MAX_DEPTH = hypsograph.index.max()
print(f"Valid depth range: {MIN_DEPTH:.2f} to {MAX_DEPTH:.2f} m")


def calc_area_from_depth(depth, hypsograph_df):
    """
    Interpolates lake area for a given depth (scalar or array).
    Clamps depth to valid range to prevent extrapolation errors.
    """
    depth_vals = hypsograph_df.index.values
    area_vals  = hypsograph_df["area_m2"].values
    
    # Clamp depth to valid range
    depth_clamped = np.clip(depth, depth_vals.min(), depth_vals.max())
    
    return np.interp(depth_clamped, depth_vals, area_vals)


def calc_volume_from_depth(depth, hypsograph_df):
    """
    Interpolates lake volume for a given depth (scalar or array).
    Clamps depth to valid range to prevent extrapolation errors.
    """
    depth_vals = hypsograph_df.index.values
    vol_vals   = hypsograph_df["vol_m3"].values
    
    # Clamp depth to valid range
    depth_clamped = np.clip(depth, depth_vals.min(), depth_vals.max())
    
    return np.interp(depth_clamped, depth_vals, vol_vals)


# --------------------------------------------------------------
# 4. FUNCTIONS FOR DATA LOADING
# --------------------------------------------------------------
def list_nc_files(folder):
    return sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".nc")])

def load_isimip_mean(folder, var, factor):
    files = list_nc_files(folder)
    if not files:
        return None
    ds = xr.open_mfdataset(files, combine="by_coords")
    if var not in ds.data_vars:
        var = list(ds.data_vars.keys())[0]
    arr = ds[var].mean(dim=["lat", "lon"]) * factor
    s = arr.to_dataframe().reset_index().set_index("time")[var]
    s.index = pd.to_datetime(s.index)
    ds.close()
    return s

# --------------------------------------------------------------
# 5. IMPROVED WATER BALANCE MODEL
# --------------------------------------------------------------

def agreed_curve_Qout(level, area):
    """
    Agreed Curve outflow function.
    FIXED: Returns outflow in m/day (properly normalized by lake area)
    
    Args:
        level: Lake level (m a.s.l.)
        area: Lake surface area (m²)
    Returns:
        Qout in m/day
    """
    if level < 1133.0:
        Q_m3s = 0.0
    elif level < 1135.0:
        Q_m3s = 600.0  # m³/s
    else:
        Q_m3s = 1200.0  # m³/s
    
    # Convert m³/s to m/day: (m³/s) * (86400 s/day) / (area in m²)
    return (Q_m3s * inicon.sec_per_day) / area


def run_gliwab_time_series(P_series, E_series, Qin_m3s, L0, hypsograph_df):
    """
    FIXED water balance model with proper unit handling.
    
    Args:
        P_series: Precipitation (m/day)
        E_series: Evaporation (m/day)
        Qin_m3s: Inflow (m³/s) - scalar constant
        L0: Initial lake level (m a.s.l.)
        hypsograph_df: Hypsographic curve
    """
    dates = P_series.index
    n = len(dates)

    L = np.zeros(n)
    A = np.zeros(n)
    V = np.zeros(n)
    Qin_arr = np.zeros(n)
    Qout_arr = np.zeros(n)

    # Initial conditions
    L[0] = L0
    depth0 = L0 - inigeom.elev_lakebottom
    A[0] = calc_area_from_depth(depth0, hypsograph_df)
    V[0] = calc_volume_from_depth(depth0, hypsograph_df)
    
    # Convert Qin from m³/s to m/day
    Qin_arr[0] = (Qin_m3s * inicon.sec_per_day) / A[0]
    Qout_arr[0] = agreed_curve_Qout(L[0], A[0])

    for t in range(1, n):
        # Get previous area for flow conversions
        A_prev = A[t-1]
        
        # Convert inflow from m³/s to m/day
        q_in = (Qin_m3s * inicon.sec_per_day) / A_prev
        
        # Get outflow in m/day
        q_out = agreed_curve_Qout(L[t-1], A_prev)

        # Water balance: ΔL = P - E + Qin - Qout
        dL = P_series.iloc[t] - E_series.iloc[t] + q_in - q_out
        L[t] = L[t-1] + dL
        
        # Clamp to physically reasonable range
        L[t] = np.clip(L[t], inigeom.elev_lakebottom + MIN_DEPTH, 
                       inigeom.elev_lakebottom + MAX_DEPTH)

        # Update geometry
        depth_t = L[t] - inigeom.elev_lakebottom
        A[t] = calc_area_from_depth(depth_t, hypsograph_df)
        V[t] = calc_volume_from_depth(depth_t, hypsograph_df)
        
        Qin_arr[t] = q_in
        Qout_arr[t] = q_out

    return pd.DataFrame({
        "L_wb": L,
        "A_wb": A,
        "V_wb": V,
        "Q_in": Qin_arr,
        "Q_out": Qout_arr
    }, index=dates)


# --------------------------------------------------------------
# 6. LOAD HISTORICAL DATA
# --------------------------------------------------------------
hist_path = r"C:\DATA\attribution\Model_level_area.csv"

df_hist = pd.read_csv(hist_path)
df_hist["date"] = pd.to_datetime(df_hist["date"])
df_hist = df_hist.set_index("date")

L0_hist = df_hist["water_level"].iloc[-1]
print(f"✓ Loaded historical lake level. Last level = {L0_hist:.3f} m")

# Estimate typical Qin from historical water balance
# Using annual mean: Qin ≈ E - P (to maintain balance) converted to m³/s
A_lake = 6.7e10  # m²
historical_mean_qin_m3s = 800.0  # Typical value for Lake Victoria (adjust based on your data)
print(f"Using typical Qin = {historical_mean_qin_m3s:.1f} m³/s")


# --------------------------------------------------------------
# 7. RUN ENSEMBLE FOR EACH SCENARIO
# --------------------------------------------------------------
def run_ensemble_for_scenario(ssp):
    print(f"\n{'='*60}")
    print(f"Running GLIWaB ensemble for {ssp.upper()}")
    print(f"{'='*60}")
    
    pr_path = cfg["input_data"]["precipitation"]["scenarios_paths"][ssp]
    ev_path = cfg["input_data"]["evaporation"]["scenarios_paths"][ssp]

    # Load ISIMIP forcing
    P = load_isimip_mean(pr_path, "pr", 86400)  # mm/day
    E = load_isimip_mean(ev_path, "hfls", 86400/2.45e6)  # mm/day

    if P is None or E is None:
        print(f"⚠️ Missing ISIMIP data for {ssp}")
        return None

    # Convert mm/day → m/day
    P = P * 1e-3
    E = E * 1e-3

    # Synchronize time range
    idx = P.index.intersection(E.index)
    P = P.loc[idx]
    E = E.loc[idx]
    
    print(f"Time range: {P.index[0]} to {P.index[-1]}")
    print(f"Data points: {len(P)}")
    print(f"Mean P: {P.mean()*1000:.2f} mm/day, Mean E: {E.mean()*1000:.2f} mm/day")

    # Run GLIWaB-style model with constant Qin
    df = run_gliwab_time_series(P, E, historical_mean_qin_m3s, L0_hist, hypsograph)

    # Add Net term (in mm/day for easy interpretation)
    df["Net_mm/day"] = (P - E + df["Q_in"] - df["Q_out"]) * 1000
    
    # Diagnostics
    print(f"Lake level range: {df['L_wb'].min():.2f} to {df['L_wb'].max():.2f} m")
    print(f"Lake area range: {df['A_wb'].min()/1e6:.0f} to {df['A_wb'].max()/1e6:.0f} km²")

    # Save CSV
    out_csv = os.path.join(OUT_DIR, f"GLIWaB_projection_{ssp}_fixed.csv")
    df.to_csv(out_csv)
    print(f"✅ Saved: {out_csv}")
    return df


# --------------------------------------------------------------
# 8. MAIN DRIVER
# --------------------------------------------------------------
def main():
    print("\n" + "="*60)
    print("Starting WBM Projection Run (FIXED VERSION)")
    print("="*60)
    
    results = {}
    for sc in ["ssp126", "ssp370", "ssp585"]:
        res = run_ensemble_for_scenario(sc)
        if res is not None:
            results[sc] = res
    
    print("\n" + "="*60)
    print("Projection runs finished successfully!")
    print(f"Outputs saved in: {OUT_DIR}")
    print("="*60)
    return results

if __name__ == "__main__":
    main()



#%%


# -*- coding: utf-8 -*-
"""
WBM_projection_visualization.py
Visualize Lake Victoria WBM projection outputs with uncertainty shading
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --------------------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------------------
OUT_DIR = r"C:\GLIWaB\outputs\ISIMIP"
FIG_DIR = os.path.join(OUT_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

SCENARIOS = ["ssp126", "ssp370", "ssp585"]

colors = {
    "ssp126": "#4FC3F7",
    "ssp370": "#F57C00",
    "ssp585": "#C62828"
}

labels = {
    "ssp126": "SSP1-2.6 (Low emissions)",
    "ssp370": "SSP3-7.0 (Medium emissions)",
    "ssp585": "SSP5-8.5 (High emissions)"
}

sns.set_style("whitegrid")
plt.rcParams["figure.dpi"] = 150
plt.rcParams["font.size"] = 11

# --------------------------------------------------------------
# 2. LOAD PROJECTION DATA
# --------------------------------------------------------------
def load_projection_data(out_dir, scenarios):
    data = {}
    for sc in scenarios:
        fpath = os.path.join(out_dir, f"GLIWaB_projection_{sc}_fixed.csv")
        if not os.path.exists(fpath):
            fpath = os.path.join(out_dir, f"GLIWaB_projection_{sc}_1980_2100.csv")

        if os.path.exists(fpath):
            df = pd.read_csv(fpath, index_col=0, parse_dates=True)

            df = df[(df["A_wb"] > 1e9) & (df["A_wb"] < 1e11)]
            df = df[(df["L_wb"] > 1110) & (df["L_wb"] < 1150)]

            data[sc] = df
            print(f"✓ Loaded {sc.upper()} ({len(df)} records)")
        else:
            print(f"⚠ Missing file: {fpath}")
    return data

# --------------------------------------------------------------
# 3. HELPER: UNCERTAINTY BAND
# --------------------------------------------------------------
def add_uncertainty_band(ax, x, y, color, window=10, alpha=0.20):
    mean = y.rolling(window=window, center=True, min_periods=3).mean()
    std = y.rolling(window=window, center=True, min_periods=3).std()

    ax.fill_between(
        x,
        mean - std,
        mean + std,
        color=color,
        alpha=alpha,
        linewidth=0
    )

# --------------------------------------------------------------
# 4. PLOTTING FUNCTIONS
# --------------------------------------------------------------
def plot_lake_level(data_dict, savepath):
    fig, ax = plt.subplots(figsize=(14, 7))

    for sc, df in data_dict.items():
        df_annual = df.resample("YE").mean()

        ax.plot(
            df_annual.index,
            df_annual["L_wb"],
            label=labels[sc],
            color=colors[sc],
            linewidth=2.5,
            alpha=0.9
        )

        add_uncertainty_band(
            ax,
            df_annual.index,
            df_annual["L_wb"],
            colors[sc]
        )

        rolling = df_annual["L_wb"].rolling(window=5, center=True).mean()
        ax.plot(
            df_annual.index,
            rolling,
            color=colors[sc],
            linestyle="--",
            linewidth=1.5,
            alpha=0.6
        )

    ax.set_title("Lake Victoria Projected Water Level (m a.s.l.)",
                 fontsize=22, fontweight="bold", pad=20)
    ax.set_xlabel("Year", fontsize=18, fontweight="bold")
    ax.set_ylabel("Lake Level (m a.s.l.)", fontsize=18, fontweight="bold")
    ax.legend(fontsize=14, loc="best", frameon=True, shadow=True)
    ax.grid(True, alpha=0.3, linestyle="--")

    plt.tight_layout()
    plt.savefig(savepath, dpi=300, bbox_inches="tight")
    plt.show()
    print(f"✅ Saved: {savepath}")

def plot_lake_area(data_dict, savepath):
    fig, ax = plt.subplots(figsize=(14, 7))

    for sc, df in data_dict.items():
        df_annual = df.resample("YE").mean()
        area_km2 = df_annual["A_wb"] / 1e6

        ax.plot(
            df_annual.index,
            area_km2,
            label=labels[sc],
            color=colors[sc],
            linewidth=2.5,
            alpha=0.9
        )

        add_uncertainty_band(
            ax,
            df_annual.index,
            area_km2,
            colors[sc]
        )

        rolling = area_km2.rolling(window=5, center=True).mean()
        ax.plot(
            df_annual.index,
            rolling,
            color=colors[sc],
            linestyle="--",
            linewidth=1.5,
            alpha=0.6
        )

    ax.set_title("Lake Victoria Projected Surface Area",
                 fontsize=22, fontweight="bold", pad=20)
    ax.set_xlabel("Year", fontsize=18, fontweight="bold")
    ax.set_ylabel("Lake Area (km²)", fontsize=18, fontweight="bold")
    ax.legend(fontsize=14, loc="best", frameon=True, shadow=True)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_ylim(66700, 67200)

    plt.tight_layout()
    plt.savefig(savepath, dpi=300, bbox_inches="tight")
    plt.show()
    print(f"✅ Saved: {savepath}")

def plot_net_water_balance(data_dict, savepath):
    fig, ax = plt.subplots(figsize=(14, 7))

    for sc, df in data_dict.items():
        net = df["Net_mm/day"] if "Net_mm/day" in df.columns else (df["Q_in"] - df["Q_out"]) * 1000
        net_annual = net.resample("YE").mean()

        ax.plot(
            net_annual.index,
            net_annual.values,
            label=labels[sc],
            color=colors[sc],
            linewidth=2.5,
            alpha=0.9
        )

        years = net_annual.index.year
        z = np.polyfit(years, net_annual.values, 1)
        trend = np.poly1d(z)

        ax.plot(
            net_annual.index,
            trend(years),
            linestyle="--",
            color=colors[sc],
            alpha=0.6,
            linewidth=1.5,
            label=f"{sc.upper()} trend ({z[0]:.3f} mm/day/yr)"
        )

    ax.axhline(0, color="black", linewidth=1, alpha=0.5)
    ax.set_title("Lake Victoria Net Water Balance (Qin − Qout)",
                 fontsize=22, fontweight="bold", pad=20)
    ax.set_xlabel("Year", fontsize=18, fontweight="bold")
    ax.set_ylabel("Net Water Balance (mm/day)", fontsize=18, fontweight="bold")
    ax.legend(fontsize=14, loc="best", frameon=True, shadow=True)
    ax.grid(True, alpha=0.3, linestyle="--")

    plt.tight_layout()
    plt.savefig(savepath, dpi=300, bbox_inches="tight")
    plt.show()
    print(f"✅ Saved: {savepath}")

def plot_all_variables_combined(data_dict, savepath):
    fig, axes = plt.subplots(3, 1, figsize=(14, 14), sharex=True)

    # Panel 1: Lake Level
    ax = axes[0]
    for sc, df in data_dict.items():
        df_annual = df.resample("YE").mean()
        ax.plot(df_annual.index, df_annual["L_wb"],
                label=labels[sc], color=colors[sc], linewidth=2.5)
        add_uncertainty_band(ax, df_annual.index, df_annual["L_wb"], colors[sc])

    ax.axhline(1135, color="darkorange", linestyle=":", linewidth=2, alpha=0.7)
    ax.set_ylabel("Lake Level (m a.s.l.)", fontweight="bold")
    ax.set_title("(a) Water Level Projections", fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel 2: Lake Area
    ax = axes[1]
    for sc, df in data_dict.items():
        df_annual = df.resample("YE").mean()
        area = df_annual["A_wb"] / 1e6
        ax.plot(df_annual.index, area,
                label=labels[sc], color=colors[sc], linewidth=2.5)
        add_uncertainty_band(ax, df_annual.index, area, colors[sc])

    ax.set_ylabel("Lake Area (km²)", fontweight="bold")
    ax.set_title("(b) Surface Area Projections", fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(66700, 67200)

    # Panel 3: Net Balance
    ax = axes[2]
    for sc, df in data_dict.items():
        net = df["Net_mm/day"] if "Net_mm/day" in df.columns else (df["Q_in"] - df["Q_out"]) * 1000
        net_annual = net.resample("YE").mean()
        ax.plot(net_annual.index, net_annual.values,
                label=labels[sc], color=colors[sc], linewidth=2.5)

    ax.axhline(0, color="black", linewidth=1, alpha=0.5)
    ax.set_ylabel("Net Balance (mm/day)", fontweight="bold")
    ax.set_xlabel("Year", fontweight="bold")
    ax.set_title("(c) Net Water Balance", fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(savepath, dpi=300, bbox_inches="tight")
    plt.show()
    print(f"✅ Saved: {savepath}")

# --------------------------------------------------------------
# 5. MAIN DRIVER
# --------------------------------------------------------------
def main():
    data = load_projection_data(OUT_DIR, SCENARIOS)
    if not data:
        print("⚠ No data loaded.")
        return

    plot_lake_level(data, os.path.join(FIG_DIR, "Lake_Level_Projections_Fixed.png"))
    plot_lake_area(data, os.path.join(FIG_DIR, "Lake_Area_Projections_Fixed.png"))
    plot_net_water_balance(data, os.path.join(FIG_DIR, "Net_Water_Balance_Projections_Fixed.png"))
    plot_all_variables_combined(data, os.path.join(FIG_DIR, "Combined_Projections_Fixed.png"))

    print(f"\n✅ All figures saved in: {FIG_DIR}")

# --------------------------------------------------------------
# 6. RUN SCRIPT
# --------------------------------------------------------------
if __name__ == "__main__":
    main()























