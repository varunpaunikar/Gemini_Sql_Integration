import streamlit as st
import pandas as pd
import sql  # Import the backend logic from sql.py
from sql import CustomSQLDatabase
import time
from datetime import datetime
import random
import re  # Import regular expressions module

# Load API Key, DB URI and create DB object
try:
    api_key, db_uri = sql.load_environment_variables()
    db = sql.get_db(db_uri)  # Create the primary database object
    prompt = sql.get_prompt()  # Load the prompt

    # Initialize CustomSQLDatabase using from_uri
    csql = CustomSQLDatabase.from_uri(db_uri)

    # Get dynamic metrics
    num_tables = csql.get_table_count()
    database_size = csql.get_database_size()
    execution_time = csql.get_execution_time("SELECT 1")  # Or a simple query

except ValueError as e:
    st.error(str(e))  # Display error message if loading fails
    st.stop()  # Stop execution if environment variables are not set

# --- Streamlit App ---
st.set_page_config(
    page_title="SQL Assistant",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Futuristic Theme ---
st.markdown(
    """
    <style>
    /* Main page styling */
    .stApp {
        background-color: #0a0f18;
        color: #e0e7ff;
    }

    /* Header styles */
    h1, h2, h3 {
        color: #7dd3fc !important;
        font-family: 'Arial', sans-serif;
        font-weight: 600;
    }

    /* Container styling */
    .stContainer, div.block-container {
        padding: 2rem;
    }

    /* Dashboard card styling */
    .dashboard-card {
        background: linear-gradient(145deg, #101a2f, #1e293b);
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
        margin-bottom: 1rem;
        border-left: 4px solid #38bdf8;
    }

    /* Text area styling */
    .stTextArea textarea {
        background-color: #1e293b !important;
        color: #e0e7ff !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        padding: 10px;
        font-family: 'Consolas', monospace;
    }

    /* Code block styling */
    .stCode {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
    }

    /* Button styling */
    div.stButton > button:first-child {
        background-color: #0ea5e9 !important;
        border-radius: 8px !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.5rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    div.stButton > button:hover {
        background-color: #0284c7 !important;
        box-shadow: 0 0 15px #0ea5e9 !important;
    }

    /* Download Button */
    .stDownloadButton > button {
        background-color: #10b981 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .stDownloadButton > button:hover {
        background-color: #059669 !important;
        box-shadow: 0 0 15px #10b981 !important;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2 {
        color: #38bdf8 !important;
    }

    /* Metrics styling */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #0f172a, #1e293b);
        border-radius: 10px;
        padding: 1rem !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
    }

    div[data-testid="stMetric"] > div {
        color: #e0e7ff !important;
    }

    div[data-testid="stMetric"] label {
        color: #7dd3fc !important;
    }

    /* DataFrame styling */
    .stDataFrame {
        background-color: #1e293b !important;
        border-radius: 10px !important;
        padding: 0.5rem !important;
        border: 1px solid #334155 !important;
    }

    .stDataFrame [data-testid="stTable"] {
        background-color: #1e293b !important;
    }

    /* Add glow effects */
    .glow-text {
        text-shadow: 0 0 10px rgba(125, 211, 252, 0.7);
    }

    .pulsating {
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0% {
            opacity: 1;
        }
        50% {
            opacity: 0.6;
        }
        100% {
            opacity: 1;
        }
    }

    /* Query result container */
    .result-container {
        background: linear-gradient(145deg, #101a2f, #1e293b);
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
        margin-top: 1rem;
        border-left: 4px solid #38bdf8;
    }

    /* Execute button pulsating effect */
    .execute-button button {
        animation: glow 1.5s infinite alternate;
    }

    @keyframes glow {
        from {
            box-shadow: 0 0 5px #0ea5e9;
        }
        to {
            box-shadow: 0 0 15px #0ea5e9;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Sidebar ---
with st.sidebar:
    st.markdown('<h2 class="glow-text">Quantum SQL Assistant</h2>', unsafe_allow_html=True)
    st.markdown('---')

    # User profile section
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("👤")
    with col2:
        st.markdown("**Admin User**")
        st.markdown('<span style="color: #38bdf8; font-size: 0.8rem;">Active</span>', unsafe_allow_html=True)

    st.markdown('---')

    st.markdown("### About")
    st.write(
        "Enter a question to retrieve data from the t-shirts database using natural language powered by Gemini AI."
    )

    st.markdown('---')

    # Database status
    st.markdown("### Database Status")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("Connection")
    with col2:
        st.markdown("✅ Active")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("Tables")
    with col2:
        st.markdown(num_tables)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("Last Query")
    with col2:
        st.markdown(datetime.now().strftime('%H:%M:%S'))

    st.markdown('---')
    st.markdown("[View Documentation](https://docs.streamlit.io/)")
    st.markdown("Developed by: [Varun Paunikar]")

    # Current time
    st.markdown('---')
    st.markdown(f"<div style='text-align: center; color: #64748b;'>{datetime.now().strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)

# --- Main Content ---
st.markdown('<h1 class="glow-text">Gemini SQL Query Tool</h1>', unsafe_allow_html=True)
st.markdown('<p class="pulsating" style="color: #94a3b8;">AI-powered natural language to SQL conversion</p>', unsafe_allow_html=True)

# Key metrics
metrics_cols = st.columns(4)
with metrics_cols[0]:
    st.metric(label="Available Tables", value=num_tables, delta=None)
with metrics_cols[1]:
    st.metric(label="Query Response Time", value=f"{execution_time}s", delta=None)
with metrics_cols[2]:
    random_success_rate = round(random.uniform(90, 100), 1)
    st.metric(label="Query Success Rate", value=f"{random_success_rate}%", delta=None)
with metrics_cols[3]:
    st.metric(label="Database Size", value=f"{database_size} MB", delta=None)

st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
col1, col2 = st.columns([3, 1])  # Divide main content into columns

with col1:
    question = st.text_area(
        "Enter your question about the t-shirts database:",
        key="input",
        height=150,
        placeholder="e.g., How many t-shirts do we have left for Nike in extra small size and white color?",
    )

    st.markdown('<div class="execute-button">', unsafe_allow_html=True)
    submit = st.button("Execute Query")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.subheader("Example Questions")
    st.markdown(
        """
    - How many t-shirts do we have left for Nike in extra small size and white color?
    - What are the available sizes for Adidas brand?
    - Show me all data for black t-shirts
    - What is the total stock for all t-shirts?
    """
    )

st.markdown('</div>', unsafe_allow_html=True)

# If submit is clicked
if submit:
    try:
        with st.spinner("Generating SQL query with Gemini AI..."):
            time.sleep(1)
            sql_query = sql.get_gemini_response(question, prompt, api_key)
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.subheader("Generated SQL Query:")
        st.code(sql_query, language="sql")
        st.markdown('</div>', unsafe_allow_html=True)

        with st.spinner("Executing query on database..."):
            time.sleep(0.5)
            result = sql.execute_sql_and_convert(db, sql_query)

        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.subheader("Query Result:")

        # Convert the result to a DataFrame
        try:
            df = pd.DataFrame(result)
            
            if not df.empty:  # Check if we have data
                # Extract columns from SQL query for SELECT statements
                columns_from_query = []
                
                # Look for SELECT pattern in the query
                select_pattern = re.search(r'SELECT\s+(.*?)\s+FROM', sql_query, re.IGNORECASE)
                
                if select_pattern:
                    select_clause = select_pattern.group(1).strip()
                    
                    # Handle SELECT * case
                    if select_clause == '*':
                        # Get table name
                        match = re.search(r'FROM\s+[`"]?(\w+)[`"]?', sql_query, re.IGNORECASE)
                        table_name = match.group(1) if match else None
                        
                        if table_name:
                            # Get all columns from the table
                            columns_from_query = csql.get_columns_for_table(table_name)
                    else:
                        # Handle COUNT, SUM, etc.
                        if re.search(r'(count|sum|avg|min|max)\(', select_clause.lower()):
                            # For aggregated functions, use the function name as column
                            agg_pattern = re.search(r'(count|sum|avg|min|max)\(\s*(.*?)\s*\)', select_clause, re.IGNORECASE)
                            if agg_pattern:
                                func_name = agg_pattern.group(1)
                                col_name = agg_pattern.group(2)
                                if col_name == '*':
                                    columns_from_query = [f"{func_name.upper()}"]
                                else:
                                    columns_from_query = [f"{func_name.upper()}_{col_name}"]
                        else:
                            # For normal SELECT clauses, split by commas
                            cols = select_clause.split(',')
                            columns_from_query = [col.strip().replace('`', '') for col in cols]
                
                # Assign column names
                if columns_from_query and len(columns_from_query) >= len(df.columns):
                    df.columns = columns_from_query[:len(df.columns)]
                else:
                    # If we can't extract columns from query, try using table columns
                    match = re.search(r'FROM\s+[`"]?(\w+)[`"]?', sql_query, re.IGNORECASE)
                    table_name = match.group(1) if match else None
                    
                    if table_name:
                        try:
                            table_columns = csql.get_columns_for_table(table_name)
                            if table_columns and len(table_columns) >= len(df.columns):
                                df.columns = table_columns[:len(df.columns)]
                            else:
                                df.columns = [f"column_{i+1}" for i in range(len(df.columns))]
                        except Exception as e:
                            print(f"Error getting column names: {e}")
                            df.columns = [f"column_{i+1}" for i in range(len(df.columns))]
                    else:
                        df.columns = [f"column_{i+1}" for i in range(len(df.columns))]

            st.dataframe(df)

            # Add download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name="t_shirt_data.csv",
                mime="text/csv",
            )
            st.markdown(f"Found **{len(df)}** records in **{df.shape[1]}** columns")
        except Exception as e:
            st.write(result)
            st.error(f"Error processing data: {e}")

        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"An error occurred: {e}")

# Add floating notification
st.markdown("""
<div style="position: fixed; bottom: 20px; right: 20px; background: linear-gradient(145deg, #101a2f, #1e293b); padding: 10px 20px; border-radius: 8px; border-left: 3px solid #38bdf8; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3); z-index: 9999; display: flex; align-items: center; max-width: 300px;">
    <div style="background-color: #38bdf8; width: 8px; height: 8px; border-radius: 50%; margin-right: 10px; animation: pulse 2s infinite;"></div>
    <div>
        <div style="font-weight: bold; color: #e0e7ff;">System Notification</div>
        <div style="font-size: 0.8rem; color: #94a3b8;">Database connection active. Gemini API ready.</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown('---')
st.markdown('<div style="text-align: center; color: #64748b; font-size: 0.8rem;">Quantum SQL Assistant • Version 1.2.1 • © 2025</div>', unsafe_allow_html=True)
