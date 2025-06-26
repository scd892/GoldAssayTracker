import streamlit as st

# Page config must be the first Streamlit command
st.set_page_config(page_title="Inter-Laboratory Comparisons", page_icon="🔬", layout="wide")

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_interlab import (
    init_interlab_db, get_external_labs, get_interlab_results, get_interlab_comparisons,
    set_external_lab_benchmark, get_external_lab_benchmark
)
from utils import create_deviation_heatmap, calculate_moving_average
from auth import require_permission, display_access_denied, check_page_access

# Initialize the interlab database tables
init_interlab_db()

# Check authentication and permissions
if not check_page_access("Interlab_Comparisons"):
    display_access_denied()
    st.stop()

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.3rem;
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
        margin-top: 20px;
        padding-left: 10px;
        border-left: 4px solid #D4AF37;
    }
    .info-box {
        background-color: rgba(212, 175, 55, 0.1);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #D4AF37;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>Inter-Laboratory Comparisons</h1>", unsafe_allow_html=True)

# Benchmark selection section
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("<div class='info-box'>", unsafe_allow_html=True)
    st.markdown("""
    This page allows you to compare your internal assayer results with external laboratory measurements.
    Use the tools below to analyze deviations, trends, and ensure quality control across laboratories.
    """)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<h3>External Lab Benchmark</h3>", unsafe_allow_html=True)
    
    # Get current benchmark
    current_benchmark = get_external_lab_benchmark()
    current_benchmark_text = "None selected" if current_benchmark is None else current_benchmark["lab_name"]
    
    # Get the list of external labs
    try:
        external_labs = get_external_labs()
        if not external_labs.empty:
            # Create a selection box with the labs
            selected_lab = st.selectbox(
                "Select Benchmark Laboratory",
                options=external_labs["lab_id"].tolist(),
                format_func=lambda x: external_labs.loc[external_labs["lab_id"] == x, "lab_name"].iloc[0],
                help="Set an external laboratory as your benchmark for comparisons"
            )
            
            # Show current benchmark
            st.info(f"Current Benchmark: {current_benchmark_text}")
            
            # Button to set benchmark
            if st.button("Set as Benchmark"):
                success, message = set_external_lab_benchmark(selected_lab)
                if success:
                    st.success(message)
                    # Rerun to update the UI
                    st.rerun()
                else:
                    st.error(message)
        else:
            st.warning("No external laboratories available. Add labs in the Data Entry page.")
    except Exception as e:
        st.error(f"Error loading external laboratories: {str(e)}")
        st.warning("Add external laboratories in the Data Entry page first.")

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["Comparison Overview", "Detailed Analysis", "Performance Metrics"])

