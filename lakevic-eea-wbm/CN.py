# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 13:51:02 2024

@author: VO000003
"""

import pandas as pd

# Sample data for land use, soil groups, and hydrologic condition
data = {
    'Land_Use': ['Urban', 'Agriculture', 'Forest'],
    'Soil_Group': ['D', 'C', 'A'],
    'Area_Acres': [100, 300, 500],
    'Hydrologic_Condition': ['Poor', 'Fair', 'Good']
}

# CN values for different land use, soil group, and condition
cn_values = {
    ('Urban', 'D', 'Poor'): 98,
    ('Agriculture', 'C', 'Fair'): 74,
    ('Forest', 'A', 'Good'): 30
}

# Convert to DataFrame
df = pd.DataFrame(data)

# Assign CN values based on land use, soil group, and condition
df['Curve_Number'] = df.apply(lambda row: cn_values.get((row['Land_Use'], row['Soil_Group'], row['Hydrologic_Condition'])), axis=1)

# Calculate weighted Curve Number
total_area = df['Area_Acres'].sum()
df['Weighted_CN'] = df['Curve_Number'] * df['Area_Acres']
weighted_cn = df['Weighted_CN'].sum() / total_area

print(f"Weighted Curve Number: {weighted_cn:.2f}")
