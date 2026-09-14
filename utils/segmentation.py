"""
Customer Segmentation Module
Implements RFM, Lifecycle, and Financial Health segmentation
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import streamlit as st

@st.cache_data
def perform_rfm_segmentation(_df_trans, reference_date=None):
    """
    Perform RFM (Recency, Frequency, Monetary) segmentation

    Args:
        _df_trans: Transactions DataFrame
        reference_date: Reference date for recency calculation (default: max date in data)

    Returns:
        DataFrame: Customer-level RFM scores and segments
    """
    if reference_date is None:
        reference_date = _df_trans['date'].max()

    # Calculate RFM metrics per customer
    rfm = _df_trans.groupby('client_id').agg({
        'date': lambda x: (reference_date - x.max()).days,  # Recency
        'id': 'count',  # Frequency
        'amount': 'sum'  # Monetary
    }).rename(columns={
        'date': 'Recency',
        'id': 'Frequency',
        'amount': 'Monetary'
    })

    # Calculate RFM scores (1-5 scale)
    # Note: For Recency, lower is better, so we reverse the scoring
    # Use rank-based scoring to handle duplicates
    rfm['R_Score'] = 6 - pd.qcut(rfm['Recency'].rank(method='first'), q=5, labels=False, duplicates='drop') - 1
    rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), q=5, labels=False, duplicates='drop') + 1
    rfm['M_Score'] = pd.qcut(rfm['Monetary'].rank(method='first'), q=5, labels=False, duplicates='drop') + 1

    # Ensure scores are in 1-5 range
    rfm['R_Score'] = rfm['R_Score'].clip(1, 5)
    rfm['F_Score'] = rfm['F_Score'].clip(1, 5)
    rfm['M_Score'] = rfm['M_Score'].clip(1, 5)

    # Calculate total RFM score
    rfm['RFM_Score'] = rfm['R_Score'] + rfm['F_Score'] + rfm['M_Score']

    # Segment assignment based on RFM scores
    rfm['Segment'] = rfm.apply(assign_rfm_segment, axis=1)

    return rfm.reset_index()

def assign_rfm_segment(row):
    """Assign RFM segment based on R, F, M scores"""
    r, f, m = row['R_Score'], row['F_Score'], row['M_Score']

    # Champions: High R, F, M
    if r >= 4 and f >= 4 and m >= 4:
        return 'Champions'

    # Loyal Customers: High F
    elif f >= 4:
        return 'Loyal'

    # Big Spenders: High M
    elif m >= 4:
        return 'Big Spenders'

    # Promising: High R
    elif r >= 4:
        return 'Promising'

    # At Risk: Low R, but high F or M
    elif r <= 2 and (f >= 3 or m >= 3):
        return 'At Risk'

    # Lost: Low R, F, M
    elif r <= 2 and f <= 2:
        return 'Lost'

    # Need Attention: Medium scores
    elif r == 3 and f <= 3:
        return 'Need Attention'

    # Others
    else:
        return 'Others'

@st.cache_data
def lifecycle_segmentation(_df_users):
    """
    Segment customers based on lifecycle stage (age and retirement planning)

    Returns:
        DataFrame: Users with lifecycle segment assignment
    """
    df = _df_users.copy()

    def assign_lifecycle(row):
        age = row['current_age']
        retirement_age = row['retirement_age']
        years_to_retirement = retirement_age - age

        if age < 30:
            return 'Young Professionals'
        elif age < 50:
            return 'Mid-Career'
        elif years_to_retirement > 5:
            return 'Pre-Retirement'
        else:
            return 'Retirees'

    df['Lifecycle_Segment'] = df.apply(assign_lifecycle, axis=1)

    return df[['id', 'current_age', 'retirement_age', 'Lifecycle_Segment']]

@st.cache_data
def financial_health_segmentation(_df_users):
    """
    Segment customers based on financial health (credit score and debt-to-income)

    Returns:
        DataFrame: Users with financial health segment
    """
    df = _df_users.copy()

    def assign_financial_health(row):
        credit_score = row['credit_score']
        dti = row['debt_to_income']

        # Handle missing DTI
        if pd.isna(dti):
            dti = df['debt_to_income'].median()

        # Excellent: High credit score, low DTI
        if credit_score >= 750 and dti < 0.3:
            return 'Excellent'

        # Good: Good credit, reasonable DTI
        elif credit_score >= 700 and dti < 0.5:
            return 'Good'

        # Fair: Medium credit or medium DTI
        elif credit_score >= 650:
            return 'Fair'

        # Poor: Low credit or high DTI
        else:
            return 'Poor'

    df['Financial_Health'] = df.apply(assign_financial_health, axis=1)

    return df[['id', 'credit_score', 'debt_to_income', 'Financial_Health']]

@st.cache_data
def calculate_customer_ltv(_df_trans, _df_users, years_horizon=5):
    """
    Calculate Customer Lifetime Value

    Args:
        _df_trans: Transactions DataFrame
        _df_users: Users DataFrame
        years_horizon: Expected years as customer

    Returns:
        DataFrame: Customer LTV
    """
    # Calculate annual spending per customer
    df = _df_trans.copy()
    df['year'] = df['date'].dt.year

    annual_spend = df.groupby(['client_id', 'year'])['amount'].sum().reset_index()
    avg_annual_spend = annual_spend.groupby('client_id')['amount'].mean().reset_index()
    avg_annual_spend.columns = ['client_id', 'avg_annual_spend']

    # Merge with users to get age
    ltv = avg_annual_spend.merge(_df_users[['id', 'current_age', 'retirement_age']],
                                  left_on='client_id', right_on='id', how='left')

    # Calculate expected years (minimum of horizon or years to retirement)
    ltv['years_to_retirement'] = ltv['retirement_age'] - ltv['current_age']
    ltv['expected_years'] = ltv['years_to_retirement'].clip(upper=years_horizon)

    # Calculate LTV
    ltv['LTV'] = ltv['avg_annual_spend'] * ltv['expected_years']

    return ltv[['client_id', 'avg_annual_spend', 'expected_years', 'LTV']]
