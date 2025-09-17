# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 17:52:42 2024

@author: VO000003
"""

import rasterio
import geopandas as gpd
from rasterio.mask import mask

# Paths to your files
boundary_path = r"C:\DATA\Lake_Victoria_Boundary_Final\LakeV_boundary.shp"
bathymetry_path = r"C:\DATA\gebco_2024_n2.0_s-7.0_w29.0_e37.0.nc"
output_path = r"C:\DATA\clipped_bathymetry_lake_victoria.tif"

# Step 1: Load the Lake Victoria boundary shapefile
lake_boundary = gpd.read_file(boundary_path)

# Step 2: Check if CRS is set; if not, set it explicitly to WGS84
if lake_boundary.crs is None:
    lake_boundary = lake_boundary.set_crs(epsg=4326)  # Set to WGS84

# Step 3: Open the bathymetry raster file
with rasterio.open(bathymetry_path) as bathymetry_raster:
    # Reproject lake boundary to match the bathymetry raster CRS if needed
    lake_boundary = lake_boundary.to_crs(bathymetry_raster.crs)

    # Step 4: Clip the bathymetry data using the lake boundary geometry
    out_image, out_transform = mask(bathymetry_raster, lake_boundary.geometry, crop=True)

    # Step 5: Update metadata for the clipped raster
    out_meta = bathymetry_raster.meta.copy()
    out_meta.update({
        "driver": "GTiff",
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform,
        "crs": bathymetry_raster.crs
    })

    # Step 6: Save the clipped raster
    with rasterio.open(output_path, "w", **out_meta) as dest:
        dest.write(out_image)

print("Bathymetry data successfully clipped to Lake Victoria boundary!")

