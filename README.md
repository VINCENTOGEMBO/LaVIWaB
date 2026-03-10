# Hydroclimatic Modelling of Lake Victoria using Lake Victoria Integrated Water Balance (LaVIWaB) Model

The LaVIWaB model `lakevic-eea-wbm` simulates lake levels and lake area for Lake Victoria based on the following inputs: precipitation, evaporation, outflow and soil types and land cover in the basin. 

The analysis scripts in `lakevic-eea-analysis` reproduce all results


## The LaVIWaB model

`lakevic-eea-wbm` contains the water balance model used in the study, it simulates daily lake levels for Lake Victoria.

The model can be run from the main `WBM_model.py` script. `WBM_settings.py` acts as a namelist and should be modified to run the model under different scenarios and forcings and to specify input data paths, `WBM_inicon.py` initiates constants in the model, `WBM_inigeom.py` imports shapefiles and geoinformation about Lake Victoria and the basin.

The model takes as inputs:
1. Precipitation data, which should be remapped using the grid specifications in `mygrid.txt`. 
2. Evaporation data `input_data/evap`
3. Information on soil classes, land use, basin and lake shapefiles `input_data/CN` and `input_data/shapefiles`
4. Outflow
    - observational run: semi-observational outflow `input_data/outflow` 
    - attribution runs: calculated by the model using the Agreed Curve.

The model is based on the Python version from [Pietroiusti et al. 2024, ESD, "Possible role of anthropogenic climate change in the record-breaking 2020 Lake Victoria levels and floods"](https://esd.copernicus.org/articles/15/225/2024/). The version was improved to include lake levels and lake extent/area with future projections.


## Data for the LaVIWaB model 

For ease of reproducibility, all data necessary to run the WBM, except for precipitation data, are provided in this GitHub repository.  

`lakevic-eea-wbm/input-data/` and `lakevic-eea-wbm/modified_data` contain:
1. Evaporation data `input_data/evap` from [Pietroiusti et al. 2024, ESD](https://esd.copernicus.org/articles/15/225/2024/)
2. Information on soil classes and land cover `input_data/CN` from  [JRC](https://publications.jrc.ec.europa.eu/repository/handle/JRC24914)
3. basin and lake shapefiles `input_data/shapefiles` from [Harvard dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/PWFW26)
4. Outflow `input_data/outflow` which is a combination of data from [Pietroiusti et al. 2024, ESD](https://esd.copernicus.org/articles/15/225/2024/) and new in situ data.
5. Lake level data were sourced from the DAHITI database (https://dahiti.dgfi.tum.de/en/2/water-level-altimetry/) and WMO Hydromet archives (https://wmo.int/resources/storymaps)
6. Bathymetric data were obtained from GEBCO (https://www.gebco.net/data-products/gridded-bathymetry-data/gebco2023-grid). 
