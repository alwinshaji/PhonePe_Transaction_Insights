import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3

# Set Streamlit page configuration
st.set_page_config(page_title="PhonePe Transaction Insights Dashboard", layout="wide")

# Custom Streamlit style
st.markdown("""
    <style>
        .sidebar .sidebar-content {
            background-color: #f0f2f6;
        }
        .css-1aumxhk {
            font-size: 18px;
        }
        .css-1v3fvcr {
            font-size: 16px;
        }
        h1, h2, h3, h4, h5 {
            color: #0e1117;
        }
    </style>
""", unsafe_allow_html=True)

# Connect to database
@st.cache_resource
def load_data():
    conn = sqlite3.connect("phonepe_data.db", check_same_thread=False)
    return conn

conn = load_data()

# Sidebar navigation
st.sidebar.title("📊 Dashboard Navigation")
view = st.sidebar.radio("Select a View:", (
    "Overview",
    "Top States by Transactions",
    "Insurance Trends",
    "Brand Analysis",
    "App Opens Insights",
    "Custom Query Runner",
    "State-Level Transaction Comparison",
    "Download Visualizations",
    "Transaction Type Pie Chart"
))

# Load available years and states for filters
years_df = pd.read_sql_query("SELECT DISTINCT year FROM aggregated_transactions ORDER BY year", conn)
years = years_df['year'].tolist()
states_df = pd.read_sql_query("SELECT DISTINCT state FROM aggregated_transactions ORDER BY state", conn)
states = states_df['state'].tolist()

# Overview
if view == "Overview":
    st.title("📈 PhonePe Transactions: Summary Overview")
    selected_state = st.sidebar.selectbox("Select State (Optional):", ["All"] + states)
    state_filter = f"WHERE state = '{selected_state}'" if selected_state != "All" else ""
    query = f"""
    SELECT year, quarter, SUM(amount) AS total_amount, SUM(count) AS total_count
    FROM aggregated_transactions
    {state_filter}
    GROUP BY year, quarter
    ORDER BY year, quarter;
    """
    df = pd.read_sql_query(query, conn)
    df['period'] = df['year'].astype(str) + ' ' + df['quarter']
    fig, ax = plt.subplots(figsize=(12,6))
    sns.lineplot(data=df, x='period', y='total_amount', marker='o', ax=ax, legend=False)
    ax.set_title("Transaction Amount Over Time", fontsize=16)
    ax.set_xlabel("Period")
    ax.set_ylabel("Amount (₹)")
    plt.xticks(rotation=45)
    st.pyplot(fig)
    st.markdown("This chart provides a clear overview of how transaction amounts vary over different quarters.")

# Top States
elif view == "Top States by Transactions":
    st.title("📍 Top States by Transaction Amount")
    query = """
    SELECT state, SUM(amount) AS total_amount
    FROM aggregated_transactions
    GROUP BY state
    ORDER BY total_amount DESC
    LIMIT 10;
    """
    df = pd.read_sql_query(query, conn)
    fig, ax = plt.subplots(figsize=(10,6))
    sns.barplot(data=df, y='state', x='total_amount', palette='Blues_d', ax=ax, legend=False)
    ax.set_title("Top 10 States by Transaction Amount")
    st.pyplot(fig)
    st.markdown("These states exhibit the highest usage, indicating strong digital adoption.")

# Insurance Trends
elif view == "Insurance Trends":
    st.title("🛡️ Insurance Growth Trends")
    selected_state = st.sidebar.selectbox("Select State (Optional):", ["All"] + states, key="insurance")
    state_filter = f"WHERE state = '{selected_state}'" if selected_state != "All" else ""
    query = f"""
    SELECT year, quarter, SUM(amount) AS total_insurance
    FROM aggregated_insurance
    {state_filter}
    GROUP BY year, quarter
    ORDER BY year, quarter;
    """
    df = pd.read_sql_query(query, conn)
    df['period'] = df['year'].astype(str) + ' ' + df['quarter']
    fig, ax = plt.subplots(figsize=(12,6))
    sns.lineplot(data=df, x='period', y='total_insurance', marker='o', ax=ax, color='purple', legend=False)
    ax.set_title("Quarterly Insurance Transaction Trends")
    st.pyplot(fig)
    st.markdown("Understanding insurance trends helps optimize new financial offerings.")

