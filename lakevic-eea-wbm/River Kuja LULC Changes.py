# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 16:27:07 2024

@author: VO000003
"""

# Import the necessary libraries
import pandas as pd
import matplotlib.pyplot as plt

# Load the Excel file
file_path = "C:\DATA\Book1.xlsx"
df = pd.read_excel(file_path)  # Ensure your Excel file is in the working directory

# Display the first few rows to check the data
print(df.head())

# Plot the graph with a larger figure size
plt.figure(figsize=(15, 6))  # Increase the width of the figure (15) to stretch horizontally

# Plot two columns (for example, 'Date' vs 'Value')
# Replace 'Date' and 'Value' with the actual column names from your data
plt.plot(df['LULC Class'], df['Area Covered1990'], label='1990')  # Line plot for one column

# If you want to plot a second column, e.g., 'AnotherValue'
plt.plot(df['LULC Class'], df['Area Covered2020'], label='2020')  # Line plot for second column

# Rotate x-axis labels if needed to prevent overlap
plt.xticks(rotation=45, ha='right')  # Rotate labels by 45 degrees, aligned to the right

# Add box tips on specific points (e.g., at max and min points)
# For simplicity, let's annotate the max and min of 'Value' column
max_value = df['Area Covered1990'].max()
min_value = df['Area Covered2020'].min()

# Get the corresponding dates
max_date = df[df['LULC Class'] == max_value]['LULC Class'].values[0]
min_date = df[df['LULC Class'] == min_value]['LULC Class'].values[0]

# Annotate the max value
plt.annotate(f'Max: {max_value}', xy=(max_date, max_value), xytext=(max_date, max_value + 5),
             arrowprops=dict(facecolor='black', shrink=0.05),
             bbox=dict(boxstyle="round,pad=0.3", edgecolor='black', facecolor='yellow'))

# Annotate the min value
plt.annotate(f'Min: {min_value}', xy=(min_date, min_value), xytext=(min_date, min_value - 5),
             arrowprops=dict(facecolor='black', shrink=0.05),
             bbox=dict(boxstyle="round,pad=0.3", edgecolor='black', facecolor='yellow'))

# Customize the graph
plt.xlabel('LULC Class')  # X-axis label
plt.ylabel('Area Covered (Km2)')  # Y-axis label
plt.title('LULC Change in Kuja Basin 1990-2020')  # Graph title
plt.legend()  # Show the legend

# Automatically adjust layout
plt.tight_layout()
plt.show()
