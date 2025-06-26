import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
import math
import random
from datetime import datetime, timedelta

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_assayers, set_benchmark_assayer, get_current_benchmark, get_deviations_from_benchmark, get_assayer_profile, get_all_assayer_profiles
from utils import get_color_for_deviation, create_deviation_heatmap
from auth import require_permission, display_access_denied, check_page_access

# Import the chat component
from simple_chat import display_chat_widget

st.set_page_config(page_title="Daily Monitoring", page_icon="📊", layout="wide")

# Check authentication and permissions
if not check_page_access("Daily_Monitoring"):
    display_access_denied()
    st.stop()

# Display the chat widget
display_chat_widget()

# Custom CSS for page styling
st.markdown("""
<style>
    /* Custom styles for the monitoring page */
</style>
""", unsafe_allow_html=True)

st.title("Daily Assayer Monitoring")
st.markdown("""Monitor deviations in gold purity (ppt) between assayers and benchmark on a daily basis.

**Understanding deviation values:**
- **Positive deviation** (+): Assayer reads higher than benchmark (potential gold loss)
- **Negative deviation** (-): Assayer reads lower than benchmark (potential gold gain)
- **Absolute deviation**: The magnitude of deviation regardless of direction""")

# Get current benchmark assayer
current_benchmark = get_current_benchmark()

# Setting benchmark assayer
st.header("Benchmark Assayer")

if current_benchmark is not None:
    st.info(f"Current benchmark assayer: **{current_benchmark['name']}** (Set on: {current_benchmark['set_date']})")
else:
    st.warning("No benchmark assayer set. Please select one below.")

# Get list of assayers for the dropdown
try:
    assayers_df = get_assayers()
    if not assayers_df.empty:
        benchmark_options = {row['name']: row['assayer_id'] for _, row in assayers_df.iterrows()}
        
        selected_benchmark = st.selectbox(
            "Select benchmark assayer",
            options=list(benchmark_options.keys())
        )
        
        if st.button("Set as Benchmark"):
            benchmark_id = benchmark_options[selected_benchmark]
            success = set_benchmark_assayer(benchmark_id)
            
            if success:
                st.success(f"Successfully set {selected_benchmark} as the benchmark assayer")
                # Force page refresh
                st.rerun()
            else:
                st.error("Failed to set benchmark assayer")
    else:
        st.error("No assayers available. Please add assayers in the Data Entry page.")
except Exception as e:
    st.error(f"Error retrieving assayers: {e}")

# Display filter options
st.header("Deviation Analysis")

time_period = st.radio(
    "Select time period:",
    ["Today", "Yesterday", "Last 7 days", "Last 30 days", "Custom"],
    horizontal=True
)

custom_start_date = None
custom_end_date = None

if time_period == "Custom":
    # Set default values
    default_start = datetime.now().date() - timedelta(days=7)
    default_end = datetime.now().date()
    
    col1, col2 = st.columns(2)
    with col1:
        custom_start_date = st.date_input("Start Date", value=default_start)
    with col2:
        custom_end_date = st.date_input("End Date", value=default_end)
        
    # Ensure we have valid dates (not None)
    if not custom_start_date:
        custom_start_date = default_start
    if not custom_end_date:
        custom_end_date = default_end

# Determine number of days to fetch and date range to use
if time_period == "Today":
    days = 1
    filter_start_date = datetime.now().date()
    filter_end_date = datetime.now().date()
elif time_period == "Yesterday":
    days = 2
    filter_start_date = (datetime.now() - timedelta(days=1)).date()
    filter_end_date = (datetime.now() - timedelta(days=1)).date()
elif time_period == "Last 7 days":
    days = 7
    filter_start_date = (datetime.now() - timedelta(days=7)).date()
    filter_end_date = datetime.now().date()
elif time_period == "Last 30 days":
    days = 30
    filter_start_date = (datetime.now() - timedelta(days=30)).date()
    filter_end_date = datetime.now().date()
else:  # Custom
    # For custom dates, we'll fetch a large range of data and filter it
    # This fixes the issue with non-current end dates
    if custom_start_date and custom_end_date:
        days = 365  # Fetch a full year of data to ensure we have enough
        filter_start_date = custom_start_date
        filter_end_date = custom_end_date
    else:
        # Fallback in case date inputs are None
        days = 30
        filter_start_date = (datetime.now() - timedelta(days=30)).date()
        filter_end_date = datetime.now().date()

