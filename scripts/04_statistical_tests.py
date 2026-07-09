import pandas as pd
import scipy.stats as stats

# Load clean data
df = pd.read_csv('data/clean/Transit_Weather_Clean.csv')

# Split data into dry and rainy groups
dry_volume = df[df['Weather_Type'] == 'Dry']['Total_Volume']
rain_volume = df[df['Weather_Type'] == 'Rain']['Total_Volume']

print("--- Statistical Analysis: Dry vs. Rainy Days ---")

# Levene's test to check variance
stat, p_levene = stats.levene(dry_volume, rain_volume)

# Independent t-test to check if means differ
t_stat, p_ttest = stats.ttest_ind(dry_volume, rain_volume, equal_var=(p_levene > 0.05))

print(f"T-statistic: {t_stat:.2f}, P-value: {p_ttest:.4f}")

if p_ttest < 0.05:
    print("Result: Significant impact of weather on transit volume.")
else:
    print("Result: No statistically significant impact found.")