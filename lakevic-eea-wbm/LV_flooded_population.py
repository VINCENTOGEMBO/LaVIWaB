# -*- coding: utf-8 -*-
"""
Created on Tue Nov 11 13:45:04 2025

@author: VO000003
"""


# -------------------------------------------------------------
# Estimate Flood-Affected Population (Lake Victoria Basin)
# Author: [Your Name]
# Date: [Today's date]
# -------------------------------------------------------------

import rasterio
from rasterio.enums import Resampling
import numpy as np
import matplotlib.pyplot as plt

# -------------------------------------------------------------
# 1. Define file paths
# -------------------------------------------------------------
pop_tif = r"C:\DATA\attribution\LV_population_distribution.tif"
flood_tif = r"C:\DATA\attribution\wbm_copdem_proj.tif"
output_tif = r"C:\DATA\attribution\LV_population_flood_affected.tif"

# -------------------------------------------------------------
# 2. Read population raster
# -------------------------------------------------------------
with rasterio.open(pop_tif) as pop_src:
    pop_data = pop_src.read(1)
    pop_meta = pop_src.meta.copy()

# Replace NaNs with zeros
pop_data = np.nan_to_num(pop_data, nan=0)

# -------------------------------------------------------------
# 3. Read flood raster and resample to population raster
# -------------------------------------------------------------
with rasterio.open(flood_tif) as flood_src:
    flood_data = flood_src.read(
        1,
        out_shape=pop_data.shape,
        resampling=Resampling.nearest
    )

# Replace NaNs with zeros
flood_data = np.nan_to_num(flood_data, nan=0)

# -------------------------------------------------------------
# 4. Create mask: flooded AND populated
# -------------------------------------------------------------
flooded_mask = (flood_data > 0) & (pop_data > 0)

# Mask population by flooded areas
pop_flooded = np.where(flooded_mask, pop_data, 0)

# -------------------------------------------------------------
# 5. Calculate total affected population
# -------------------------------------------------------------
total_affected = pop_flooded.sum()
print("-------------------------------------------------------------")
print(f"✅ Estimated total population affected within flood zone: {total_affected:,.0f} people")
print("-------------------------------------------------------------")

# -------------------------------------------------------------
# 6. Save flood-affected population raster
# -------------------------------------------------------------
pop_meta.update({"dtype": "float32", "compress": "lzw"})

with rasterio.open(output_tif, "w", **pop_meta) as dest:
    dest.write(pop_flooded.astype("float32"), 1)

print(f"🗺️ Flood-affected population raster saved to:\n{output_tif}")

# -------------------------------------------------------------
# 7. Optional: Quick visualization
# -------------------------------------------------------------
plt.figure(figsize=(10, 8), dpi=150)
plt.imshow(np.where(flooded_mask, pop_data, np.nan), cmap='Reds')
plt.title("Lake Victoria Basin — Flood-Affected Population Map")
plt.xlabel("Column")
plt.ylabel("Row")
plt.colorbar(label="Population count per pixel")
plt.tight_layout()
plt.show()