# Fetch deviation data
if current_benchmark is not None:
    # Get deviations without time filtering - we'll filter in pandas
    deviations_df = get_deviations_from_benchmark(days=9999)  # Use a large value to get all data
    
    if deviations_df is not None and not deviations_df.empty:
        # Filter by the appropriate date range
        deviations_df = deviations_df[
            (deviations_df['test_date'].dt.date >= filter_start_date) & 
            (deviations_df['test_date'].dt.date <= filter_end_date)
        ]
        
        if deviations_df.empty:
            st.info(f"No deviation data available for the selected time period.")
        else:
            # Display summary statistics
            st.subheader("Summary Statistics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Calculate total samples consistently with Analytics page
                # This counts the total samples across all assayers
                sample_counts = deviations_df.groupby('assayer_name')['sample_id'].count().sum()
                st.metric("Total Samples", sample_counts)
                
                # Also show unique samples for clarity
                unique_samples = deviations_df['sample_id'].nunique()
                st.caption(f"({unique_samples} unique sample IDs)")
            
            with col2:
                num_assayers = deviations_df['assayer_name'].nunique()
                st.metric("Assayers", num_assayers)
            
            with col3:
                avg_deviation = deviations_df['deviation'].mean()
                # Display both the value and the sign to indicate direction
                st.metric("Avg Deviation", f"{avg_deviation:+.1f} ppt", 
                          delta=f"{'+' if avg_deviation > 0 else ''}{avg_deviation:.1f} ppt",
                          delta_color="inverse")
            
            # Jump directly to the deviation analysis
            st.markdown("")  # Add a little spacing
            
            # Deviation heatmap visualization
            st.subheader("Deviation Heatmap")
            
            fig = create_deviation_heatmap(deviations_df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                
                # Automatically provide AI analysis of the heatmap
                import sys
                import os
                # Add parent directory to path to import modules
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from deepseek_assistant import analyze_heatmap
                
                with st.spinner("Analyzing heatmap patterns..."):
                    heatmap_analysis = analyze_heatmap(deviations_df, time_period)
                
                st.info(f"**📊 AI Heatmap Analysis:**\n\n{heatmap_analysis}")
            else:
                st.info("Not enough data to create heatmap visualization.")
            
            # Display average deviations by assayer
            st.subheader("Average Deviations by Assayer")
            
            # Automatically provide AI analysis of the deviations
            import sys
            import os
            # Add parent directory to path to import modules
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from deepseek_assistant import analyze_deviation_data
            
            with st.spinner("Analyzing assayer performance..."):
                ai_analysis = analyze_deviation_data(deviations_df, time_period)
            
            # Add toggle for showing/hiding performance analysis
            show_performance_analysis = st.toggle("Show Performance Analysis Interpretation", value=False)
            if show_performance_analysis:
                st.info(f"**🤖 Performance Interpretation:**\n\n{ai_analysis}")
            
            # Calculate statistics including min and max for pin bar chart
            assayer_stats = deviations_df.groupby('assayer_name').agg({
                'deviation': ['mean', 'std', 'min', 'max'],  # Added min and max for pin bars
                'absolute_deviation': ['mean', 'std', 'count'],
                'percentage_deviation': ['mean', 'std']
            }).reset_index()
            
            # Flatten the multi-level columns
            assayer_stats.columns = ['assayer_name', 
                                    'avg_deviation', 'std_deviation', 'min_deviation', 'max_deviation',
                                    'avg_abs_deviation', 'std_abs_deviation', 'sample_count',
                                    'avg_pct_deviation', 'std_pct_deviation']
            
            # Round consistently with Analytics page
            # Use 3 decimal places for more precision (matching Analytics page)
            assayer_stats['avg_deviation'] = assayer_stats['avg_deviation'].round(3)
            assayer_stats['std_deviation'] = assayer_stats['std_deviation'].round(3)
            assayer_stats['min_deviation'] = assayer_stats['min_deviation'].round(3)
            assayer_stats['max_deviation'] = assayer_stats['max_deviation'].round(3)
            assayer_stats['avg_abs_deviation'] = assayer_stats['avg_abs_deviation'].round(3)
            assayer_stats['std_abs_deviation'] = assayer_stats['std_abs_deviation'].round(3)
            assayer_stats['avg_pct_deviation'] = assayer_stats['avg_pct_deviation'].round(2)
            assayer_stats['std_pct_deviation'] = assayer_stats['std_pct_deviation'].round(2)
            
            # Calculate error bars for min/max pin bar chart
            # The error_y parameter needs the distances from the mean to min/max, not the absolute values
            assayer_stats['error_y_plus'] = assayer_stats['max_deviation'] - assayer_stats['avg_deviation']
            assayer_stats['error_y_minus'] = assayer_stats['avg_deviation'] - assayer_stats['min_deviation']
            
            # Create a pin bar chart like the image shared, but with a different approach
            # Since the error_y dictionary was causing length mismatch issues, let's use a different method
            
            # First create the base bar chart
            fig = px.bar(
                assayer_stats.sort_values('avg_deviation'),
                x='assayer_name',
                y='avg_deviation',  # Use actual deviation (with sign) for bar body
                labels={'assayer_name': 'Assayer', 'avg_deviation': 'Deviation (ppt)'},
                title="Average Deviation by Assayer (ppt)",
                color='avg_deviation',  # Color by actual deviation
                color_continuous_scale=px.colors.diverging.RdBu_r,
                color_continuous_midpoint=0,
                text='sample_count',
                hover_data=['min_deviation', 'avg_deviation', 'max_deviation', 'sample_count']  # Show min/max in hover
            )
            
            # Convert to regular DataFrame for easier attribute access
            sorted_data = assayer_stats.sort_values('avg_deviation').reset_index()
            
            # Now add the error bars for each bar manually
            for i in range(len(sorted_data)):
                # Get values for each row
                avg_dev = sorted_data.loc[i, 'avg_deviation']
                max_dev = sorted_data.loc[i, 'max_deviation']
                min_dev = sorted_data.loc[i, 'min_deviation']
                
                # Add error bars from mean to max
                fig.add_shape(
                    type="line",
                    x0=i,
                    y0=avg_dev,
                    x1=i,
                    y1=max_dev,
                    line=dict(color="rgba(0,0,0,0.7)", width=1.5),
                )
                # Add the top cap
                fig.add_shape(
                    type="line",
                    x0=i-0.1,
                    y0=max_dev,
                    x1=i+0.1,
                    y1=max_dev,
                    line=dict(color="rgba(0,0,0,0.7)", width=1.5),
                )
                
                # Add error bars from mean to min
                fig.add_shape(
                    type="line",
                    x0=i,
                    y0=avg_dev,
                    x1=i,
                    y1=min_dev,
                    line=dict(color="rgba(0,0,0,0.7)", width=1.5),
                )
                # Add the bottom cap
                fig.add_shape(
                    type="line",
                    x0=i-0.1,
                    y0=min_dev,
                    x1=i+0.1,
                    y1=min_dev,
                    line=dict(color="rgba(0,0,0,0.7)", width=1.5),
                )
            
            # Add sample counts above bars
            fig.update_traces(
                textposition='outside',
                texttemplate='%{text} samples',
                textfont=dict(size=10)
            )
            
            # Set color scale range to highlight 0.3 ppt deviation
            fig.update_layout(
                coloraxis_colorbar=dict(
                    title="Deviation (ppt)",
                    tickvals=[-0.3, 0, 0.3],
                    ticktext=["-0.3", "0", "0.3"]
                ),
                coloraxis=dict(
                    cmin=-0.3,
                    cmax=0.3,
                    colorscale="RdBu_r"
                ),
                # Adjust y-axis to show 0.3 ppt range like in the reference image
                yaxis=dict(
                    range=[-0.3, 0.3],
                    zeroline=True,
                    zerolinecolor='black',
                    zerolinewidth=1
                )
            )
            fig.update_layout(height=500)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Individual assayer tabs
            st.subheader("Individual Assayer Analysis")
            
            # Prepare data for individual assayer display
            display_df = deviations_df.copy()
            # Ensure test_date is a datetime type before using dt accessor
            display_df['test_date'] = pd.to_datetime(display_df['test_date'])
            display_df['test_date_fmt'] = display_df['test_date'].dt.strftime('%Y-%m-%d %H:%M')
            display_df['absolute_deviation'] = display_df['absolute_deviation'].round(1)
            display_df['percentage_deviation'] = display_df['percentage_deviation'].round(2)
            
            # Round deviation values for display
            display_df['deviation'] = display_df['deviation'].round(1)
            
            # Reorder and select columns for display
            display_df = display_df[[
                'sample_id', 'assayer_name', 'gold_content', 'benchmark_value', 
                'deviation', 'absolute_deviation', 'percentage_deviation', 'test_date_fmt'
            ]]
            # Rename the column for display
            display_df = display_df.rename(columns={'test_date_fmt': 'test_date'})
            
            # Get unique assayer names for tabs
            assayer_names = ["All Assayers"] + sorted(display_df['assayer_name'].unique().tolist())
            
            # Check if we have a selected assayer from query params (from dashboard clicks)
            selected_assayer_id = st.query_params.get("selected_assayer", None)
            
            # If assayer ID is specified in query params, find the corresponding tab
            default_tab_index = 0
            if selected_assayer_id:
                try:
                    # Get the assayer name for the ID
                    assayer_info = get_assayer_profile(int(selected_assayer_id))
                    if assayer_info:
                        assayer_name = assayer_info.get('name')
                        if assayer_name in assayer_names:
                            default_tab_index = assayer_names.index(assayer_name)
                        # Clear the query parameter to allow normal navigation
                        st.query_params.clear()
                except (ValueError, TypeError):
                    # Invalid ID format, ignore
                    pass
                        
            # Create tabs for each assayer
            assayer_tabs = st.tabs(assayer_names)
            
            # If default_tab_index is not 0, we need to reorder tabs
            if default_tab_index > 0:
                st.markdown(f"""
                <script>
                    // Wait for the DOM to fully load
                    document.addEventListener('DOMContentLoaded', function() {{
                        // Find the tab buttons
                        var tabButtons = document.querySelectorAll('[role="tab"]');
                        if (tabButtons.length > {default_tab_index}) {{
                            // Click the selected tab
                            setTimeout(function() {{
                                tabButtons[{default_tab_index}].click();
                            }}, 100);
                        }}
                    }});
                </script>
                """, unsafe_allow_html=True)
                
            # Display data for all assayers in the first tab
            with assayer_tabs[0]:
                st.dataframe(display_df, use_container_width=True)
                
                # Summary statistics
                if not display_df.empty:
                    # Calculate both actual and absolute deviation stats
                    avg_dev = display_df['deviation'].mean()
                    avg_abs_dev = display_df['absolute_deviation'].mean()
                    avg_pct_dev = display_df['percentage_deviation'].mean()
                    max_dev = display_df['deviation'].max()
                    min_dev = display_df['deviation'].min()
                    
                    col1, col2 = st.columns(2)
                    # Show actual deviation with sign, using 3 decimal places for consistency
                    col1.metric("Average Actual Deviation", f"{avg_dev:+.3f} ppt", 
                              delta=f"{'+' if avg_dev > 0 else ''}{avg_dev:.3f} ppt",
                              delta_color="inverse")
                    
                    # Show absolute deviation (magnitude) - with 3 decimal places for consistency
                    col2.metric("Average Absolute Deviation", f"{abs(avg_abs_dev):.3f} ppt")
                    
                    col1, col2, col3 = st.columns(3)
                    # Using consistent decimal places (3) for all deviation metrics
                    col1.metric("Max Positive Deviation", f"{max_dev:+.3f} ppt")
                    col2.metric("Max Negative Deviation", f"{min_dev:+.3f} ppt")
                    col3.metric("Average % Deviation", f"{avg_pct_dev:.2f}%")
                    
                    # Create a histogram of actual deviations (with sign) for all assayers
                    fig = px.histogram(
                        display_df, 
                        x="deviation",  # Use actual deviation with sign
                        nbins=30,
                        title="Distribution of Deviations Across All Assayers",
                        labels={"deviation": "Deviation (ppt)"},
                        color_discrete_sequence=['#3498DB']  # Blue color for signed values
                    )
                    # Add a vertical line at zero to mark the neutral point
                    fig.add_vline(x=0, line_dash="dash", line_color="black")
                    # Add annotations to explain meaning
                    fig.add_annotation(
                        x=-0.2, y=0.9, 
                        text="Reads lower than benchmark<br>(potential gold gain)",
                        showarrow=False, 
                        xref="paper", yref="paper",
                        align="center",
                        bgcolor="rgba(255, 255, 255, 0.8)"
                    )
                    fig.add_annotation(
                        x=0.8, y=0.9,
                        text="Reads higher than benchmark<br>(potential gold loss)",
                        showarrow=False,
                        xref="paper", yref="paper",
                        align="center",
                        bgcolor="rgba(255, 255, 255, 0.8)"
                    )
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
            
            # Display individual assayer data in their respective tabs
            for i, assayer_name in enumerate(sorted(display_df['assayer_name'].unique().tolist())):
                with assayer_tabs[i+1]:  # +1 because "All Assayers" is the first tab
                    # Filter data for this assayer
                    assayer_df = display_df[display_df['assayer_name'] == assayer_name]
                    
                    # Display the assayer's data
                    st.dataframe(assayer_df, use_container_width=True)
                    
                    # Summary statistics for this assayer
                    if not assayer_df.empty:
                        # Calculate statistics using both actual and absolute deviation
                        avg_dev = assayer_df['deviation'].mean()
                        avg_abs_dev = assayer_df['absolute_deviation'].mean()
                        avg_pct_dev = assayer_df['percentage_deviation'].mean()
                        max_dev = assayer_df['deviation'].max()
                        min_dev = assayer_df['deviation'].min()
                        
                        col1, col2 = st.columns(2)
                        # Show actual deviation with sign, using 3 decimal places for consistency
                        col1.metric("Average Actual Deviation", f"{avg_dev:+.3f} ppt", 
                                  delta=f"{'+' if avg_dev > 0 else ''}{avg_dev:.3f} ppt",
                                  delta_color="inverse")
                        
                        # Show absolute deviation (magnitude) - ensuring it's positive
                        # Take abs() to ensure the value is positive even if there's a data issue
                        # Using 3 decimal places for consistency with Analytics page
                        col2.metric("Average Absolute Deviation", f"{abs(avg_abs_dev):.3f} ppt")
                        
                        col1, col2, col3 = st.columns(3)
                        # Using consistent decimal places (3) for all deviation metrics
                        col1.metric("Maximum Deviation", f"{max_dev:+.3f} ppt")
                        col2.metric("Minimum Deviation", f"{min_dev:+.3f} ppt")
                        col3.metric("Average % Deviation", f"{avg_pct_dev:.2f}%")
                        
                        # Create a histogram of actual deviations (with sign) for this assayer
                        fig = px.histogram(
                            assayer_df, 
                            x="deviation",  # Use actual deviation with sign
                            nbins=20,
                            title=f"Distribution of Deviations for {assayer_name}",
                            labels={"deviation": "Deviation (ppt)"},
                            color_discrete_sequence=['#3498DB']  # Blue color for signed values
                        )
                        # Add a vertical line at zero to mark the neutral point
                        fig.add_vline(x=0, line_dash="dash", line_color="black")
                        # Add annotations to explain meaning
                        fig.add_annotation(
                            x=-0.2, y=0.9, 
                            text="Reads lower than benchmark<br>(potential gold gain)",
                            showarrow=False, 
                            xref="paper", yref="paper",
                            align="center",
                            bgcolor="rgba(255, 255, 255, 0.8)"
                        )
                        fig.add_annotation(
                            x=0.8, y=0.9,
                            text="Reads higher than benchmark<br>(potential gold loss)",
                            showarrow=False,
                            xref="paper", yref="paper",
                            align="center",
                            bgcolor="rgba(255, 255, 255, 0.8)"
                        )
                        fig.update_layout(showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Timeline of deviations - need to use original data with datetime
                        timeline_df = deviations_df[deviations_df['assayer_name'] == assayer_name].copy()
                        timeline_df = timeline_df.sort_values('test_date')
                        
                        fig = px.scatter(
                            timeline_df,
                            x="test_date",
                            y="deviation",  # Use actual deviation with sign
                            title=f"Deviation Timeline for {assayer_name}",
                            labels={"test_date": "Date", "deviation": "Deviation (ppt)"},
                            color="deviation", # Color by actual deviation
                            color_continuous_scale=px.colors.diverging.RdBu_r,
                            color_continuous_midpoint=0,
                            hover_data=["sample_id", "gold_content", "benchmark_value", "absolute_deviation"]
                        )
                        fig.add_hline(y=0, line_dash="dash", line_color="gray")
                        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No deviation data available for the selected time period.")
else:
    st.warning("Please set a benchmark assayer to view deviation data.")

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

# Footer note (we've already added the chat widget at the top of the page)
# No need to display it again here
