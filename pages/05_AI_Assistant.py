import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_deviations_from_benchmark, get_current_benchmark, get_assayer_performance
from utils import create_moving_average_chart, create_deviation_distribution_chart
from deepseek_assistant import (
    analyze_deviation_data, 
    analyze_heatmap, 
    analyze_trend_chart, 
    analyze_distribution_chart, 
    generate_performance_recommendations
)
from auth import require_permission, display_access_denied, check_page_access

st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="wide")

# Check authentication and permissions
if not check_page_access("AI_Assistant"):
    display_access_denied()
    st.stop()

st.title("AI Assistant Analysis")
st.markdown("Advanced AI analysis of assayer performance, trends, and deviations. The AI assistant provides expert interpretations and recommendations based on your gold assay data.")

# Check if benchmark is set
current_benchmark = get_current_benchmark()

if current_benchmark is None:
    st.warning("No benchmark assayer set. Please set one in the Daily Monitoring page.")
    st.stop()

# Display benchmark info
st.info(f"Current benchmark assayer: **{current_benchmark['name']}**")

# Define analysis time period
st.header("Analysis Settings")

time_period = st.select_slider(
    "Select analysis period:",
    options=["Last 30 days", "Last 90 days", "Last 180 days", "Last 365 days", "All time"],
    value="Last 90 days"
)

# Convert time period to days
if time_period == "Last 30 days":
    days = 30
elif time_period == "Last 90 days":
    days = 90
elif time_period == "Last 180 days":
    days = 180
elif time_period == "Last 365 days":
    days = 365
else:  # All time
    days = 9999  # Large number to get all data

# Moving average window for trend analysis
ma_window = st.slider("Moving Average Window (days):", min_value=3, max_value=30, value=7)

# Get deviation data
deviations_df = get_deviations_from_benchmark(days=days)

if deviations_df is None or deviations_df.empty:
    st.info(f"No deviation data available for the selected time period.")
    st.stop()

# Create tabs for different AI analyses
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overall Analysis", 
    "Heatmap Interpretation", 
    "Trend Analysis", 
    "Distribution Analysis",
    "Recommendations"
])

with tab1:
    st.header("Overall Performance Analysis")
    
    with st.spinner("AI is analyzing your data..."):
        analysis = analyze_deviation_data(deviations_df, time_period)
    
    # Use expander to make the analysis toggleable
    with st.expander("View AI Insights", expanded=False):
        st.markdown(analysis)
    
    # Show key metrics alongside AI analysis
    st.subheader("Key Performance Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_samples = deviations_df['sample_id'].nunique()
        st.metric("Total Samples", total_samples)
    
    with col2:
        num_assayers = deviations_df['assayer_name'].nunique()
        st.metric("Active Assayers", num_assayers)
    
    with col3:
        avg_deviation = deviations_df['percentage_deviation'].mean()
        st.metric("Avg % Deviation", f"{avg_deviation:.2f}%")

with tab2:
    st.header("Heatmap Analysis")
    
    # Show the heatmap visualization
    st.subheader("Deviation Heatmap")
    from utils import create_deviation_heatmap
    
    heatmap_fig = create_deviation_heatmap(deviations_df)
    if heatmap_fig:
        st.plotly_chart(heatmap_fig, use_container_width=True)
    else:
        st.info("Not enough data to create heatmap visualization.")
    
    with st.spinner("AI is analyzing the heatmap..."):
        heatmap_analysis = analyze_heatmap(deviations_df, time_period)
    
    # Use expander to make the analysis toggleable
    with st.expander("View Heatmap Interpretation", expanded=False):
        st.markdown(heatmap_analysis)

with tab3:
    st.header("Trend Analysis")
    
    # Show the moving average trend visualization
    st.subheader(f"{ma_window}-Day Moving Average Trends")
    
    ma_fig = create_moving_average_chart(deviations_df, window=ma_window)
    
    if ma_fig:
        st.plotly_chart(ma_fig, use_container_width=True)
    else:
        st.info(f"Not enough data to calculate {ma_window}-day moving average.")
        
    with st.spinner("AI is analyzing trends..."):
        trend_analysis = analyze_trend_chart(deviations_df, ma_window, time_period)
    
    # Use expander to make the analysis toggleable
    with st.expander("View Trend Analysis Interpretation", expanded=False):
        st.markdown(trend_analysis)

with tab4:
    st.header("Distribution Analysis")
    
    # Show the distribution visualization
    st.subheader("Deviation Distribution by Assayer")
    
    dist_fig = create_deviation_distribution_chart(deviations_df)
    
    if dist_fig:
        st.plotly_chart(dist_fig, use_container_width=True)
    else:
        st.info("Not enough data to create distribution visualization.")
    
    with st.spinner("AI is analyzing distributions..."):
        distribution_analysis = analyze_distribution_chart(deviations_df, time_period)
    
    # Use expander to make the analysis toggleable
    with st.expander("View Distribution Analysis Interpretation", expanded=False):
        st.markdown(distribution_analysis)

with tab5:
    st.header("AI Recommendations")
    
    with st.spinner("AI is generating recommendations..."):
        recommendations = generate_performance_recommendations(deviations_df, time_period)
    
    # Use expander to make the recommendations toggleable
    with st.expander("View Performance Analysis and Recommendations", expanded=False):
        st.markdown(recommendations)
    
    # Download recommendations as text
    if st.button("Download Recommendations"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gold_assay_recommendations_{timestamp}.txt"
        
        # Combine all analyses
        all_recommendations = f"""# GOLD ASSAY PERFORMANCE ANALYSIS
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
Period: {time_period}

## OVERALL ANALYSIS
{analysis}

## HEATMAP INTERPRETATION
{heatmap_analysis}

## TREND ANALYSIS
{trend_analysis}

## DISTRIBUTION ANALYSIS
{distribution_analysis}

## RECOMMENDATIONS
{recommendations}
"""
        
        st.download_button(
            label="Download Complete Analysis",
            data=all_recommendations,
            file_name=filename,
            mime="text/plain"
        )

# Information about AI analysis
st.markdown("---")
st.markdown("""
**About AI Analysis:**
- The AI analyzes your actual gold assay data to provide insights and recommendations
- All analyses are generated in real-time based on current data
- The AI uses advanced statistical methods to identify patterns, trends, and anomalies
- Recommendations are specific to your laboratory's performance
""")

# Disclaimer
st.caption("""
**Disclaimer:** The AI assistant provides analysis based solely on available data and general best practices. 
Always use professional judgment when implementing recommendations.
""")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888;'>"
    "© 2025 AEG Monitoring System<br>"
    "Developed by Algo Digital Solutions, powered by Mureri Technologies<br>"
    "All Rights Reserved"
    "</div>", 
    unsafe_allow_html=True
)

# Add the chat component from the shared module
import sys
import os
# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simple_chat import display_chat_widget
display_chat_widget()