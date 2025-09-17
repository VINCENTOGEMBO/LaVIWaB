# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 11:59:45 2024

@author: VO000003
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the CSV data into a DataFrame
file_path = 'C:\DATA\Precipitation\Rainfall_Daily_1981_Jul2024_CHIRPS.csv'  # Replace with your file path
data = pd.read_csv(file_path)

# Convert the 'Date' column to a datetime format
data['Date'] = pd.to_datetime(data['Date'])

# Set 'Date' as the DataFrame index for easier plotting
data.set_index('Date', inplace=True)

# Plotting the data
plt.figure(figsize=(12, 6))
sns.lineplot(data=data, x='Date', y='Precipitation (mm)', marker='o', color='blue')

# Add labels and title
plt.xlabel('Year')
plt.ylabel('Precipitation (mm)')
plt.title('Daily Precipitation over Lake Victoria')

# Show the plot
plt.xticks(rotation=5)  # Rotate x-axis labels for better readability
plt.tight_layout()  # Adjust layout to prevent clipping
plt.show()
