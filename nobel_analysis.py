# nobel_analysis.py
# Project: Nobel Prize Data Analysis
# Author: Kiarash Aghakhani
# Description: Comprehensive analysis of Nobel Prize winners (1901–2023)
# GitHub: https://github.com/k-aghakhani/nobel-prize-analysis.git

# --- Import Libraries ---
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import numpy as np

# Set style for better visuals
sns.set(style="whitegrid", font_scale=1.1)
plt.rcParams['figure.figsize'] = (12, 6)

# Create results directory
if not os.path.exists('results'):
    os.makedirs('results')

# --- Load Data ---
print("Loading Nobel Prize dataset...")
nobel = pd.read_csv('data/nobel.csv')

# Debug: Show columns and first few rows
print("\nColumns in dataset:", list(nobel.columns))
print("First 3 rows:")
print(nobel.head(3))

# --- Map Column Names (Handle Variations) ---
def map_columns(df):
    col_map = {
        'year': ['year', 'year_award', 'awardYear', 'Year', 'prizeYear'],
        'full_name': ['full_name', 'name', 'laureate_name', 'Full Name', 'firstname', 'surname'],
        'sex': ['sex', 'gender', 'Sex', 'Gender'],
        'birth_country': ['birth_country', 'bornCountry', 'country', 'birthCountry', 'Birth Country', 'birth_countryNow'],
        'category': ['category', 'prize_category', 'Category', 'discipline']
    }
    mapped = df.copy()
    for std, variants in col_map.items():
        for v in variants:
            if v in df.columns:
                mapped[std] = df[v]
                print(f"Mapped '{v}' → '{std}'")
                break
        else:
            print(f"Warning: No column found for '{std}'")
            mapped[std] = None
    return mapped

nobel = map_columns(nobel)

# Standardize gender to lowercase
if 'sex' in nobel.columns:
    nobel['sex'] = nobel['sex'].str.lower().fillna('unknown')

# Combine first + last name if separate
if 'givenName' in nobel.columns and 'familyName' in nobel.columns:
    nobel['full_name'] = nobel['givenName'].fillna('') + ' ' + nobel['familyName'].fillna('')
elif 'firstname' in nobel.columns and 'surname' in nobel.columns:
    nobel['full_name'] = nobel['firstname'].fillna('') + ' ' + nobel['surname'].fillna('')
nobel['full_name'] = nobel['full_name'].str.strip()

# Check essential columns
essential = ['year', 'full_name', 'sex', 'birth_country', 'category']
missing = [c for c in essential if c not in nobel.columns or nobel[c].isna().all()]
if missing:
    raise ValueError(f"Missing or empty columns: {missing}")

print(f"\nDataset loaded: {len(nobel)} winners from {nobel['year'].min()} to {nobel['year'].max()}")

