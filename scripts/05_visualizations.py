import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.read_csv('data/clean/Transit_Weather_Clean.csv')

# Use a professional style for the presentation
sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Chart 1: Scatter plot with regression line
sns.regplot(
    x='Precipitation', 
    y='Total_Volume', 
    data=df[df['Precipitation'] > 0], 
    ax=axes[0], 
    color='blue'
)
axes[0].set_title('Transit Volume vs. Daily Precipitation')
axes[0].set_xlabel('Precipitation (mm)')
axes[0].set_ylabel('Total Passengers')

# Chart 2: Boxplot comparing the distribution
sns.boxplot(
    x='Weather_Type', 
    y='Total_Volume', 
    data=df, 
    ax=axes[1],
    palette='Set2'
)
axes[1].set_title('Passenger Distribution: Dry vs. Rain')
axes[1].set_xlabel('Weather Condition')
axes[1].set_ylabel('Total Passengers')

plt.tight_layout()
plt.savefig('outputs/weather_transit_analysis.png')
print("Visualizations saved to outputs/weather_transit_analysis.png")