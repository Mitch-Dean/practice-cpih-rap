# -*- coding: utf-8 -*-
"""
Created on Tue Jan 27 12:59:49 2026

@author: deanm
"""

import pandas as pd

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

#create lagged index for each category
cpih_data['lag_1'] = grouped['index_value'].shift(1)
cpih_data['lag_12'] = grouped['index_value'].shift(12)

#QA check: ensure lag columns have been created
assert 'lag_1' in cpih_data.columns and 'lag_12' in cpih_data.columns, "Lag columns not created."

#compute inflation rates
cpih_data['monthly_pct'] = (cpih_data['index_value'] / cpih_data['lag_1'] - 1) * 100
cpih_data['annual_pct'] = (cpih_data['index_value'] / cpih_data['lag_12'] -1) * 100

#QA check: ensure pct columns have been populated
assert cpih_data['monthly_pct'].notna().any(), "Monthly_pct has no values."
assert cpih_data['annual_pct'].notna().any(), "Annual_pct has no values."