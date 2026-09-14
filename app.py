"""
Company X Financial Analytics Dashboard
Module 2 Final Project - COLE.VN DS Course K06

Main Streamlit application file
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# Import custom modules
from utils.data_loader import load_all_data, get_sample_data, get_merged_data
from utils.segmentation import perform_rfm_segmentation, lifecycle_segmentation, financial_health_segmentation, calculate_customer_ltv
from utils.visualizations import *

# Page configuration
st.set_page_config(
    page_title="Company X Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .insight-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'use_sample' not in st.session_state:
    st.session_state.use_sample = True

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/300x100/1f77b4/ffffff?text=Company+X", width='stretch')
    st.markdown("## ⚙️ Settings")

    # Data source selection
    use_sample = st.checkbox("Use 25% Sample Data (Faster)", value=True,
                            help="Recommended for faster loading. Uncheck to use full dataset.")
    st.session_state.use_sample = use_sample

    # Load data button
    if st.button("🔄 Load/Reload Data", type="primary"):
        with st.spinner("Loading data..."):
            st.session_state.data_loaded = False
            st.session_state.df_trans, st.session_state.df_cards, st.session_state.df_users, \
            st.session_state.df_fraud, st.session_state.df_mcc = load_all_data(use_sample=use_sample)
            st.session_state.data_loaded = True
            st.success("✅ Data loaded successfully!")

    st.markdown("---")
    st.markdown("### 📊 Dashboard Sections")
    st.markdown("""
    - **Executive Summary**: Key insights at a glance
    - **Customer Behavior**: 10 core behavior analyses
    - **Segmentation**: 3 segmentation approaches
    - **Segment Deep-Dive**: Behavior by segment
    - **Strategy & Fraud**: Recommendations + Risk analysis
    """)

    st.markdown("---")
    st.markdown("### 📖 About")
    st.markdown("""
    **Project**: Module 2 Final Project
    **Course**: COLE.VN DS K06
    **Dataset**: Financial transactions 2010-2019
    **Questions Analyzed**: 25 core questions
    """)

# Main content
st.markdown('<div class="main-header">📊 Company X Financial Analytics Dashboard</div>', unsafe_allow_html=True)

# Check if data is loaded
if not st.session_state.data_loaded:
    st.warning("⚠️ Please load data using the button in the sidebar to begin analysis.")
    st.info("""
    **Getting Started:**
    1. Click "Load/Reload Data" in the sidebar
    2. Choose whether to use sample (25%) or full dataset
    3. Wait for data to load
    4. Explore the dashboard tabs
    """)
    st.stop()

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Executive Summary",
    "👥 Customer Behavior",
    "🎯 Segmentation",
    "🔍 Segment Deep-Dive",
    "💡 Strategy & Fraud"
])

# Tab 1: Executive Summary
with tab1:
    st.markdown('<div class="sub-header">Executive Summary</div>', unsafe_allow_html=True)

    # Prepare merged data
    with st.spinner("Preparing data for analysis..."):
        if 'df_merged' not in st.session_state:
            st.session_state.df_merged = get_merged_data(
                st.session_state.df_trans,
                st.session_state.df_cards,
                st.session_state.df_users,
                st.session_state.df_fraud,
                st.session_state.df_mcc
            )

        # Calculate RFM segmentation
        if 'rfm_df' not in st.session_state:
            st.session_state.rfm_df = perform_rfm_segmentation(st.session_state.df_trans)

        # Calculate LTV
        if 'ltv_df' not in st.session_state:
            st.session_state.ltv_df = calculate_customer_ltv(
                st.session_state.df_trans,
                st.session_state.df_users
            )

    # Key metrics row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        total_customers = st.session_state.df_users.shape[0]
        st.metric("Total Customers", f"{total_customers:,}")

    with col2:
        total_transactions = st.session_state.df_trans.shape[0]
        st.metric("Total Transactions", f"{total_transactions:,}")

    with col3:
        total_value = st.session_state.df_trans['amount'].sum()
        st.metric("Total Value", format_currency(total_value))

    with col4:
        avg_transaction = st.session_state.df_trans['amount'].mean()
        st.metric("Avg Transaction", f"${avg_transaction:,.2f}")

    with col5:
        fraud_rate = (st.session_state.df_fraud['target'].sum() / len(st.session_state.df_fraud))
        st.metric("Fraud Rate", f"{fraud_rate:.2%}")

    st.markdown("---")

    # Top 5 most important insights
    st.markdown("### 🎯 Top 5 Key Insights")

    # Insight 1: Transaction Trends (Q1)
    st.markdown("#### 1️⃣ Transaction Trends Over Time (2010-2019)")
    fig1 = plot_transaction_trends(st.session_state.df_merged)
    st.plotly_chart(fig1, width='stretch', key='plot_transaction_trends_summary')

    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    # Calculate growth metrics
    yearly_trans = st.session_state.df_merged.groupby('year')['amount'].agg(['sum', 'count'])
    growth_rate = ((yearly_trans['sum'].iloc[-1] / yearly_trans['sum'].iloc[0]) - 1) * 100
    st.markdown(f"""
    **💡 Key Insight:** Transaction volume and value show {'growth' if growth_rate > 0 else 'decline'} of **{abs(growth_rate):.1f}%**
    from 2010 to 2019. {'Strong upward trend indicates healthy business growth.' if growth_rate > 0 else 'Declining trend requires attention.'}
    """)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Insights 2 & 3: Side by side
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 2️⃣ Customer Spending Distribution (Q2)")
        fig2 = plot_customer_distribution(st.session_state.df_merged)
        st.plotly_chart(fig2, width='stretch', key='plot_customer_distribution_summary')

        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        st.markdown("""
        **💡 Key Insight:** The distribution follows the Pareto principle - a small percentage of customers
        generate majority of revenue. Focus retention efforts on high-value customers.
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("#### 3️⃣ RFM Customer Segments (Q11)")
        fig3 = plot_rfm_segments(st.session_state.rfm_df)
        st.plotly_chart(fig3, width='stretch', key='plot_rfm_segments_summary')

        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        champions_count = len(st.session_state.rfm_df[st.session_state.rfm_df['Segment'] == 'Champions'])
        champions_pct = (champions_count / len(st.session_state.rfm_df)) * 100
        st.markdown(f"""
        **💡 Key Insight:** **{champions_count:,}** customers ({champions_pct:.1f}%) are in the "Champions" segment
        with high recency, frequency, and monetary value. These are our most valuable customers.
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Insights 4 & 5: Side by side
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 4️⃣ Lifetime Value by Segment (Q18)")
        fig4 = plot_segment_ltv(st.session_state.ltv_df, st.session_state.rfm_df)
        st.plotly_chart(fig4, width='stretch', key='plot_segment_ltv_summary')

        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        # Calculate LTV difference
        ltv_with_seg = st.session_state.ltv_df.merge(
            st.session_state.rfm_df[['client_id', 'Segment']],
            on='client_id'
        )
        champions_ltv = ltv_with_seg[ltv_with_seg['Segment'] == 'Champions']['LTV'].mean()
        avg_ltv = ltv_with_seg['LTV'].mean()
        ltv_multiple = champions_ltv / avg_ltv if avg_ltv > 0 else 0
        st.markdown(f"""
        **💡 Key Insight:** Champions segment has **{ltv_multiple:.1f}x** higher LTV than average.
        Investing in customer retention and upselling to this segment yields highest returns.
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("#### 5️⃣ Credit Card Cross-Sell Opportunities (Q19)")
        fig5 = plot_crosssell_opportunities(st.session_state.df_merged, st.session_state.df_cards)
        st.plotly_chart(fig5, width='stretch', key='plot_crosssell_summary')

        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        st.markdown("""
        **💡 Key Insight:** Significant opportunity to cross-sell Credit cards to high-spending Debit users.
        Target "High" and "Very High" segments first for best conversion rates and revenue impact.
        """)
        st.markdown('</div>', unsafe_allow_html=True)

# Tab 2: Customer Behavior
with tab2:
    st.markdown('<div class="sub-header">Customer Behavior Analysis</div>', unsafe_allow_html=True)
    st.markdown("**Questions Q1-Q10**: Comprehensive analysis of customer transaction patterns")

    # Question selector
    question = st.selectbox(
        "Select Analysis Question:",
        [
            "Q1: Transaction Trends Over Time (2010-2019)",
            "Q2: Transaction Value Distribution & Top Spenders",
            "Q3: Payment Method Usage & Trends",
            "Q4: Top Merchant Categories",
            "Q5: Gender Spending Comparison",
            "Q6: Age Group Analysis",
            "Q7: Income vs Spending Relationship",
            "Q8: Seasonality Analysis",
            "Q9: Transaction Frequency",
            "Q10: Geographic Distribution"
        ]
    )

    st.markdown("---")

    # Filters section (common for most questions)
    with st.expander("🔍 Filters (Optional)", expanded=False):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            gender_filter = st.selectbox(
                "Gender",
                options=['All'] + list(st.session_state.df_merged['gender'].dropna().unique()),
                index=0
            )

        with col2:
            age_filter = st.selectbox(
                "Age Group",
                options=['All'] + list(st.session_state.df_merged['age_group'].dropna().unique()),
                index=0
            )

        with col3:
            card_filter = st.selectbox(
                "Card Type",
                options=['All'] + list(st.session_state.df_merged['card_type'].dropna().unique()),
                index=0
            )

        with col4:
            year_filter = st.selectbox(
                "Year",
                options=['All'] + sorted(st.session_state.df_merged['year'].dropna().unique().tolist()),
                index=0
            )

    # Build filters dict
    filters = {}
    if gender_filter != 'All':
        filters['gender'] = gender_filter
    if age_filter != 'All':
        filters['age_group'] = age_filter
    if card_filter != 'All':
        filters['card_type'] = card_filter
    if year_filter != 'All':
        filters['year'] = year_filter

    # Display selected chart
    if "Q1" in question:
        st.markdown("### Q1: Transaction Trends Over Time (2010-2019)")
        st.markdown("**Analysis:** How transaction volume and value evolved from 2010 to 2019")
        fig = plot_transaction_trends(st.session_state.df_merged, filters)
        st.plotly_chart(fig, width='stretch', key='plot_transaction_trends_q1')

        # Insights
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        st.markdown("""
        **💡 Key Insights:**
        - Track growth/decline trends over the decade
        - Identify peak periods and growth accelerations
        - Understand seasonal patterns across years
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    elif "Q2" in question:
        st.markdown("### Q2: Transaction Value Distribution & Top Spenders")
        st.markdown("**Analysis:** Customer spending distribution following the Pareto principle")
        fig = plot_customer_distribution(st.session_state.df_merged, filters)
        st.plotly_chart(fig, width='stretch', key='plot_customer_distribution_q2')

        # Insights
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        st.markdown("""
        **💡 Key Insights:**
        - Understand the concentration of revenue among customers
        - Identify high-value customer segments
        - Validate 80-20 rule in your customer base
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    elif "Q3" in question:
        st.markdown("### Q3: Payment Method Usage & Trends")
        st.markdown("**Analysis:** How different payment methods (Credit/Debit) are used over time")
        fig = plot_payment_method_trends(st.session_state.df_merged, filters)
        st.plotly_chart(fig, width='stretch', key='plot_payment_method_q3')

        # Insights
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        st.markdown("""
        **💡 Key Insights:**
        - Track adoption of different payment methods
        - Identify shifts from Debit to Credit cards
        - Understand customer payment preferences
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    elif "Q4" in question:
        st.markdown("### Q4: Top Merchant Categories")
        st.markdown("**Analysis:** Which merchant categories generate the most revenue")
        fig = plot_top_merchant_categories(st.session_state.df_merged, filters)
        st.plotly_chart(fig, width='stretch', key='plot_top_merchant_q4')

        # Insights
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        st.markdown("""
        **💡 Key Insights:**
        - Identify most popular spending categories
        - Focus partnership efforts on high-volume categories
        - Tailor rewards programs to customer preferences
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    elif "Q5" in question:
        st.markdown("### Q5: Gender Spending Comparison")
        st.markdown("**Analysis:** How spending patterns differ between male and female customers")
        fig = plot_gender_spending_comparison(st.session_state.df_merged, filters)
        st.plotly_chart(fig, width='stretch', key='plot_gender_spending_q5')

        # Insights
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        st.markdown("""
        **💡 Key Insights:**
        - Understand gender-based spending differences
        - Tailor marketing campaigns by gender
        - Identify cross-sell opportunities by segment
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    elif "Q6" in question:
        st.markdown("### Q6: Age Group Analysis")
        st.markdown("**Analysis:** Spending behavior across different age groups")
        fig = plot_age_group_analysis(st.session_state.df_merged, filters)
        st.plotly_chart(fig, width='stretch', key='plot_age_group_q6')

        # Insights
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        st.markdown("""
        **💡 Key Insights:**
        - Identify highest-spending age groups
        - Understand lifecycle-based spending patterns
        - Target products/services to specific age segments
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    elif "Q7" in question:
        st.markdown("### Q7: Income vs Spending Relationship")
        st.markdown("**Analysis:** Correlation between customer income and spending behavior")
        fig = plot_income_vs_spending(st.session_state.df_merged, filters)
        st.plotly_chart(fig, width='stretch', key='plot_income_vs_spending_q7')

        # Insights
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        st.markdown("""
        **💡 Key Insights:**
        - Validate income-spending correlation
        - Identify high-spending low-income customers (risk)
        - Target credit limit increases to high-income customers
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    elif "Q8" in question:
        st.markdown("### Q8: Seasonality Analysis")
        st.markdown("**Analysis:** Monthly and quarterly spending patterns")
        fig = plot_seasonality_analysis(st.session_state.df_merged, filters)
        st.plotly_chart(fig, width='stretch', key='plot_seasonality_q8')

        # Insights
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        st.markdown("""
        **💡 Key Insights:**
        - Identify peak spending months (e.g., holidays)
        - Plan promotional campaigns around high-spend periods
        - Understand seasonal cash flow patterns
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    elif "Q9" in question:
        st.markdown("### Q9: Transaction Frequency Distribution")
        st.markdown("**Analysis:** How often customers transact")
        fig = plot_transaction_frequency(st.session_state.df_merged, filters)
        st.plotly_chart(fig, width='stretch', key='plot_transaction_frequency_q9')

        # Insights
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        st.markdown("""
        **💡 Key Insights:**
        - Identify highly active vs occasional customers
        - Target engagement campaigns to low-frequency users
        - Reward high-frequency customers with loyalty programs
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    elif "Q10" in question:
        st.markdown("### Q10: Geographic Distribution")
        st.markdown("**Analysis:** Transaction volume across different states")
        fig = plot_geographic_distribution(st.session_state.df_merged, filters)
        st.plotly_chart(fig, width='stretch', key='plot_geographic_q10')

        # Insights
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        st.markdown("""
        **💡 Key Insights:**
        - Identify highest-revenue geographic markets
        - Focus expansion efforts on high-potential states
        - Understand regional spending differences
        """)
        st.markdown('</div>', unsafe_allow_html=True)

# Tab 3: Segmentation
with tab3:
    st.markdown('<div class="sub-header">Customer Segmentation</div>', unsafe_allow_html=True)
    st.markdown("**Questions Q11-Q13**: Three complementary segmentation approaches")

    seg_type = st.radio(
        "Select Segmentation Type:",
        ["Q11: RFM Segmentation", "Q12: Lifecycle Segmentation", "Q13: Financial Health Segmentation"],
        horizontal=True
    )

    if "Q11" in seg_type:
        st.markdown("### Q11: RFM Segmentation")
        st.markdown("**Recency, Frequency, Monetary** - Behavioral segmentation")
        fig_rfm = plot_rfm_segments(st.session_state.rfm_df)
        st.plotly_chart(fig_rfm, use_container_width=True)

    elif "Q12" in seg_type:
        st.markdown("### Q12: Lifecycle Segmentation")
        st.markdown("Segments: Young Professionals, Mid-Career, Pre-Retirement, Retirees")
        # Implementation here

    else:
        st.markdown("### Q13: Financial Health Segmentation")
        st.markdown("Based on Credit Score and Debt-to-Income ratio")
        # Implementation here

# Tab 4: Segment Deep-Dive
with tab4:
    st.markdown('<div class="sub-header">Segment Behavior Deep-Dive</div>', unsafe_allow_html=True)
    st.markdown("**Questions Q14-Q18**: Detailed analysis of each customer segment")

    question = st.selectbox(
        "Select Analysis:",
        [
            "Q14: Card Type Preferences by Segment",
            "Q15: Merchant Category Preferences by Segment",
            "Q16: Spending Behavior Comparison",
            "Q17: Credit Limit & Utilization by Segment",
            "Q18: Lifetime Value (LTV) by Segment"
        ]
    )

    st.markdown(f"Analysis for: **{question}**")
    # Implementation here

# Tab 5: Strategy & Fraud
with tab5:
    st.markdown('<div class="sub-header">Strategic Recommendations & Fraud Analysis</div>', unsafe_allow_html=True)

    analysis_type = st.radio(
        "Select Analysis Type:",
        ["Strategic Recommendations (Q19-Q23)", "Fraud & Risk Analysis (Q24-Q25)"],
        horizontal=True
    )

    if "Strategic" in analysis_type:
        st.markdown("### Strategic Recommendations")
        question = st.selectbox(
            "Select Recommendation:",
            [
                "Q19: Credit Card Cross-sell Opportunities",
                "Q20: Credit Limit Up-sell Opportunities",
                "Q21: At-Risk Customer Analysis",
                "Q22: High-Value Customer Retention",
                "Q23: Product Recommendation Engine"
            ]
        )
        # Implementation here
    else:
        st.markdown("### Fraud & Risk Analysis")
        question = st.selectbox(
            "Select Analysis:",
            [
                "Q24: Fraud Detection Overview",
                "Q25: Dark Web Exposure & Fraud Correlation"
            ]
        )
        # Implementation here

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d; padding: 2rem 0;'>
    <p>📊 Company X Financial Analytics Dashboard | Module 2 Final Project | COLE.VN DS K06</p>
    <p>Built with Streamlit & Plotly | Data: 2010-2019 Financial Transactions</p>
</div>
""", unsafe_allow_html=True)
