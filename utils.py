import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional, Tuple

def get_assayer_color_map(assayer_names: List[str]) -> Dict[str, str]:
    """
    Create a consistent color mapping for assayers using Plotly's default color palette
    
    Args:
        assayer_names: List of assayer names
        
    Returns:
        Dict mapping assayer names to hex colors
    """
    # Use Plotly's default color sequence
    plotly_colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
        '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
        '#c49c94', '#f7b6d3', '#c7c7c7', '#dbdb8d', '#9edae5'
    ]
    
    # Sort assayer names for consistency
    sorted_names = sorted(assayer_names)
    
    # Create mapping
    color_map = {}
    for i, name in enumerate(sorted_names):
        color_map[name] = plotly_colors[i % len(plotly_colors)]
    
    return color_map

def calculate_moving_average(df: pd.DataFrame, column: str, window: int) -> pd.Series:
    """Calculate moving average for a column in a dataframe"""
    return df[column].rolling(window=window).mean()

def format_deviation(value: float, as_percentage: bool = False) -> str:
    """Format deviation value for display"""
    if as_percentage:
        return f"{value:.2f}%"
    else:
        # Include sign to clarify positive (reading high) or negative (reading low)
        return f"{value:+.1f} ppt"

def explain_deviation(value: float) -> str:
    """
    Provide an explanation of what a deviation value means
    
    Args:
        value: The deviation value in parts per thousand (ppt)
        
    Returns:
        str: Explanation of the deviation
    """
    abs_value = abs(value)
    
    if value > 0:
        direction = "higher than"
    elif value < 0:
        direction = "lower than"
    else:
        direction = "exactly the same as"
        
    severity = ""
    if abs_value == 0:
        severity = "perfectly matching"
    elif abs_value < 0.1:
        severity = "excellent agreement with"
    elif abs_value < 0.3:
        severity = "acceptable agreement with"
    else:
        severity = "significant deviation from"
        
    return f"{value:+.1f} ppt ({severity} the benchmark, reading {direction} benchmark)"

def get_color_for_deviation(value: float, threshold_warning: float = 0.1, threshold_error: float = 0.3) -> str:
    """
    Return a color based on the severity of the deviation
    
    Args:
        value: The deviation value in ppt (parts per thousand)
        threshold_warning: Warning threshold in ppt (default: 0.1 ppt)
        threshold_error: Error threshold in ppt (default: 0.3 ppt)
    
    Returns:
        str: Color code ("green", "orange", or "red")
    """
    if abs(value) < threshold_warning:
        return "green"
    elif abs(value) < threshold_error:
        return "orange"
    else:
        return "red"

def create_deviation_heatmap(deviations_df: pd.DataFrame) -> go.Figure:
    """Create a heatmap visualization of deviations by assayer and date"""
    if deviations_df.empty:
        return None
    
    # Convert to datetime if not already
    deviations_df['test_date'] = pd.to_datetime(deviations_df['test_date'])
    deviations_df['test_date'] = deviations_df['test_date'].dt.date
    
    # Group by assayer and date, calculate mean deviation
    # Use actual deviation (not absolute) to allow positive/negative values to be properly displayed
    pivot_df = deviations_df.pivot_table(
        index='assayer_name', 
        columns='test_date', 
        values='deviation',  # Use actual deviation to show positive and negative values
        aggfunc='mean'
    )
    
    # Create heatmap with modified color scale and range
    fig = px.imshow(
        pivot_df,
        labels=dict(x="Date", y="Assayer", color="Deviation (ppt)"),  # Changed from % Deviation to Deviation (ppt)
        x=pivot_df.columns,
        y=pivot_df.index,
        color_continuous_scale="RdBu_r",
        color_continuous_midpoint=0,
        zmin=-0.3,  # Set minimum deviation color scale
        zmax=0.3,   # Set maximum deviation color scale
        aspect="auto",
        text_auto=".1f",  # Format the displayed text to 1 decimal place
    )
    
    # Configure the hover template to display properly formatted values with explanation
    fig.update_traces(
        hovertemplate="<b>Assayer:</b> %{y}<br>" +
                     "<b>Date:</b> %{x}<br>" +
                     "<b>Deviation:</b> %{z:+.1f} ppt<br>" +
                     "<i>Positive = reads higher than benchmark<br>" +
                     "Negative = reads lower than benchmark</i><extra></extra>"
    )
    
    fig.update_layout(
        title="Deviation Heatmap by Assayer and Date (ppt)",
        xaxis_title="Date",
        yaxis_title="Assayer",
        height=500,
    )
    
    return fig

