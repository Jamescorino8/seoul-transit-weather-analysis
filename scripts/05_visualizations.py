import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.read_csv('data/processed/Transit_Weather_Clean.csv')

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
    hue='Weather_Type',
    palette='Set2',
    legend=False
)
axes[1].set_title('Passenger Distribution: Dry vs. Rain')
axes[1].set_xlabel('Weather Condition')
axes[1].set_ylabel('Total Passengers')

plt.tight_layout()
plt.savefig('outputs/weather_transit_analysis.png')
print("Visualizations saved to outputs/weather_transit_analysis.png")

# ----- Text Analysis Visualizations -----

text_df = pd.read_csv(
    "data/processed/Rain_Commute_Clean.csv"
)

emotion_group_map = {
    "Frustration": "Negative_Emotion",
    "Anxiety": "Negative_Emotion",
    "Fear": "Negative_Emotion",
    "Exhaustion": "Negative_Emotion",
    "Resignation": "Resigned_Humor",
    "Humor": "Resigned_Humor",
    "Appreciation": "Positive_Emotion",
    "Relief": "Positive_Emotion",
    "Neutral": "Neutral_Other",
    "Other": "Neutral_Other"
}

issue_group_map = {
    "Flooding": "Flooding",
    "Workplace_Pressure": "Workplace_Pressure",
    "Delay": "Delay",
    "Comfort": "Other_Issues",
    "Congestion": "Other_Issues",
    "Safety": "Other_Issues",
    "Transportation_Preference": "Other_Issues",
    "Other": "Other_Issues"
}

text_df["Emotion_Group"] = (
    text_df["Emotion_Type"].map(emotion_group_map)
)

text_df["Issue_Group"] = (
    text_df["Issue_Type"].map(issue_group_map)
)

# ----- Chart 3: Emotion Frequency -----

emotion_counts = (
    text_df["Emotion_Type"]
    .value_counts()
)

plt.figure(figsize=(10, 6))

ax = sns.barplot(
    x=emotion_counts.index,
    y=emotion_counts.values
)

plt.title(
    "Emotions Associated with Rainy Commuting Experiences"
)

plt.xlabel("Emotion Type")
plt.ylabel("Number of Comments")

plt.xticks(
    rotation=45,
    ha="right"
)

for container in ax.containers:
    ax.bar_label(
        container,
        padding=3
    )

plt.tight_layout()

plt.savefig(
    "outputs/rain_emotion_analysis.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ----- Chart 4: Emotion Groups by Issue Type -----

grouped_percent = pd.crosstab(
    text_df["Issue_Group"],
    text_df["Emotion_Group"],
    normalize="index"
) * 100

emotion_order = [
    "Negative_Emotion",
    "Resigned_Humor",
    "Positive_Emotion",
    "Neutral_Other"
]

# Include only categories that exist in the data
available_columns = [
    column
    for column in emotion_order
    if column in grouped_percent.columns
]

grouped_percent = grouped_percent[
    available_columns
]

ax = grouped_percent.plot(
    kind="bar",
    stacked=True,
    figsize=(11, 6)
)

plt.title(
    "Emotional Responses by Rainy Commuting Issue Type"
)

plt.xlabel("Commuting Issue Type")
plt.ylabel("Percentage of Comments")

plt.xticks(
    rotation=20,
    ha="right"
)

plt.legend(
    title="Emotion Group",
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

plt.savefig(
    "outputs/emotion_issue_analysis.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print(
    "Text analysis visualizations saved to outputs."
)