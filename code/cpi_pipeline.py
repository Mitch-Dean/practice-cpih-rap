# -*- coding: utf-8 -*-
"""
Created on Tue Jan 27 12:59:49 2026

@author: deanm
"""

#------------------------------------------------------------------------------
#IMPORT AND TIDY

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

cpih_data = pd.read_csv('C:/Users/deanm/OneDrive - Office for National Statistics/Projects/Practice RAP Project/data/raw/cpih_filtered_2020-2025.csv')

#convert to snake case
cpih_data.columns = (
    cpih_data.columns
        .str.strip()
        .str.lower()
        .str.replace('-', '_')
        .str.replace(' ', '_')
    )

#convert to datetime
cpih_data['month'] = pd.to_datetime(cpih_data['time'], format='%b-%y', errors='coerce')

#rename columns and remove excess
cpih_data = cpih_data.rename(columns={
    'v4_0':'index_value',
    'cpih1dim1aggid':'coicop_code',
    'aggregate':'coicop_category'})

cpih_data = cpih_data[['month','coicop_code','coicop_category','index_value']]

#sort and group rows by item category
cpih_data = cpih_data.sort_values(['coicop_code','month'])
grouped = cpih_data.groupby(['coicop_code', 'coicop_category'], group_keys=False)

#QA check: dtype and values present
assert pd.api.types.is_datetime64_any_dtype(cpih_data['month']), "Month column not parsed as datetime." #checks that the month column is in datetime
assert cpih_data[['coicop_code','coicop_category','index_value']].isnull().sum().sum() == 0, "Unexpected missing values." #checks that the specified columns are fully populated by making sure there are no null values

#------------------------------------------------------------------------------
#CALCULATIONS

#create lagged index for each category
cpih_data['lag_1'] = grouped['index_value'].shift(1)
cpih_data['lag_12'] = grouped['index_value'].shift(12)

#QA check: ensure lag columns have been created
assert 'lag_1' in cpih_data.columns and 'lag_12' in cpih_data.columns, "Lag columns not created."

#compute inflation rates
cpih_data['monthly_pct'] = (cpih_data['index_value'] / cpih_data['lag_1'] - 1) * 100
cpih_data['annual_pct'] = (cpih_data['index_value'] / cpih_data['lag_12'] -1) * 100

#compute standard deviation
volatility_df = (
    cpih_data
    .groupby(['coicop_code','coicop_category'])['monthly_pct']
    .std()
    .reset_index(name='volatility')
    )

#QA check: ensure pct columns have been populated
assert cpih_data['monthly_pct'].notna().any(), "Monthly_pct has no values."
assert cpih_data['annual_pct'].notna().any(), "Annual_pct has no values."

#save output
cpih_data.to_csv("../data/processed/cpih_processed.csv")

#------------------------------------------------------------------------------
#SUMMARY TABLE

latest_month = cpih_data['month'].max() #select latest month (makes it reproducable)
latest_data = cpih_data[cpih_data['month'] == latest_month] #select rows belonging to the latest month

summary_table = latest_data[['coicop_code','coicop_category','monthly_pct','annual_pct']]#assign relevant columns to the table
summary_table = summary_table.sort_values('annual_pct', ascending=False) #sort categories in order of annual inflation rate

#merge volatility
summary_table = summary_table.merge(
    volatility_df,
    on=['coicop_code','coicop_category'],
    how='left'
    )

#round pcts
summary_table['monthly_pct'] = summary_table['monthly_pct'].round(1)
summary_table['annual_pct'] = summary_table['annual_pct'].round(1)
summary_table['volatility'] = summary_table['volatility'].round(2)

#save
summary_table.to_csv("../tables/summary_table.csv", index=False)

#------------------------------------------------------------------------------
#HEADLINE INDEX CHART

headline_cpih = cpih_data[cpih_data['coicop_code'] == 'CP00'] # isolate the headline figures

#plot
figure, axes = plt.subplots(figsize=(10,5)) #create figure and axes
axes.plot(headline_cpih['month'], headline_cpih['index_value'], linewidth=2, color="#005ea5")

#title/labels
plt.title('CPIH Monthly Rate: All Items 2020-2025')
#plt.xlabel('Month')
#plt.ylabel('Index value')

#layout
plt.grid(True, alpha=0.3)
plt.tight_layout()

#save
plt.savefig('../figures/headline_index.png', dpi=200)
plt.close()

#------------------------------------------------------------------------------
#MOST VOLATILE ITEM CHART

#identify most volatile category
most_volatile_row = summary_table.loc[summary_table['volatility'].idxmax()]

most_volatile_code = most_volatile_row['coicop_code']
most_volatile_label = most_volatile_row['coicop_category']

#print(most_volatile_code)
#print(most_volatile_label)

most_volatile_category = cpih_data[cpih_data['coicop_code'] == most_volatile_code]

#plot
figure, axes = plt.subplots(figsize=(10,5))
axes.plot(most_volatile_category['month'], most_volatile_category['index_value'], linewidth=2, color='#d4351c')

#title/labels
plt.title(f'CPIH Most Volatile Item Category: {most_volatile_label}') # f-string allows the title to be dynamic in case the most volatile category changes
#plt.xlabel('Month')
#plt.ylabel('Index value')

#layout
plt.grid(True, alpha=0.3)
plt.tight_layout()

#save
plt.savefig('../figures/most_volatile_category.png', dpi=200)
plt.close()

#------------------------------------------------------------------------------
#ALL-CATEGORY VOLATILITY BAR CHART

volatility_df = volatility_df.sort_values('volatility', ascending=False)

#plot
figure, axes = plt.subplots(figsize=(10,5))
axes.barh(volatility_df['coicop_category'], volatility_df['volatility'], color='#005ea5')

#title/labels
plt.title('Price Volatility of CPIH Categories (2020-2025)')
plt.xlabel('Volatility (standard deviation of monthly % change)')
#plt.ylabel('COICOP category')

#layout
plt.gca().invert_yaxis() #Get Current Axes ('gca') and flip the visual order so the most volatile categoires appear at the top (without affecting the actual ordering)
plt.grid(True, axis='x', alpha=0.3)
plt.tight_layout()

#save
plt.savefig('../figures/volatility_barchart.png', dpi=200)
plt.close()