#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-------------------------------------
Lake Victoria Water Balance Model 
-------------------------------------
    - Read in precipitation data and dividing into Plake and Pbasin --> 1 per day for each year
    - Convert to 1D P_lake
    - Read in evaporation data, reprojecting to own grid --> 1 per day for 1 year, copied for each year
    - Convert to 1D E_lake
    - Read in outflow data --> 1 per day for each year 
    - Convert to 1D Qout
    - Calculate runoff per grid cell using Curve Number method --> add citations  
    - Convert to 1D Qin 
    - Calculate WB

Created on Mon Aug 19 10:28:27 2024

@author: Vincent Ogembo vincent.ogembo@vub.be

Adapted and modified from R. Pietrousti et al. 2024 Python model

Environment: geo_env 

Notes:
    - check structure of scripts and sub-scripts
    - the precip remapping was done with remapcon2 (on supercomputer) vs. the evaporation with bilinear interpolation (here with cdo-python)
    check which one is better and why remapcon2 introduces negative precip values 
    - is basin evaporation taken into account? (I dont think so, read theory of CN to understand what is and isn't taken into account and if CN=100 for all water bodies in basin makes sense or not)
    - insert possibility to choose A_lake used to divide Qin and Qout, evaluate sensitivity to this 
    - make loop to tune CN : figure out how to put this whole model in a loop and tune to observed lake levels -> maybe not necessary anymore
    - make it possible to modify Ppn if necessary to correct model (a flag before the creation of the 1D timeseries)
    - check how CRS and rio.clip are used and if this is correct
    - ext: persiann obs nan data fill with climato

Notes resolved: 
    - make a check early in code that checks ppn files are in order time,lat,lon --> check if this creates inconsistency in matlab v. python run (it does, matlab wants lon,lat=r,c then flipud, Python xarray to numpy array wants lat,lon then flipud) 
    --> RESOLVED. Maybe make the error in Ppn file stop the code instead of just giving a warning message? 
"""

#%%
#=============#
#== IMPORTS ==#
#=============#

# basics
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import sys, os , glob, gc
import pandas as pd
import rioxarray
from osgeo import gdal
from scipy.optimize import curve_fit
import seaborn as sns 
import pandas as pd
import rasterio
import matplotlib.animation as animation

# For vector data
import regionmask

# keep this - used it to reproject evap
# python-cdo  
#from cdo import *
#cdo=Cdo()
#%%

#=========================================================#
#== INITIALISE FILEPATHS, PHYS CONSTANTS AND GEOMETRY ====#
#=========================================================#

# append path to call other scripts from here
WBM_path = os.path.dirname(__file__) # "C:\Users\VO000003\OneDrive - Vrije Universiteit Brussel\Ogembo_LVictoria_IWBM\lakevic-eea-wbm\WBM_model.py"
sys.path.append(WBM_path)

from WBM_settings import * # imports all variables - put all user defined settings and paths and flags here (?) like a namelist 
import WBM_inicon as inicon # initialise physical constants - e.g. print(inicon.Lvap)
import WBM_inigeom as inigeom # lake victoria boundaries, size of a grid cell and resolution, shapefiles - e.g. print(inigeom.res_m, inigeom.A_cell)
from WBM_myfunctions import compare_lake_areas, check_zeroarray, check_valuesarray, check_dimorders, check_punits, fig_showsave, update_fign # functions I defined 


# # For raster data - check this, delete if not necessary
# if run_where == 0 :
#     from osgeo import gdal # local computer
# if run_where == 1 :
#     import gdal # for HPC 


# Start message from settings file
print(start_message_1)
print(start_message_2)

#%% read in geo data / read in WB terms data 
print('...reading in data')

#=========================#
#== READ WBM TERMS DATA ==#
#=========================#

# Precipitation 
#=========================#
if run_type == 0:
    var = 'precipitation'
if run_type == 1 or run_type == 2:
    var = 'pr' #SOFT CODE THIS
with xr.open_dataset(filepath_precip, decode_coords="all") as ds:
    print('precipitation data')
    print(str(list(ds.keys())))
    print(str(list(ds.dims)))
    ds_dims_precip = list(ds.dims) # new: time, lat, lon (reordered, WBM is made to work for this order)   # old: time,lon, lat
    ds_varnames = list(ds.keys()) # get names of variables precipitation
    time_precip = np.array(ds.get('time'))
    lats_precip = np.array(ds.get('lat'))
    lons_precip = np.array(ds.get('lon'))
    precip_raw = ds[str(var)].sel(time=slice(startDATE, endDATE))  # slice to modelling timeperiod
    precip_units = precip_raw.units
    precip_raw.rio.write_crs("epsg:4326", inplace=True) # \\\\ see if this should be done here or not and that CRS is correct !!\\\\
    check_dimorders(ds)
    precip_raw = check_punits(precip_raw) # this function modifies ppn, check it is ok


# Evaporation (Latent Heat Flux)
#=========================#
# Cut and remapped to own grid -  using cdo-python, different remapping algorithms are possible: see https://stackoverflow.com/questions/61806343/regrid-netcdf-file-in-python
    #remapbic : bicubic interpolation
    #remapbil : bilinear interpolation
    #remapnn : nearest neighbour interpolation
    #remapcon : first order conservative remapping
    #remapcon2 : 2nd order conservative remapping
#=========================#

# cdo.remapbil(filepath_grid, input=filepath_evap, output=filepath_evap_remap) # the remapping done with bilinear interpolation 

var = 'ALHFL_S' 
with xr.open_dataset(filepath_evap_remap, decode_coords="all") as ds: # open the remapped file
    print('evaporation COSMO-CLM data')
    print(str(list(ds.keys())))
    print(str(list(ds.dims)))
    ds_dims_evap = list(ds.dims) # time,lon, lat ---> check this is OK 
    ds_varnames = list(ds.keys()) # get names of variables
    time_evap = np.array(ds.get('time'))
    lats_evap = np.array(ds.get('lat'))
    lons_evap = np.array(ds.get('lon'))
    evap_raw = ds[str(var)] # order: time, y, x
    evap_raw.rio.write_crs("epsg:4326", inplace=True) # \\\\ see if this should be done here or not and that CRS is correct \\\\
    check_dimorders(ds)
    
# Outflow multi-source (m^3 /day)
#=========================#
outflow_raw = pd.read_csv(filepath_outflow)
outflow = outflow_raw.copy()
outflow.columns = ['date', 'outflow']
outflow['date'] = pd.to_datetime(outflow['date'])
outflow = outflow.set_index(['date'])

# Observed lake levels 
#=========================#
df = pd.read_csv(filepath_lakelevels_hist)
df['date'] = pd.to_datetime(df['date'], dayfirst=True)
lakelevels = df.set_index(['date'])

#===================#
#== READ GEO DATA ==# 
#===================#

lake_shp = inigeom.lake_shp
basin_shp = inigeom.basin_shp 

# Make lake and basin masks - I moved this here because it was giving problems in the inigeom file, see if better to truncate lat/lon values in Ppn xarray/get higher tolerance level for masking so that I can move this to inigeom script
#=========================#
rmask_lake = regionmask.mask_geopandas(lake_shp, lons_precip, lats_precip) + 1       # only lake set = 1
rmask_basinlake = regionmask.mask_geopandas(basin_shp, lons_precip, lats_precip) + 1 # lake+ basin set = 1
rmask_basin = rmask_basinlake * np.where(np.isnan(rmask_lake),1,np.nan) # only basin set = 1


#%% Precipitation
print('...manipulating precipitation')

#=====================#
#== 1) MANIP PRECIP ==#
#=====================#
# Convert units and separate precip over lake and precip over basin over modelling time-period 

if flag_plotprecip == 1:
    # --- Test --- 
    precip_raw.mean('time').plot()
    plt.title('P_mean mm/day')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)

# Select to modelling period and convert from mm/day (kg/m2/day) to m/day (1000 kg/m2/day)
precip = precip_raw * 1e-3

# Clear some memory
del precip_raw 
gc.collect()

if flag_plotprecip == 1:
    # --- Test --- 
    precip.mean('time').plot()
    plt.title('P_mean m/day')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)

# Check the dates are all there and there are no negative numbers 
if list(set(np.array(DATEs)) - set(np.array(precip['time']))): 
    print("model dates and precip (sliced) dates do not match")
if np.any(precip < 0): 
    print("there are some negative values in your precipitation input file \n ... setting them to 0")
    precip = precip.where(precip>0, 0) #0 or neg are turned to 0
if np.any(precip != precip): 
    print("there are some Nan values in your precipitation input file \n ... go check them")

# Mask : Precipitation over the lake (using regionmask)     
precip_lake = precip.where(rmask_lake == 1 )

# Mask: Precipitation over the basin (regionmask)
precip_basinlake = precip.where(rmask_basinlake == 1 )
precip_basin = precip.where(rmask_basin == 1 )

if flag_plotprecip == 1:
    # --- Test --- 
    rmask_lake.plot()
    plt.title('lake mask (regionmask)')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    
    # --- Test --- 
    rmask_basinlake.plot()
    plt.title('basinlake mask (regionmask)')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    # --- Test --- 
    rmask_basin.plot()
    plt.title('basin mask (regionmask)')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    
    # --- Test --- 
    precip_lake[0].plot() # .transpose() not necessary if dimensions are reordered to time,lat,lon
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    # --- Test --- 
    precip_lake.mean('time').plot() 
    plt.title('mean precip lake')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    # --- Test --- 
    precip_basin[6].plot()
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    # --- Test --- 
    precip_basin.mean('time').plot()
    plt.title('mean precip basin')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    # --- Test --- 
    precip_basinlake[0].plot()
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    # --- Test --- 
    precip_basinlake.mean('time').plot()
    plt.title('mean precip basinlake')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)

# Check masking is ok (make this more foolproof)
print('number of lake pixels {}'.format((~np.isnan(rmask_lake)).sum().values))
print('number of basin+lake pixels {}'.format( (~np.isnan(rmask_basinlake)).sum().values)  )
print('number of basin pixels {}'.format( (~np.isnan(rmask_basin)).sum().values)  )
if (~np.isnan(precip_lake[0])).sum().values != 1298: 
    print("Your masked P_lake might not have the right number of lake pixels on all days")
if (~np.isnan(precip_basinlake[0])).sum().values != 4934: 
    print("Your masked basinlake might not have the right number of pixels on all days")
if (~np.isnan(precip_basin[0])).sum().values != 3637: 
    print("Your masked P_basin might not have the right number of pixels on all days")

  

# /////////// Can insert modifications to P_lake or P_basin here //////////// 

#=================#
#== 1D: P_lake ===# # xarray dataarray
#=================#

# Get 1D timeseries : P_lake

#P_wb = precip_lake.mean('lat').mean('lon') # xarray dataarray ---> Incorrect way of taking mean, overestimates P_lake 
P_wb = precip_lake.mean(dim=('lat','lon'), skipna=True) # ---> I think this is more correct way of taking spatial mean, mean P_lake becomes about 126 mm/mo (for period 1993-2014) which is approx what Inne had, skipna is True by default so not really necessary to specify
# --- Test --- 
P_wb.plot()
plt.title('P_wb [m/d]')
fig_showsave(plt, flag_savefig, fig_path, fig_n)
fig_n = update_fign(flag_savefig, fig_n)

# to get time: np.array(P_wb['time'])
# to get variables: np.array(P_wb) or P_wb.values

# Clear memory
del precip_basinlake , precip_basin , precip_lake
gc.collect()  

#%% Evaporation
print('...manipulating evaporation')
#=====================#
#== 2) MANIP EVAP ====# 
#=====================#
# Convert from W m-2 to mm/day and from negative to positive 
# Repeat climatology to fill modelling time-period

if flag_plotevap == 1:
    # --- Test --- 
    #evap_raw[0].plot() # 366 days (2018 was leap year, repeat the daily value for each E term in WBM based on calendar day!)
    evap_raw.mean('time').plot() 
    plt.title('evap raw mean W m-2')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)

# Convert from W m-2 to mm/day (kg m-2 day-1) and from neg to pos
evap_conv = - evap_raw / inicon.Lvap * inicon.sec_per_day

if flag_plotevap == 1:
    # --- Test --- 
    evap_conv.mean('time').plot()
    plt.title('evap raw mean mm/day (pos)')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)

# Convert from mm/day to m/day
evap_conv = evap_conv * 1e-3

if flag_plotevap == 1:
    # --- Test --- 
    evap_conv.mean('time').plot()
    plt.title('evap raw mean m/day')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    # --- Test --- 
    evap_conv[0].plot() # 366 days (2018 was leap year, repeat the daily value for each E term in WBM)
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)

# Mask: evaporation over lake 
evap_lake = evap_conv * (rmask_lake.values) # \\ CHECK THIS CLIPPING !! \\\ IT WORKS BUT WHY??

if flag_plotevap == 1:
    # --- Test --- 
    evap_lake[0].plot()
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)

print('number of lake evap pixels {}'.format( (~np.isnan(evap_lake[0])).sum().values)  )
if (~np.isnan(evap_lake[0])).sum().values != 1298: 
    print("Your masked E_lake might not have the right number of lake pixels on all days")
  
#============#
#== 1D: E ===#   # numpy array 
#============#

# Get 1D timeseries : turn 1D for one year 

#E_mean_year = evap_lake.mean('lat').mean('lon') 
E_mean_year = evap_lake.mean(dim=('lat','lon'), skipna=True) 
# --- Test --- 
E_mean_year.plot()
plt.title('E_wb')
fig_showsave(plt, flag_savefig, fig_path, fig_n)
fig_n = update_fign(flag_savefig, fig_n)

# Numpy method of getting E_lake for all years
# Slicing and hard-coding index of Feb 29th (couldn't find a way of soft-coding that day's index)
# See alternative method using for loop and xarray dates in extrascripts

if evap_climatology:
    j = 0 
    E_lake = []
    for i in range(len(np.unique(DATEs.year))):
        year = np.unique(DATEs.year)[i]
        year_length = sum(DATEs.year == year)
        start_slice = j
        j = j + year_length
        end_slice = j-1
        if year_length == 366: 
            #df[start_slice:end_slice, 'E_lake'] = E_mean_year.values
            E_slice = E_mean_year.values
        elif year_length == 365:
            #df[start_slice:end_slice, 'E_lake'] = E_mean_year.drop_sel(time="28-02-2008", axis=time) # doesn't work ! 
            #df[start_slice:end_slice, 'E_lake'] = E_mean_year.values[np.r_[0:59,60:366]] # get rid of Feb 29th, index 59, doenst work   
            E_slice = E_mean_year.values[np.r_[0:59,60:366]]
        else : 
            print('**ERROR** in length of years ')
        E_lake.extend(E_slice.flatten())
else:
    E_lake = E_mean_year
   
# \\\\\ Add a check that length of E is the same as modelling timeperiod \\\\

# Get 1D timeseries as numpy array 

E_wb = np.array(E_lake)
# --- Test --- 
plt.plot(E_wb)
plt.title('E_wb')
fig_showsave(plt, flag_savefig, fig_path, fig_n)
fig_n = update_fign(flag_savefig, fig_n)


# Clear memory 
del evap_raw , evap_lake , evap_conv
gc.collect()


#%% Inflow CN

#=====================#
#== 3) CALC INFLOW ===# 
#=====================#
# Determine CN pixel values of grid based on land cover and hydrologic soil class 
# USDA curve number method: Chapter 10, https://www.nrcs.usda.gov/wps/portal/nrcs/detailfull/national/water/manage/hydrology/?cid=stelprdb1043063 
# Natural Resources Conservation Service (NRCS) method of estimating direct runoff from storm rainfall


# Read map of soil types
dataset = gdal.Open(filepath_soilclass_map, gdal.GA_ReadOnly)
soilclass_map = band = dataset.GetRasterBand(1).ReadAsArray().astype('int64') # numpy array

# Read hydrologic soil classes 
soilclass_hydro = np.loadtxt(filepath_soilclass_txt)

# Read map of land cover
dataset = gdal.Open(filepath_landcover_map, gdal.GA_ReadOnly)
landcover_map = dataset.GetRasterBand(1).ReadAsArray().astype('int64') # numpy array

# Read possible CN values --> cite source 
CN_values = np.loadtxt(filepath_CN_values_txt)  

# /////////// CAN TUNE CN VALUES HERE, MAKE EXTERNAL LOOP //////////// 

#==================#
#== MAKE CN MAP ===#  
#==================#
print('...making curve number map')
# Determine CN value per pixel based on soil hydrological class and land use (under standard moisture conditions, CN-II)

CN_map = np.zeros((len(precip['lat']), len(precip['lon'])), dtype=np.int64) # initialize array
soil_type = np.zeros((len(precip['lat']), len(precip['lon'])), dtype=np.int64) # initialize array
for i in range(len(precip['lat'])):
    for j in range(len(precip['lon'])):
        # determine hydrological soil type per pixel
        soil_type[i,j] = soilclass_hydro[soilclass_map[i,j] - 1] # check the minus one! 
        
        # if water body CN = 100 so then S (max soil retention) = 0, all of it becomes runoff
        if landcover_map[i,j] == 8 or soil_type[i,j] == 0:
            CN_map[i,j] = 100 # in old code set to 100 but was 0 in calculations I guess? Or should it be 100? 
        else: 
            #find CN value. this also depends on antecedent moisture condition (see settings file), default AMC is 2 (where?? in paper AMC=5)
            CN_map[i,j] = CN_values[landcover_map[i,j] - 1, soil_type[i,j] - 1] # check this ! I reduced index by 1 because of Python v. MATLAB indexing

if flag_plotinflow == 1:
    # --- Test --- 
    cmap = plt.get_cmap('viridis', 10)   # discrete colors
    cax = plt.imshow(CN_map, cmap = cmap)
    plt.colorbar(cax, orientation='vertical')
    plt.title('CN map, max {:.0f}, mean {:.0f} \n mean without 100 : {:.0f}'.format(np.nanmax(CN_map), np.nanmean(CN_map),  CN_map[CN_map != 100].mean()))
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)


# Inflow: Antecedent moisture
#==================#
#== SOLVE INFLOW ==# 
#==================#

if flag_plotinflow == 1:
    # Check: how to read precip correctly into numpy array (flip upside down if dims are time,lat,lon)
    precip_test = np.array(precip.mean('time'))     # the same as .values 
    precip_test = np.flipud(precip_test)            # flipud
    # --- Test --- 
    cax = plt.imshow(precip_test)                   # m/day
    plt.title('P mean m/day as array (to check spatial pattern)')
    plt.colorbar(cax, orientation='vertical')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)

# -------------------------------------------------------
# 1) Initialise runoff and antecedent moisture 3D arrays
# -------------------------------------------------------
Q_map = np.zeros((len(precip['time']), len(precip['lat']), len(precip['lon'])))     # numpy array 3D, runoff per pixel
AM_map = np.zeros((len(precip['time']), len(precip['lat']), len(precip['lon'])))    # numpy array 3D, antecedent moisture condition per pixel

# Check they are only zeros and there are no NaN 
check_zeroarray(Q_map, 'runoff')
check_zeroarray(AM_map, 'runoff')


# -------------------------------------------------------
# 2) Set the first 5 days of antecedent soil moisture to the initial AMC value
# -------------------------------------------------------
AM_map[0:amc_days] = amc_initialvalue

# mean AMC 0.0112 --> in Matlab this seems to be 0.0145, masking out the lake and the non-basin, here in Python seems to be 0.0167 \\ CHECK THIS \\

# Check initialisation is as desired, fxn: array to check, name of variable, desired value
check_valuesarray(AM_map[0:amc_days], 'antecedent moisture', amc_initialvalue)

if flag_plotinflow == 1:
    # --- Test ---                                                  
    cax = plt.imshow(AM_map[0])                                     
    plt.title('Antecedent moisture day 1')
    plt.colorbar(cax, orientation='vertical')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)


# -------------------------------------------------------
# 3) Initialize empty data arrays of time-dependent curve numbers (modified by AMC), 
# soil water retention, and runoff per pixel
# -------------------------------------------------------
CN_AMC_da = np.zeros((len(precip['time']), len(precip['lat']), len(precip['lon']))) # numpy array 3D,curve number modified by AMC
S_da = np.zeros((len(precip['time']), len(precip['lat']), len(precip['lon'])))      # numpy array 3D, max soil moisture retention


# /////////// I FLIP HERE //////////// 

print('...calculating antecedent moisture')
# -------------------------------------------------------
# 4) Determine antecedent soil moisure for whole time period
# soil moisture (AMC) = the sum of the Ppn of the previous 5 days (P_5day)
# -------------------------------------------------------
for t in range(amc_days-1, len(DATEs)):                          # from 5 (6th item) to 8035-1 (last item)
    if t > amc_days-1:                                           # e.g. t = 5 (6th day)
        cumprecip = precip.isel(time=slice(t-amc_days,t))        # cumprecip, shape 5,130,130: precipitation in previous 5 days - e.g. from 0 to 4 (5 days)
        cummoisture = cumprecip.sum('time').values[::-1,:]        # cummoisture, shape 130,130: sum of the precip in the previous 5 days flipud on a 2d array flips along row axis, understand how to specify re 3d array                                                      # note. if you use precip_basin, becomes 0 outside of basin                                                                
        AM_map[t] = AM_map[t] + cummoisture                      # map of antecedent moisture, 3D [m.w.e.]

if flag_plotinflow == 1:        
    # --- Test --- 
    cax = plt.imshow(np.mean(AM_map, axis=0))                       # mean of this mean map = 0.0167 [m.w.e.] = 16.7 mm, including whole domain and lake -> check over only basin  
    plt.title('Antecedent moisture mean m.w.e.')
    plt.colorbar(cax, orientation='vertical')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    # --- Test --- 
    cax = plt.imshow(cummoisture)                                   # mean value of last cummoisture = 0.0163 m 
    plt.title('cumulative moisture day {} m.w.e'.format(t+1))
    plt.colorbar(cax, orientation='vertical')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    # calc mean AM in basin and look at basin mask on CN 
    # --- Test --- 
    AM_basin = np.mean(AM_map,axis=0) * np.flipud(rmask_basinlake.values) 
    plt.imshow(AM_basin)
    plt.title('mean AM basinlake {:.6f}'.format(np.nanmean(AM_basin)))
    plt.colorbar(orientation='vertical')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    # --- Test --- 
    AM_basin = np.mean(AM_map,axis=0) * np.flipud(rmask_basin.values) 
    plt.imshow(AM_basin)
    plt.title('mean AM basin {:.6f}'.format(np.nanmean(AM_basin)))  # 0.016285 m mean AM in basin
    plt.colorbar(orientation='vertical')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    # --- Test --- 
    cmap = plt.get_cmap('viridis', 10)   # discrete colors
    cax = plt.imshow(CN_map * np.flipud(rmask_basinlake.values), cmap = cmap)  
    plt.colorbar(cax, orientation='vertical')
    plt.title('CN map masked basinlake') 
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    # --- Test --- 
    cmap = plt.get_cmap('viridis', 10)   # discrete colors
    cax = plt.imshow(CN_map * np.flipud(rmask_basin.values), cmap = cmap) 
    plt.colorbar(cax, orientation='vertical')
    plt.title('CN map maskedbasin ')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)  # --> outline of lake doesn't correspond, careful because this will affect inflow on the lake... 
                # I should change the values of these pixels to something other than 100, like take their nearest neighbor value... 
                # also check about the smaller lakes being treated as 100% runoff 

# OPTIONAL :             
# Expand the lake buffer a bit, get index numbers of non-nan values, compare with CN map. If any of the CN in those indices
# are equal to 100 set them to nearest non-100 value (i.e. turn them into land pixels, update CN_map)

# dilation: https://stackoverflow.com/questions/29027249/create-buffer-zone-within-a-numpy-array
# replace value by closest value below a threshold: https://gis.stackexchange.com/questions/207700/nearest-numpy-array-element-whose-value-is-less-than-the-current-element 

# Clear memory 
del cumprecip, cummoisture
gc.collect()

#%% Apply AM on CN
print('...applying antecedent moisture on curve numbers')

# -------------------------------------------------------------------------------------------------------------------------
# 5) Apply antecedent moisture condition on curve number : dry day (AMI), normal day (AMII), wet day (AMIII)
            # (Descheemaeker et al 2008) for AMI, AMII, AMIII conditions
            # (Ponce and Hawkins, 1996, Eq. 15-16) for CNI and CNIII formulas 
            # units AM: m 
# -------------------------------------------------------------------------------------------------------------------------
CN_AMC_da = np.where(AM_map < 0.0125, (CN_map / (2.281 - 0.01281 * CN_map))  , CN_map) # condition (dry day), where true (CN-I), where false (CN-II)
CN_AMC_da = np.where(AM_map >  0.0275,  (CN_map / (0.427 + 0.00573 * CN_map)) , CN_AMC_da) # condition (wet day), where true (CN-III), where false (whatever it was before, CN-I or CN-II)

# Each grid cell has 3 possible CN values depending on AM conditions

# -------------------------------------------------------------------------------------------------------------------------
# 6) Calculate S (max soil water retention), note where water: CN = 100 and S = 0 --> max CN, less soil retention, it all becomes runoff 
# (so I need to be careful to mask out the lake, as we already count the P_lake). 
# Where S=0, Q=P -->  So in fact P_lake is not strictly necessary, the CN method could calculate it by itself
            # (USDA, 2004 Eq 10-13)
            # units S: mm
# -------------------------------------------------------------------------------------------------------------------------
S_da = (25400 / CN_AMC_da) - 254 
             

if flag_plotinflow == 1:
    # --- Test --- 
    plt.set_cmap('viridis')
    cax = plt.imshow(CN_map) 
    plt.title('original CN map')
    plt.colorbar(cax, orientation='vertical')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    
    # --- Test --- 
    cax = plt.imshow(np.nanmean(CN_AMC_da, axis=0))
    plt.title('time-dependent CN map mean')
    plt.colorbar(cax, orientation='vertical')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)

if flag_plotCNdiff == 1:    
    # --- Test --- 
    CN_AMC_meandiff = np.nanmean(CN_AMC_da, axis=0) - CN_map
    cax = plt.imshow( CN_AMC_meandiff , vmin=-18, vmax=18)
    plt.title('Difference CN_AMC - original CN') # --> understand better the CNs and how AMC changes them and explain well in thesis 
    plt.set_cmap('bwr')
    plt.colorbar(cax, orientation='vertical')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)           # --> CNs decrease over almost all of basin (i.e. S increases), they increase where there is most Ppn (S decreases there, makes sense I guess, the soil is saturated more often?)
    plt.set_cmap('viridis')
    
if flag_plotinflow == 1:    
    # --- Test --- 
    t_sel = 1
    cax = plt.imshow(CN_AMC_da[t_sel]) 
    plt.title('time-dependent CN map, day {}'.format(t_sel))
    plt.colorbar(cax, orientation='vertical')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    
    # --- Test --- 
    t_sel = 1
    cax = plt.imshow(S_da[t_sel]) 
    plt.title('max soil water retention S, day {} [mm]'.format(t_sel)) # Values of S look ok 
    plt.colorbar(cax, orientation='vertical')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    
    
    # --- Test --- 
    cax = plt.imshow(np.nanmean(S_da, axis=0)) 
    plt.title('max soil water retention S, mean [mm]')
    plt.colorbar(cax, orientation='vertical')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)


#%% Calc Q per grid cell: New version using whole precip and not precipbasinlake and masking afterwards : Version 2 
# THIS IS VERY SLOW, IMPROVE

print('...calculating runoff Q_map')
# -------------------------------------------------------
# 7) Calculate outflow Q per grid cell (source: USDA 2004, Eq. 10-11) --> check if all is working, order of magnitude of Qin now is good but seasonality is not convincing 
    # condition: where P (mm) > 0.2*S
    # where true : calc Q
    # where false : Q = 0
# -------------------------------------------------------

# could use precip_raw instead but need to remove neg vals
precip_arr_mm = precip.values[:,::-1,:] * 1e3   

# Clear memory
del precip
gc.collect()

if flag_plotflip == 1:
    # --- Test --- 
    cax = plt.imshow(np.nanmean(precip_arr_mm, axis=0)) 
    plt.title('P mean mm/day as array flipped [mm]')
    plt.colorbar(cax, orientation='vertical')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    
    # --- Test --- 
    cax = plt.imshow(np.nanmean(S_da, axis=0)) 
    plt.title('S mean mm/day as array [mm]')
    plt.colorbar(cax, orientation='vertical')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)


# Calc Q part 2
Q_map = np.where( ( (precip_arr_mm) > (S_da * 0.2) ),  #  CHECK THIS CONDITION AND FORMULA MAKE IT INTO A FOR LOOP MAYBE... !!! removed : (S_da != 0) as this would get rid of rivers also (if they show in CN map, so I need to mask out lake surface), removed & (precip_arr_mm_test != 0) as this doesn't help re the divide by zero
                 ( (precip_arr_mm - 0.2*S_da)**2 / (precip_arr_mm + 0.8*S_da)  ), # I get warning: invalid value encountered in true_divide, check this, a divide by 0 error (if P and S are both = 0) but should give a nan and there are no nan, also this would lead to condition=False
                 0)                             # Q in mm l.w.e./day = kg m-2 day-1  

# \\\ CHECK FOR NaNs HERE \\\
    
# Clear memory
del precip_arr_mm
gc.collect()
    

print('...converting units of runoff Q_map')
# -------------------------------------------------------
# 8) Convert Q in mm/day per grid cell in basin to lake level equivalent m/day
        # kg m-2 day-1 (Q_map) * m2 (A_cell) = kg day-1
        # kg day-1 * 0.001 m3 kg-1 water = m3 / day (Q_map_m3) per grid cell
        # Masked over basin only, removing lake and outside of basin
        # Sum over all basin cells (nansum) = total m3 entering lake/day
        # Divide by lake area m2 = m lake level eq.
        
                # note.check alternate possibilities for A_lake
                # note. made this more compact for code running better
# -------------------------------------------------------
Q_map_masked_m3 = Q_map * inigeom.A_cell \
    * 1e-3 \
    * np.flipud(rmask_basin.values)                      
Qin_m = np.nansum(Q_map_masked_m3, axis=(1,2)) / inigeom.A_lake                             


# Plots inflow 
if flag_plotinflow == 1:
    # --- Test --- 
    cax = plt.imshow(np.flipud(rmask_basin.values)) 
    plt.title('check mask')
    plt.colorbar(cax, orientation='vertical')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    # --- Test --- 
    cax = plt.imshow(Q_map[10]) 
    plt.title('Qmap mm/day test')
    plt.colorbar(cax, orientation='vertical')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    # --- Test --- 
    cax = plt.imshow(Q_map_masked_m3[10]) 
    plt.title('Qmap m3/day test')
    plt.colorbar(cax, orientation='vertical')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    # --- Test --- 
    cax = plt.imshow(np.nanmean(Q_map_masked_m3, axis=0)) # --> way more runoff in the water bodies (CN=100 all P becomes runoff)
    plt.title('Qmap m3/day mean (different scales)')
    plt.colorbar(cax, orientation='vertical')
    #c = plt.colorbar()
    plt.clim(0, 1e5) 
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
    # --- Test --- 
    cax = plt.imshow(np.nanmean(Q_map_masked_m3, axis=0)) 
    plt.title('Qmap m3/day mean (different scales)')
    plt.colorbar(cax, orientation='vertical')
    #c = plt.colorbar()
    plt.clim(0, 1e4) 
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)


#===============#
#== 1D: Q_in ===# 
#===============#

Qin_wb = Qin_m 
# 1D array

# --- Test --- 
plt.plot(Qin_wb)
plt.title('Qin_wb')
fig_showsave(plt, flag_savefig, fig_path, fig_n)
fig_n = update_fign(flag_savefig, fig_n)

# Clear memory
del Q_map_masked_m3 , Q_map, S_da, CN_AMC_da, AM_map
gc.collect()


#%% Calc Qout
print('...manipulating outflow')
#=====================#
#== 4) CALC OUTFLOW ==# 
#=====================#

if run_type == 0 and flag_obs_outflow == 0: # use multi-source outflow (not agreed curve) 
    # Cut to correct dates 
    outflow = outflow.loc[startDATE:endDATE] 
    
    # Check dates and Nan/negative values 
    if list(set(np.array(DATEs)) - set(np.array(outflow.index))): 
        print("model dates and outflow dates do not match")
    if np.any(outflow < 0) or np.any(outflow != outflow): 
        print("there are some negative or NaN values in your outflow \n ... please check them")
    
    
    # /////////// CAN CHOOSE LAKE AREA HERE (see inigeom) //////////// 
    
    #==============#
    #== 1D: Qout ==#   # dataframe 
    #==============#
    
    Qout_wb = outflow['outflow'] / inigeom.A_lake #try also A_lake_old // with A_lake mean = 0.001323 (higher), with A_lake_old mean = 0.001295 (lower), with A_shp mean = 0.001316 (somewhere inbetween) // difference about 1 mm I think? not a big deal
    
    # --- Test --- 
    plt.plot(Qout_wb)
    plt.title('Qout_wb')
    fig_showsave(plt, flag_savefig, fig_path, fig_n)
    fig_n = update_fign(flag_savefig, fig_n)
else:
    print('setting Qout to zero to calculate with agreed curve')
    Qout_wb = np.zeros(len(DATEs))

#==========================================#
#== EXTRA: COMPARE LAKE AREA ESTIMATES ====# 
#==========================================#

# Compare different A_lake estimates, this will affect Qin and Qout and differences in estimates suggest differences in how masking has been done
# See which one works best... Feed it two masked files so it can count the number of unmasked pixels and multiply by pixel area 

# compare_lake_areas(evap_lake[0], precip_lake[0]) # see function file to get information on different estimates and sources


#%% Calc LL
print('...calculating lake levels')
#=========================#
#== 5) CALC Lake Levels ==# 
#=========================#


# initialise empty lake level array 
L_wb = np.zeros(len(DATEs))

# Initialise first level in masl 
if run_type == 0: # OBS PPN, where I have lake levels
    L0 = lakelevels.loc[startDATE] 
    L_wb[0] = L0['water_level']
else: 
    lakelevels_slice = lakelevels.loc[lakelevels.index[0]:'1960-12-31'] 
    L0 = lakelevels_slice.mean()
    L_wb[0] = L0['water_level']

# Calculate lake levels time-stepping
for t in range(1,len(DATEs)):

    if run_type == 0 and flag_obs_outflow == 0: 
        # observational run, observational outflow  
        print('observed outflow being used to calculate lake levels')
        L_wb[t] = L_wb[t-1] - Qout_wb.values[t] + Qin_wb[t] - E_wb[t] + P_wb.values[t] # --> make these dtypes consistent 
    
    # For the test with the old NaN data
    # L_wb[t] = L_wb[t-1] - Qout_wb.values[t] + Qin_wb[t] - E_wb[t] + np.nan_to_num(P_wb.values)[t]

    else: 
        # Apply agreed curve formula each day to calculate Qout
        print('calculating agreed curve')
        L_insitu = L_wb[t-1] - 1123.319
        Qout_ac_cumecs = 66.3*((L_insitu - 7.96)**(2.01)) # formula from Vanderkelen et al 2018, from Sene 2000
        Qout_ac_cmd = Qout_ac_cumecs * inicon.sec_per_day  
        Qout_wb_ac = Qout_ac_cmd / inigeom.A_lake
        Qout_wb[t] = Qout_wb_ac
        if t == 1: 
            # fill first day
            Qout_wb[t-1] = Qout_wb[t]
        
        L_wb[t] = L_wb[t-1] - Qout_wb[t] + Qin_wb[t] - E_wb[t] + P_wb.values[t] # --> make these dtypes consistent 
         
        # V[t] = V[t-1] - Qout_wb[t] + Qin_wb[t] - E_wb[t] + P_wb.values[t] # make sure everything is in m3
        # from hypsograph read A and L as functions of V 
    
print('...done !')

#%% Plot the levels 

plt.plot(L_wb)
plt.title('{} \n v0{}r0{}, DeltaL = {:.03f} m ({:.3f} m/yr)'.format(run_name, ver_n, run_n, (L_wb[len(DATEs)-1] - L_wb[0]), (L_wb[len(DATEs)-1] - L_wb[0]) /(endYEAR - startYEAR +1) ))
fig_showsave(plt, flag_savefig, fig_path, fig_n)
fig_n = update_fign(flag_savefig, fig_n)

#%% Save the output

data = {'date':  DATEs,
        'L_wb': L_wb,
        'P_lake': P_wb.values,
        'E_lake': E_wb,# ['E_lake']
        'Q_in': Qin_wb,
        'Q_out': Qout_wb,
        }

df = pd.DataFrame(data)
df = df.set_index('date')
df.to_csv(os.path.join(out_path, 'WBM_run_{}_v0{}r0{}_{}_{}_m.csv'.format(run_name, ver_n, run_n, startYEAR, endYEAR)))

data = { 'date':  DATEs, # maybe delete this extra column?? or keep as a check?
        'L_wb': L_wb,
        'P_lake': P_wb.values * 1e3,
        'E_lake': E_wb  * 1e3, #['E_lake']
        'Q_in': Qin_wb  * 1e3,
        'Q_out': Qout_wb  * 1e3,
        }

df_mm = pd.DataFrame(data)
df_mm = df_mm.set_index('date') # why was this not necessary before the AC ouflow??
df_mm.to_csv(os.path.join(out_path, 'WBM_run_{}_v0{}r0{}_{}_{}_mm.csv'.format(run_name, ver_n, run_n, startYEAR, endYEAR)), index=True)

# v01
# ----------
# run1 --> Qout was overwritten by Qin, looked quite good, rising lake levels but not super dramatic
# run2 --> Qin is much too high, something is wrong in the inflow calculations, fix this (it was a unit problem, fixed)
# run3 --> falling lake levels, by 6 meters, Qin is much too low, check this, get it approx to the magnitude of Qout
# run4 --> falling lake levels, by 8 meters, Qin is much too low, and I lowered P_lake by changing how I took the daily mean (I think P_lake is good now, we just need to get Qin up)
# run5 --> much better!! I rewrote the Qin calculation making it more explicit, but still dry
# run6 --> the same as run5 but initialised levels correctly, -75 mm/r
# run7 --> test 1983-2020, -111 mm/yr
# run6.5 --> the same result as run6, I changed the way of masking but no numerical effect apparent. 

# v02 (regionmasking and NaN data) :
# ----------------------
# run 1 (with old NaN data reordered to be read in correctly as numpy array as well) --> weirdly the same results as with previous masking..
# different NaN runs, coherence with matlab in P_lake and E_lake (when mean taken in same way)

# v03 observational: 
# ----------------------
        # Plake and Elake spatial mean is now taken over all cells, not first x then y
        # the lake and basin masks are made with regionmask in main script, always check in plots that they work!
        # Elake climatology is now correct 
# run 1 --> good, smaller bias (4.5 mm/month = 48 mm/year). P_lake is around 126 mm (ok), Evap has fallen a bit to 122 mm because of different way of taking spatial mean. Qin needs to be fixed. Qout ok 
# run 2 1983-2020 --> good ! 

# v04 observational: 
# ----------------------
# new outflow, AC earlier (from 2006)

# v03 historical:
# run 1 ISIMIP3b_hist_GFDL-ESM4 --> hadn't converted mm/s to mm/day, now done! it dries
# v02 hist-nat:
# it wets ! 

# version numbering starts again in version made for HPC, from v01 and each run is a different input data
# ----------------------


#%% Plot LL with dates 

df['L_wb'].plot()
plt.title('{} \n v0{}r0{}, DeltaL = {:.03f} m ({:.3f} m/yr)'.format(run_name, ver_n, run_n, (L_wb[len(DATEs)-1] - L_wb[0]), (L_wb[len(DATEs)-1] - L_wb[0]) /(endYEAR - startYEAR +1) ))
if flag_savefig == 1:
    plt.savefig(os.path.join(fig_path,'LL_{}_{}_{}_v0{}r0{}_dates.png'.format(run_name, startYEAR, endYEAR, ver_n, run_n)),dpi=300)


#%% Plot LL with obs and modelled levels 

#lakelevels.plot()
fig,ax=plt.subplots()
df['L_wb'].plot(ax=ax,label='modelled')
lakelevels['water_level'].plot(ax=ax, label='observed')
plt.legend()
plt.title('{} \n v0{}r0{}, DeltaL = {:.03f} m ({:.3f} m/yr)'.format(run_name, ver_n, run_n, (L_wb[len(DATEs)-1] - L_wb[0]), (L_wb[len(DATEs)-1] - L_wb[0]) /(endYEAR - startYEAR +1) ))
if flag_savefig == 1:
    plt.savefig(os.path.join(fig_path,'LL_obs_{}_{}_{}_v0{}r0{}_dates.png'.format(run_name, startYEAR, endYEAR, ver_n, run_n)),dpi=300)




















#%% Calculate area from level 

#open depth-area curve

df_depth_area = pd.read_csv(filepath_depth_area)

depth = df['L_wb'] - inigeom.elev_lakebottom # check if these are reasonable 

depth.plot()


def calc_area_from_depth(depth, hypsograph):
    
    areas = []
    
    for i in range(len(depth)):
        idx_closest = (depth[i] - hypsograph['depth_m']).abs().argsort().iloc[0]
        area_closest = hypsograph['area_m2'].iloc[idx_closest]
        
        areas.append(area_closest)
        
    return areas 
        

#%%

areas = calc_area_from_depth(depth, df_depth_area)

df_output = df.copy()
df_output['d_wb'] = depth
df_output['A_wb'] = areas

#%%
# plot lake area calculated from model 

(df_output['A_wb']/1e6).plot()


# save df_output from modelled levels

#%%

# calc from observed

depth_obs = lakelevels['water_level'] - inigeom.elev_lakebottom
areas_obs = calc_area_from_depth(depth_obs, df_depth_area)

lakelevels['area'] = areas_obs

#%%

# plot lake area calculated from obs lake levels

# Create a larger figure
fig, ax = plt.subplots(figsize=(10, 6))  

# Plot modeled lake area (from water balance model)
(df_output['A_wb']/1e6).plot(ax=ax, label='Modeled Area', linestyle='-', color='blue')

# Plot observed lake area
(lakelevels['area']/1e6).plot(ax=ax, label='Observed Area', linestyle='-', color='red')

# Add title and labels
ax.set_title('Lake Victoria Area: Observed vs. Modeled', fontsize=18)
ax.set_xlabel('Date', fontsize=16)
ax.set_ylabel('Lake Area (Km²)', fontsize=16)

# Add legend
ax.legend()

# Show grid for better readability
ax.grid(True, linestyle='--', alpha=0.3)
plt.show()


# save lakelevel area from satellite-derived levels



#%%

# PLOT AREA PLOT AND LEVEL PLOT IN ONE FRAME

fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(12, 10), sharex=True) # Create a figure with two subplots (stacked vertically)

# ----------- PLOT 1: Lake Area (Top) -----------
ax1.plot(df_output.index, df_output['A_wb'] / 1e6, label='Modeled Area', linestyle='-', color='blue')
ax1.plot(lakelevels.index, lakelevels['area'] / 1e6, label='Observed Area', linestyle='-', color='red')

ax1.set_ylabel('Lake Area (Km²)', fontsize=16) # Formatting for the lake area plot
ax1.set_title('Lake Victoria: Observed vs. Modeled Lake Area and Levels', fontsize=16)
ax1.legend(loc='upper left', fontsize=12)
ax1.grid(True, linestyle='--', alpha=0.3)

# ----------- PLOT 2: Lake Level (Bottom) -----------
ax2.plot(df.index, df['L_wb'], label='Modeled Level', linestyle='-', color='green')
ax2.plot(lakelevels.index, lakelevels['water_level'], label='Observed Level', linestyle='-', color='purple')

ax2.set_xlabel('Date', fontsize=16)  # Formatting for the lake level plot
ax2.set_ylabel('Lake Level (m)', fontsize=16)
ax2.legend(loc='upper left', fontsize=12)
ax2.grid(True, linestyle='--', alpha=0.3)

plt.tight_layout() # Adjust layout for better spacing

plt.show()  # Show the plot


#%%

# Lake Area 1984-2023

import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, r2_score

# Filter data from 1984
start_date = '1984-01-01'
modeled_area = df_output.loc[start_date:]['A_wb'] / 1e6
observed_area = lakelevels.loc[start_date:]['area'] / 1e6

# Align time indices (important for fair metric comparison)
common_index = modeled_area.index.intersection(observed_area.index)
modeled_area = modeled_area.loc[common_index]
observed_area = observed_area.loc[common_index]

# Optional: Apply smoothing (comment out if not desired)
modeled_area_smooth = modeled_area.rolling(window=3, center=True).mean()
observed_area_smooth = observed_area.rolling(window=3, center=True).mean()

# Compute model performance metrics
r2 = r2_score(observed_area.dropna(), modeled_area.dropna())
rmse = mean_squared_error(observed_area.dropna(), modeled_area.dropna(), squared=False)

# Create a high-quality figure
plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

# Plot smoothed or original data
ax.plot(modeled_area_smooth, label='Modeled Area (LaVIWaB)', color='blue', linewidth=2)
ax.plot(observed_area_smooth, label='Observed Area', color='red', linewidth=1.8)

# Set focused y-limits
ax.set_ylim(65100, 67600)

# Labels and legend
ax.set_title('Lake Victoria Area: Observed vs. Modeled Using LaVIWaB Model (1984–2023)', fontsize=16)
ax.set_xlabel('Year', fontsize=14)
ax.set_ylabel('Lake Area (km²)', fontsize=14)
ax.tick_params(axis='both', labelsize=12)
ax.legend(loc='upper right', fontsize=12)

# Annotate with metrics
#metrics_text = (f'RMSE = {rmse:.3f}\n'
                #f'NSE = {nse:.3f}\n'
               # f'$R^2$ = {r2:.2f}')
#ax.text(0.02, 0.95, metrics_text, transform=ax.transAxes, fontsize=14,
#       verticalalignment='top', bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.6))

# Improve layout and save
plt.tight_layout()
plt.savefig('lake_victoria_area_vs_model_pub_ready.png', dpi=300, bbox_inches='tight')
plt.show()





#%%
# Lake Modelled Area  1984-2023

import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, r2_score

# Filter data from 1984
start_date = '1984-01-01'
modeled_area = df_output.loc[start_date:]['A_wb'] / 1e6
observed_area = lakelevels.loc[start_date:]['area'] / 1e6

# Align time indices (important for fair metric comparison)
common_index = modeled_area.index.intersection(observed_area.index)
modeled_area = modeled_area.loc[common_index]
observed_area = observed_area.loc[common_index]

# Optional: Apply smoothing (comment out if not desired)
modeled_area_smooth = modeled_area.rolling(window=3, center=True).mean()
observed_area_smooth = observed_area.rolling(window=3, center=True).mean()

# Compute model performance metrics
r2 = r2_score(observed_area.dropna(), modeled_area.dropna())
rmse = mean_squared_error(observed_area.dropna(), modeled_area.dropna(), squared=False)

# Create a high-quality figure
plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

# Plot smoothed or original data
ax.plot(modeled_area_smooth, label='Modeled Area (LaVIWaB)', color='blue', linewidth=2)
#ax.plot(observed_area_smooth, label='Observed Area', color='red', linewidth=1.8)

# Set focused y-limits
ax.set_ylim(66800, 67300)

# Labels and legend
ax.set_title('Lake Victoria Modelled Area (1984–2023) - LaVIWaB Model)', fontsize=16)
ax.set_xlabel('Year', fontsize=14)
ax.set_ylabel('Lake Area (km²)', fontsize=14)
ax.tick_params(axis='both', labelsize=12)
ax.legend(loc='upper right', fontsize=12)

# Annotate with metrics
#metrics_text = (f'RMSE = {rmse:.3f}\n'
                #f'NSE = {nse:.3f}\n'
               # f'$R^2$ = {r2:.2f}')
#ax.text(0.02, 0.95, metrics_text, transform=ax.transAxes, fontsize=14,
#       verticalalignment='top', bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.6))

# Improve layout and save
plt.tight_layout()
plt.savefig('lake_victoria_area_vs_model_pub_ready.png', dpi=300, bbox_inches='tight')
plt.show()







#%%
#%% ----------------------------------------------------------------------


#%% ----------------------------------------------------------------------
# Load Data
# Modeled + Observed lake levels/areas
# (Assumes df_output, df, and lakelevels are already loaded in workspace)

# Validation data from Wu et al. (2023)
df_wu = pd.read_csv(r"C:\DATA\Lake Extent csv 1993-2023\lakevic_area_wuetal_2023.csv")[['Date', 'Area_km2']]
df_wu['Date'] = pd.to_datetime(df_wu['Date'])
df_wu = df_wu.set_index('Date')

#%% ----------------------------------------------------------------------
# 1. Plot: Modeled vs Observed Lake Area
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

(df_output['A_wb'] / 1e6).plot(ax=ax, label='Modeled Area (LaVIWaB)', color='blue')
(lakelevels['area'] / 1e6).plot(ax=ax, label='Observed Area (Satellite-derived Levels)', color='red')
df_wu['Area_km2'].plot(ax=ax, label='Satellite Observed - Wu et al. (2023)', color='green', linestyle='--')

ax.set_title('Lake Victoria Area: Observed vs. Modeled', fontsize=18)
ax.set_xlabel('Date', fontsize=16)
ax.set_ylabel('Lake Area (km²)', fontsize=16)
ax.legend()
ax.grid(True, linestyle='--', alpha=0.3)
plt.show()


#%% ----------------------------------------------------------------------
# 2. Long-term Area Comparison (1984–2023)
start_date = '1984-01-01'
modeled_area = df_output.loc[start_date:]['A_wb'] / 1e6
observed_area = lakelevels.loc[start_date:]['area'] / 1e6
wu_area = df_wu.loc[start_date:]['Area_km2']

# Align indices for fair metrics
common_index = modeled_area.index.intersection(observed_area.index).intersection(wu_area.index)
modeled_area = modeled_area.loc[common_index]
observed_area = observed_area.loc[common_index]
wu_area = wu_area.loc[common_index]

# Smooth (optional)
modeled_area_smooth = modeled_area.rolling(window=3, center=True).mean()
#observed_area_smooth = observed_area.rolling(window=3, center=True).mean()
wu_area_smooth = wu_area.rolling(window=3, center=True).mean()

# Metrics
r2 = r2_score(observed_area.dropna(), modeled_area.dropna())
rmse = mean_squared_error(observed_area.dropna(), modeled_area.dropna(), squared=False)
# NSE defined manually if needed:
def nse(obs, sim):
    return 1 - np.sum((obs - sim)**2) / np.sum((obs - np.mean(obs))**2)
nse_val = nse(observed_area.dropna(), modeled_area.dropna())

# Plot
plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

ax.plot(modeled_area_smooth, label='Modeled Area (LaVIWaB)', color='blue', linewidth=2)
#ax.plot(observed_area_smooth, label='Observed Area (Semi-Observationally derived)', color='red', linewidth=1.8)
ax.plot(wu_area_smooth, label='Satellite Observed - Wu et al. (2023)', color='green', linestyle='--', linewidth=1.8)

ax.set_ylim(65950, 67600)
ax.set_title('Lake Victoria Area: Observed vs. Modeled (1984–2023)', fontsize=16)
ax.set_xlabel('Year', fontsize=14)
ax.set_ylabel('Lake Area (km²)', fontsize=14)
ax.tick_params(axis='both', labelsize=12)
ax.legend(loc='upper right', fontsize=12)

#metrics_text = f'RMSE = {rmse:.2f}\nNSE = {nse_val:.2f}\n$R^2$ = {r2:.2f}'
#ax.text(0.02, 0.95, metrics_text, transform=ax.transAxes, fontsize=14,
#        verticalalignment='top', bbox=dict(boxstyle='round,pad=0.3',
#                                           facecolor='white', alpha=0.6))

plt.tight_layout()
plt.savefig('lake_victoria_area_vs_model_with_wu.png', dpi=300, bbox_inches='tight')
plt.show()

#%%


# --- 2. Validation
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score, mean_squared_error

# -----------------------
# Existing data preparation
# -----------------------
start_date = '1984-01-01'
modeled_area = df_output.loc[start_date:]['A_wb'] / 1e6
observed_area = lakelevels.loc[start_date:]['area'] / 1e6
wu_area = df_wu.loc[start_date:]['Area_km2']

# Align indices for fair metrics
common_index = modeled_area.index.intersection(observed_area.index).intersection(wu_area.index)
modeled_area = modeled_area.loc[common_index]
observed_area = observed_area.loc[common_index]
wu_area = wu_area.loc[common_index]

# Smooth (optional)
modeled_area_smooth = modeled_area.rolling(window=3, center=True).mean()
wu_area_smooth = wu_area.rolling(window=3, center=True).mean()

# -----------------------
# Metrics
# -----------------------
r2 = r2_score(observed_area.dropna(), modeled_area.dropna())
rmse = mean_squared_error(observed_area.dropna(), modeled_area.dropna(), squared=False)

def nse(obs, sim):
    return 1 - np.sum((obs - sim)**2) / np.sum((obs - np.mean(obs))**2)
nse_val = nse(observed_area.dropna(), modeled_area.dropna())

# -----------------------
# Validation points data
# -----------------------
validation_data = pd.DataFrame({
    'Source': ['Vanderkelen et al, 2018', 'Dataverse Products', 'Copernicus Digital Elevation Model'],
    'lake_area_km2': [66867.0, 66793.0, 66829.0],
    'Year': [2018, 2015, 2011]
})
validation_data['Year'] = pd.to_datetime(validation_data['Year'], format='%Y')

# -----------------------
# Plot setup
# -----------------------
plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

ax.plot(modeled_area_smooth, label='Modeled Area (LaVIWaB)', color='blue', linewidth=2)
ax.plot(wu_area_smooth, label='Satellite Observed – Wu et al. (2023)', color='green', linestyle='--', linewidth=1.8)

# Add validation points
ax.scatter(validation_data['Year'], validation_data['lake_area_km2'],
           color='red', s=50, zorder=5, label='Independent Validation (World Basin Model data)')

# Annotate each validation point
for _, row in validation_data.iterrows():
    ax.text(row['Year'], row['lake_area_km2'] + 25, row['Source'],
            fontsize=9, ha='center', color='black')

# -----------------------
# Formatting
# -----------------------
ax.set_ylim(65950, 67600)
ax.set_title('Lake Victoria Area: Observed vs. Modeled', fontsize=16)
ax.set_xlabel('Year', fontsize=14)
ax.set_ylabel('Lake Area (km²)', fontsize=14)
ax.tick_params(axis='both', labelsize=12)
ax.legend(loc='upper right', fontsize=11)

# Optional metrics box
# metrics_text = f'RMSE = {rmse:.2f}\nNSE = {nse_val:.2f}\n$R^2$ = {r2:.2f}'
# ax.text(0.02, 0.95, metrics_text, transform=ax.transAxes, fontsize=13,
#         verticalalignment='top', bbox=dict(boxstyle='round,pad=0.3',
#                                           facecolor='white', alpha=0.6))

plt.tight_layout()
plt.savefig('lake_victoria_area_vs_model_with_validation_points.png', dpi=300, bbox_inches='tight')
plt.show()


#%% 3.#Metrics strictly between LaVIWaB Modeled Area and Wu et al. (2023) Satellite Observed ----------------------------------------------------------------------


from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# -----------------------
def nse(obs, sim):
    obs = np.asarray(obs); sim = np.asarray(sim)
    return 1 - np.sum((obs - sim)**2) / np.sum((obs - np.mean(obs))**2)

def print_metrics(obs, sim, label=''):
    mask = (~np.isnan(obs)) & (~np.isnan(sim))
    obs0, sim0 = obs[mask], sim[mask]
    rmse = mean_squared_error(obs0, sim0, squared=False)
    r2 = r2_score(obs0, sim0)
    nse_val = nse(obs0, sim0)
    print(f"{label} RMSE={rmse:.2f}, R2={r2:.3f}, NSE={nse_val:.3f}")

def quantile_map(obs, ref):
    """Bias correct obs to match ref distribution by empirical quantile mapping."""
    obs_vals = obs.dropna().values
    ref_vals = ref.dropna().values
    obs_sorted = np.sort(obs_vals)
    ref_sorted = np.sort(ref_vals)
    ranks = np.searchsorted(obs_sorted, obs_vals, side='left') / (len(obs_sorted)-1)
    mapped = np.interp(ranks, np.linspace(0,1,len(ref_sorted)), ref_sorted)
    s = pd.Series(index=obs.dropna().index, data=mapped)
    return obs.where(obs.isna(), s)

# -----------------------
# Example input (replace with your data)
# modeled_area = pd.Series(...)
# wu_area = pd.Series(...)
# -----------------------

# Align series
common_index = modeled_area.index.intersection(wu_area.index)
modeled = modeled_area.loc[common_index]
wu = wu_area.loc[common_index]

# -----------------------
# 1) Constant offset correction
# -----------------------
offset = modeled.mean() - wu.mean()
wu_const = wu + offset

# -----------------------
# 2) Affine (linear regression) correction
# -----------------------
lr = LinearRegression().fit(wu.values.reshape(-1,1), modeled.values)
a, b = lr.intercept_, lr.coef_[0]
wu_affine = pd.Series(lr.predict(wu.values.reshape(-1,1)), index=wu.index)

# -----------------------
# 3) Quantile mapping correction
# -----------------------
wu_qmap = quantile_map(wu, modeled)

# -----------------------
# Metrics
# -----------------------
print("=== Performance Metrics ===")
print_metrics(wu.values, modeled.values, 'Raw Wu')
print_metrics(wu_const.values, modeled.values, 'Constant offset')
print_metrics(wu_affine.values, modeled.values, 'Affine regression')
print_metrics(wu_qmap.values, modeled.values, 'Quantile mapping')

# -----------------------
# Plot
# -----------------------
plt.figure(figsize=(12,6), dpi=300)
plt.plot(modeled.index, modeled, label='Modeled (LaVIWaB)', color='blue', linewidth=2)
plt.plot(wu_const.index, wu_const, label='Wu et al. (2023) corrected (Offset)', color='red', linestyle='-.')
plt.plot(wu_affine.index, wu_affine, label='Wu et al. (2023) corrected (Affine)', color='orange', linestyle=':')
plt.plot(wu_qmap.index, wu_qmap, label='Wu et al. (2023) corrected (Quantile mapping)', color='purple', linestyle='-')
plt.legend()
plt.xlabel("Year")
plt.ylabel("Lake Area (km²)")
plt.title("Observed Area (Wu et al.) vs Modeled Area (LaVIWaB)")
plt.grid(True, alpha=0.3)
plt.show()




#%%

#  4.  Metrics - Observerd Offset vs Modelled


# -----------------------
def nse(obs, sim):
    obs = np.asarray(obs); sim = np.asarray(sim)
    return 1 - np.sum((obs - sim)**2) / np.sum((obs - np.mean(obs))**2)

def calc_metrics(obs, sim):
    """Return correlation, RMSE, R2, NSE"""
    mask = (~np.isnan(obs)) & (~np.isnan(sim))
    obs0, sim0 = obs[mask], sim[mask]
    corr = np.corrcoef(obs0, sim0)[0,1]
    rmse = mean_squared_error(obs0, sim0, squared=False)
    r2 = r2_score(obs0, sim0)
    nse_val = nse(obs0, sim0)
    return corr, rmse, r2, nse_val

# -----------------------
# Example input (replace with your data)
# modeled_area = pd.Series(...)
# wu_area = pd.Series(...)
# -----------------------

# Align series
common_index = modeled_area.index.intersection(wu_area.index)
modeled = modeled_area.loc[common_index]
wu = wu_area.loc[common_index]

# -----------------------
# Constant offset correction
# -----------------------
offset = modeled.mean() - wu.mean()
wu_const = wu + offset

# -----------------------
# Metrics: Wu (corrected offset) vs Modeled
# -----------------------
corr, rmse, r2, nse_val = calc_metrics(wu_const.values, modeled.values)

print("=== Performance Metrics (Wu offset vs Modeled) ===")
print(f"Correlation = {corr:.3f}")
print(f"RMSE        = {rmse:.2f}")
print(f"R²          = {r2:.3f}")
print(f"NSE         = {nse_val:.3f}")

# -----------------------
# Plot
# -----------------------
plt.figure(figsize=(12,6), dpi=300)
plt.plot(modeled.index, modeled, label='Modeled (LaVIWaB)', color='blue', linewidth=2)
plt.plot(wu_const.index, wu_const, label='Satellite Observed (Wu et al. (2023) corrected (Offset)', 
         color='red', linestyle='-.')

plt.legend()
plt.xlabel("Year")
plt.ylabel("Lake Area (km²)")
plt.title("Observed Area Wu et al. (Corrected by Offset) vs Modeled Area (LaVIWaB)")
plt.grid(True, alpha=0.3)

# Add metrics box on plot
# metrics_text = (f"Corr = {corr:.3f}\n"
#                 f"RMSE = {rmse:.2f}\n"
#                 f"$R^2$ = {r2:.3f}\n"
#                 f"NSE = {nse_val:.3f}")
# plt.text(0.02, 0.95, metrics_text, transform=plt.gca().transAxes,
#          fontsize=12, verticalalignment='top',
#          bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.6))

# plt.tight_layout()
# plt.show()



#%%

#   5.   ANNOMALLY PLOT

from sklearn.metrics import mean_squared_error, r2_score

# -----------------------
# Helper functions
# -----------------------
def nse(obs, sim):
    obs = np.asarray(obs); sim = np.asarray(sim)
    return 1 - np.sum((obs - sim)**2) / np.sum((obs - np.mean(obs))**2)

def calc_metrics(obs, sim):
    """Return correlation, RMSE, R2, NSE"""
    mask = (~np.isnan(obs)) & (~np.isnan(sim))
    obs0, sim0 = obs[mask], sim[mask]
    corr = np.corrcoef(obs0, sim0)[0,1]
    rmse = mean_squared_error(obs0, sim0, squared=False)
    r2 = r2_score(obs0, sim0)
    nse_val = nse(obs0, sim0)
    return corr, rmse, r2, nse_val

# -----------------------
# Example input (replace with your data)
# modeled_area = pd.Series(..., index=...)
# wu_area = pd.Series(..., index=...)
# -----------------------

# Align series
common_index = modeled_area.index.intersection(wu_area.index)
modeled = modeled_area.loc[common_index]
wu = wu_area.loc[common_index]

# -----------------------
# Constant offset correction
# -----------------------
offset = modeled.mean() - wu.mean()
wu_const = wu + offset

# -----------------------
# Metrics: Wu (corrected offset) vs Modeled
# -----------------------
corr, rmse, r2, nse_val = calc_metrics(wu_const.values, modeled.values)

print("=== Performance Metrics (Wu offset vs Modeled) ===")
print(f"Correlation = {corr:.3f}")
print(f"RMSE        = {rmse:.2f}")
print(f"R²          = {r2:.3f}")
print(f"NSE         = {nse_val:.3f}")

# -----------------------
# Anomalies (relative to each mean)
# -----------------------
modeled_anom = modeled - modeled.mean()
wu_anom = wu_const - wu_const.mean()

# -----------------------
# Plot anomalies
# -----------------------
plt.figure(figsize=(12,6), dpi=300)
plt.axhline(0, color='black', linewidth=1.2)  # centerline at 0
plt.plot(modeled_anom.index, modeled_anom, label='Modeled Anomaly (LaVIWaB)',
         color='blue', linewidth=2)
plt.plot(wu_anom.index, wu_anom, label='Satellite Observed - Offset Anomaly (Wu et al., 2023) ',
         color='red', linestyle='-.')

plt.legend()
plt.xlabel("Year")
plt.ylabel("Anomaly in Lake Area (km²)")
plt.title("Anomalies (Relative to Mean) of Wu Offset vs Modeled (LaVIWaB)")
plt.grid(True, alpha=0.3)

# Add metrics box
# metrics_text = (f"Corr = {corr:.3f}\n"
#                 f"RMSE = {rmse:.2f}\n"
#                 f"$R^2$ = {r2:.3f}\n"
#                 f"NSE = {nse_val:.3f}")
# plt.text(0.02, 0.95, metrics_text, transform=plt.gca().transAxes,
#          fontsize=12, verticalalignment='top',
#          bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.6))

# plt.tight_layout()
# plt.show()



#%%
#%%
#%%
#Lake Levels 1984-2023



start_date = '1984-01-01'
end_date = '2023-12-31'

# Filter dataframes to the date range
df_filtered = df.loc[(df.index >= start_date) & (df.index <= end_date)]
lakelevels_filtered = lakelevels.loc[(lakelevels.index >= start_date) & (lakelevels.index <= end_date)]

# Align modeled and observed data by their common dates within filtered range
common_index = df_filtered.index.intersection(lakelevels_filtered.index)
modeled = df_filtered.loc[common_index, 'L_wb']
observed = lakelevels_filtered.loc[common_index, 'water_level']

# Calculate metrics
rmse = np.sqrt(mean_squared_error(observed, modeled))

nse = 1 - np.sum((observed - modeled) ** 2) / np.sum((observed - np.mean(observed)) ** 2)

r2 = r2_score(observed, modeled)

# Plot
# Create a high-quality figure
fig, ax2 = plt.subplots(figsize=(10, 6), dpi=300)

ax2.plot(df_filtered.index, df_filtered['L_wb'], label='Modeled Level', color='green')
ax2.plot(lakelevels_filtered.index, lakelevels_filtered['water_level'], label='Observed Level', color='purple')

ax2.set_xlabel('Date', fontsize=14)
ax2.set_ylabel('Lake Level (masl)', fontsize=14)
ax2.legend(loc='lower right')
ax2.grid(True, linestyle='--', alpha=0.5)

# Add metrics text box
metrics_text = (f'RMSE = {rmse:.3f}\n'
                f'NSE = {nse:.3f}\n'
                f'R² = {r2:.3f}\n')
ax2.text(0.02, 0.95, metrics_text, transform=ax2.transAxes, fontsize=12,
         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

# Title for the whole figure
fig.suptitle('Lake Victoria Levels: Observed vs. Modeled (1984-2023)', fontsize=16)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.show()




#%%%


# CALCULATING LAKE SURFACE AREA ABOVE SPECIFIED DEPTH






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
bathymetry_tiff = "C:\DATA\Lake V Bathymentry\lake_bathymetry_UTM.tif"
lake_area = calculate_lake_area(bathymetry_tiff)

print(f"Calculated surface area of Lake Victoria: {lake_area:.2f} km²")



#%%


# Bathymetry and topography to make hypsograph level - area 

# Open bathymetry raster
basin_topography_tiff = "C:\DATA\Processed\Reprojected_Resampled_DEM.tif"



#%%
# 1. Load Bathymetry Data
file_path = "C:\DATA\Lake V Bathymentry\lake_bathymetry_UTM.tif"
with rasterio.open(file_path) as bathy:
    depth_data = bathy.read(1)  # Read the first band (depth values)
    transform = bathy.transform
    pixel_size = transform[0]  # Pixel size in meters (assumes square pixels)

# Replace no-data values with NaN
depth_data[depth_data == bathy.nodata] = np.nan


#%%

   
# 1b. Open topography data and merge with bathymetry 

bathymetry_tiff = "C:\DATA\Lake V Bathymentry\lake_bathymetry_UTM.tif"

# Open bathymetry raster

basin_topography_tiff = "C:\DATA\Processed\Reprojected_Resampled_DEM.tif"

# Open bathymetry and topography rasters
with rasterio.open(bathymetry_tiff) as bathy_src, rasterio.open(basin_topography_tiff) as topo_src:
    # Convert bathymetry and topography to float32 for NaN handling
    bathymetry_data = bathy_src.read(1).astype('float32')
    topography_data = topo_src.read(1).astype('float32')
    
    # Replace NoData with NaN
    if bathy_src.nodata is not None:
        bathymetry_data[bathymetry_data == bathy_src.nodata] = np.nan
    if topo_src.nodata is not None:
        topography_data[topography_data == topo_src.nodata] = np.nan
    
    # Turn zeros in topography (outside basin) into NaN
    topography_data[topography_data == 0] = np.nan

    # Resample bathymetry to match topography grid if shapes differ
    if bathymetry_data.shape != topography_data.shape:
        resampled_bathy = np.empty_like(topography_data)
        reproject(
            source=bathymetry_data,
            destination=resampled_bathy,
            src_transform=bathy_src.transform,
            src_crs=bathy_src.crs,
            dst_transform=topo_src.transform,
            dst_crs=topo_src.crs,
            resampling=Resampling.bilinear
        )
        bathymetry_data = resampled_bathy

# Combine bathymetry and topography
bath_zeros = np.nan_to_num(bathymetry_data, nan=0)  # keep bathymetry NaNs as 0
bath_topo = topography_data - bath_zeros

# Plot Topography - Bathymetry
fig, ax = plt.subplots(figsize=(10, 8))
plot = ax.imshow(bath_topo, cmap='terrain')
cbar = fig.colorbar(plot, ax=ax, shrink=0.4)
cbar.set_label("Elevation difference (m)")
ax.set_title("Topography - Bathymetry")
plt.show()

# Print minimum elevation
print(f"min elevation: {np.nanmin(bath_topo)}")


#%%


# 2. Define Depth Bins
bin_size = .01  # Bin thickness in meters
min_depth = np.nanmin(depth_data)  # Minimum depth
max_depth = np.nanmax(depth_data)  # Maximum depth
depth_bins = np.arange(np.floor(min_depth), np.ceil(max_depth) + bin_size, bin_size)


#%%


# # 3. Calculate Volumes for different depths
# pixel_area = pixel_size ** 2  # Area of one pixel in square meters
# volumes_at_depth = []
# areas_at_depth = []

# for depth in depth_bins:
#     # Mask pixels below the current depth
#     mask = (depth >= (np.nanmax(depth_data) - depth_data) )
#     # get area at current depth
#     area_at_depth = np.nansum(mask) * pixel_area  # Sum of areas at this depth (number of pixels * pixel area) m2
#     # get masked depth
#     masked_depth = np.where(mask, depth_data, np.nan)
#     # calculate volume as sum of depth, maxed out at the depth of water
#     max_depth = np.where(mask, np.minimum(masked_depth, depth), np.nan)
#     volume = np.nansum(max_depth)
#     # save output
#     volumes_at_depth.append(volume)
#     areas_at_depth.append(area_at_depth)


# #%%

# # 4. Plot Depth vs. Volume
# plt.figure(figsize=(10, 6))
# plt.plot( np.array(volumes_at_depth) / 1e6 , depth_bins, marker='o', linestyle='-', color='blue')
# plt.gca().invert_yaxis()  # Depth increases downward
# plt.title("Lake Victoria Depth-Volume Curve")
# plt.xlabel("Volume (km³)")
# plt.ylabel("Depth (m)")
# plt.grid()
# plt.show()

# #%%

# # 5. Depth vs. area

# plt.figure(figsize=(10, 6))
# plt.plot( np.array(areas_at_depth) / 1e6 , depth_bins, marker='o', linestyle='-', color='blue')
# plt.gca().invert_yaxis()  # Depth increases downward
# plt.title("Lake Victoria Depth-Area Curve")
# plt.xlabel("Area (km$^2$)")
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

# # make it into a function

# # get point where lake has maximum abslute depth
# max_index = np.unravel_index(np.nanargmax(bathymetry_data), bathymetry_data.shape)
# # Get the corresponding bath_topo value, ie baseline elevation at this point
# bath_topo_at_max_bathy = bath_topo[max_index]

# def calculate_areas_per_depth_bin(
#         depth_bins,
#         bath_topo, # bathymetry and topography together 
#         bath_topo_at_max_bathy = bath_topo_at_max_bathy,
#         pixel_area = pixel_size ** 2 # pixel_size has to be defined 
#         ):
    
#     volumes_at_depth = []
#     areas_at_depth = []

#     for depth in depth_bins:
#         # Mask pixels below the current depth
#         mask = (bath_topo <= bath_topo_at_max_bathy + depth )
#         # get area at current depth
#         area_at_depth = np.nansum(mask) * pixel_area  # Sum of areas at this depth (number of pixels * pixel area) m2
#         # get masked depth
#         masked_depth = np.where(mask, bath_topo - bath_topo_at_max_bathy , np.nan)
#         # calculate volume as sum of depth*area, maxed out at the depth of water
#         max_depth = np.where(mask, np.minimum(masked_depth, depth), np.nan)
#         volume = np.nansum(max_depth * pixel_area)
#         # save output
#         volumes_at_depth.append(volume)
#         areas_at_depth.append(area_at_depth)
        
        
#     data=np.stack([depth_bins, np.array(areas_at_depth), np.array(volumes_at_depth)]).T
    
#     df_area_depth_curve = pd.DataFrame(
#         data=data,
#         columns= ['depth_m','area_m2', 'vol_m3']
#         )
    
#     return df_area_depth_curve.set_index('depth_m')




# df_area_depth_curve = calculate_areas_per_depth_bin(depth_bins, bath_topo)

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
fig, ax1 = plt.subplots(figsize=(10, 6), dpi=300)

# Plot Lake Area (Left Y-Axis)
ax1.plot(lake_levels, df_area_depth_curve['area_m2'] / 1e6, label="Lake Area", color='b')
ax1.set_xlabel('Lake Levels (m.a.s.l)')
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
plt.title('Hypsography of Lake Victoria WB Model: Area & Volume vs Lake Levels', fontsize=14)

# Show plot
plt.show()


#%%

# LAKE VICTORIA PLAN VIEW 

import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# Path to your bathymetry GeoTIFF file
tif_file = "C:\DATA\Lake V Bathymentry\LakeVictoria_BathymetryGEE.tif"

# Open the GeoTIFF file
with rasterio.open(tif_file) as src:
    # Read the raster data
    bathymetry = src.read(1)  # Read the first band
    # Mask invalid data (e.g., NaN or no-data values)
    bathymetry = np.ma.masked_where(bathymetry == src.nodata, bathymetry)

    # Extract spatial metadata
    extent = (src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top)

# Plot the bathymetry
plt.figure(figsize=(12, 10), dpi=500)
plt.imshow(
    bathymetry,
    cmap="viridis",  # Use a perceptual colormap for better depth visualization
    extent=extent,
    origin="upper",
)
plt.colorbar(label="Depth (m)")  # Add a color bar


# Add grid lines
plt.grid(visible=True, linestyle="--", color="gray", alpha=0.7)

# Label the axes
plt.title("Bathymetric Plan View of Lake Victoria")
plt.xlabel("Longitude")
plt.ylabel("Latitude")

# Ensure the aspect ratio is correct
plt.gca().set_aspect('equal', adjustable='box')

# Add major ticks for grid lines
plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))

# Show the plot
plt.show()


#%%

import rasterio
import numpy as np
import matplotlib.pyplot as plt
from rasterio.sample import sample_gen
from shapely.geometry import LineString

# Paths to the bathymetry and topography GeoTIFF files
tif_file_bathymetry = r"C:\DATA\Lake V Bathymentry\LakeVictoria_BathymetryGEE.tif"
tif_file_topography = r"C:\DATA\Lake Basin Topography\LakeVictoriaBasinDEM.tif"

# Define the cross-section line (coordinates in the same CRS as the rasters)
start_point = (31.6, -1.0)  # Example start point (Longitude, Latitude)
end_point = (34.3, -1.0)   # Example end point (Longitude, Latitude)

# Generate line coordinates for sampling, considering 30m resolution
num_points = 500  # Number of points to sample along the line
line_coords = np.linspace(start_point, end_point, num_points)  # Generate line sample points
longitudes = [coord[0] for coord in line_coords]  # Extract longitudes for x-axis
latitudes = [coord[1] for coord in line_coords]   # Extract latitudes for y-axis

# Function to extract data along the cross-section line at a given resolution
def extract_profile(tif_file, line_coords):
    with rasterio.open(tif_file) as src:
        # Calculate the sample points based on the resolution (30m)
        values = list(
            sample_gen(src, [(coord[0], coord[1]) for coord in line_coords])
        )
        # Replace no data values with NaN
        values = [val[0] if val[0] != src.nodata else np.nan for val in values]
    return np.array(values)

# Extract bathymetry and topography data
bathymetry_values = extract_profile(tif_file_bathymetry, line_coords)
topography_values = extract_profile(tif_file_topography, line_coords)

# Combine bathymetry and topography into a uniform elevation scale
lake_surface_elevation = 1134  # Lake Victoria surface elevation above sea level (m)
bathymetry_values = lake_surface_elevation - bathymetry_values  # Convert depth to elevation

# Identify transition point (where bathymetry ends and topography begins)
transition_point = np.argmax(bathymetry_values > lake_surface_elevation)

# Create a transition zone: 5% of the profile length around the transition point
transition_zone_size = int(0.05 * len(longitudes))  # 5% of total length for the transition zone
start_transition = max(0, transition_point - transition_zone_size)  # Avoid going out of bounds
end_transition = min(len(longitudes), transition_point + transition_zone_size)

# Interpolate smoothly between bathymetry and topography
if transition_point > 0 and start_transition < end_transition:
    # Generate a linear transition
    transition_values = np.linspace(
        bathymetry_values[start_transition], topography_values[end_transition - 1],
        end_transition - start_transition
    )
    combined_values = np.copy(bathymetry_values)
    combined_values[start_transition:end_transition] = transition_values
    combined_values[end_transition:] = topography_values[end_transition:]
else:
    # Directly combine without transition if no overlap
    combined_values = np.where(
        bathymetry_values < lake_surface_elevation, bathymetry_values, topography_values
    )

# Plot the bathymetry and topography
plt.figure(figsize=(12, 6), dpi=300)
plt.plot(longitudes, combined_values, label="Lake Victoria Profile Along Lat -1.0°", color="black")
plt.fill_between(
    longitudes, combined_values, lake_surface_elevation,
    where=(combined_values < lake_surface_elevation), color="blue", alpha=0.4, label="Water Column"
)
plt.fill_between(
    longitudes, lake_surface_elevation, combined_values,
    where=(combined_values > lake_surface_elevation), color="green", alpha=0.3, label="Land Elevation"
)

# Customize the plot
plt.title("Lake Victoria Bathymetric and Topographic Profile")
plt.axhline(y=lake_surface_elevation, color="black", linestyle="--", linewidth=0.8, label="Lake Surface Level")
plt.xlabel("Longitude (°)")
plt.ylabel("Elevation (m)")
plt.grid(visible=True, linestyle="--", alpha=0.5)
plt.legend()
plt.show()


#%%


# MAPPING LAKE EXTENT SUBMERGED BETWEEN 1138M AND 1135M

# import rasterio
# import numpy as np
# import matplotlib.pyplot as plt
# from rasterio.warp import reproject, Resampling

# # Paths to the bathymetry and topography GeoTIFF files
# tif_file_bathymetry = r"C:\DATA\Lake V Bathymentry\LakeVictoria_BathymetryGEE.tif"
# tif_file_topography = r"C:\DATA\Lake Basin Topography\LakeVictoriaBasinDEM.tif"

# # Read the raster data
# def read_raster(tif_file):
#     with rasterio.open(tif_file) as src:
#         data = src.read(1)  # Read the first band (elevation data)
#         transform = src.transform
#         bounds = src.bounds
#         crs = src.crs
#         nodata = src.nodata
#     return data, transform, bounds, crs, nodata

# bathymetry_data, bathymetry_transform, bathymetry_bounds, bathymetry_crs, bathymetry_nodata = read_raster(tif_file_bathymetry)
# topography_data, topography_transform, topography_bounds, topography_crs, topography_nodata = read_raster(tif_file_topography)

# # Resample topography data to match bathymetry resolution
# def resample_raster(src_data, src_transform, src_crs, target_shape, target_transform, target_crs):
#     resampled_data = np.empty(target_shape, dtype=np.float32)
#     reproject(
#         src_data, resampled_data,
#         src_transform=src_transform,
#         src_crs=src_crs,
#         dst_transform=target_transform,
#         dst_crs=target_crs,
#         resampling=Resampling.nearest
#     )
#     return resampled_data

# topography_resampled = resample_raster(
#     topography_data, topography_transform, topography_crs,
#     bathymetry_data.shape, bathymetry_transform, bathymetry_crs
# )

# # Identify water at 1135m and transition areas
# def calculate_areas(topography, bathymetry, elevation_high, elevation_low):
#     water_at_low = topography < elevation_low  # Water at elevation 1135m
#     submerged_at_high = topography < elevation_high  # Water at elevation 1142m
#     transition_strip = np.logical_and(submerged_at_high, ~water_at_low)  # Exposed between 1142m and 1135m
#     return water_at_low, transition_strip

# elevation_high = 1145
# elevation_low = 1134.3
# water_at_low, transition_strip = calculate_areas(
#     topography_resampled, bathymetry_data, elevation_high, elevation_low
# )

# # Generate a static map showing water and the transition strip
# fig, ax = plt.subplots(figsize=(12, 10), dpi=300)
# plt.title("Lake Victoria Flood Prone Areas", fontsize=18)

# # Base map: Topography
# plt.imshow(topography_resampled, extent=(bathymetry_bounds.left, bathymetry_bounds.right,
#                                          bathymetry_bounds.bottom, bathymetry_bounds.top),
#            cmap='terrain', alpha=0.7)

# # Overlay water area at 1135m in blue
# plt.imshow(np.where(water_at_low, 1, np.nan), extent=(bathymetry_bounds.left, bathymetry_bounds.right,
#                                                      bathymetry_bounds.bottom, bathymetry_bounds.top),
#            cmap='Blues', alpha=0.6, label='Water at 1135m')

# # Overlay transition strip in maroon
# plt.imshow(np.where(transition_strip, 1, np.nan), extent=(bathymetry_bounds.left, bathymetry_bounds.right,
#                                                           bathymetry_bounds.bottom, bathymetry_bounds.top),
#            cmap='Reds', alpha=0.8, label='Transition Strip')


# # Labels and Color Bar
# plt.colorbar(label="Elevation (m)")
# plt.xlabel("Longitude (°)")
# plt.ylabel("Latitude (°)")
# plt.grid(alpha=0.5, linestyle='--')
# plt.tight_layout()

# # Save the map as an image
# output_map_path = r"C:\TEMP\LakeVictoria_1135m_water_transition_strip.png"
# plt.savefig(output_map_path, dpi=300)
# plt.show()

# print(f"Map saved successfully: {output_map_path}")



#%% Plot WB terms monthly acc


fig, ax = plt.subplots(figsize=(10,5), dpi=300) 
df_mm_resample = df_mm.resample('M', label='right').sum()
df_mm_resample.plot(y=["P_lake", "E_lake", "Q_in", "Q_out"]) #
if flag_savefig == 1:
    plt.savefig(os.path.join(fig_path,'WBM_terms_{}_{}_v0{}r0{}_M.png'.format(startYEAR, endYEAR, ver_n, run_n)))
plt.ylabel('Quantity (mm/month)', fontsize=10)
plt.title('Lake Victoria Water Balance Monthly Accummulation', fontsize=12)

#%% Plot WB terms yearly acc

fig, ax = plt.subplots(figsize=(9, 6), dpi=300)

df_mm_resample = df_mm.iloc[:,1:5].resample('Y', label='right').sum()
df_mm_resample.plot(y=["P_lake", "E_lake", "Q_in", "Q_out"], ax=ax)
df_residual = df_mm_resample["P_lake"] - df_mm_resample["E_lake"] + df_mm_resample["Q_in"] - df_mm_resample["Q_out"]
df_residual.plot(color='lightgray', ax=ax, label = 'residual' )
plt.axhline(y=0, color='gray', ls='--')
# plot formatting
plt.legend(loc='lower left')
ax.grid(True)
ax.set_ylabel('Quantity of Water (mm/year)')
# add text
pos_x = 1.02
pos_y = 0.9
ax.text(pos_x, pos_y, 'WB Yearly Mean \n(mm/year):', transform=ax.transAxes)
summarystats = pd.DataFrame(round(df_mm_resample.mean(),1))
summarystats.columns = ['']
pos_y = 0.88
ax.text(pos_x, pos_y, str(summarystats),
          horizontalalignment='left',
          verticalalignment='top', transform=ax.transAxes)

mean_bias = df_mm_resample.mean()[0] - df_mm_resample.mean()[1] + df_mm_resample.mean()[2] - df_mm_resample.mean()[3]
pos_y = 0.02
ax.text(pos_x,pos_y,'{} \n({}-{}) v0{}r0{} \n \nMean Residual {:.2f} mm/yr'.
        format(run_name, startYEAR, endYEAR,ver_n, run_n, mean_bias), transform=ax.transAxes)
plt.title('Lake Victoria Water Balance Yearly Mean', fontsize=14)
fig.tight_layout()
if flag_savefig == 1:
    plt.savefig(os.path.join(fig_path,'WBM_terms_{}_{}_{}_v0{}r0{}_Y_res.png'.
                             format(run_name, startYEAR, endYEAR, ver_n, run_n)),dpi=300)


#%% WBM terms climatology
fig, ax = plt.subplots(figsize=(9, 6), dpi=300)

df_mm_resample = df_mm.iloc[:,1:5].resample('M', label='right').sum()
df_mm_climatology = df_mm_resample.groupby(df_mm_resample.index.month).mean() # climatology
df_mm_climatology.plot(y=["P_lake", "E_lake", "Q_in", "Q_out"], ax=ax)
ax.set_xticks([2,4,6,8,10,12])
ax.set_xticklabels(['F','A','J','A','O','D'])
ax.grid(True)
# add summary stats
pos_x = 1.02
pos_y = 0.9
ax.text(pos_x, pos_y, 'WB Monthly Mean\n(mm/month):', transform=ax.transAxes)
summarystats = pd.DataFrame(round(df_mm_climatology.mean(),1))
summarystats.columns = ['']
pos_y = 0.88
ax.text(pos_x, pos_y, str(summarystats),
         horizontalalignment='left',
         verticalalignment='top',
         transform=ax.transAxes)
mean_bias = df_mm_climatology.mean()[0] - df_mm_climatology.mean()[1] + df_mm_climatology.mean()[2] - df_mm_climatology.mean()[3]
pos_y = 0.02
ax.text(pos_x, pos_y,'{} \n({}-{}) WBM v0{}r0{} \n \nMean Residual {:.2f} mm/mo'.
         format(run_name, startYEAR, endYEAR,ver_n, run_n, mean_bias),
         transform=ax.transAxes)
fig.tight_layout()
plt.ylabel('Quantity (mm/month)', fontsize=12)
plt.title('Lake Victoria Water Balance Monthly Mean', fontsize=14)

if flag_savefig == 1:
    plt.savefig(os.path.join(fig_path,'WBM_terms_{}_{}_{}_v0{}r0{}_climatology.png'.format(run_name,startYEAR, endYEAR, ver_n, run_n)),dpi=200, bbox_inches = "tight")



#%% WBM terms climatology
fig, ax = plt.subplots(figsize=(9, 6), dpi=300)

# Resample and compute climatology
df_mm_resample = df_mm.iloc[:, 1:5].resample('M', label='right').sum()
df_mm_climatology = df_mm_resample.groupby(df_mm_resample.index.month).mean()  # climatology

# Plot
df_mm_climatology.plot(y=["P_lake", "E_lake", "Q_in", "Q_out"], ax=ax)

# xticks for months
ax.set_xticks(range(1, 13))
ax.set_xticklabels(['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'])

# Labels and grid
ax.set_ylabel('Quantity (mm/month)', fontsize=12)
ax.set_xlabel('Month', fontsize=12)
ax.set_title('Lake Victoria Water Balance Monthly Mean', fontsize=14)
ax.grid(True)

# Add summary stats
pos_x = 1.02
pos_y = 0.9
ax.text(pos_x, pos_y, 'WB Monthly Mean\n(mm/month):', transform=ax.transAxes)

summarystats = pd.DataFrame(round(df_mm_climatology.mean(), 1))
summarystats.columns = ['']
pos_y = 0.88
ax.text(pos_x, pos_y, str(summarystats),
        horizontalalignment='left',
        verticalalignment='top',
        transform=ax.transAxes)

# Compute mean bias
mean_bias = (df_mm_climatology.mean()["P_lake"] -
             df_mm_climatology.mean()["E_lake"] +
             df_mm_climatology.mean()["Q_in"] -
             df_mm_climatology.mean()["Q_out"])

pos_y = 0.02
ax.text(pos_x, pos_y,
        '{} \n({}-{}) WBM v0{}r0{} \n \nMean Residual {:.2f} mm/mo'.
        format(run_name, startYEAR, endYEAR, ver_n, run_n, mean_bias),
        transform=ax.transAxes)

fig.tight_layout()

# Save figure if flagged
if flag_savefig == 1:
    plt.savefig(os.path.join(
        fig_path,
        'WBM_terms_{}_{}_{}_v0{}r0{}_climatology.png'.format(
            run_name, startYEAR, endYEAR, ver_n, run_n)
        ), dpi=200, bbox_inches="tight")