# --- Preprocessing ---
nobel['decade'] = (nobel['year'] // 10) * 10
nobel['birth_country'] = nobel['birth_country'].fillna('Unknown').astype(str)

# --- DEBUG: Unique values ---
print("\nUnique genders:", nobel['sex'].unique())
print("Unique birth countries (sample):", nobel['birth_country'].unique()[:10])

# --- Question 1: Most common gender and birth country ---
top_gender = nobel['sex'].value_counts().idxmax()
top_country = nobel['birth_country'].value_counts().idxmax()

print(f"\nMost common gender: {top_gender}")
print(f"Most common birth country: {top_country}")

# Plot: Gender Distribution
plt.figure()
sns.countplot(data=nobel, x='sex', palette='Set2')
plt.title('Gender Distribution of Nobel Laureates')
plt.xlabel('Gender')
plt.ylabel('Count')
plt.tight_layout()
plt.savefig('results/gender_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# --- Question 2: USA-born ratio by decade ---
# Flexible USA matching
usa_mask = nobel['birth_country'].str.contains('United States|USA|America|U.S.A.', case=False, na=False)
usa_winners = nobel[usa_mask]

print(f"\nFound {len(usa_winners)} USA-born winners")

if len(usa_winners) == 0:
    print("Warning: No USA-born winners found. Skipping USA analysis.")
    max_decade_usa = None
else:
    usa_per_decade = usa_winners.groupby('decade').size()
    total_per_decade = nobel.groupby('decade').size()
    usa_ratio = usa_per_decade / total_per_decade
    usa_ratio = usa_ratio.fillna(0)
    
    max_decade_usa = int(usa_ratio.idxmax())
    print(f"Decade with highest US-born ratio: {max_decade_usa} (Ratio: {usa_ratio[max_decade_usa]:.3f})")

    # Plot USA Ratio
    plt.figure()
    ratio_series = usa_ratio[usa_ratio.index >= 1900]
    ratio_series.plot(kind='bar', color='skyblue', edgecolor='black')
    plt.title('Ratio of US-Born Nobel Winners by Decade')
    plt.xlabel('Decade')
    plt.ylabel('Ratio')
    plt.xticks(rotation=45)
    plt.axhline(y=ratio_series.max(), color='red', linestyle='--', label=f'Max: {max_decade_usa}')
    plt.legend()
    plt.tight_layout()
    plt.savefig('results/usa_ratio_by_decade.png', dpi=300, bbox_inches='tight')
    plt.close()

# --- Question 3: Highest female proportion ---
female_winners = nobel[nobel['sex'] == 'female']
print(f"Found {len(female_winners)} female winners")

if len(female_winners) == 0:
    print("No female winners found!")
    max_female_dict = {1900: "Unknown"}
    prop = pd.Series()
    prop_df = pd.DataFrame(columns=nobel['category'].unique(), index=nobel['decade'].unique()).fillna(0)
else:
    female_group = female_winners.groupby(['decade', 'category']).size()
    total_group = nobel.groupby(['decade', 'category']).size()
    prop = (female_group / total_group).fillna(0)
    
    if len(prop) == 0:
        max_female_dict = {1900: "Unknown"}
    else:
        max_idx = prop.idxmax()
        max_female_dict = {int(max_idx[0]): max_idx[1]}
        print(f"Highest female proportion: {max_idx[1]} in {max_idx[0]}s ({prop.max():.3f})")
    
    prop_df = prop.unstack().fillna(0)

# Heatmap (always plot, even if empty)
plt.figure(figsize=(10, 8))
sns.heatmap(prop_df, annot=True, fmt='.2f', cmap='YlGnBu')
plt.title('Female Proportion by Decade & Category')
plt.xlabel('Category')
plt.ylabel('Decade')
plt.tight_layout()
plt.savefig('results/female_proportion_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()

# --- Question 4: First woman ---
if len(female_winners) > 0:
    first = female_winners.sort_values('year').iloc[0]
    first_woman_name = first['full_name']
    first_woman_category = first['category']
    print(f"First woman: {first_woman_name} in {first_woman_category} ({first['year']})")
else:
    first_woman_name = "Unknown"
    first_woman_category = "Unknown"

# --- Question 5: Repeat winners ---
repeat_counts = nobel['full_name'].value_counts()
repeat_list = repeat_counts[repeat_counts > 1].index.tolist()

print(f"\nRepeat winners ({len(repeat_list)}):")
for name in repeat_list:
    wins = repeat_counts[name]
    cats = nobel[nobel['full_name'] == name]['category'].unique()
    years = sorted(nobel[nobel['full_name'] == name]['year'].tolist())
    print(f"  • {name}: {wins} wins → {', '.join(cats)} ({years})")

# --- Final Summary ---
print("\n" + "="*60)
print("FINAL ANSWERS SUMMARY")
print("="*60)
print(f"top_gender = '{top_gender}'")
print(f"top_country = '{top_country}'")
print(f"max_decade_usa = {max_decade_usa}")
print(f"max_female_dict = {max_female_dict}")
print(f"first_woman_name = '{first_woman_name}'")
print(f"first_woman_category = '{first_woman_category}'")
print(f"repeat_list = {repeat_list}")
print("="*60)

print("\nAnalysis complete! Charts saved in 'results/'")