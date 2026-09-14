"""
Data Loading and Preprocessing Module
Handles loading of all CSV files and basic preprocessing
"""

import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st

# Base path
BASE_PATH = Path(__file__).parent.parent

@st.cache_data
def load_all_data(use_sample=True):
    """
    Load all datasets for the dashboard

    Args:
        use_sample (bool): If True, use 25% sample for transactions, else use full dataset

    Returns:
        tuple: (df_trans, df_cards, df_users, df_fraud, df_mcc)
    """
    # Select transactions file
    trans_file = 'transactions_data_25pc.csv' if use_sample else 'transactions_data.csv'

    # Load data with optimized dtypes
    print(f"Loading {trans_file}...")
    df_trans = pd.read_csv(
        BASE_PATH / trans_file,
        dtype={
            'id': 'int32',
            'client_id': 'int16',
            'card_id': 'int16',
            # 'amount' will be cleaned in preprocessing
            'use_chip': 'category',
            'merchant_id': 'int32',
            'merchant_city': 'category',
            'merchant_state': 'category',
            'zip': 'str',
            'mcc': 'int16'
        },
        parse_dates=['date']
    )

    print("Loading cards_data.csv...")
    df_cards = pd.read_csv(
        BASE_PATH / 'cards_data.csv',
        dtype={
            'id': 'int16',
            'client_id': 'int16',
            'card_brand': 'category',
            'card_type': 'category',
            'has_chip': 'category',
            'card_on_dark_web': 'category'
        },
        parse_dates=['expires', 'acct_open_date']
    )

    print("Loading users_data.csv...")
    df_users = pd.read_csv(
        BASE_PATH / 'users_data.csv',
        dtype={
            'id': 'int16',
            'current_age': 'int8',
            'retirement_age': 'int8',
            'birth_year': 'int16',
            'birth_month': 'int8',
            'gender': 'category',
            'num_credit_cards': 'int8'
        }
    )

    print("Loading train_fraud_labels.csv...")
    df_fraud = pd.read_csv(
        BASE_PATH / 'train_fraud_labels.csv',
        dtype={
            'id': 'int32'
            # 'label' will be converted in preprocessing
        }
    )
    # Convert label column: 'Yes' -> 1, 'No' -> 0
    df_fraud['target'] = (df_fraud['label'] == 'Yes').astype('int8')

    print("Loading mcc_codes.csv...")
    df_mcc = pd.read_csv(
        BASE_PATH / 'mcc_codes.csv',
        dtype={
            'mcc_code': 'int16',
            'merchant_category': 'str'
        }
    )

    # Basic preprocessing
    df_trans = preprocess_transactions(df_trans)
    df_users = preprocess_users(df_users)
    df_cards = preprocess_cards(df_cards)

    print("Data loading complete!")
    return df_trans, df_cards, df_users, df_fraud, df_mcc

def preprocess_transactions(df):
    """Preprocess transactions data"""
    # Clean amount column (remove $ and convert to float)
    if df['amount'].dtype == 'object':
        df['amount'] = df['amount'].str.replace('$', '', regex=False).str.replace(',', '', regex=False).astype('float32')
    else:
        df['amount'] = df['amount'].astype('float32')

    # Extract date components
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['day_of_week'] = df['date'].dt.dayofweek
    df['hour'] = df['date'].dt.hour
    df['quarter'] = df['date'].dt.quarter

    # Handle errors column
    df['has_error'] = df['errors'].notna().astype('int8')

    return df

def preprocess_users(df):
    """Preprocess users data"""
    # Clean currency columns (remove $ and convert to numeric)
    currency_cols = ['per_capita_income', 'yearly_income', 'total_debt']
    for col in currency_cols:
        if df[col].dtype == 'object':
            df[col] = df[col].str.replace('$', '', regex=False).str.replace(',', '', regex=False).astype('float64')

    # Create age groups
    df['age_group'] = pd.cut(
        df['current_age'],
        bins=[0, 25, 35, 45, 55, 65, 120],
        labels=['18-25', '26-35', '36-45', '46-55', '56-65', '65+']
    )

    # Create income tiers
    df['income_tier'] = pd.qcut(
        df['yearly_income'],
        q=3,
        labels=['Low', 'Medium', 'High'],
        duplicates='drop'
    )

    # Debt to income ratio
    df['debt_to_income'] = df['total_debt'] / df['yearly_income']
    df['debt_to_income'] = df['debt_to_income'].replace([np.inf, -np.inf], np.nan)

    # Credit score categories
    df['credit_category'] = pd.cut(
        df['credit_score'],
        bins=[0, 600, 700, 750, 850],
        labels=['Poor', 'Fair', 'Good', 'Excellent']
    )

    return df

def preprocess_cards(df):
    """Preprocess cards data"""
    # Clean credit_limit column (remove $ and convert to numeric)
    if 'credit_limit' in df.columns and df['credit_limit'].dtype == 'object':
        df['credit_limit'] = df['credit_limit'].str.replace('$', '', regex=False).str.replace(',', '', regex=False).astype('float64')

    # Extract account open year
    df['acct_open_year'] = df['acct_open_date'].dt.year

    # Card age (as of 2019, end of data period)
    df['card_age_years'] = 2019 - df['acct_open_year']

    return df

@st.cache_data
def get_merged_data(_df_trans, _df_cards, _df_users, _df_fraud, _df_mcc):
    """
    Merge all datasets for comprehensive analysis

    Returns:
        DataFrame: Merged dataset with all information
    """
    # Start with transactions
    df = _df_trans.copy()

    # Merge with fraud labels
    df = df.merge(_df_fraud[['id', 'target']], on='id', how='left', suffixes=('', '_fraud'))
    df['is_fraud'] = df['target'].fillna(0).astype('int8')
    df.drop('target', axis=1, inplace=True, errors='ignore')

    # Merge with MCC codes
    df = df.merge(_df_mcc, left_on='mcc', right_on='mcc_code', how='left')

    # Merge with cards
    df = df.merge(
        _df_cards[['id', 'client_id', 'card_type', 'card_brand', 'credit_limit',
                   'has_chip', 'card_on_dark_web', 'card_age_years']],
        left_on='card_id',
        right_on='id',
        how='left',
        suffixes=('', '_card')
    )

    # Merge with users
    df = df.merge(
        _df_users[['id', 'current_age', 'age_group', 'gender', 'yearly_income',
                   'income_tier', 'total_debt', 'debt_to_income', 'credit_score',
                   'credit_category', 'num_credit_cards']],
        left_on='client_id',
        right_on='id',
        how='left',
        suffixes=('', '_user')
    )

    return df

def get_sample_data(df, n=10000):
    """Get a random sample of data for testing"""
    return df.sample(n=min(n, len(df)))