with tab1:
    st.markdown("<h2 class='sub-header'>Comparison Overview</h2>", unsafe_allow_html=True)
    
    # Time period selection
    st.subheader("Select Time Period")
    
    # Use a number input for flexible day selection
    days = st.number_input(
        "Select number of days for analysis:", 
        min_value=1, 
        max_value=9999, 
        value=90,
        step=1,
        help="Specify any number of days from 1 to 9999 for your analysis period"
    )
    
    # Set time period description for context
    if days == 1:
        time_period = "Last 1 day"
    elif days == 7:
        time_period = "Last week"
    elif days == 30:
        time_period = "Last month"
    elif days == 90:
        time_period = "Last quarter"
    elif days == 365:
        time_period = "Last year"
    elif days >= 9000:
        time_period = "All time"
    else:
        time_period = f"Last {days} days"
    
    # Get comparison data
    comparison_df = get_interlab_comparisons(days=days)
    
    if comparison_df is not None and not comparison_df.empty:
        # Show summary statistics
        st.subheader("Summary Statistics")
        
        # Create metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_comparisons = len(comparison_df)
            st.metric("Total Comparisons", total_comparisons)
        
        with col2:
            avg_deviation = comparison_df['absolute_deviation'].mean()
            st.metric("Average Deviation", f"{avg_deviation:.1f} ppt")
        
        with col3:
            max_deviation = comparison_df['absolute_deviation'].abs().max()
            st.metric("Maximum Deviation", f"{max_deviation:.1f} ppt")
        
        with col4:
            labs_count = comparison_df['lab_name'].nunique()
            st.metric("External Labs", labs_count)
        
        # Create a bar chart of average deviations by external lab
        st.subheader("Average Deviations by External Laboratory")
        
        lab_stats = comparison_df.groupby('lab_name').agg({
            'absolute_deviation': ['mean', 'std', 'count']
        }).reset_index()
        
        lab_stats.columns = ['lab_name', 'avg_deviation', 'std_deviation', 'comparison_count']
        
        # Create bar chart
        bar_fig = px.bar(
            lab_stats.sort_values('avg_deviation'),
            x='lab_name',
            y='avg_deviation',
            error_y='std_deviation',
            text='comparison_count',
            labels={
                'lab_name': 'External Laboratory',
                'avg_deviation': 'Average Deviation (ppt)',
                'comparison_count': 'Comparison Count'
            },
            color='avg_deviation',
            color_continuous_scale=px.colors.diverging.RdBu_r,
            color_continuous_midpoint=0,
            title="Average Deviation by External Laboratory (ppt)"
        )
        
        # Set color scale range to highlight 0.3 ppt deviation
        bar_fig.update_layout(
            coloraxis_colorbar=dict(
                title="Deviation (ppt)",
                tickvals=[-0.3, -0.1, 0, 0.1, 0.3],
                ticktext=["-0.3", "-0.1", "0", "0.1", "0.3"]
            ),
            coloraxis=dict(
                cmin=-0.3,
                cmax=0.3,
                colorscale="RdBu_r"
            ),
            height=400
        )
        
        bar_fig.update_traces(texttemplate='%{text} samples', textposition='outside')
        
        st.plotly_chart(bar_fig, use_container_width=True)
        
        # Display recent comparisons table
        st.subheader("Recent Comparisons")
        
        # Format the data for display
        display_df = comparison_df.copy()
        display_df['comparison_date'] = pd.to_datetime(display_df['comparison_date']).dt.strftime('%Y-%m-%d')
        display_df['internal_test_date'] = pd.to_datetime(display_df['internal_test_date']).dt.strftime('%Y-%m-%d')
        display_df['external_test_date'] = pd.to_datetime(display_df['external_test_date']).dt.strftime('%Y-%m-%d')
        display_df['absolute_deviation'] = display_df['absolute_deviation'].round(1)
        display_df['percentage_deviation'] = display_df['percentage_deviation'].round(2)
        
        # Select the columns to display
        display_cols = [
            'internal_sample_id', 'external_sample_id', 'internal_gold_content', 
            'external_gold_content', 'absolute_deviation', 'assayer_name', 
            'lab_name', 'comparison_date'
        ]
        
        st.dataframe(display_df[display_cols].head(10), use_container_width=True)
        
        # Show full data in expandable section
        with st.expander("View All Comparison Data"):
            st.dataframe(display_df[display_cols], use_container_width=True)
    else:
        st.info("No inter-laboratory comparison data available for the selected time period. Please add comparison data using the Data Entry page.")
        
        # Show guidance on how to add data
        st.markdown("""
        ### How to add Inter-Laboratory Comparison data:
        
        1. First, add external laboratories in the **Inter-Lab Data Entry** tab of the Data Entry page
        2. Next, add test results from those external laboratories
        3. Finally, create comparisons between your internal samples and the external lab samples
        """)