# Brand Analysis
elif view == "Brand Analysis":
    st.title("🏷️ Brand Performance")
    query = """
    SELECT u.brand, 
           SUM(t.amount) AS total_amount,
           SUM(u.count) AS total_users,
           (SUM(t.amount) * 1.0 / SUM(u.count)) AS avg_transaction_amount
    FROM aggregated_users u
    JOIN aggregated_transactions t 
      ON u.state = t.state AND u.year = t.year AND u.quarter = t.quarter
    GROUP BY u.brand
    HAVING total_users > 100000
    ORDER BY avg_transaction_amount DESC
    LIMIT 10;
    """
    df = pd.read_sql_query(query, conn)
    fig, ax = plt.subplots(figsize=(10,6))
    sns.barplot(data=df, y='brand', x='avg_transaction_amount', palette='crest', ax=ax, legend=False)
    ax.set_title("User Brand vs Avg. Transaction Amount")
    st.pyplot(fig)
    st.markdown("This visualization compares the average transaction value across user brands.")

# App Opens
elif view == "App Opens Insights":
    st.title("📱 App Opens Analysis")
    selected_state = st.sidebar.selectbox("Select State:", states, key="appopens")
    query = f"""
    SELECT year, quarter, SUM(app_opens) AS app_opens
    FROM map_users
    WHERE state = '{selected_state}'
    GROUP BY year, quarter
    ORDER BY year, quarter;
    """
    df = pd.read_sql_query(query, conn)
    df['period'] = df['year'].astype(str) + ' ' + df['quarter']
    fig, ax = plt.subplots(figsize=(10,6))
    sns.lineplot(data=df, x='period', y='app_opens', marker='o', ax=ax, color='green', legend=False)
    ax.set_title(f"Quarterly App Opens in {selected_state}")
    st.pyplot(fig)
    st.markdown("Tracks user engagement through app open trends.")

# Custom Query
elif view == "Custom Query Runner":
    st.title("🛠️ Custom SQL Query Runner")
    query_input = st.text_area("Enter your SQL query:", height=150)
    if st.button("Run Query"):
        try:
            result_df = pd.read_sql_query(query_input, conn)
            st.dataframe(result_df)
        except Exception as e:
            st.error(f"Error: {e}")

# Additional analysis example: compare two states
elif view == "State-Level Transaction Comparison":
    st.title("🔍 Compare Transaction Counts Between Two States")
    state1 = st.selectbox("Select First State:", states, key="state1")
    state2 = st.selectbox("Select Second State:", states, key="state2")

    query = f"""
    SELECT state, year, quarter, SUM(count) AS txn_count
    FROM aggregated_transactions
    WHERE state IN ('{state1}', '{state2}')
    GROUP BY state, year, quarter
    ORDER BY year, quarter;
    """
    df = pd.read_sql_query(query, conn)
    df['period'] = df['year'].astype(str) + ' ' + df['quarter']
    fig, ax = plt.subplots(figsize=(12,6))
    sns.lineplot(data=df, x='period', y='txn_count', hue='state', marker='o', ax=ax)
    ax.set_title(f"Quarterly Transaction Count Comparison: {state1} vs {state2}")
    plt.xticks(rotation=45)
    st.pyplot(fig)
    st.markdown("This chart helps compare transaction activity across two different states over time.")

# Download Feature
elif view == "Download Visualizations":
    st.title("📥 Download Sample Visual")
    query = """
    SELECT state, SUM(amount) AS total_amount
    FROM aggregated_transactions
    GROUP BY state
    ORDER BY total_amount DESC;
    """
    df = pd.read_sql_query(query, conn)
    fig, ax = plt.subplots(figsize=(10,6))
    sns.barplot(data=df, x='state', y='total_amount', ax=ax, legend=False)
    plt.xticks(rotation=90)
    ax.set_title("Total Transaction by State")
    st.pyplot(fig)
    st.download_button("Download CSV", df.to_csv(index=False), "state_transactions.csv")

# Additional Feature: Transaction Pie
elif view == "Transaction Type Pie Chart":
    st.title("📊 Transaction Distribution by Type")
    query = """
    SELECT transaction_type, SUM(count) AS txn_count
    FROM aggregated_transactions
    GROUP BY transaction_type;
    """
    df = pd.read_sql_query(query, conn)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.pie(df['txn_count'], labels=df['transaction_type'], autopct='%1.1f%%', startangle=140)
    ax.set_title("Share of Transaction Types")
    st.pyplot(fig)
    st.markdown("This pie chart breaks down the overall transaction types to understand user preferences.")
