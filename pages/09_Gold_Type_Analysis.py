import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Import database functions
from database import get_gold_type_analysis, get_assayer_gold_type_performance
from ai_assistant import analyze_deviation_data
from auth import require_permission, display_access_denied, check_page_access

# Set page config
st.set_page_config(page_title="AEG Gold Type Analysis", page_icon="📊", layout="wide")

# Check authentication and permissions
if not check_page_access("Gold_Type_Analysis"):
    display_access_denied()
    st.stop()

# Inline CSS for consistent styling
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: 700;
    color: #1E3A8A;
    margin-bottom: 1rem;
    text-align: center;
}
.sub-header {
    font-size: 1.8rem;
    font-weight: 600;
    color: #1E3A8A;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
}
.sidebar-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: #1E3A8A;
}
.card-container {
    background-color: #F3F4F6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
}
.analysis-box {
    background-color: #F0F9FF;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #3B82F6;
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("<h1 class='main-header'>Gold Type Consistency Analysis</h1>", unsafe_allow_html=True)

# Sidebar for options
with st.sidebar:
    st.markdown("<h3 class='sidebar-title'>Analysis Options</h3>", unsafe_allow_html=True)
    
    # Time period selection
    period_options = {
        "Last 30 days": 30,
        "Last 90 days": 90,
        "Last 180 days": 180,
        "Last 365 days": 365,
        "All time": 9999
    }
    
    selected_period = st.selectbox(
        "Time Period",
        options=list(period_options.keys()),
        index=3  # Default to "Last 365 days"
    )
    
    days = period_options[selected_period]
    
    # Option to filter by specific assayer
    st.markdown("<h3 class='sidebar-title'>Assayer Filter</h3>", unsafe_allow_html=True)
    
    # Import database functions
    from database import get_assayers
    
    # Get all assayers
    assayers = get_assayers()
    
    # Add "All Assayers" option
    if not assayers.empty:
        assayer_options = {"All Assayers": None}
        assayer_options.update({row['name']: row['assayer_id'] for _, row in assayers.iterrows()})
        
        selected_assayer = st.selectbox(
            "Filter by Assayer",
            options=list(assayer_options.keys()),
            index=0  # Default to "All Assayers"
        )
        
        # Get the assayer_id from the selection (None for "All Assayers")
        selected_assayer_id = assayer_options[selected_assayer]
    else:
        selected_assayer_id = None

# Main content
tab1, tab2 = st.tabs(["Gold Type Overview", "Assayer Performance by Gold Type"])

# Gold Type Overview Tab
with tab1:
    st.markdown("<h2 class='sub-header'>Gold Type Consistency Analysis</h2>", unsafe_allow_html=True)
    
    try:
        # Get overall gold type analysis
        gold_type_data = get_gold_type_analysis(days=days)
        
        if gold_type_data is None or gold_type_data.empty:
            st.warning("⚠️ No gold type data available for analysis. The system is now excluding samples with 'Unknown' gold type. Please ensure that you have assigned specific gold types to your samples and that a benchmark assayer is set.")
        else:
            try:
                # Display summary statistics
                st.markdown("<div class='card-container'>", unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                
                try:
                    with col1:
                        most_consistent = gold_type_data.loc[gold_type_data['consistency_rank'] == 1, 'gold_type'].values[0]
                        st.metric("Most Consistent Gold Type", most_consistent)
                    
                    with col2:
                        most_variable = gold_type_data.loc[gold_type_data['variability_rank'] == 1, 'gold_type'].values[0]
                        st.metric("Most Variable Gold Type", most_variable)
                except Exception as e:
                    st.error(f"Error calculating consistency metrics: {e}")
                    most_consistent = "N/A"
                    most_variable = "N/A"
                
                try:    
                    with col3:
                        total_samples = gold_type_data['sample_count'].sum()
                        st.metric("Total Samples", f"{total_samples}")
                    
                    with col4:
                        avg_deviation = gold_type_data['avg_deviation'].mean()
                        st.metric("Average Deviation (ppt)", f"{avg_deviation:.3f}")
                except Exception as e:
                    st.error(f"Error calculating sample metrics: {e}")
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Display the raw data
                st.markdown("<h3 class='sub-header'>Gold Type Statistics</h3>", unsafe_allow_html=True)
                
                try:
                    # Format the data for display
                    display_data = gold_type_data.copy()
                    
                    # Round numeric columns
                    for col in ['avg_deviation', 'std_deviation', 'min_deviation', 'max_deviation']:
                        if col in display_data.columns:
                            display_data[col] = display_data[col].round(3)
                    
                    # Create a custom formatter for highlighting
                    def highlight_best_consistency(row):
                        if 'consistency_rank' in row and row['consistency_rank'] == 1:
                            return ['background-color: rgba(0, 255, 0, 0.2); color: #000;'] * len(row)
                        return [''] * len(row)
                    
                    def highlight_worst_consistency(row):
                        if 'variability_rank' in row and row['variability_rank'] == 1:
                            return ['background-color: rgba(255, 0, 0, 0.2); color: #000;'] * len(row)
                        return [''] * len(row)
                    
                    # Apply the styling
                    styled_data = display_data.style.apply(highlight_best_consistency, axis=1).apply(highlight_worst_consistency, axis=1)
                    
                    # Display the table
                    st.dataframe(styled_data, use_container_width=True)
                except Exception as e:
                    st.error(f"Error displaying data table: {e}")
                    # Still show the raw data if styling fails
                    try:
                        st.dataframe(gold_type_data, use_container_width=True)
                    except:
                        st.error("Could not display gold type data.")
                
                # Create visualizations if we have at least one gold type
                if len(gold_type_data) > 0:
                    st.markdown("<h3 class='sub-header'>Visualizations</h3>", unsafe_allow_html=True)
                    
                    viz_col1, viz_col2 = st.columns(2)
                    
                    with viz_col1:
                        try:
                            # Standard Deviation Bar Chart
                            fig_std = px.bar(
                                gold_type_data.sort_values('std_deviation'), 
                                x='gold_type', 
                                y='std_deviation',
                                title="Standard Deviation by Gold Type (Lower is Better)",
                                color='std_deviation',
                                color_continuous_scale='RdYlGn_r',  # Reversed green-to-red scale
                                labels={
                                    'gold_type': 'Gold Type',
                                    'std_deviation': 'Standard Deviation (ppt)'
                                }
                            )
                            
                            fig_std.update_layout(
                                height=400,
                                template='plotly_white',
                                coloraxis_showscale=True,
                                coloraxis_colorbar=dict(title="Std Dev")
                            )
                            
                            st.plotly_chart(fig_std, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error creating standard deviation chart: {e}")
                    
                    with viz_col2:
                        try:
                            # Sample Count Pie Chart
                            fig_samples = px.pie(
                                gold_type_data, 
                                values='sample_count', 
                                names='gold_type',
                                title="Distribution of Samples by Gold Type",
                                color='gold_type',
                                hover_data=['sample_count', 'avg_deviation']
                            )
                            
                            fig_samples.update_layout(
                                height=400,
                                template='plotly_white'
                            )
                            
                            st.plotly_chart(fig_samples, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error creating pie chart: {e}")
                    
                    try:
                        # Boxplot showing deviation distribution by gold type
                        fig_box = px.box(
                            gold_type_data,
                            x='gold_type',
                            y=['min_deviation', 'avg_deviation', 'max_deviation'],
                            title="Deviation Range by Gold Type",
                            labels={
                                'gold_type': 'Gold Type',
                                'value': 'Deviation (ppt)',
                                'variable': 'Metric'
                            },
                            points='all'
                        )
                        
                        fig_box.update_layout(
                            height=500,
                            template='plotly_white',
                            xaxis_title='Gold Type',
                            yaxis_title='Deviation (ppt)'
                        )
                        
                        st.plotly_chart(fig_box, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating boxplot: {e}")
                else:
                    st.info("Not enough gold type data available to create visualizations.")
            except Exception as e:
                st.error(f"Error analyzing gold type data: {e}")
    except Exception as e:
        st.warning(f"Unable to retrieve gold type data: {e}. Please ensure a benchmark assayer is set and multiple assay results exist.")
        
        # Get combined data for AI analysis
        try:
            from database import get_deviations_from_benchmark
            deviations_df = get_deviations_from_benchmark(days=days)
            
            if deviations_df is not None and not deviations_df.empty:
                # Add AI analysis
                st.markdown("<h3 class='sub-header'>AI Analysis</h3>", unsafe_allow_html=True)
                
                with st.spinner("Generating AI analysis..."):
                    try:
                        # Add gold type column to the analysis if it's missing
                        if 'gold_type' not in deviations_df.columns:
                            deviations_df['gold_type'] = 'Unknown'
                        
                        # Fill missing values
                        deviations_df['gold_type'] = deviations_df['gold_type'].fillna('Unknown')
                        
                        analysis = analyze_deviation_data(deviations_df, time_period=selected_period)
                        st.markdown(f"<div class='analysis-box'>{analysis}</div>", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Could not generate AI analysis: {e}")
                        st.info("Using statistical summary instead.")
                        
                        try:
                            # Fallback to simple analysis
                            analysis = f"""
                            ### Statistical Summary
                            
                            The analysis shows that {most_consistent} has the highest consistency with the lowest standard deviation,
                            while {most_variable} shows the highest variability. 
                            
                            The average deviation across all gold types is {avg_deviation:.3f} ppt.
                            """
                            st.markdown(analysis)
                        except Exception:
                            st.warning("Could not generate statistical summary. Please ensure you have benchmark data and results for multiple gold types.")
        except Exception as e:
            st.warning("Unable to perform deviation analysis. Please ensure a benchmark assayer is set and multiple assay results exist.")

# Assayer Performance by Gold Type Tab
with tab2:
    st.markdown("<h2 class='sub-header'>Assayer Performance by Gold Type</h2>", unsafe_allow_html=True)
    
    try:
        # Get assayer performance by gold type
        assayer_gold_type_data = get_assayer_gold_type_performance(assayer_id=selected_assayer_id, days=days)
        
        if assayer_gold_type_data is None or assayer_gold_type_data.empty:
            st.warning("⚠️ No gold type data available for analysis. The system is now excluding samples with 'Unknown' gold type. Please ensure that you have assigned specific gold types to your samples and that a benchmark assayer is set.")
        else:
            try:
                # Format data for display
                display_data = assayer_gold_type_data.copy()
                
                # Round numeric columns
                for col in ['avg_deviation', 'std_deviation', 'min_deviation', 'max_deviation']:
                    if col in display_data.columns:
                        display_data[col] = display_data[col].round(3)
                
                # Display the table
                st.dataframe(display_data, use_container_width=True)
                
                # Create visualizations only if we have enough data
                if len(display_data) > 0:
                    try:
                        # Create a grouped bar chart for average deviation by assayer and gold type
                        fig_bar = px.bar(
                            assayer_gold_type_data,
                            x='assayer_name',
                            y='avg_deviation',
                            color='gold_type',
                            barmode='group',
                            title="Average Deviation by Assayer and Gold Type",
                            labels={
                                'assayer_name': 'Assayer',
                                'avg_deviation': 'Average Deviation (ppt)',
                                'gold_type': 'Gold Type'
                            }
                        )
                        
                        fig_bar.update_layout(
                            height=500,
                            template='plotly_white',
                            xaxis_title='Assayer',
                            yaxis_title='Average Deviation (ppt)'
                        )
                        
                        st.plotly_chart(fig_bar, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating bar chart: {e}")
                
                    try:
                        # Only create the heatmap if we have multiple assayers and gold types
                        if len(assayer_gold_type_data['assayer_name'].unique()) > 1 and len(assayer_gold_type_data['gold_type'].unique()) > 1:
                            # Create a heatmap of standard deviation by assayer and gold type
                            # Pivot the data for the heatmap
                            heatmap_data = assayer_gold_type_data.pivot_table(
                                index='assayer_name',
                                columns='gold_type',
                                values='std_deviation',
                                aggfunc='mean'
                            ).fillna(0)
                            
                            # Create the heatmap
                            fig_heatmap = go.Figure(data=go.Heatmap(
                                z=heatmap_data.values,
                                x=heatmap_data.columns,
                                y=heatmap_data.index,
                                colorscale='RdYlGn_r',  # Reversed green-to-red scale
                                colorbar=dict(title="Std Deviation"),
                                hovertemplate="Assayer: %{y}<br>Gold Type: %{x}<br>Std Deviation: %{z:.3f}<extra></extra>"
                            ))
                            
                            fig_heatmap.update_layout(
                                title="Standard Deviation by Assayer and Gold Type (Lower is Better)",
                                height=500,
                                template='plotly_white',
                                xaxis_title='Gold Type',
                                yaxis_title='Assayer'
                            )
                            
                            st.plotly_chart(fig_heatmap, use_container_width=True)
                        else:
                            st.info("Need data from multiple assayers and gold types to generate heatmap visualization.")
                    except Exception as e:
                        st.error(f"Error creating heatmap: {e}")
                    
                    try:
                        # Scatter plot showing average deviation vs standard deviation by gold type
                        # Only create if we have multiple gold types
                        if len(assayer_gold_type_data['gold_type'].unique()) > 1:
                            fig_scatter = px.scatter(
                                assayer_gold_type_data,
                                x='avg_deviation',
                                y='std_deviation',
                                color='gold_type',
                                facet_col='gold_type',
                                hover_name='assayer_name',
                                title="Avg. Deviation vs Std. Deviation by Gold Type",
                                labels={
                                    'avg_deviation': 'Average Deviation (ppt)',
                                    'std_deviation': 'Standard Deviation (ppt)',
                                    'gold_type': 'Gold Type',
                                    'assayer_name': 'Assayer'
                                },
                                size='sample_count',
                                size_max=20
                            )
                            
                            fig_scatter.update_layout(
                                height=400,
                                template='plotly_white'
                            )
                            
                            st.plotly_chart(fig_scatter, use_container_width=True)
                        else:
                            st.info("Need data from multiple gold types to generate scatter plot visualization.")
                    except Exception as e:
                        st.error(f"Error creating scatter plot: {e}")
                else:
                    st.info("Not enough data to generate visualizations.")
            except Exception as e:
                st.error(f"Error processing performance data: {e}")
    except Exception as e:
        st.warning(f"Unable to retrieve gold type performance data: {e}")