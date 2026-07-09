import pandas as pd
import numpy as np

# Load raw data
df = pd.read_csv('data/raw/Transit_Weather_Raw.csv')
df['Date'] = pd.to_datetime(df['Date'])

# Fill missing precipitation with 0
df['Precipitation'] = df['Precipitation'].fillna(0.0)

# Identify Outliers using Standard Deviation
mean_vol = df['Total_Volume'].mean()
std_vol = df['Total_Volume'].std()

# Drop rows exceeding 2 standard deviations
upper_limit = mean_vol + (2 * std_vol)
lower_limit = mean_vol - (2 * std_vol)
clean_df = df[(df['Total_Volume'] <= upper_limit) & (df['Total_Volume'] >= lower_limit)].copy()

# Save processed data
clean_df.to_csv('data/processed/Transit_Weather_Clean.csv', index=False)