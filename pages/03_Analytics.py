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
from auth import require_permission, display_access_denied, check_page_access

st.set_page_config(page_title="Analytics", page_icon="📈", layout="wide")

# Check authentication and permissions
if not check_page_access("Analytics"):
    display_access_denied()
    st.stop()

st.title("Assayer Performance Analytics")
st.markdown("""Analyze long-term trends and performance of assayers against benchmark. Gold purity is measured in parts per thousand (ppt).

**Understanding deviation values:**
- **Positive deviation** (+): Assayer reads higher than benchmark (potential gold loss)
- **Negative deviation** (-): Assayer reads lower than benchmark (potential gold gain)
- **Absolute deviation**: The magnitude of deviation regardless of direction""")

# Check if benchmark is set
current_benchmark = get_current_benchmark()

if current_benchmark is None:
    st.warning("No benchmark assayer set. Please set one in the Daily Monitoring page.")
    st.stop()

# Display benchmark info
st.info(f"Current benchmark assayer: **{current_benchmark['name']}**")

# Define analysis time period
st.header("Analysis Settings")

# Add radio buttons for different time period options
period_options = st.radio(
    "Select time period:",
    ["Last 7 days", "Last 30 days", "Last 90 days", "Last 365 days", "Custom"],
    horizontal=True
)

custom_start_date = None
custom_end_date = None

# Initialize default values
days = 30
time_period = "Last month"
filter_start_date = (datetime.now() - timedelta(days=30)).date()
filter_end_date = datetime.now().date()

# Handle different time period selections
if period_options == "Last 7 days":
    days = 7
    time_period = "Last week"
    filter_start_date = (datetime.now() - timedelta(days=7)).date()
    filter_end_date = datetime.now().date()
elif period_options == "Last 30 days":
    days = 30
    time_period = "Last month"
    filter_start_date = (datetime.now() - timedelta(days=30)).date()
    filter_end_date = datetime.now().date()
elif period_options == "Last 90 days":
    days = 90
    time_period = "Last quarter"
    filter_start_date = (datetime.now() - timedelta(days=90)).date()
    filter_end_date = datetime.now().date()
elif period_options == "Last 365 days":
    days = 365
    time_period = "Last year"
    filter_start_date = (datetime.now() - timedelta(days=365)).date()
    filter_end_date = datetime.now().date()
elif period_options == "Custom":
    # Set default values for custom date selection
    default_start = datetime.now().date() - timedelta(days=90)
    default_end = datetime.now().date()
    
    col1, col2 = st.columns(2)
    with col1:
        custom_start_date = st.date_input("Start Date", value=default_start)
    with col2:
        custom_end_date = st.date_input("End Date", value=default_end)
    
    # Ensure we have valid dates
    if not custom_start_date:
        custom_start_date = default_start
    if not custom_end_date:
        custom_end_date = default_end
    
    # Calculate days for API requests - we'll fetch a large amount of data then filter
    days = 9999
    filter_start_date = custom_start_date
    filter_end_date = custom_end_date
    time_period = f"{custom_start_date.strftime('%Y-%m-%d')} to {custom_end_date.strftime('%Y-%m-%d')}"

# Moving average window
ma_window = st.slider("Moving Average Window (days):", min_value=3, max_value=30, value=7)

# Get deviation data - use a large number to ensure we get all data
deviations_df = get_deviations_from_benchmark(days=9999)

if deviations_df is None or deviations_df.empty:
    st.info(f"No deviation data available for the selected time period.")
    st.stop()

# Convert test_date to datetime for filtering
deviations_df['test_date'] = pd.to_datetime(deviations_df['test_date'])

# Filter by date range based on selected period
if period_options == "Custom" or filter_start_date is not None:
    # Filter the dataframe based on the date range
    filtered_df = deviations_df[
        (deviations_df['test_date'].dt.date >= filter_start_date) & 
        (deviations_df['test_date'].dt.date <= filter_end_date)
    ]
    
    if filtered_df.empty:
        st.info(f"No data available for the selected time period: {time_period}")
        st.stop()
    
    # Replace the original dataframe with the filtered one
    deviations_df = filtered_df

# Display overall statistics
st.header("Overall Performance Metrics")

# Get performance data with the same date filter
if period_options == "Custom":
    performance_df = get_assayer_performance(days=9999, start_date=filter_start_date, end_date=filter_end_date)
else:
    performance_df = get_assayer_performance(days=days)

