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
from database_trainee import get_trainees, get_trainee_summary
from database_trainee import get_trainee_evaluations, get_trainee_performance_history
from auth import require_permission, display_access_denied, check_page_access

st.set_page_config(page_title="Trainee Evaluation", page_icon="🎓", layout="wide")

# Check authentication and permissions
if not check_page_access("Trainee_Evaluation"):
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
        border-bottom: 1px solid rgba(212, 175, 55, 0.4);
    }
    
    .sub-header {
        font-size: 1.6rem;
        color: #D4AF37;
        margin-bottom: 20px;
        text-align: center;
        text-shadow: 1px 1px 1px rgba(0,0,0,0.1);
    }
    
    .section-header {
        font-size: 1.2rem;
        color: #D4AF37;
        margin-bottom: 10px;
        margin-top: 20px;
        border-bottom: 1px solid rgba(212, 175, 55, 0.2);
        padding-bottom: 5px;
    }
    
    .data-container {
        background-color: rgba(255, 255, 255, 0.03);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid rgba(212, 175, 55, 0.2);
    }
    
    .highlight-certified {
        color: green;
        font-weight: bold;
    }
    
    .highlight-pending {
        color: #4682B4;
        font-weight: bold;
    }
    
    .highlight-needs-training {
        color: #CCCC00;
        font-weight: bold;
    }
    
    .metric-container {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 10px;
        border: 1px solid rgba(212, 175, 55, 0.1);
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        text-align: center;
    }
    
    .metric-label {
        font-size: 0.9rem;
        text-align: center;
        color: #B0B0B0;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        border-radius: 4px 4px 0 0;
        padding: 10px 16px;
        background-color: rgba(212, 175, 55, 0.1);
        border-bottom: 1px solid rgba(212, 175, 55, 0.2);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(212, 175, 55, 0.2);
        border-bottom: 2px solid #D4AF37;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("<h1 class='main-header'>Trainee Evaluation & Certification</h1>", unsafe_allow_html=True)

# Get trainee data
trainees_df = get_trainees()
trainee_summary = get_trainee_summary()

if not trainees_df.empty:
    # Sidebar for trainee selection
    st.sidebar.title("Trainee Selection")
    
    # Create a dictionary mapping display names to trainee IDs
    trainee_options = {f"{row['assayer_name']} ({row['employee_id']})": row['trainee_id'] for _, row in trainees_df.iterrows()}
    selected_trainee_label = st.sidebar.selectbox(
        "Select Trainee",
        options=list(trainee_options.keys())
    )
    
    # Get the trainee_id from the selection
    selected_trainee_id = trainee_options[selected_trainee_label]
    
    # Get the selected trainee's data
    selected_trainee = trainee_summary[trainee_summary['trainee_id'] == selected_trainee_id].iloc[0]
    
    # Period selection for performance history
    history_period = st.sidebar.slider(
        "Performance History Period (Days)",
        min_value=7,
        max_value=365,
        value=90,
        step=1
    )
    
    # Display trainee information
    st.markdown("<div class='data-container'>", unsafe_allow_html=True)
    
    # Trainee header with status highlighting
    status = selected_trainee['certification_status']
    status_class = "highlight-certified" if status == "Certified" else "highlight-needs-training" if status == "Needs More Training" else "highlight-pending"
    
    st.markdown(f"""
    <h2 class='sub-header'>
        {selected_trainee['assayer_name']} - <span class='{status_class}'>{status}</span>
    </h2>
    """, unsafe_allow_html=True)
    
    # Trainee details in two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("<p class='section-header'>Trainee Details</p>", unsafe_allow_html=True)
        
        # Format date information
        start_date = pd.to_datetime(selected_trainee['start_date']).strftime('%Y-%m-%d') if pd.notna(selected_trainee['start_date']) else "Not available"
        certification_date = pd.to_datetime(selected_trainee['certification_date']).strftime('%Y-%m-%d') if pd.notna(selected_trainee['certification_date']) else "Not certified yet"
        
        st.markdown(f"""
        <div class='metric-container'>
            <div class='metric-label'>Employee ID</div>
            <div class='metric-value'>{selected_trainee['employee_id']}</div>
        </div>
        
        <div class='metric-container'>
            <div class='metric-label'>Training Started</div>
            <div class='metric-value'>{start_date}</div>
        </div>
        
        <div class='metric-container'>
            <div class='metric-label'>Certification Date</div>
            <div class='metric-value'>{certification_date}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("<p class='section-header'>Certification Requirements</p>", unsafe_allow_html=True)
        
        target_tolerance = selected_trainee['target_tolerance']
        min_samples = selected_trainee['min_samples_required']
        
        # Get total samples if it exists, otherwise default to 0
        total_samples = selected_trainee.get('total_samples_evaluated', 0)
        
        # Get average deviation if it exists, otherwise default to 0
        avg_deviation = selected_trainee.get('average_deviation', 0.0)
        
        st.markdown(f"""
        <div class='metric-container'>
            <div class='metric-label'>Samples Done vs Required</div>
            <div class='metric-value'>{int(total_samples)} / {min_samples}</div>
        </div>
        
        <div class='metric-container'>
            <div class='metric-label'>Target vs Current Deviation</div>
            <div class='metric-value'>{target_tolerance:.2f} / {avg_deviation:.2f} ppt</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Create tabs for different types of analysis
    tab1, tab2, tab3 = st.tabs(["Overall Performance", "Accuracy Analysis", "Consistency Analysis"])
    
    # Tab 1: Overall Performance
    with tab1:
        st.markdown("<div class='data-container'>", unsafe_allow_html=True)
        st.markdown("<p class='section-header'>Overall Performance Metrics</p>", unsafe_allow_html=True)
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Using .get() method to avoid KeyError if key doesn't exist
            total_samples = selected_trainee.get('total_samples_evaluated', 0)
            st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-label'>Total Samples</div>
                <div class='metric-value'>{int(total_samples)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            percent_within_tolerance = selected_trainee.get('percent_within_tolerance', 0.0)
            st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-label'>Overall Accuracy</div>
                <div class='metric-value'>{percent_within_tolerance:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            avg_deviation = selected_trainee.get('average_deviation', 0.0)
            st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-label'>Average Deviation</div>
                <div class='metric-value'>{avg_deviation:.2f} ppt</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            std_deviation = selected_trainee.get('standard_deviation', 0.0)
            st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-label'>Standard Deviation</div>
                <div class='metric-value'>{std_deviation:.2f} ppt</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Performance history chart
        st.markdown("<p class='section-header'>Performance History</p>", unsafe_allow_html=True)
        
        # Get performance history data
        history_df = get_trainee_performance_history(selected_trainee_id, days=history_period)
        
        if not history_df.empty:
            # Create a line chart showing performance over time
            fig1 = go.Figure()
            
            # Add deviation line
            fig1.add_trace(go.Scatter(
                x=history_df['test_date'],
                y=history_df['avg_deviation'],
                mode='lines+markers',
                name='Average Deviation (ppt)',
                line=dict(color='#D4AF37', width=2),
                marker=dict(size=8)
            ))
            
            # Add accuracy percentage line
            fig1.add_trace(go.Scatter(
                x=history_df['test_date'],
                y=history_df['daily_accuracy_percentage'],
                mode='lines+markers',
                name='Accuracy (%)',
                line=dict(color='#4682B4', width=2),
                marker=dict(size=8),
                yaxis='y2'
            ))
            
            # Update layout with dual y-axes
            fig1.update_layout(
                title='Performance Metrics Over Time',
                xaxis=dict(title='Date'),
                yaxis=dict(
                    title=dict(text='Deviation (ppt)', font=dict(color='#D4AF37')),
                    tickfont=dict(color='#D4AF37')
                ),
                yaxis2=dict(
                    title=dict(text='Accuracy (%)', font=dict(color='#4682B4')),
                    tickfont=dict(color='#4682B4'),
                    anchor='x',
                    overlaying='y',
                    side='right'
                ),
                showlegend=True,
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                hovermode='x unified',
                template='plotly_dark'
            )
            
            st.plotly_chart(fig1, use_container_width=True)
            
            # Sample count chart
            fig2 = px.bar(
                history_df,
                x='test_date',
                y='daily_samples',
                title='Number of Samples Evaluated Per Day',
                labels={'test_date': 'Date', 'daily_samples': 'Number of Samples'},
                color_discrete_sequence=['rgba(212, 175, 55, 0.7)']
            )
            
            fig2.update_layout(
                template='plotly_dark',
                xaxis=dict(title='Date'),
                yaxis=dict(title='Number of Samples')
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info(f"No performance history data available for the last {history_period} days.")
        
        # Recent evaluations
        st.markdown("<p class='section-header'>Recent Evaluations</p>", unsafe_allow_html=True)
        
        # Get recent evaluations for this trainee
        recent_evals = get_trainee_evaluations(trainee_id=selected_trainee_id, days=30)
        
        if not recent_evals.empty:
            # Format the dataframe for display
            display_cols = [
                'reference_name', 'certified_gold_content', 'measured_gold_content', 
                'deviation_ppt', 'test_date', 'evaluation_type'
            ]
            
            col_rename = {
                'reference_name': 'Reference',
                'certified_gold_content': 'Certified (ppt)',
                'measured_gold_content': 'Measured (ppt)',
                'deviation_ppt': 'Deviation (ppt)',
                'test_date': 'Date',
                'evaluation_type': 'Type'
            }
            
            # Apply formatting and conditional formatting
            def highlight_deviation(val):
                if abs(val) <= 0.1:
                    return 'background-color: rgba(0, 255, 0, 0.2)'
                elif abs(val) <= 0.3:
                    return 'background-color: rgba(255, 255, 0, 0.2)'
                else:
                    return 'background-color: rgba(255, 0, 0, 0.2)'
            
            # Format the dataframe
            display_df = recent_evals[display_cols].rename(columns=col_rename)
            display_df['Type'] = display_df['Type'].str.capitalize()
            
            styled_evals = display_df.style.applymap(
                highlight_deviation, subset=['Deviation (ppt)']
            ).format({
                'Certified (ppt)': '{:.1f}',
                'Measured (ppt)': '{:.1f}',
                'Deviation (ppt)': '{:.2f}'
            })
            
            st.dataframe(styled_evals, use_container_width=True)
        else:
            st.info("No recent evaluations in the last 30 days.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Tab 2: Accuracy Analysis
    with tab2:
        st.markdown("<div class='data-container'>", unsafe_allow_html=True)
        st.markdown("<p class='section-header'>Accuracy Performance Metrics</p>", unsafe_allow_html=True)
        
        # Key metrics for accuracy
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            accuracy_samples = selected_trainee.get('accuracy_samples', 0)
            st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-label'>Accuracy Samples</div>
                <div class='metric-value'>{int(accuracy_samples)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            accuracy_within_tolerance = selected_trainee.get('accuracy_within_tolerance', 0.0)
            st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-label'>Accuracy Percentage</div>
                <div class='metric-value'>{accuracy_within_tolerance:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            accuracy_avg_deviation = selected_trainee.get('accuracy_avg_deviation', 0.0)
            st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-label'>Average Deviation</div>
                <div class='metric-value'>{accuracy_avg_deviation:.2f} ppt</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            accuracy_std_deviation = selected_trainee.get('accuracy_std_deviation', 0.0)
            st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-label'>Standard Deviation</div>
                <div class='metric-value'>{accuracy_std_deviation:.2f} ppt</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Accuracy performance history
        st.markdown("<p class='section-header'>Accuracy Performance History</p>", unsafe_allow_html=True)
        
        # Get accuracy performance history data
        accuracy_history_df = get_trainee_performance_history(selected_trainee_id, days=history_period, evaluation_type='accuracy')
        
        if not accuracy_history_df.empty:
            # Create a line chart showing accuracy performance over time
            fig3 = go.Figure()
            
            # Add deviation line
            fig3.add_trace(go.Scatter(
                x=accuracy_history_df['test_date'],
                y=accuracy_history_df['avg_deviation'],
                mode='lines+markers',
                name='Average Deviation (ppt)',
                line=dict(color='#D4AF37', width=2),
                marker=dict(size=8)
            ))
            
            # Add accuracy percentage line
            fig3.add_trace(go.Scatter(
                x=accuracy_history_df['test_date'],
                y=accuracy_history_df['daily_accuracy_percentage'],
                mode='lines+markers',
                name='Accuracy (%)',
                line=dict(color='#4682B4', width=2),
                marker=dict(size=8),
                yaxis='y2'
            ))
            
            # Update layout with dual y-axes
            fig3.update_layout(
                title='Accuracy Performance Metrics Over Time',
                xaxis=dict(title='Date'),
                yaxis=dict(
                    title=dict(text='Deviation (ppt)', font=dict(color='#D4AF37')),
                    tickfont=dict(color='#D4AF37')
                ),
                yaxis2=dict(
                    title=dict(text='Accuracy (%)', font=dict(color='#4682B4')),
                    tickfont=dict(color='#4682B4'),
                    anchor='x',
                    overlaying='y',
                    side='right'
                ),
                showlegend=True,
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                hovermode='x unified',
                template='plotly_dark'
            )
            
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info(f"No accuracy performance history available for the last {history_period} days.")
        
        # Recent accuracy evaluations
        st.markdown("<p class='section-header'>Recent Accuracy Evaluations</p>", unsafe_allow_html=True)
        
        # Get recent accuracy evaluations for this trainee
        recent_accuracy_evals = get_trainee_evaluations(trainee_id=selected_trainee_id, days=30)
        if not recent_accuracy_evals.empty:
            recent_accuracy_evals = recent_accuracy_evals[recent_accuracy_evals['evaluation_type'] == 'accuracy']
        
        if not recent_accuracy_evals.empty:
            # Format the dataframe for display
            display_cols = [
                'reference_name', 'certified_gold_content', 'measured_gold_content', 
                'deviation_ppt', 'test_date'
            ]
            
            col_rename = {
                'reference_name': 'Reference',
                'certified_gold_content': 'Certified (ppt)',
                'measured_gold_content': 'Measured (ppt)',
                'deviation_ppt': 'Deviation (ppt)',
                'test_date': 'Date'
            }
            
            # Format the dataframe
            display_df = recent_accuracy_evals[display_cols].rename(columns=col_rename)
            
            styled_evals = display_df.style.applymap(
                highlight_deviation, subset=['Deviation (ppt)']
            ).format({
                'Certified (ppt)': '{:.1f}',
                'Measured (ppt)': '{:.1f}',
                'Deviation (ppt)': '{:.2f}'
            })
            
            st.dataframe(styled_evals, use_container_width=True)
            
            # Distribution of deviations
            st.markdown("<p class='section-header'>Distribution of Accuracy Deviations</p>", unsafe_allow_html=True)
            
            # Create a histogram of deviations
            fig4 = px.histogram(
                recent_accuracy_evals,
                x='deviation_ppt',
                nbins=20,
                title='Distribution of Accuracy Deviations',
                labels={'deviation_ppt': 'Deviation (ppt)'},
                color_discrete_sequence=['rgba(212, 175, 55, 0.7)']
            )
            
            # Add vertical lines for tolerance bounds
            tolerance = selected_trainee['target_tolerance']
            fig4.add_vline(x=tolerance, line_dash="dash", line_color="green")
            fig4.add_vline(x=-tolerance, line_dash="dash", line_color="green")
            
            fig4.update_layout(
                template='plotly_dark',
                xaxis=dict(title='Deviation (ppt)'),
                yaxis=dict(title='Count')
            )
            
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No recent accuracy evaluations in the last 30 days.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Tab 3: Consistency Analysis
    with tab3:
        st.markdown("<div class='data-container'>", unsafe_allow_html=True)
        st.markdown("<p class='section-header'>Consistency Performance Metrics</p>", unsafe_allow_html=True)
        
        # Key metrics for consistency
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            consistency_samples = selected_trainee.get('consistency_samples', 0)
            st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-label'>Consistency Samples</div>
                <div class='metric-value'>{int(consistency_samples)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            consistency_within_tolerance = selected_trainee.get('consistency_within_tolerance', 0.0)
            st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-label'>Consistency Percentage</div>
                <div class='metric-value'>{consistency_within_tolerance:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            consistency_avg_deviation = selected_trainee.get('consistency_avg_deviation', 0.0)
            st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-label'>Average Deviation</div>
                <div class='metric-value'>{consistency_avg_deviation:.2f} ppt</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            consistency_std_deviation = selected_trainee.get('consistency_std_deviation', 0.0)
            st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-label'>Standard Deviation</div>
                <div class='metric-value'>{consistency_std_deviation:.2f} ppt</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Consistency performance history
        st.markdown("<p class='section-header'>Consistency Performance History</p>", unsafe_allow_html=True)
        
        # Get consistency performance history data
        consistency_history_df = get_trainee_performance_history(selected_trainee_id, days=history_period, evaluation_type='consistency')
        
        if not consistency_history_df.empty:
            # Create a line chart showing consistency performance over time
            fig5 = go.Figure()
            
            # Add deviation line
            fig5.add_trace(go.Scatter(
                x=consistency_history_df['test_date'],
                y=consistency_history_df['avg_deviation'],
                mode='lines+markers',
                name='Average Deviation (ppt)',
                line=dict(color='#D4AF37', width=2),
                marker=dict(size=8)
            ))
            
            # Add standard deviation line
            fig5.add_trace(go.Scatter(
                x=consistency_history_df['test_date'],
                y=consistency_history_df['std_deviation'],
                mode='lines+markers',
                name='Standard Deviation (ppt)',
                line=dict(color='#FF7F50', width=2),
                marker=dict(size=8)
            ))
            
            # Add accuracy percentage line
            fig5.add_trace(go.Scatter(
                x=consistency_history_df['test_date'],
                y=consistency_history_df['daily_accuracy_percentage'],
                mode='lines+markers',
                name='Within Tolerance (%)',
                line=dict(color='#4682B4', width=2),
                marker=dict(size=8),
                yaxis='y2'
            ))
            
            # Update layout with dual y-axes
            fig5.update_layout(
                title='Consistency Performance Metrics Over Time',
                xaxis=dict(title='Date'),
                yaxis=dict(
                    title=dict(text='Deviation (ppt)', font=dict(color='#D4AF37')),
                    tickfont=dict(color='#D4AF37')
                ),
                yaxis2=dict(
                    title=dict(text='Within Tolerance (%)', font=dict(color='#4682B4')),
                    tickfont=dict(color='#4682B4'),
                    anchor='x',
                    overlaying='y',
                    side='right'
                ),
                showlegend=True,
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                hovermode='x unified',
                template='plotly_dark'
            )
            
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info(f"No consistency performance history available for the last {history_period} days.")
        
        # Recent consistency evaluations
        st.markdown("<p class='section-header'>Recent Consistency Evaluations</p>", unsafe_allow_html=True)
        
        # Get recent consistency evaluations for this trainee
        recent_consistency_evals = get_trainee_evaluations(trainee_id=selected_trainee_id, days=30)
        if not recent_consistency_evals.empty:
            recent_consistency_evals = recent_consistency_evals[recent_consistency_evals['evaluation_type'] == 'consistency']
        
        if not recent_consistency_evals.empty:
            # Format the dataframe for display
            display_cols = [
                'reference_name', 'certified_gold_content', 'measured_gold_content', 
                'deviation_ppt', 'test_date'
            ]
            
            col_rename = {
                'reference_name': 'Reference',
                'certified_gold_content': 'Certified (ppt)',
                'measured_gold_content': 'Measured (ppt)',
                'deviation_ppt': 'Deviation (ppt)',
                'test_date': 'Date'
            }
            
            # Format the dataframe
            display_df = recent_consistency_evals[display_cols].rename(columns=col_rename)
            
            styled_evals = display_df.style.applymap(
                highlight_deviation, subset=['Deviation (ppt)']
            ).format({
                'Certified (ppt)': '{:.1f}',
                'Measured (ppt)': '{:.1f}',
                'Deviation (ppt)': '{:.2f}'
            })
            
            st.dataframe(styled_evals, use_container_width=True)
            
            # Reference material specific analysis
            st.markdown("<p class='section-header'>Consistency by Reference Material</p>", unsafe_allow_html=True)
            
            # Group by reference material and calculate stats
            ref_stats = recent_consistency_evals.groupby('reference_name').agg(
                count=('evaluation_id', 'count'),
                avg_deviation=('deviation_ppt', 'mean'),
                std_deviation=('deviation_ppt', 'std'),
                within_tolerance=('is_within_tolerance', 'sum')
            ).reset_index()
            
            # Calculate percentage within tolerance
            ref_stats['percent_within_tolerance'] = (ref_stats['within_tolerance'] / ref_stats['count']) * 100
            
            # Fill NaN values in std_deviation
            ref_stats['std_deviation'] = ref_stats['std_deviation'].fillna(0.0)
            
            # Create a bar chart for reference material consistency
            fig6 = px.bar(
                ref_stats,
                x='reference_name',
                y='std_deviation',
                color='percent_within_tolerance',
                color_continuous_scale='YlOrRd_r',
                title='Consistency by Reference Material',
                labels={
                    'reference_name': 'Reference Material',
                    'std_deviation': 'Standard Deviation (ppt)',
                    'percent_within_tolerance': 'Within Tolerance (%)'
                },
                hover_data=['count', 'avg_deviation', 'percent_within_tolerance']
            )
            
            fig6.update_layout(
                template='plotly_dark',
                xaxis=dict(title='Reference Material'),
                yaxis=dict(title='Standard Deviation (ppt)'),
                coloraxis_colorbar=dict(title='Within Tolerance (%)')
            )
            
            st.plotly_chart(fig6, use_container_width=True)
        else:
            st.info("No recent consistency evaluations in the last 30 days.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
else:
    st.warning("No trainees registered in the system. Please register trainees first in the Data Entry page.")

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