with tab2:
    st.markdown("<h2 class='sub-header'>Detailed Analysis</h2>", unsafe_allow_html=True)
    
    # Get comparison data (same as in tab1)
    comparison_df = get_interlab_comparisons(days=days)
    
    if comparison_df is not None and not comparison_df.empty:
        # Create a line chart showing deviations over time
        st.subheader("Deviation Trends Over Time")
        
        # Prepare the data
        comparison_df['comparison_date'] = pd.to_datetime(comparison_df['comparison_date'])
        
        # Sort by date
        sorted_df = comparison_df.sort_values('comparison_date')
        
        # Create line chart
        line_fig = px.line(
            sorted_df,
            x='comparison_date',
            y='absolute_deviation',
            color='lab_name',
            labels={
                'comparison_date': 'Date',
                'absolute_deviation': 'Deviation (ppt)',
                'lab_name': 'External Laboratory'
            },
            title="Inter-Laboratory Deviations Over Time (ppt)"
        )
        
        line_fig.update_layout(
            height=500,
            yaxis=dict(
                range=[-0.3, 0.3]  # Set y-axis range to highlight the 0.3 ppt threshold
            ),
            hovermode="x unified"
        )
        
        # Add reference lines
        line_fig.add_hline(y=0, line_dash="dash", line_color="gray")
        line_fig.add_hline(y=0.3, line_dash="dot", line_color="red", line_width=1)
        line_fig.add_hline(y=-0.3, line_dash="dot", line_color="red", line_width=1)
        
        st.plotly_chart(line_fig, use_container_width=True)
        
        # Create a scatter plot to visualize correlation
        st.subheader("Correlation Between Internal and External Results")
        
        scatter_fig = px.scatter(
            comparison_df,
            x='internal_gold_content',
            y='external_gold_content',
            color='lab_name',
            hover_data=['internal_sample_id', 'external_sample_id', 'absolute_deviation'],
            labels={
                'internal_gold_content': 'Internal Gold Content (ppt)',
                'external_gold_content': 'External Gold Content (ppt)',
                'lab_name': 'External Laboratory'
            },
            title="Correlation between Internal and External Measurements"
        )
        
        # Add perfect correlation line (y=x)
        min_val = min(comparison_df['internal_gold_content'].min(), comparison_df['external_gold_content'].min())
        max_val = max(comparison_df['internal_gold_content'].max(), comparison_df['external_gold_content'].max())
        scatter_fig.add_trace(
            go.Scatter(
                x=[min_val, max_val],
                y=[min_val, max_val],
                mode='lines',
                line=dict(color='gray', dash='dash'),
                name='Perfect Correlation'
            )
        )
        
        scatter_fig.update_layout(height=500)
        
        st.plotly_chart(scatter_fig, use_container_width=True)
        
        # Method comparison
        st.subheader("Comparison by Testing Method")
        
        # Only display if method data is available
        if 'method_used' in comparison_df.columns and comparison_df['method_used'].notna().any():
            # Group by method
            method_stats = comparison_df.groupby('method_used').agg({
                'absolute_deviation': ['mean', 'std', 'count']
            }).reset_index()
            
            method_stats.columns = ['method_used', 'avg_deviation', 'std_deviation', 'comparison_count']
            
            # Create bar chart for methods
            method_fig = px.bar(
                method_stats.sort_values('avg_deviation'),
                x='method_used',
                y='avg_deviation',
                error_y='std_deviation',
                text='comparison_count',
                labels={
                    'method_used': 'Testing Method',
                    'avg_deviation': 'Average Deviation (ppt)',
                    'comparison_count': 'Count'
                },
                title="Average Deviation by Testing Method (ppt)"
            )
            
            method_fig.update_layout(height=400)
            method_fig.update_traces(texttemplate='%{text} samples', textposition='outside')
            
            st.plotly_chart(method_fig, use_container_width=True)
        else:
            st.info("No testing method data available for comparison.")
    else:
        st.info("No inter-laboratory comparison data available for the selected time period.")

