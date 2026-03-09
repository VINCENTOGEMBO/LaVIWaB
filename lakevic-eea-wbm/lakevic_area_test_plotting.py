#%%

import pandas as pd
import matplotlib.pyplot as plt

# open digitized data
df_raw = pd.read_csv("C:\DATA\Lake Extent csv 1993-2023\lakevic_area_wuetal_2023.csv")[['Date', 'Area_km2']]

#%%

# clean data

df = df_raw.copy()
df['Date'] = df['Date'].round(2)
df['Area_km2'] = df['Area_km2'].round(3)
df = df.sort_values('Date').reset_index(drop=True)



# %%

# plot


fig, ax=plt.subplots()
df.set_index('Date').plot(ax=ax)
mean_val = df['Area_km2'].mean()
ax.axhline(mean_val, color='gray', linestyle='--')
ax.text(
    .65, mean_val-8, 
    f"Mean = {mean_val:.2f} km2", 
    color='gray', 
    transform=ax.get_yaxis_transform()
)
# %%

# optional: turn time into datetime from decimal

def decimal_year_to_datetime(decimal_year):
    year = int(decimal_year)
    rem = decimal_year - year
    # Calculate the number of days in the year
    start = pd.Timestamp(year=year, month=1, day=1)
    if pd.Timestamp(year=year, month=12, day=31).is_leap_year:
        days = 366
    else:
        days = 365
    # Round to nearest day
    delta_days = int(round(rem * days))
    date = start + pd.Timedelta(days=delta_days)
    return date.normalize()

df_datetime = df.copy()
df_datetime['Date'] = df_datetime['Date'].apply(decimal_year_to_datetime)

df_datetime.set_index('Date').plot()


# save the cleaned data 
#df_datetime.to_csv('lakevic_area_wuetal_2023_digitized_cleaned.csv', index=False)

# %%

df_monthly = (
    df_datetime.set_index('Date')
    .resample('MS')  # 'MS' = Month Start
    .mean()
    .dropna()
    .reset_index()
)

# %%

df_monthly.plot(x='Date', y='Area_km2')
#df_monthly.to_csv('lakevic_area_wuetal_2023_digitized_cleaned_monthly.csv', index=False)


