import streamlit as st
import pandas as pd
import sqlite3
import os
from database import init_db
from database_interlab import init_interlab_db
from dotenv import load_dotenv
from auth import (
    is_logged_in, display_login_form, display_user_info, 
    require_permission, get_current_user, has_permission, initialize_session
)
from user_management import display_user_management

# Load environment variables
load_dotenv()

# Initialize databases
init_db()
init_interlab_db()

# Clean startup without health check interference

# Page configuration
st.set_page_config(
    page_title="AEG labsync- Monitor",
    page_icon="attached_assets/lab-system-logo-png_seeklogo-511943_1750441877909.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for persistent login
initialize_session()

# Check authentication first
if not is_logged_in():
    display_login_form()
    st.stop()

# User is logged in, show user info in sidebar
display_user_info()

# Check if user has permission to access home page
require_permission("app")

# Add PWA manifest and favicon
st.markdown("""
<link rel="icon" type="image/x-icon" href="./app/static/attached_assets/lab-system-logo-png_seeklogo-511943_1750441877909.ico">
<link rel="manifest" href="./app/static/manifest.json">
<meta name="theme-color" content="#D4AF37">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="AEG labsync">
<link rel="apple-touch-icon" href="./app/static/attached_assets/lab-system-logo-png_seeklogo-511943_1750441877909.ico">
""", unsafe_allow_html=True)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #D4AF37;
        margin-bottom: 20px;
        text-align: center;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        padding-bottom: 10px;
        border-bottom: 2px solid #D4AF37;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 30px;
        padding-left: 10px;
        border-left: 4px solid #D4AF37;
    }
    .info-box {
        background-color: rgba(212, 175, 55, 0.1);
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #D4AF37;
        margin-bottom: 20px;
    }
    .metric-container {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin: 10px 0;
    }

    /* Styles for tables and cards */
    .assayer-card {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        padding: 15px;
        margin-bottom: 15px;
    }

    .profile-image {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #D4AF37;
    }

    .benchmark-label {
        background-color: #D4AF37;
        color: white;
        font-size: 0.8rem;
        padding: 3px 8px;
        border-radius: 10px;
        display: inline-block;
    }
    /* Chat container styles */
    .chat-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 300px;
        max-height: 400px;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        z-index: 1000;
        overflow: hidden;
    }
    .chat-header {
        background-color: #D4AF37;
        color: white;
        padding: 8px 12px;
        font-weight: bold;
        font-size: 0.9rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: pointer;
    }
    .chat-messages {
        height: 200px;
        overflow-y: auto;
        padding: 8px;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        align-self: flex-end;
        background-color: #E8F0FE;
        border-radius: 12px 12px 0 12px;
        padding: 6px 10px;
        margin: 3px 0;
        max-width: 90%;
        font-size: 0.85rem;
    }
    .ai-message {
        align-self: flex-start;
        background-color: #F0F0F0;
        border-radius: 12px 12px 12px 0;
        padding: 6px 10px;
        margin: 3px 0;
        max-width: 90%;
        font-size: 0.85rem;
    }
    .chat-input {
        padding: 6px;
        border-top: 1px solid #E0E0E0;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Main app header with logo
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    # Create company logo with CSS styling
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; flex-direction: column;">
        <div style="background: linear-gradient(135deg, #D4AF37 0%, #FFDF00 50%, #D4AF37 100%); 
                    width: 80px; height: 80px; border-radius: 50%; 
                    display: flex; justify-content: center; align-items: center; 
                    margin-bottom: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
            <span style="font-size: 40px; color: #1E3A8A; font-weight: bold;">AG</span>
        </div>
        <h1 class='main-header'>AEG labsync- Monitor</h1>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div class='info-box'>", unsafe_allow_html=True)
st.markdown("""
This application helps monitor and analyze deviations in gold purity testing (in parts per thousand) among laboratory assayers.
""")
st.markdown("</div>", unsafe_allow_html=True)

# Show user management section for admin users
current_user = get_current_user()
if current_user and has_permission(current_user, "user_management"):
    with st.expander("👥 User Management (Admin Only)", expanded=False):
        display_user_management()

# Navigation section with bot icon
nav_col1, nav_col2, nav_col3 = st.columns([3, 1, 1])

with nav_col1:
    # Show navigation based on user permissions
    st.markdown("### Navigation")
    st.markdown("Use the sidebar to navigate to different sections:")

    # Get user's accessible pages
    from auth import get_accessible_pages
    accessible_pages = get_accessible_pages()

    # Define all navigation items with their descriptions
    nav_items = {
        "Data_Entry": "📋 **Data Entry**: Input daily assay results with gold purity in ppt",
        "Daily_Monitoring": "📊 **Daily Monitoring**: View current deviations from benchmark values with detailed individual assayer analysis tabs",
        "Analytics": "📈 **Analytics**: Analyze long-term trends and moving averages",
        "AI_Assistant": "🤖 **AI Assistant**: Get AI-powered analysis and recommendations",
        "Assayer_Profiles": "👤 **Assayer Profiles**: View and manage detailed assayer profiles with work history",
        "Gold_Type_Analysis": "🥇 **Gold Type Analysis**: Analyze performance by different gold types",
        "Mass_Impact_Analysis": "⚖️ **Mass Impact Analysis**: Calculate physical mass impact of deviations",
        "Trainee_Evaluation": "🎓 **Trainee Evaluation**: Evaluate trainee performance and progress"
    }

    # Show only accessible pages
    for page_key, description in nav_items.items():
        if page_key in accessible_pages:
            st.markdown(f"- {description}")

    # Show current role information
    role = st.session_state.get("role", "Unknown")
    st.info(f"Your current role: **{role}**")

with nav_col3:
    # Add some vertical spacing to position icon lower
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.image("assets/bot_icon.png", width=400, use_container_width=False)

# Initialize database connection
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('gold_assay.db')

# Check if benchmark is set and display benchmark info
benchmark_df = pd.read_sql("SELECT assayer_id FROM benchmark_assayers WHERE is_active = 1 LIMIT 1", conn)
benchmark_id = None
if benchmark_df.empty:
    st.warning("⚠️ No benchmark assayer has been set. Please go to the Daily Monitoring page to set a benchmark.")
else:
    # Display benchmark assayer name
    benchmark_id = benchmark_df.iloc[0]['assayer_id']
    benchmark_name_df = pd.read_sql(f"SELECT name FROM assayers WHERE assayer_id = {benchmark_id}", conn)
    if not benchmark_name_df.empty:
        benchmark_name = benchmark_name_df.iloc[0]['name']
        st.success(f"✅ Current benchmark assayer: **{benchmark_name}**")



# Key Metrics Highlights
st.markdown("<h2 class='sub-header'>Key Metrics Highlights</h2>", unsafe_allow_html=True)

# Calculate time periods
today = datetime.now()
yesterday_start = (today - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
yesterday_end = today.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(microseconds=1)
last_week_start = (today - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
last_month_start = (today - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)

# Format dates for SQL queries
yesterday_start_fmt = yesterday_start.strftime('%Y-%m-%d %H:%M:%S')
yesterday_end_fmt = yesterday_end.strftime('%Y-%m-%d %H:%M:%S')
last_week_start_fmt = last_week_start.strftime('%Y-%m-%d %H:%M:%S')
last_month_start_fmt = last_month_start.strftime('%Y-%m-%d %H:%M:%S')
today_fmt = today.strftime('%Y-%m-%d %H:%M:%S')

try:
    # Check if benchmark is set for more metrics
    benchmark_exists = not benchmark_df.empty

    # Create three tabs for different time periods
    period_tabs = st.tabs(["Last 30 Days", "Last Week", "Yesterday"])

    # Last 30 Days tab
    with period_tabs[0]:
        # Get total samples in last 30 days
        monthly_samples_df = pd.read_sql(f"""
            SELECT COUNT(*) as count FROM assay_results 
            WHERE test_date BETWEEN '{last_month_start_fmt}' AND '{today_fmt}'
        """, conn)
        monthly_samples = monthly_samples_df.iloc[0]['count'] if not monthly_samples_df.empty else 0

        # Get unique assayers who conducted tests in last 30 days
        monthly_assayers_df = pd.read_sql(f"""
            SELECT COUNT(DISTINCT assayer_id) as count FROM assay_results 
            WHERE test_date BETWEEN '{last_month_start_fmt}' AND '{today_fmt}'
        """, conn)
        monthly_assayers = monthly_assayers_df.iloc[0]['count'] if not monthly_assayers_df.empty else 0

        # Get average deviation if benchmark exists
        monthly_avg_deviation = None
        if benchmark_exists:
            from database import get_deviations_from_benchmark
            deviations_df = get_deviations_from_benchmark(days=30)
            if deviations_df is not None and not deviations_df.empty:
                monthly_avg_deviation = deviations_df['percentage_deviation'].mean()

        # Display metrics in 3 columns
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Samples", monthly_samples)
        col2.metric("Active Assayers", monthly_assayers)
        if monthly_avg_deviation is not None:
            col3.metric("Average Deviation", f"{monthly_avg_deviation:.2f}%")
        else:
            col3.info("No deviation data available")

        # Link to Analytics page
        st.info("View detailed monthly trends in the [Analytics](/Analytics) page")

    # Last Week tab
    with period_tabs[1]:
        # Get total samples in last week
        weekly_samples_df = pd.read_sql(f"""
            SELECT COUNT(*) as count FROM assay_results 
            WHERE test_date BETWEEN '{last_week_start_fmt}' AND '{today_fmt}'
        """, conn)
        weekly_samples = weekly_samples_df.iloc[0]['count'] if not weekly_samples_df.empty else 0

        # Get unique assayers who conducted tests in last week
        weekly_assayers_df = pd.read_sql(f"""
            SELECT COUNT(DISTINCT assayer_id) as count FROM assay_results 
            WHERE test_date BETWEEN '{last_week_start_fmt}' AND '{today_fmt}'
        """, conn)
        weekly_assayers = weekly_assayers_df.iloc[0]['count'] if not weekly_assayers_df.empty else 0

        # Get average deviation if benchmark exists
        weekly_avg_deviation = None
        if benchmark_exists:
            from database import get_deviations_from_benchmark
            deviations_df = get_deviations_from_benchmark(days=7)
            if deviations_df is not None and not deviations_df.empty:
                weekly_avg_deviation = deviations_df['percentage_deviation'].mean()

        # Display metrics in 3 columns
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Samples", weekly_samples)
        col2.metric("Active Assayers", weekly_assayers)
        if weekly_avg_deviation is not None:
            col3.metric("Average Deviation", f"{weekly_avg_deviation:.2f}%")
        else:
            col3.info("No deviation data available")

        # Link to Daily Monitoring page
        st.info("View detailed weekly data in the [Daily Monitoring](/Daily_Monitoring) page")

    # Yesterday tab
    with period_tabs[2]:
        # Get total samples yesterday
        yesterday_samples_df = pd.read_sql(f"""
            SELECT COUNT(*) as count FROM assay_results 
            WHERE test_date BETWEEN '{yesterday_start_fmt}' AND '{yesterday_end_fmt}'
        """, conn)
        yesterday_samples = yesterday_samples_df.iloc[0]['count'] if not yesterday_samples_df.empty else 0

        # Get unique assayers who conducted tests yesterday
        yesterday_assayers_df = pd.read_sql(f"""
            SELECT COUNT(DISTINCT assayer_id) as count FROM assay_results 
            WHERE test_date BETWEEN '{yesterday_start_fmt}' AND '{yesterday_end_fmt}'
        """, conn)
        yesterday_assayers = yesterday_assayers_df.iloc[0]['count'] if not yesterday_assayers_df.empty else 0

        # Get average deviation if benchmark exists
        yesterday_avg_deviation = None
        if benchmark_exists and benchmark_id is not None:
            yesterday_deviations_df = pd.read_sql(f"""
                SELECT AVG(ABS(r.gold_content - b.gold_content) / b.gold_content * 100) as avg_deviation
                FROM assay_results r
                JOIN assay_results b ON r.sample_id = b.sample_id AND b.assayer_id = {benchmark_id}
                WHERE r.assayer_id != b.assayer_id
                AND r.test_date BETWEEN '{yesterday_start_fmt}' AND '{yesterday_end_fmt}'
            """, conn)
            if not yesterday_deviations_df.empty and pd.notna(yesterday_deviations_df.iloc[0]['avg_deviation']):
                yesterday_avg_deviation = yesterday_deviations_df.iloc[0]['avg_deviation']

        # Display metrics in 3 columns
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Samples", yesterday_samples)
        col2.metric("Active Assayers", yesterday_assayers)
        if yesterday_avg_deviation is not None:
            col3.metric("Average Deviation", f"{yesterday_avg_deviation:.2f}%")
        else:
            col3.info("No deviation data available")

        # Link to Data Entry page
        st.info("Enter today's sample data in the [Data Entry](/Data_Entry) page")

except Exception as e:
    st.info("Limited data available for analysis. Add more sample data for detailed metrics.")

conn.close()

# Footer with improved branding
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center;'>
        <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 15px;">
            <div style="background: linear-gradient(135deg, #D4AF37 0%, #FFDF00 50%, #D4AF37 100%); 
                        width: 40px; height: 40px; border-radius: 50%; 
                        display: flex; justify-content: center; align-items: center; 
                        box-shadow: 0 2px 5px rgba(0,0,0,0.2); margin-right: 10px;">
                <span style="font-size: 20px; color: #1E3A8A; font-weight: bold;">AG</span>
            </div>
            <div>
                <span style="font-size: 20px; font-weight: bold; color: #1E3A8A;">Algol Digital Solutions</span>
                <span style="font-size: 14px; color: #666;"> by Mureri Technologies</span>
            </div>
        </div>
        <div style='color: #888; font-size: 12px;'>
            © 2025 AEG Monitoring System<br>
            All Rights Reserved
        </div>
    </div>
    """, 
    unsafe_allow_html=True
)

# Add the chat component from the shared module
from simple_chat import display_chat_widget
display_chat_widget()