with tab3:
    st.markdown("<h2 class='sub-header'>Performance Metrics</h2>", unsafe_allow_html=True)
    
    # Get comparison data (same as in tab1)
    comparison_df = get_interlab_comparisons(days=days)
    
    if comparison_df is not None and not comparison_df.empty:
        # Create metrics for performance evaluation
        st.subheader("Statistical Performance Metrics")
        
        # Calculate z-scores
        # Z-score = (external value - internal value) / uncertainty
        comparison_df['z_score'] = None
        
        has_uncertainty = False
        if 'uncertainty' in comparison_df.columns and comparison_df['uncertainty'].notna().any():
            has_uncertainty = True
            # Calculate z-score where uncertainty is available
            mask = comparison_df['uncertainty'] > 0  # Avoid division by zero
            comparison_df.loc[mask, 'z_score'] = (
                comparison_df.loc[mask, 'external_gold_content'] - 
                comparison_df.loc[mask, 'internal_gold_content']
            ) / comparison_df.loc[mask, 'uncertainty']
        
        # Calculate En-scores (normalized error)
        # En = |external value - internal value| / sqrt(u_ext^2 + u_int^2)
        # For simplicity, assume internal uncertainty is 0.2 ppt if not provided
        internal_uncertainty = 0.2
        comparison_df['en_score'] = None
        
        if has_uncertainty:
            comparison_df['en_score'] = abs(
                comparison_df['external_gold_content'] - comparison_df['internal_gold_content']
            ) / np.sqrt(comparison_df['uncertainty']**2 + internal_uncertainty**2)
        
        # Display statistics by laboratory
        if has_uncertainty:
            # Group by lab and calculate metrics
            perf_stats = comparison_df.groupby('lab_name').agg({
                'absolute_deviation': ['mean', 'std'],
                'z_score': ['mean', 'std'],
                'en_score': ['mean', 'count']
            }).reset_index()
            
            perf_stats.columns = [
                'lab_name', 'avg_deviation', 'std_deviation', 
                'avg_z_score', 'std_z_score', 'avg_en_score', 'count'
            ]
            
            # Format for display
            display_perf = perf_stats.copy()
            display_perf['avg_deviation'] = display_perf['avg_deviation'].round(2)
            display_perf['std_deviation'] = display_perf['std_deviation'].round(2)
            display_perf['avg_z_score'] = display_perf['avg_z_score'].round(2)
            display_perf['std_z_score'] = display_perf['std_z_score'].round(2)
            display_perf['avg_en_score'] = display_perf['avg_en_score'].round(2)
            
            st.dataframe(display_perf, use_container_width=True)
            
            # Create performance scatter plot (Z-score vs En-score)
            scatter_fig = px.scatter(
                perf_stats,
                x='avg_z_score',
                y='avg_en_score',
                color='lab_name',
                size='count',
                hover_data=['avg_deviation', 'std_deviation'],
                labels={
                    'avg_z_score': 'Average Z-Score',
                    'avg_en_score': 'Average En-Score',
                    'lab_name': 'External Laboratory',
                    'count': 'Number of Comparisons'
                },
                title="Laboratory Performance: Z-Score vs En-Score"
            )
            
            # Add reference lines
            scatter_fig.add_hline(y=1, line_dash="dash", line_color="red")
            scatter_fig.add_vline(x=-2, line_dash="dash", line_color="red")
            scatter_fig.add_vline(x=2, line_dash="dash", line_color="red")
            
            # Add annotations
            scatter_fig.add_annotation(
                text="Acceptable En",
                x=0,
                y=0.9,
                showarrow=False
            )
            
            scatter_fig.add_annotation(
                text="Acceptable Z",
                x=0,
                y=1.5,
                showarrow=False
            )
            
            scatter_fig.update_layout(height=500)
            st.plotly_chart(scatter_fig, use_container_width=True)
            
            st.markdown("""
            ### Performance Evaluation Criteria:
            
            - **Z-score**: Measures how many standard deviations an external result is from the internal result
                - |Z| ≤ 2.0: Satisfactory performance
                - 2.0 < |Z| < 3.0: Questionable performance
                - |Z| ≥ 3.0: Unsatisfactory performance
                
            - **En-score**: Normalized error that accounts for both labs' measurement uncertainties
                - |En| < 1.0: Acceptable agreement
                - |En| ≥ 1.0: Unacceptable disagreement, indicates potential measurement issues
            """)
        else:
            st.warning("Performance metrics require uncertainty data, which is not available in the current dataset. Please add uncertainty values when entering interlab results.")
            
            # Show simple metrics without uncertainty
            perf_stats = comparison_df.groupby('lab_name').agg({
                'absolute_deviation': ['mean', 'std', 'min', 'max', 'count']
            }).reset_index()
            
            perf_stats.columns = [
                'lab_name', 'avg_deviation', 'std_deviation', 
                'min_deviation', 'max_deviation', 'count'
            ]
            
            # Format for display
            display_perf = perf_stats.copy()
            display_perf['avg_deviation'] = display_perf['avg_deviation'].round(2)
            display_perf['std_deviation'] = display_perf['std_deviation'].round(2)
            display_perf['min_deviation'] = display_perf['min_deviation'].round(2)
            display_perf['max_deviation'] = display_perf['max_deviation'].round(2)
            
            st.dataframe(display_perf, use_container_width=True)
    else:
        st.info("No inter-laboratory comparison data available for the selected time period.")

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