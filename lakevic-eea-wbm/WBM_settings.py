#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 26 15:25:28 2024

@author: Vincent Ogembo  vincent.ogembo@vub.be

settings and filepaths - this should be the only file the user modifies 
WBM "namelist" for user control:
    - set file paths
    - set start and end dates
    - set CN method parameter (AMC)
    - re-run with new PERSIANN file 
"""

#%%

import pandas as pd
import sys, os , glob

WBM_path = os.path.dirname(__file__)

#=======================#
#== VERSION AND RUN ====#
#=======================#
run_where = 0 
                # 0: LOCAL
                # 1: HPC
                
# Model version
ver_type = 'HPC'
ver_n = 1
run_n = 2 
# history runs local - PERSIANN: 1: standard, 2:test agreed curve, 3: standard with df settings from ac (??)
# history runs HPC - GFDL-ESM4 1: 1850-1860 test, 2: total 
# v01r02 - PERSIANN nan filled 

#=================#
#== FLAGS:RUN ====#
#=================#

run_type = 1
                # 0: OBS
                # 1: MODEL ISIMIP3b
                # 2: ISIMIP3a obsclim and counterclim

if run_type == 0: # IF OBS
    flag_obs_precip = 0
                # 0: PERSIANN
                # 1: CHIRPS - add these flags later
                # 2: MSWEP - add these flags            
    flag_obs_outflow = 0 
                # 0: Observed, input file
                # 1: Agreed curve, calculated at each timestep (standard for model run) --> MAKE THIS FLAG !! 
                
if run_type == 1: # IF MODEL
    flag_model_scenario = 0
                # 0: HIST
                # 1: HIST-NAT
                # 2: PROJ - SSP126
                # 3: SSP370
    flag_model_precip = 0
                # 0: CanESM5
                # 1: CNRM-CM6-1
                # 2: GFDL-ESM4
                # 3: IPSL-CM6A-LR
                # 4: MIROC6
                # 5: MRI-ESM2-0
    flag_evap_climatology = 0 
                # 0 : repeat one year from Wim output
                # 1 : use modelled time-varying values 



if run_type == 2: # IF ISIMIP3a
    flag_scenario = 1                           # OLD: flag_model_scenario
                # 0: obsclim
                # 1: counterclim
    flag_data = 0                               # OLD flag_model_precip
                # 0: 20CRv3-ERA5

#======================#
#== FLAGS:PLOTTING ====#
#======================#

flag_plotprecip = 1   # 1: plot all 
                      # 0: no plots
flag_plotevap = 1                                   
flag_plotinflow = 1 
flag_plotarea = 1         # Newly introduced     
flag_plotCNdiff = 1                
flag_plotflip = 1   
flag_savefig = 0 # 1: save, 0: show

#============================#
#== SET GENERAL DIRECTORIES =#
#============================#

# Precipitation files 
if run_where == 0:
    inDIR =  os.path.join(os.path.dirname(__file__)) #"C:\Users\VO000003\OneDrive - Vrije Universiteit Brussel\Ogembo_LVictoria_IWBM\lakevic-eea-wbm" # outdated
if run_where == 1: 
    inDIR = '/data/brussel/vo/000/bvo00012/vsc10419/Thesis' 
    
# General output and input 
outDIR = os.path.join(WBM_path, '..', 'output')
figDIR = os.path.join(WBM_path, '..',  'figures')


#=================================#
#== INITIALISE BASED ON FLAGS ====#
#=================================#

# TIME: set start and end time - COULD AUTOMATE THIS START/END YEAR FROM INPUT FILES ! 
#=================================#
# OBS
if run_type == 0 : 
    if flag_obs_precip == 0: # PERSIANN (could rename this to flag_data)
        startYEAR = 1985 # test to see if better  
        endYEAR =   2023 
    if flag_obs_precip == 1: # CHIRPS - NEED MORE YEARS !! (try also centrends)
        startYEAR = 1981 
        endYEAR =   2015
    if flag_obs_precip == 2: # MSWEP - NEED MORE YEARS !!
        startYEAR = 1979 
        endYEAR =   2017 
        
# ISIMIP3b
if run_type == 1: 
    startYEAR = 1850
    endYEAR =   2020 # 2100 - TOCHANGE WHEN DATA REMAPPED

# ISIMIP3a 
if run_type == 2: 
    startYEAR = 1901
    endYEAR =   2023 

startDATE = str(startYEAR)+'-01-01'
endDATE = str(endYEAR)+'-12-31'
DATEs = pd.date_range(startDATE, endDATE)

# NAMES: 
#=================================#
# OBS: 
if run_type == 0:
    obs_list = ['PERSIANN', 'CHIRPS', 'MSWEP']
    obs_select = obs_list[flag_obs_precip]
    PRECIP_data = obs_select 
    run_name = obs_select + '_' + 'obs'
    
# MODEL: set GCM and scenario name 
if run_type == 1:
    GCM_list = ['CanESM5', 'CNRM-CM6-1','GFDL-ESM4','IPSL-CM6A-LR','MIROC6','MRI-ESM2-0'] #'20CRv3-ERA5',
    GCM_select = GCM_list[flag_model_precip]
    scenario_list = ['hist', 'hist-nat']
    scenario_select = scenario_list[flag_model_scenario]
    scenario_dir_list = ['hist-rcp70', 'hist-nat'] # add ssp126, ssp345 
    scenario_dir_select = scenario_dir_list[flag_model_scenario]
    PRECIP_data = scenario_select + ' ' + GCM_select
    run_name = 'ISIMIP3b_' + scenario_select + '_' + GCM_select

# ISIMIP3a: set data and scenario name 
if run_type == 2:
    data_list = ['20CRv3-ERA5'] # not a gcm but just to not change all code, if time rename this to make more sense 
    data_select = data_list[flag_data]
    scenario_list = ['obsclim', 'counterclim']
    scenario_select = scenario_list[flag_scenario]
    scenario_dir_list = scenario_list
    scenario_dir_select = scenario_dir_list[flag_scenario]
    PRECIP_data = scenario_select + ' ' + data_select
    run_name = 'ISIMIP3b_' + scenario_select + '_' + data_select


# FIGURE NUMBERS initialise
# =================================#
fig_n = 1


#%%
#====================================#
#== SET DIRECTORIES SPECIFIC TO RUN =#
#====================================#

# PRECIPITATION INPUT PATH
# =================================#
# LOCAL
if run_where == 0: 
    if run_type == 0: # OBS
        in_path_precip = os.path.join(inDIR, 'modified_data',PRECIP_data)
    if run_type == 1: # MODEL
        in_path_precip = os.path.join(inDIR,'ISIMIP3b', 'output', scenario_dir_select, GCM_select)
# HPC
if run_where == 1: 
    if run_type == 0: # OBS
        in_path_precip = os.path.join(inDIR, PRECIP_data)
    if run_type == 1:
        in_path_precip = os.path.join(inDIR, 'ISIMIP3b', scenario_dir_select, GCM_select)
    if run_type == 2:
        in_path_precip = os.path.join(inDIR, 'ISIMIP3a', scenario_dir_select, data_select)
        
        #%%
# SPECIFIC OUTPUT PATHS      
# =================================#  
if run_type == 0: #OBS
    out_path = os.path.join(outDIR, PRECIP_data, 'v0{}r0{}'.format(ver_n, run_n) )# specific to model run
    fig_path = os.path.join(figDIR, PRECIP_data, 'v0{}r0{}'.format(ver_n, run_n) )
if run_type == 1:
    out_path = os.path.join(outDIR, scenario_dir_select, GCM_select, 'v0{}r0{}'.format(ver_n, run_n) )# specific to model run
    fig_path = os.path.join(figDIR, scenario_dir_select, GCM_select, 'v0{}r0{}'.format(ver_n, run_n) )  
if run_type == 2:
    out_path = os.path.join(outDIR, scenario_dir_select, data_select, 'v0{}r0{}'.format(ver_n, run_n) )# specific to model run
    fig_path = os.path.join(figDIR, scenario_dir_select, data_select, 'v0{}r0{}'.format(ver_n, run_n) )  

if os.path.exists(out_path):
    print("The directory", out_path, "exists!")
else:
    os.makedirs(out_path)
    
if os.path.exists(fig_path):
    print("The directory", fig_path, "exists!")
else:
    os.makedirs(fig_path)

#=====================#
#== START MESSAGE ====#
#=====================#

start_1 = '===========\nRunning model version: {} v0{}r0{}'.format(ver_type, ver_n, run_n)
start_2 = '\nPrecip data: {} from {} to {}'.format(PRECIP_data, startYEAR, endYEAR)
start_3 = '\n===========\nPrecip folder: {}'.format(in_path_precip)
start_4 = '\nOutput folder: {}'.format(out_path)
start_5 = '\nFigures folder: {}'.format(fig_path)
start_message_1 = start_1 + start_2 + start_3 + start_4 + start_5
#print(start_message_1)


#====================#
#== SET DATA PATHS ==#
#====================#

# Geometry data
filepath_shp_lake = os.path.join(WBM_path, 'input_data', 'shapefiles', 'LakeVictoria.shp' ) #Path to the file
filepath_shp_basin = os.path.join(WBM_path,'input_data', 'shapefiles', 'Watsub.shp' ) #Path to the file
filepath_grid = os.path.join(WBM_path, 'input_data', 'mygrid.txt') #Path to the file

# WBM terms : evap and outflow
filepath_evap = os.path.join(WBM_path,'input_data', 'evap', '1996-2008_FLake_out02_LHF_ydaymean.nc' ) #Path to the file
filepath_evap_remap = os.path.join(WBM_path,'modified_data', 'evap_remapbil.nc') #Path to the file
    #agreed curve from 2011
filepath_outflow = os.path.join(WBM_path,'input_data', 'outflow', 'Outflow_merged_cmd_1950_2024.csv') #Path to the file
    #agreed curve from 2006
#filepath_outflow = os.path.join(WBM_path,'input_data', 'outflow', 'outflow_merged_cmd_1948_2021.csv') #Path to the file

# CN method: Soil and hydrological classes 
filepath_soilclass_map = os.path.join(WBM_path,'input_data', 'CN', 'soils_old.tif') #Path to the file
filepath_soilclass_txt = os.path.join(WBM_path,'input_data', 'CN', 'soil_classification.txt') #Path to the file
filepath_landcover_map = os.path.join(WBM_path,'input_data', 'CN', 'landcover.tif') #Path to the file
filepath_CN_values_txt = os.path.join(WBM_path,'input_data', 'CN', 'CNvalues.txt') #Path to the file

# Observed lakelevels (HM+DAHITI, interpolated to daily resolution) from LV_levelsanalysis.ipynb
filepath_lakelevels_hist = os.path.join(WBM_path,'input_data', 'lakelevels', 'Lake_Victoria_level_Jun2024.csv') #Path to the file   # masl


# LAKE AREA AND LAKE VOLUME 
WBM_path = "C:/users/vo000003/OneDrive - Vrije Universiteit Brussel/Ogembo_LVictoria_IWBM/lakevic-eea-wbm"
filepath_depth_area=os.path.join(WBM_path, 'input_data/hypsograph/WBM_depth_area_curve.csv')
#filepath_depth_area=os.path.join(WBM_path, 'input_data/hypsograph/WBM_depth_area_curve_v0210.csv')

# Computed Lake Area (Processed from Lake water occurence Pekel data, lake levels, bathymetry and topography)
#filepath_lake_area = os.path.join(WBM_path,'input_data', 'lakearea', 'lake_area_1948_2023') #Path to the file
#lake_area_df = pd.read_csv(filepath_lake_area)

# Computed Lake Volume (Calculated from Lake Area with an average lake depth)
#filepath_lake_volume = os.path.join(WBM_path,'input_data', 'lakevolume', 'lake_volume_1948_2023') #Path to the file
#lake_volume_df = pd.read_csv(filepath_lake_volume)


#======================================#
#PRECIPITATION 
#======================================#


# WBM terms : Precipitation
if run_where == 0: # LOCAL
    if run_type == 0: # OBS
        if PRECIP_data == 'PERSIANN':
            filename_precip = 'PERSIANN-CDR_v01r01_1983_2024_remapped_owngrid_reorder_timelatlon.nc' # _reorder_timelatlon PERSIANN_new mm/d reordered: (time lat lon)
        if PRECIP_data == 'MSWEP':
            filename_precip = 'mswep_pr_owngrid_1979_2017.nc'
        filepath_precip = os.path.join(in_path_precip, filename_precip)
    if run_type == 1: # ISIMIP3b
        filepath_precip = glob.glob(in_path_precip + f'/*_{startYEAR}_{endYEAR}.nc')[0]

if run_where == 1: # HPC
     if run_type == 0:
        if PRECIP_data == 'PERSIANN':
            filename_precip = 'PERSIANN-CDR_v01r01_1983_2024_remapped_owngrid_reorder_timelatlon.nc' #PERSIANN_new mm/d reordered: (time lat lon) # _fillnan_climatofillnan with climato
        if PRECIP_data == 'MSWEP':
            filename_precip = 'mswep_pr_owngrid_1979_2017.nc'
        if PRECIP_data == 'CHIRPS':
            filename_precip = 'chirps_pr_owngrid_1981_2015.nc'
        filepath_precip = os.path.join(in_path_precip, filename_precip)
     if run_type == 1 or run_type == 2: # ISIMIP3b or ISIMIP3a
        filepath_precip = glob.glob(in_path_precip + '/*pr_owngrid_*.nc')[0]   

start_message_2 = '===========\nPrecip filepath: {}'.format(filepath_precip)
#print(start_message_2)

#==========================#
#== CN METHOD SETTINGS ====#
#==========================#

amc_days = 5 
amc_initialvalue = 0.0112 # mean condition, from original Vanderkelen WBM obs - check this value

             

     