def create_moving_average_chart(deviations_df: pd.DataFrame, window: int = 7, all_assayers_df: pd.DataFrame = None) -> go.Figure:
    """Create a line chart with moving average of deviations with consistent colors"""
    # Handle empty DataFrame or None with early exit
    if deviations_df is None or deviations_df.empty:
        return None
    
    # Wrap the entire function in try/except to catch division by zero and other errors
    try:
        # Convert to datetime if not already
        deviations_df['test_date'] = pd.to_datetime(deviations_df['test_date'])
        
        # Always use the actual deviation (signed values) for trend charts
        # This allows the moving average to show if an assayer consistently reads high or low
        
        # Group by date and assayer, calculate mean deviation
        grouped_df = deviations_df.groupby(['test_date', 'assayer_name'])['deviation'].mean().reset_index()
        
        # Early exit if we don't have enough data after grouping
        if grouped_df.empty:
            return None
            
        # Get unique assayers
        assayers = grouped_df['assayer_name'].unique()
        
        # Create consistent color mapping
        # Use all_assayers_df if provided to get complete list, otherwise use current data
        if all_assayers_df is not None and not all_assayers_df.empty:
            all_assayer_names = all_assayers_df['assayer_name'].unique().tolist()
        else:
            all_assayer_names = assayers.tolist()
        
        color_map = get_assayer_color_map(all_assayer_names)
        
        # Create figure
        fig = go.Figure()
        
        # Flag to track if we've added any traces
        traces_added = False
        
        for assayer in assayers:
            assayer_df = grouped_df[grouped_df['assayer_name'] == assayer].sort_values('test_date')
            
            # Calculate moving average if enough data points
            if len(assayer_df) >= window:
                assayer_df['moving_avg'] = assayer_df['deviation'].rolling(window=window).mean()
                
                # Only add the trace if we have valid data after the rolling window
                valid_data = assayer_df.dropna(subset=['moving_avg'])
                if not valid_data.empty:
                    fig.add_trace(go.Scatter(
                        x=valid_data['test_date'],
                        y=valid_data['moving_avg'],
                        mode='lines',
                        name=f"{assayer} ({window}-day MA)",
                        line=dict(width=2, color=color_map.get(assayer, '#1f77b4'))
                    ))
                    traces_added = True
        
        # If no traces were added, return None
        if not traces_added:
            return None
            
        # If we got this far, we have a valid figure with traces
        fig.update_layout(
            title=f"{window}-Day Moving Average of Deviations (ppt)",
            xaxis_title="Date",
            yaxis_title="Deviation (ppt)",
            height=500,
            legend_title="Assayer",
            hovermode="x unified",
            # Set y-axis range to highlight the 0.3 ppt threshold
            yaxis=dict(
                range=[-0.3, 0.3]
            )
        )
        
        # Add zero line reference
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        # Add threshold references at ±0.3 ppt
        fig.add_hline(y=0.3, line_dash="dot", line_color="red", line_width=1)
        fig.add_hline(y=-0.3, line_dash="dot", line_color="red", line_width=1)
        
        return fig
        
    except Exception as e:
        print(f"Error in trend analysis: {str(e)}")
        return None

def create_deviation_distribution_chart(deviations_df: pd.DataFrame, all_assayers_df: pd.DataFrame = None) -> go.Figure:
    """Create a box plot of deviation distributions by assayer with consistent colors"""
    # Handle empty DataFrame or None with early exit
    if deviations_df is None or deviations_df.empty:
        return None
    
    try:
        # Check how many unique assayers we have
        unique_assayers = deviations_df['assayer_name'].nunique()
        
        # Create consistent color mapping
        # Use all_assayers_df if provided to get complete list, otherwise use current data
        if all_assayers_df is not None and not all_assayers_df.empty:
            all_assayer_names = all_assayers_df['assayer_name'].unique().tolist()
        else:
            all_assayer_names = deviations_df['assayer_name'].unique().tolist()
        
        color_map = get_assayer_color_map(all_assayer_names)
        
        # Create a color sequence that matches our mapping
        assayers_in_chart = sorted(deviations_df['assayer_name'].unique())
        color_sequence = [color_map.get(assayer, '#1f77b4') for assayer in assayers_in_chart]
        
        # Always use the actual deviation (signed values) for distribution charts
        # This allows the distribution to show if an assayer reads consistently high or low
        fig = px.box(
            deviations_df,
            x="assayer_name",
            y="deviation",  # Use actual deviation to show positive/negative values
            points="all",
            color="assayer_name",
            color_discrete_sequence=color_sequence,
            category_orders={"assayer_name": assayers_in_chart},
            title="Distribution of Deviations by Assayer (ppt)",
            labels={
                "assayer_name": "Assayer",
                "deviation": "Deviation (ppt)"  # Updated label
            }
        )
        
        # Adjust box width based on number of assayers
        if unique_assayers == 1:
            # For single assayer, make box much narrower and center it
            fig.update_traces(width=0.15)  # Much narrower box
            fig.update_layout(
                xaxis=dict(
                    range=[-0.8, 0.8],  # Wider x-axis range to show the narrow box better
                    fixedrange=True
                ),
                # Add more padding around the plot
                margin=dict(l=50, r=50, t=80, b=50)
            )
        elif unique_assayers == 2:
            # For 2 assayers, make boxes narrower
            fig.update_traces(width=0.25)
        elif unique_assayers <= 4:
            # For 3-4 assayers, make boxes narrower
            fig.update_traces(width=0.35)
        else:
            # For more assayers, use moderate width
            fig.update_traces(width=0.5)
        
        fig.update_layout(
            xaxis_title="Assayer",
            yaxis_title="Deviation (ppt)",
            height=500,
            showlegend=False,
            # Set y-axis range to highlight the 0.3 ppt threshold
            yaxis=dict(
                range=[-0.3, 0.3]
            )
        )
        
        # Add zero line reference
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        # Add threshold references at ±0.3 ppt
        fig.add_hline(y=0.3, line_dash="dot", line_color="red", line_width=1)
        fig.add_hline(y=-0.3, line_dash="dot", line_color="red", line_width=1)
        
        return fig
        
    except Exception as e:
        print(f"Error in distribution analysis: {str(e)}")
        return None

def export_data_to_csv(df: pd.DataFrame, filename: str = "gold_assay_data.csv") -> str:
    """Export dataframe to CSV and return the path"""
    df.to_csv(filename, index=False)
    return filename

def parse_date_input(date_str: str) -> datetime:
    """Parse date string input into datetime object"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None
