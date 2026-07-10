import pandas as pd
import scipy.stats as stats
import numpy as np

# Load clean data
df = pd.read_csv('data/processed/Transit_Weather_Clean.csv')

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


# ----- Text Analysis: Issue Type and Emotion -----

text_df = pd.read_csv(
    "data/processed/Rain_Commute_Clean.csv"
)

# Create grouped categories if they are not already included
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

# Remove rows with missing grouped labels
test_df = text_df.dropna(
    subset=["Issue_Group", "Emotion_Group"]
).copy()

# Create contingency table
grouped_table = pd.crosstab(
    test_df["Issue_Group"],
    test_df["Emotion_Group"]
)

print(
    "\n--- Statistical Analysis: "
    "Rainy Commuting Issues and Emotions ---"
)

print("\nObserved frequencies:")
print(grouped_table)

# Chi-square test of independence
chi2, p_value, dof, expected = (
    stats.chi2_contingency(grouped_table)
)

expected_df = pd.DataFrame(
    expected,
    index=grouped_table.index,
    columns=grouped_table.columns
)

# Calculate Cramér's V
n = grouped_table.to_numpy().sum()

min_dimension = min(
    grouped_table.shape[0] - 1,
    grouped_table.shape[1] - 1
)

if min_dimension > 0:
    cramers_v = np.sqrt(
        chi2 / (n * min_dimension)
    )
else:
    cramers_v = np.nan

print(f"\nChi-square statistic: {chi2:.3f}")
print(f"Degrees of freedom: {dof}")
print(f"P-value: {p_value:.4f}")
print(f"Cramér's V: {cramers_v:.3f}")

print("\nExpected frequencies:")
print(expected_df.round(2))

low_expected_count = int(
    (expected_df < 5).sum().sum()
)

total_cells = expected_df.size

low_expected_percent = (
    low_expected_count / total_cells
) * 100

print(
    "\nCells with expected frequency below 5:",
    low_expected_count
)

print(
    f"Percentage of cells below 5: "
    f"{low_expected_percent:.1f}%"
)

print(
    "Minimum expected frequency:",
    round(expected_df.min().min(), 3)
)

if p_value < 0.05:
    print(
        "Result: Rainy commuting issue type and "
        "emotional response are significantly associated."
    )
else:
    print(
        "Result: No statistically significant association "
        "was found between issue type and emotional response."
    )

if low_expected_percent > 20:
    print(
        "Caution: More than 20% of expected frequencies "
        "are below 5, so the chi-square result should be "
        "interpreted as exploratory."
    )
