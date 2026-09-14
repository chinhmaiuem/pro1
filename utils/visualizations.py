"""
Visualization Helper Functions
Plotly-based interactive visualizations for the dashboard
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# Color schemes
COLORS = px.colors.qualitative.Set2
SEQUENTIAL = px.colors.sequential.Blues

def create_metric_cards(metrics_dict):
    """
    Create metric cards HTML

    Args:
        metrics_dict: Dictionary of {label: value} pairs

    Returns:
        str: HTML string for metric cards
    """
    html = '<div style="display: flex; flex-wrap: wrap; gap: 1rem;">'

    for label, value in metrics_dict.items():
        html += f'''
        <div class="metric-card" style="flex: 1; min-width: 200px;">
            <h4 style="margin: 0; color: #7f8c8d;">{label}</h4>
            <h2 style="margin: 0.5rem 0 0 0; color: #2c3e50;">{value}</h2>
        </div>
        '''

    html += '</div>'
    return html

## ==========================================
## EXECUTIVE SUMMARY VISUALIZATIONS
## ==========================================

def plot_transaction_trends(df, filters=None):
    """
    Q1: Transaction trends over time (2010-2019)

    Args:
        df: Merged transactions DataFrame
        filters: Dict with filter values {gender, age_group, card_type, mcc_category}

    Returns:
        plotly figure
    """
    # Apply filters
    df_filtered = apply_filters(df, filters)

    # Aggregate by year-month
    df_agg = df_filtered.groupby(df_filtered['date'].dt.to_period('M')).agg({
        'amount': ['sum', 'mean', 'count']
    }).reset_index()

    df_agg.columns = ['date', 'total_value', 'avg_value', 'count']
    df_agg['date'] = df_agg['date'].dt.to_timestamp()

    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Total Transaction Value Over Time', 'Number of Transactions Over Time'),
        vertical_spacing=0.12,
        row_heights=[0.5, 0.5]
    )

    # Total value trend
    fig.add_trace(
        go.Scatter(
            x=df_agg['date'],
            y=df_agg['total_value'],
            mode='lines',
            name='Total Value',
            line=dict(color=COLORS[0], width=2),
            fill='tozeroy',
            hovertemplate='<b>%{x|%Y-%m}</b><br>Total: $%{y:,.0f}<extra></extra>'
        ),
        row=1, col=1
    )

    # Transaction count trend
    fig.add_trace(
        go.Scatter(
            x=df_agg['date'],
            y=df_agg['count'],
            mode='lines',
            name='Count',
            line=dict(color=COLORS[1], width=2),
            fill='tozeroy',
            hovertemplate='<b>%{x|%Y-%m}</b><br>Transactions: %{y:,.0f}<extra></extra>'
        ),
        row=2, col=1
    )

    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Total Value ($)", row=1, col=1)
    fig.update_yaxes(title_text="Transaction Count", row=2, col=1)

    fig.update_layout(
        height=600,
        showlegend=False,
        hovermode='x unified',
        template='plotly_white'
    )

    return fig

def plot_customer_distribution(df, filters=None):
    """
    Q2: Customer distribution and Pareto analysis (80-20 rule)

    Returns:
        plotly figure
    """
    df_filtered = apply_filters(df, filters)

    # Calculate customer spending
    customer_spend = df_filtered.groupby('client_id')['amount'].sum().sort_values(ascending=False).reset_index()
    customer_spend.columns = ['client_id', 'total_spend']

    # Calculate cumulative percentage
    customer_spend['cumsum'] = customer_spend['total_spend'].cumsum()
    customer_spend['cumsum_pct'] = (customer_spend['cumsum'] / customer_spend['total_spend'].sum()) * 100
    customer_spend['customer_pct'] = (np.arange(1, len(customer_spend) + 1) / len(customer_spend)) * 100

    # Create Pareto chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Histogram of spending
    fig.add_trace(
        go.Histogram(
            x=customer_spend['total_spend'],
            nbinsx=50,
            name='Customers',
            marker_color=COLORS[0],
            opacity=0.7
        ),
        secondary_y=False
    )

    # Add 80-20 line
    top_20_pct_customers = int(len(customer_spend) * 0.2)
    revenue_from_top_20 = customer_spend.iloc[:top_20_pct_customers]['total_spend'].sum()
    total_revenue = customer_spend['total_spend'].sum()
    pct_from_top_20 = (revenue_from_top_20 / total_revenue) * 100

    fig.update_layout(
        title=f'Customer Spending Distribution<br><sup>Top 20% customers generate {pct_from_top_20:.1f}% of revenue</sup>',
        xaxis_title='Total Spending ($)',
        yaxis_title='Number of Customers',
        height=400,
        template='plotly_white',
        showlegend=False
    )

    return fig

def plot_rfm_segments(rfm_df):
    """
    Q11: RFM Segmentation overview

    Args:
        rfm_df: RFM DataFrame from segmentation module

    Returns:
        plotly figure
    """
    # Count customers per segment
    segment_counts = rfm_df['Segment'].value_counts().reset_index()
    segment_counts.columns = ['Segment', 'Count']

    # Calculate metrics per segment
    segment_metrics = rfm_df.groupby('Segment').agg({
        'Recency': 'mean',
        'Frequency': 'mean',
        'Monetary': 'mean',
        'RFM_Score': 'mean'
    }).reset_index()

    segment_data = segment_counts.merge(segment_metrics, on='Segment')

    # Sort by RFM score
    segment_data = segment_data.sort_values('RFM_Score', ascending=False)

    # Create stacked bar chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=segment_data['Segment'],
        x=segment_data['Count'],
        orientation='h',
        marker=dict(
            color=segment_data['RFM_Score'],
            colorscale='Blues',
            showscale=True,
            colorbar=dict(title="RFM Score")
        ),
        text=segment_data['Count'],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>' +
                     'Customers: %{x:,.0f}<br>' +
                     'Avg Recency: %{customdata[0]:.0f} days<br>' +
                     'Avg Frequency: %{customdata[1]:.0f} transactions<br>' +
                     'Avg Monetary: $%{customdata[2]:,.0f}<br>' +
                     '<extra></extra>',
        customdata=segment_data[['Recency', 'Frequency', 'Monetary']].values
    ))

    fig.update_layout(
        title='RFM Customer Segments',
        xaxis_title='Number of Customers',
        yaxis_title='Segment',
        height=500,
        template='plotly_white'
    )

    return fig

def plot_segment_ltv(ltv_df, segment_df):
    """
    Q18: Lifetime Value by segment

    Args:
        ltv_df: LTV DataFrame
        segment_df: Segment assignment DataFrame

    Returns:
        plotly figure
    """
    # Merge LTV with segments
    df = ltv_df.merge(segment_df[['client_id', 'Segment']], on='client_id', how='left')

    # Calculate average LTV per segment
    segment_ltv = df.groupby('Segment').agg({
        'LTV': ['mean', 'sum', 'count']
    }).reset_index()

    segment_ltv.columns = ['Segment', 'Avg_LTV', 'Total_LTV', 'Count']
    segment_ltv = segment_ltv.sort_values('Avg_LTV', ascending=True)

    # Create horizontal bar chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=segment_ltv['Segment'],
        x=segment_ltv['Avg_LTV'],
        orientation='h',
        marker_color=COLORS[2],
        text=['${:,.0f}'.format(x) for x in segment_ltv['Avg_LTV']],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>' +
                     'Average LTV: $%{x:,.0f}<br>' +
                     'Total LTV: $%{customdata[0]:,.0f}<br>' +
                     'Customers: %{customdata[1]:,.0f}<br>' +
                     '<extra></extra>',
        customdata=segment_ltv[['Total_LTV', 'Count']].values
    ))

    fig.update_layout(
        title='Lifetime Value by Customer Segment',
        xaxis_title='Average Lifetime Value ($)',
        yaxis_title='Segment',
        height=500,
        template='plotly_white'
    )

    return fig

def plot_crosssell_opportunities(df, df_cards):
    """
    Q19: Cross-selling opportunities - Target Debit users for Credit cards

    Returns:
        plotly figure with opportunity matrix
    """
    # Merge transactions with card info
    df = df.drop(columns=['id_card', 'client_id_card'], errors='ignore')
    df_with_cards = df.merge(df_cards[['id', 'card_type', 'client_id']],
                              left_on='card_id', right_on='id',
                              how='left', suffixes=('', '_card'))

    # Find high-spending Debit users
    debit_users = df_with_cards[df_with_cards['card_type'].isin(['Debit', 'Debit (Prepaid)'])]

    debit_spending = debit_users.groupby('client_id').agg({
        'amount': 'sum',
        'id': 'count'
    }).reset_index()
    debit_spending.columns = ['client_id', 'total_spend', 'transaction_count']

    # Categorize opportunity
    debit_spending['opportunity'] = pd.cut(
        debit_spending['total_spend'],
        bins=[0, 10000, 50000, 100000, float('inf')],
        labels=['Low', 'Medium', 'High', 'Very High']
    )

    opportunity_counts = debit_spending['opportunity'].value_counts().reset_index()
    opportunity_counts.columns = ['Opportunity', 'Count']

    # Create funnel chart
    fig = go.Figure(go.Funnel(
        y=opportunity_counts['Opportunity'],
        x=opportunity_counts['Count'],
        textinfo="value+percent initial",
        marker=dict(color=COLORS[:len(opportunity_counts)])
    ))

    fig.update_layout(
        title='Credit Card Cross-Sell Opportunities<br><sup>Debit users by spending level</sup>',
        height=400,
        template='plotly_white'
    )

    return fig


## ==========================================
## CUSTOMER BEHAVIOR VISUALIZATIONS (Q3-Q10)
## ==========================================

def plot_payment_method_trends(df, filters=None):
    """
    Q3: Payment Method Usage & Trends

    Returns:
        plotly figure showing payment method usage over time
    """
    df_filtered = apply_filters(df, filters)

    # Aggregate by card type and year
    payment_trends = df_filtered.groupby(['year', 'card_type'])['amount'].agg(['sum', 'count']).reset_index()
    payment_trends.columns = ['year', 'card_type', 'total_amount', 'transaction_count']

    # Create stacked area chart
    fig = go.Figure()

    for card_type in payment_trends['card_type'].unique():
        data = payment_trends[payment_trends['card_type'] == card_type]
        fig.add_trace(go.Scatter(
            x=data['year'],
            y=data['total_amount'],
            name=card_type,
            mode='lines',
            stackgroup='one',
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Year: %{x}<br>' +
                         'Amount: $%{y:,.0f}<br>' +
                         '<extra></extra>'
        ))

    fig.update_layout(
        title='Payment Method Usage Trends (2010-2019)',
        xaxis_title='Year',
        yaxis_title='Total Transaction Amount ($)',
        height=500,
        template='plotly_white',
        hovermode='x unified'
    )

    return fig

def plot_top_merchant_categories(df, filters=None, top_n=10):
    """
    Q4: Top Merchant Categories

    Returns:
        plotly figure showing top merchant categories by spending
    """
    df_filtered = apply_filters(df, filters)

    # Aggregate by merchant category
    category_spend = df_filtered.groupby('merchant_category').agg({
        'amount': ['sum', 'count'],
        'client_id': 'nunique'
    }).reset_index()

    category_spend.columns = ['merchant_category', 'total_amount', 'transaction_count', 'unique_customers']
    category_spend = category_spend.sort_values('total_amount', ascending=False).head(top_n)

    # Create horizontal bar chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=category_spend['merchant_category'][::-1],
        x=category_spend['total_amount'][::-1],
        orientation='h',
        marker_color=COLORS[3],
        text=['${:,.0f}'.format(x) for x in category_spend['total_amount'][::-1]],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>' +
                     'Total: $%{x:,.0f}<br>' +
                     'Transactions: %{customdata[0]:,.0f}<br>' +
                     'Customers: %{customdata[1]:,.0f}<br>' +
                     '<extra></extra>',
        customdata=category_spend[['transaction_count', 'unique_customers']][::-1].values
    ))

    fig.update_layout(
        title=f'Top {top_n} Merchant Categories by Spending',
        xaxis_title='Total Spending ($)',
        yaxis_title='Merchant Category',
        height=500,
        template='plotly_white'
    )

    return fig

def plot_gender_spending_comparison(df, filters=None):
    """
    Q5: Gender Spending Comparison

    Returns:
        plotly figure comparing spending patterns by gender
    """
    df_filtered = apply_filters(df, filters)

    # Remove null gender values
    df_filtered = df_filtered[df_filtered['gender'].notna()]

    # Aggregate by gender and year
    gender_spend = df_filtered.groupby(['year', 'gender'])['amount'].agg(['sum', 'mean', 'count']).reset_index()
    gender_spend.columns = ['year', 'gender', 'total_spend', 'avg_spend', 'transaction_count']

    # Create subplots
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Total Spending by Gender', 'Average Transaction Value by Gender'),
        horizontal_spacing=0.12
    )

    # Total spending
    for gender in gender_spend['gender'].unique():
        data = gender_spend[gender_spend['gender'] == gender]
        fig.add_trace(
            go.Scatter(
                x=data['year'],
                y=data['total_spend'],
                name=gender,
                mode='lines+markers',
                hovertemplate='<b>%{fullData.name}</b><br>Year: %{x}<br>Total: $%{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )

    # Average transaction value
    for gender in gender_spend['gender'].unique():
        data = gender_spend[gender_spend['gender'] == gender]
        fig.add_trace(
            go.Scatter(
                x=data['year'],
                y=data['avg_spend'],
                name=gender,
                mode='lines+markers',
                showlegend=False,
                hovertemplate='<b>%{fullData.name}</b><br>Year: %{x}<br>Avg: $%{y:,.2f}<extra></extra>'
            ),
            row=1, col=2
        )

    fig.update_xaxes(title_text="Year", row=1, col=1)
    fig.update_xaxes(title_text="Year", row=1, col=2)
    fig.update_yaxes(title_text="Total Spending ($)", row=1, col=1)
    fig.update_yaxes(title_text="Average Transaction ($)", row=1, col=2)

    fig.update_layout(
        height=500,
        template='plotly_white',
        hovermode='x unified'
    )

    return fig

def plot_age_group_analysis(df, filters=None):
    """
    Q6: Age Group Analysis

    Returns:
        plotly figure showing spending by age group
    """
    df_filtered = apply_filters(df, filters)

    # Remove null age groups
    df_filtered = df_filtered[df_filtered['age_group'].notna()]

    # Aggregate by age group
    age_spend = df_filtered.groupby('age_group').agg({
        'amount': ['sum', 'mean', 'count'],
        'client_id': 'nunique'
    }).reset_index()

    age_spend.columns = ['age_group', 'total_spend', 'avg_spend', 'transaction_count', 'unique_customers']

    # Sort by age group order
    age_order = ['18-25', '26-35', '36-45', '46-55', '56-65', '65+']
    age_spend['age_group'] = pd.Categorical(age_spend['age_group'], categories=age_order, ordered=True)
    age_spend = age_spend.sort_values('age_group')

    # Create grouped bar chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=age_spend['age_group'],
        y=age_spend['total_spend'],
        name='Total Spending',
        marker_color=COLORS[0],
        yaxis='y',
        hovertemplate='<b>%{x}</b><br>Total: $%{y:,.0f}<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=age_spend['age_group'],
        y=age_spend['avg_spend'],
        name='Avg Transaction',
        mode='lines+markers',
        marker_color=COLORS[1],
        yaxis='y2',
        hovertemplate='<b>%{x}</b><br>Avg: $%{y:,.2f}<extra></extra>'
    ))

    fig.update_layout(
        title='Spending Analysis by Age Group',
        xaxis_title='Age Group',
        yaxis=dict(title='Total Spending ($)'),
        yaxis2=dict(title='Average Transaction ($)', overlaying='y', side='right'),
        height=500,
        template='plotly_white',
        hovermode='x unified'
    )

    return fig

def plot_income_vs_spending(df, filters=None):
    """
    Q7: Income vs Spending Relationship

    Returns:
        plotly figure showing correlation between income and spending
    """
    df_filtered = apply_filters(df, filters)

    # Aggregate spending by customer
    customer_spend = df_filtered.groupby('client_id').agg({
        'amount': 'sum',
        'yearly_income': 'first',
        'income_tier': 'first'
    }).reset_index()

    customer_spend.columns = ['client_id', 'total_spend', 'yearly_income', 'income_tier']

    # Remove null values
    customer_spend = customer_spend.dropna(subset=['yearly_income', 'income_tier'])

    # Create scatter plot with income tiers
    fig = px.scatter(
        customer_spend,
        x='yearly_income',
        y='total_spend',
        color='income_tier',
        color_discrete_sequence=COLORS,
        opacity=0.6,
        labels={
            'yearly_income': 'Yearly Income ($)',
            'total_spend': 'Total Spending ($)',
            'income_tier': 'Income Tier'
        },
        title='Income vs Spending Relationship',
        trendline='ols',
        trendline_scope='overall'
    )

    fig.update_layout(
        height=500,
        template='plotly_white'
    )

    return fig

def plot_seasonality_analysis(df, filters=None):
    """
    Q8: Seasonality Analysis

    Returns:
        plotly figure showing seasonal spending patterns
    """
    df_filtered = apply_filters(df, filters)

    # Aggregate by month and quarter
    monthly_spend = df_filtered.groupby('month')['amount'].agg(['sum', 'mean', 'count']).reset_index()
    monthly_spend.columns = ['month', 'total_spend', 'avg_spend', 'transaction_count']

    quarterly_spend = df_filtered.groupby('quarter')['amount'].agg(['sum', 'mean', 'count']).reset_index()
    quarterly_spend.columns = ['quarter', 'total_spend', 'avg_spend', 'transaction_count']

    # Create subplots
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Monthly Spending Patterns', 'Quarterly Spending Patterns'),
        horizontal_spacing=0.12
    )

    # Monthly chart
    fig.add_trace(
        go.Bar(
            x=monthly_spend['month'],
            y=monthly_spend['total_spend'],
            name='Monthly',
            marker_color=COLORS[2],
            hovertemplate='Month: %{x}<br>Total: $%{y:,.0f}<extra></extra>'
        ),
        row=1, col=1
    )

    # Quarterly chart
    fig.add_trace(
        go.Bar(
            x=quarterly_spend['quarter'],
            y=quarterly_spend['total_spend'],
            name='Quarterly',
            marker_color=COLORS[3],
            hovertemplate='Q%{x}<br>Total: $%{y:,.0f}<extra></extra>'
        ),
        row=1, col=2
    )

    fig.update_xaxes(title_text="Month", row=1, col=1)
    fig.update_xaxes(title_text="Quarter", row=1, col=2)
    fig.update_yaxes(title_text="Total Spending ($)", row=1, col=1)
    fig.update_yaxes(title_text="Total Spending ($)", row=1, col=2)

    fig.update_layout(
        height=500,
        showlegend=False,
        template='plotly_white'
    )

    return fig

def plot_transaction_frequency(df, filters=None):
    """
    Q9: Transaction Frequency Analysis

    Returns:
        plotly figure showing customer transaction frequency distribution
    """
    df_filtered = apply_filters(df, filters)

    # Calculate transactions per customer
    customer_freq = df_filtered.groupby('client_id')['id'].count().reset_index()
    customer_freq.columns = ['client_id', 'transaction_count']

    # Create frequency bins
    customer_freq['frequency_bin'] = pd.cut(
        customer_freq['transaction_count'],
        bins=[0, 10, 50, 100, 500, float('inf')],
        labels=['1-10', '11-50', '51-100', '101-500', '500+']
    )

    freq_dist = customer_freq['frequency_bin'].value_counts().sort_index().reset_index()
    freq_dist.columns = ['frequency_bin', 'customer_count']

    # Create bar chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=freq_dist['frequency_bin'],
        y=freq_dist['customer_count'],
        marker_color=COLORS[4],
        text=freq_dist['customer_count'],
        textposition='outside',
        hovertemplate='<b>%{x} transactions</b><br>Customers: %{y:,.0f}<extra></extra>'
    ))

    fig.update_layout(
        title='Customer Transaction Frequency Distribution',
        xaxis_title='Number of Transactions',
        yaxis_title='Number of Customers',
        height=500,
        template='plotly_white'
    )

    return fig

def plot_geographic_distribution(df, filters=None, top_n=15):
    """
    Q10: Geographic Distribution

    Returns:
        plotly figure showing spending by state
    """
    df_filtered = apply_filters(df, filters)

    # Aggregate by state
    state_spend = df_filtered.groupby('merchant_state').agg({
        'amount': ['sum', 'count'],
        'client_id': 'nunique'
    }).reset_index()

    state_spend.columns = ['state', 'total_spend', 'transaction_count', 'unique_customers']
    state_spend = state_spend.sort_values('total_spend', ascending=False).head(top_n)

    # Create map-style bar chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=state_spend['state'][::-1],
        y=state_spend['total_spend'][::-1],
        marker=dict(
            color=state_spend['total_spend'][::-1],
            colorscale='Blues',
            showscale=True,
            colorbar=dict(title="Total Spending")
        ),
        text=['${:,.0f}'.format(x) for x in state_spend['total_spend'][::-1]],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>' +
                     'Total: $%{y:,.0f}<br>' +
                     'Transactions: %{customdata[0]:,.0f}<br>' +
                     'Customers: %{customdata[1]:,.0f}<br>' +
                     '<extra></extra>',
        customdata=state_spend[['transaction_count', 'unique_customers']][::-1].values
    ))

    fig.update_layout(
        title=f'Top {top_n} States by Transaction Volume',
        xaxis_title='State',
        yaxis_title='Total Spending ($)',
        height=500,
        template='plotly_white'
    )

    return fig


## ==========================================
## HELPER FUNCTIONS
## ==========================================

def apply_filters(df, filters):
    """
    Apply filters to DataFrame

    Args:
        df: DataFrame to filter
        filters: Dict with filter values

    Returns:
        Filtered DataFrame
    """
    if filters is None:
        return df

    df_filtered = df.copy()

    if 'gender' in filters and filters['gender']:
        df_filtered = df_filtered[df_filtered['gender'] == filters['gender']]

    if 'age_group' in filters and filters['age_group']:
        df_filtered = df_filtered[df_filtered['age_group'] == filters['age_group']]

    if 'card_type' in filters and filters['card_type']:
        df_filtered = df_filtered[df_filtered['card_type'] == filters['card_type']]

    if 'year' in filters and filters['year']:
        df_filtered = df_filtered[df_filtered['year'] == filters['year']]

    if 'mcc_category' in filters and filters['mcc_category']:
        df_filtered = df_filtered[df_filtered['merchant_category'] == filters['mcc_category']]

    return df_filtered

def format_currency(value):
    """Format value as currency"""
    if value >= 1e9:
        return f'${value/1e9:.2f}B'
    elif value >= 1e6:
        return f'${value/1e6:.2f}M'
    elif value >= 1e3:
        return f'${value/1e3:.2f}K'
    else:
        return f'${value:.2f}'

def format_number(value):
    """Format number with commas"""
    return f'{value:,.0f}'