if performance_df is not None and not performance_df.empty:
    # Format data for display - use 3 decimal places consistently
    performance_df['avg_deviation'] = performance_df['avg_deviation'].round(3)
    performance_df['avg_absolute_deviation'] = performance_df['avg_absolute_deviation'].round(3)
    performance_df['avg_percentage_deviation'] = performance_df['avg_percentage_deviation'].round(2)
    performance_df['first_test'] = pd.to_datetime(performance_df['first_test']).dt.strftime('%Y-%m-%d')
    performance_df['last_test'] = pd.to_datetime(performance_df['last_test']).dt.strftime('%Y-%m-%d')
    
    # Create a color scale for absolute deviation in ppt
    performance_df['color'] = np.where(
        performance_df['avg_absolute_deviation'].abs() < 0.1, 'green',
        np.where(performance_df['avg_absolute_deviation'].abs() < 0.3, 'orange', 'red')
    )
    
    # Create 3 columns for key metrics
    st.subheader("Assayer Performance Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_samples = performance_df['sample_count'].sum()
        st.metric("Total Samples Analyzed", total_samples)
    
    with col2:
        avg_deviation = performance_df['avg_deviation'].mean()
        # Use a delta indicator showing if trending positive or negative
        # Using 3 decimal places for consistency with Daily Monitoring
        st.metric("Overall Avg Deviation", f"{avg_deviation:+.3f} ppt", 
                 delta=f"{'+' if avg_deviation > 0 else ''}{avg_deviation:.3f} ppt",
                 delta_color="inverse")
    
    with col3:
        best_assayer = performance_df.loc[performance_df['avg_absolute_deviation'].abs().idxmin()]
        # Using 3 decimal places for consistency across the application
        st.metric("Best Performing Assayer", best_assayer['assayer_name'], 
                 f"{best_assayer['avg_absolute_deviation']:.3f} ppt")
    
    # Display performance table
    st.dataframe(
        performance_df[['assayer_name', 'sample_count', 'avg_deviation', 'avg_absolute_deviation', 
                      'avg_percentage_deviation', 'first_test', 'last_test']],
        use_container_width=True
    )
    
    # Performance visualization
    perf_fig = px.bar(
        performance_df.sort_values('avg_deviation'),
        x='assayer_name',
        y='avg_deviation',
        color='avg_deviation',
        color_continuous_scale=px.colors.diverging.RdBu_r,
        color_continuous_midpoint=0,
        text='sample_count',
        labels={
            'assayer_name': 'Assayer',
            'avg_deviation': 'Avg Deviation (ppt)',
            'sample_count': 'Samples'
        },
        title="Performance Ranking by Average Deviation (ppt)"
    )
    
    # Set color scale range to highlight 0.3 ppt deviation
    perf_fig.update_layout(
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
    
    perf_fig.update_traces(texttemplate='%{text} samples', textposition='outside')
    
    st.plotly_chart(perf_fig, use_container_width=True)
else:
    st.info("No performance data available for the selected time period.")

# Trend Analysis
st.header("Trend Analysis")

# Add individual assayer selection for trend analysis
st.subheader("Assayer Selection")
# Ensure we have a DataFrame and get unique assayer names
if isinstance(deviations_df, pd.DataFrame) and not deviations_df.empty:
    available_assayers = sorted(deviations_df['assayer_name'].unique().tolist())
    assayer_options = ["All Assayers"] + available_assayers

    selected_assayer = st.selectbox(
        "Select assayer for trend analysis:",
        options=assayer_options,
        index=0,
        help="Choose a specific assayer to view individual trends, or 'All Assayers' to see everyone together"
    )

    # Filter data based on selection
    if selected_assayer == "All Assayers":
        filtered_trend_df = deviations_df.copy()
        chart_title_suffix = ""
    else:
        filtered_trend_df = deviations_df[deviations_df['assayer_name'] == selected_assayer].copy()
        chart_title_suffix = f" - {selected_assayer}"
else:
    st.error("No data available for trend analysis.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["Moving Averages", "Deviation Distribution", "Deviation Over Time"])

with tab1:
    st.subheader(f"{ma_window}-Day Moving Average Trends{chart_title_suffix}")
    
    # Create moving average chart with filtered data and consistent colors
    ma_fig = create_moving_average_chart(filtered_trend_df, window=ma_window, all_assayers_df=deviations_df)
    
    if ma_fig:
        # Update chart title to reflect selection
        if selected_assayer != "All Assayers":
            ma_fig.update_layout(title=f"{ma_window}-Day Moving Average - {selected_assayer}")
        
        st.plotly_chart(ma_fig, use_container_width=True)
        
        # Add AI analysis of the trend chart
        import sys
        import os
        # Add parent directory to path to import modules
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from deepseek_assistant import analyze_trend_chart
        
        with st.spinner("Analyzing trend chart..."):
            trend_analysis = analyze_trend_chart(filtered_trend_df, ma_window=ma_window, time_period=time_period)
        
        # Add toggle for showing/hiding trend analysis
        show_trend_analysis = st.toggle("Show Trend Chart Interpretation", value=False)
        if show_trend_analysis:
            st.info(f"**📊 Trend Interpretation{chart_title_suffix}:**\n\n{trend_analysis}")
    else:
        if selected_assayer == "All Assayers":
            st.info(f"Not enough data to calculate {ma_window}-day moving average.")
        else:
            st.info(f"Not enough data for {selected_assayer} to calculate {ma_window}-day moving average.")

with tab2:
    st.subheader(f"Deviation Distribution{chart_title_suffix}")
    
    # Create deviation distribution chart with filtered data and consistent colors
    dist_fig = create_deviation_distribution_chart(filtered_trend_df, all_assayers_df=deviations_df)
    
    if dist_fig:
        # Update chart title to reflect selection
        if selected_assayer != "All Assayers":
            dist_fig.update_layout(title=f"Deviation Distribution - {selected_assayer}")
        
        st.plotly_chart(dist_fig, use_container_width=True)
        
        # Add AI analysis of the distribution chart
        import sys
        import os
        # Add parent directory to path to import modules
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from deepseek_assistant import analyze_distribution_chart
        
        with st.spinner("Analyzing distribution..."):
            distribution_analysis = analyze_distribution_chart(filtered_trend_df, time_period=time_period)
        
        # Add toggle for showing/hiding distribution analysis
        show_dist_analysis = st.toggle("Show Distribution Chart Interpretation", value=False)
        if show_dist_analysis:
            st.info(f"**📊 Distribution Interpretation{chart_title_suffix}:**\n\n{distribution_analysis}")
    else:
        if selected_assayer == "All Assayers":
            st.info("Not enough data to create distribution visualization.")
        else:
            st.info(f"Not enough data for {selected_assayer} to create distribution visualization.")

with tab3:
    st.subheader(f"Deviation Trend Over Time{chart_title_suffix}")
    
    # Group by date using filtered data
    filtered_trend_df['test_date'] = pd.to_datetime(filtered_trend_df['test_date'])
    
    # Use actual deviation (not absolute) to show positive/negative trends
    # This allows positive and negative deviations to cancel each other out
    daily_avg = filtered_trend_df.groupby([pd.Grouper(key='test_date', freq='D'), 'assayer_name'])['deviation'].mean().reset_index()
    
    if not daily_avg.empty:
        # Create consistent color mapping for line chart
        from utils import get_assayer_color_map
        all_assayer_names = deviations_df['assayer_name'].unique().tolist()
        color_map = get_assayer_color_map(all_assayer_names)
        
        # Create a color sequence that matches our mapping
        assayers_in_chart = sorted(daily_avg['assayer_name'].unique())
        color_sequence = [color_map.get(assayer, '#1f77b4') for assayer in assayers_in_chart]
        
        # Create line chart
        if selected_assayer == "All Assayers":
            chart_title = "Daily Average Deviation by Assayer (ppt)"
        else:
            chart_title = f"Daily Average Deviation - {selected_assayer} (ppt)"
            
        trend_fig = px.line(
            daily_avg,
            x='test_date',
            y='deviation',
            color='assayer_name',
            color_discrete_sequence=color_sequence,
            category_orders={"assayer_name": assayers_in_chart},
            labels={
                'test_date': 'Date',
                'deviation': 'Deviation (ppt)',
                'assayer_name': 'Assayer'
            },
            title=chart_title
        )
        
        trend_fig.update_layout(
            height=500,
            yaxis=dict(
                range=[-0.3, 0.3]  # Set y-axis range to highlight the 0.3 ppt threshold
            )
        )
        
        # Add reference lines
        trend_fig.add_hline(y=0, line_dash="dash", line_color="gray")
        trend_fig.add_hline(y=0.3, line_dash="dot", line_color="red", line_width=1)
        trend_fig.add_hline(y=-0.3, line_dash="dot", line_color="red", line_width=1)
        
        st.plotly_chart(trend_fig, use_container_width=True)
    else:
        if selected_assayer == "All Assayers":
            st.info("No deviation data available for trend analysis.")
        else:
            st.info(f"No deviation data available for {selected_assayer} for trend analysis.")

# Consistency Analysis
st.header("Consistency Analysis")

# Calculate consistency metrics
# Use actual deviation (allows positive and negative values to cancel out) for average
# Use absolute_deviation for std calculation (consistency measurement)
deviation_stats = deviations_df.groupby('assayer_name')['deviation'].agg(['mean']).reset_index()
absolute_stats = deviations_df.groupby('assayer_name')['absolute_deviation'].agg(['std', 'count']).reset_index()

# Merge the results
consistency_df = pd.merge(deviation_stats, absolute_stats, on='assayer_name')
consistency_df.columns = ['assayer_name', 'avg_deviation', 'std_deviation', 'sample_count']
consistency_df = consistency_df.sort_values('std_deviation')

# Create scatter plot
scatter_fig = px.scatter(
    consistency_df,
    x='avg_deviation',
    y='std_deviation',
    color='assayer_name',
    size='sample_count',
    hover_data=['sample_count'],
    labels={
        'avg_deviation': 'Average Deviation (ppt)',
        'std_deviation': 'Standard Deviation (Consistency)',
        'sample_count': 'Sample Count',
        'assayer_name': 'Assayer'
    },
    title="Accuracy vs. Consistency Analysis"
)

# Set axis ranges to highlight 0.3 ppt
scatter_fig.update_layout(
    height=500,
    xaxis=dict(
        range=[-0.3, 0.3],
        tickvals=[-0.3, -0.1, 0, 0.1, 0.3],
        ticktext=["-0.3", "-0.1", "0", "0.1", "0.3"]
    ),
    yaxis=dict(
        range=[0, 0.3]
    )
)

scatter_fig.add_vline(x=0, line_dash="dash", line_color="gray")
# Add quadrant explanations
scatter_fig.add_annotation(
    text="High Consistency<br>Reads High<br>(+values)",
    x=0.2,
    y=0.05,
    showarrow=False,
    font=dict(color="blue")
)

scatter_fig.add_annotation(
    text="High Consistency<br>Reads Low<br>(-values)",
    x=-0.2,
    y=0.05,
    showarrow=False,
    font=dict(color="blue")
)

scatter_fig.add_annotation(
    text="More Consistent →",
    x=consistency_df['avg_deviation'].mean(),
    y=consistency_df['std_deviation'].min() * 0.8,
    showarrow=False
)
scatter_fig.add_annotation(
    text="More Accurate",
    x=0,
    y=consistency_df['std_deviation'].mean(),
    showarrow=False,
    textangle=90
)

st.plotly_chart(scatter_fig, use_container_width=True)

# Display explanation
st.markdown("""
**Interpretation Guide:**
- **X-axis**: Average deviation in ppt (closer to 0 = more accurate, positive = reads high, negative = reads low)
- **Y-axis**: Standard deviation of deviations in ppt (lower = more consistent)
- **Bubble size**: Number of samples tested
- **Ideal position**: Bottom center of the chart (accurate and consistent)
- **Significance**: Absolute deviations of 0.3 ppt or more warrant further investigation
""")

# Add AI analysis of the consistency chart
import sys
import os
# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from deepseek_assistant import analyze_deviation_data

with st.spinner("Analyzing consistency data..."):
    consistency_analysis = analyze_deviation_data(deviations_df, time_period=time_period)

# Add toggle for showing/hiding consistency analysis
show_consistency_analysis = st.toggle("Show Consistency Chart Interpretation", value=False)
if show_consistency_analysis:
    st.info(f"**📊 Consistency Interpretation:**\n\n{consistency_analysis}")

# Add AI recommendations section
st.header("AI Recommendations")

show_ai_recommendations = st.checkbox("Generate AI Recommendations", value=False, 
                                      help="Use AI to analyze the data and provide specific recommendations")

if show_ai_recommendations:
    import sys
    import os
    # Add parent directory to path to import modules
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from deepseek_assistant import generate_performance_recommendations
    
    with st.spinner("AI is generating recommendations..."):
        recommendations = generate_performance_recommendations(deviations_df, time_period)
    
    st.info(f"**🤖 AI Recommendations:**\n\n{recommendations}")
    
    # Download recommendations
    if st.button("Download Recommendations"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gold_assay_recommendations_{timestamp}.txt"
        
        st.download_button(
            label="Download as Text",
            data=recommendations,
            file_name=filename,
            mime="text/plain"
        )

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
