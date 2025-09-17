# -*- coding: utf-8 -*-
"""
Created on Thu Dec  5 13:35:29 2024

@author: VO000003
"""

import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter  # Import for smoothing

# File path (replace with your actual file path)
file_path = r"C:\DATA\Book123.csv"  # Use raw string (r'path') to avoid escape issues

# Read the CSV file
data = pd.read_csv(file_path)

# Display the first few rows to verify the data
print("Data Preview:")
print(data.head())

# Ensure numeric data for smoothing
data.iloc[:, 1:] = data.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')  # Convert to numeric, coerce errors
data = data.dropna()  # Drop rows with missing values

# Plot the graph
plt.figure(figsize=(10, 6))

# Assuming the first column is the X-axis, and the others are Y-values
x = data.iloc[:, 0]  # First column as X-axis (categorical or numeric)
for col in data.columns[1:]:
    # Apply Savitzky-Golay filter for smoothing
    if len(data[col]) >= 5:  # Ensure enough data points for the filter
        smoothed_y = savgol_filter(data[col], window_length=5, polyorder=2)
    else:
        smoothed_y = data[col]  # Use raw data if insufficient points
    plt.plot(x, smoothed_y, marker='o', label=f"{col}")  # Plot the smoothed curve

# Customize the plot
plt.title("Overall Land Cover Land Use Change from 1990 to 2020")
plt.xlabel("LULC Class")
plt.ylabel("Area Covered (Km²)")
plt.xticks(rotation=45)  # Rotate X-axis labels if necessary
plt.legend()
plt.grid(True)

# Show the plot
plt.tight_layout()  # Adjust layout to prevent clipping
plt.show()

