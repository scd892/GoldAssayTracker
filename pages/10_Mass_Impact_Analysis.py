import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Import database functions
from database import get_weighted_mass_impact
from auth import require_permission, display_access_denied, check_page_access

# Set page config
st.set_page_config(page_title="AEG Mass & Financial Impact Analysis", page_icon="⚖️", layout="wide")

# Check authentication and permissions
if not check_page_access("Mass_Impact_Analysis"):
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
.explanation-text {
    background-color: #F0F9FF;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
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
.positive-metric {
    font-size: 1.8rem;
    font-weight: bold;
    color: #047857;
}
.negative-metric {
    font-size: 1.8rem;
    font-weight: bold;
    color: #B91C1C;
}
.neutral-metric {
    font-size: 1.8rem;
    font-weight: bold;
    color: #4B5563;
}
.positive-card {
    background-color: #ECFDF5;
    padding: 1.5rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    border-left: 4px solid #047857;
}
.negative-card {
    background-color: #FEF2F2;
    padding: 1.5rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    border-left: 4px solid #B91C1C;
}
.neutral-card {
    background-color: #F3F4F6;
    padding: 1.5rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    border-left: 4px solid #4B5563;
}
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("<h1 class='main-header'>Mass & Financial Impact Analysis</h1>", unsafe_allow_html=True)

# Sidebar for options
with st.sidebar:
    st.markdown("<h3 class='sidebar-title'>Analysis Options</h3>", unsafe_allow_html=True)
    
    # Time period selection
    period_options = [
        "Today",
        "Yesterday",
        "Last 7 days",
        "Last 30 days",
        "Last 365 days",
        "Custom period"
    ]
    
    selected_period = st.radio("Time Period", period_options, index=3)
    
    # Calculate days based on selection
    today = datetime.now().date()
    
    if selected_period == "Today":
        # Just today
        days = 1
        start_date = today
        end_date = today
    elif selected_period == "Yesterday":
        # Just yesterday
        days = 2  # Need to include today as well due to SQLite date logic
        start_date = today - timedelta(days=1)
        end_date = today - timedelta(days=1)
    elif selected_period == "Last 7 days":
        days = 7
        start_date = today - timedelta(days=6)
        end_date = today
    elif selected_period == "Last 30 days":
        days = 30
        start_date = today - timedelta(days=29)
        end_date = today
    elif selected_period == "Last 365 days":
        days = 365
        start_date = today - timedelta(days=364)
        end_date = today
    elif selected_period == "Custom period":
        # Allow custom date selection
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start date", value=today - timedelta(days=30))
        with col2:
            end_date = st.date_input("End date", value=today)
        
        # Calculate days between dates
        if start_date <= end_date:
            # Calculate days to cover the range from start_date to today
            days = (today - start_date).days + 1  # +1 to include today
        else:
            st.error("Start date must be before end date")
            days = 30  # Default fallback
    
    # Display selected date range
    st.info(f"Analyzing data from {start_date} to {end_date} ({days} day{'s' if days != 1 else ''})")
    
    # Important note about how the database query works for custom period with past end date
    if selected_period == "Custom period" and end_date < today:
        st.info("Note: Using specific date range filtering to ensure only data between the selected dates is included.")
    
    # Set min_gold_content to 0 (removing the slider as requested)
    min_gold_content = 0
    
    # Gold price input for financial impact calculations
    st.markdown("<h3 class='sidebar-title'>Financial Impact Options</h3>", unsafe_allow_html=True)
    gold_price_per_gram = st.number_input(
        "24K Gold Price (USD per gram)",
        min_value=0.0,
        max_value=1000.0,
        value=85.0,  # Current approximate value as of May 2025
        step=0.01,
        format="%.2f",
        help="Enter the current price of 24K gold in USD per gram for financial impact calculations"
    )

# Main content
st.markdown("<h2 class='sub-header'>Net Mass & Financial Impact of Deviations</h2>", unsafe_allow_html=True)
st.markdown("""
<div class='explanation-text'>
<p>This page analyzes both the <strong>physical mass impact</strong> and <strong>financial impact</strong> of gold testing deviations, weighted by bar mass.</p>

<p><strong>Why This Matters:</strong> Even when the average deviation in parts per thousand (ppt) is zero, the weight of each bar influences the net physical result:</p>
<ul>
<li>A -0.2 ppt deviation on a 5kg bar = -0.001kg gold loss</li>
<li>A +0.2 ppt deviation on a 10kg bar = +0.002kg gold gain</li>
</ul>

<p>In this example, the <strong>net result</strong> is a +0.001kg gain in physical gold mass, even though the average deviation in ppt is zero.</p>

<p><strong>Financial Impact:</strong> The fine gold gain/loss is calculated as (purity/1000 × bar weight) and then multiplied by the current gold price per gram to determine the financial impact.</p>
</div>
""", unsafe_allow_html=True)

try:
    # Get weighted mass impact data with proper date filtering
    if selected_period == "Today":
        # Special case for today - use specific date range for just today
        impact_data = get_weighted_mass_impact(
            days=None,
            min_gold_content=min_gold_content,
            start_date=today.strftime('%Y-%m-%d'),
            end_date=today.strftime('%Y-%m-%d')
        )
    elif selected_period == "Custom period":
        # Use specific date range for custom period
        impact_data = get_weighted_mass_impact(
            days=None, 
            min_gold_content=min_gold_content,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
    elif selected_period == "Yesterday":
        # Special case for yesterday - use specific date range
        yesterday = today - timedelta(days=1)
        impact_data = get_weighted_mass_impact(
            days=None,
            min_gold_content=min_gold_content,
            start_date=yesterday.strftime('%Y-%m-%d'),
            end_date=yesterday.strftime('%Y-%m-%d')
        )
    else:
        # For other options, use days parameter
        impact_data = get_weighted_mass_impact(
            days=days, 
            min_gold_content=min_gold_content
        )
    
    if impact_data is None:
        st.warning("⚠️ No benchmark assayer is set. Please set a benchmark assayer in the settings before analyzing mass impact.")
    elif impact_data.empty:
        if selected_period == "Today":
            st.warning(f"⚠️ No data available for today ({today}). Please select a different time period or ensure that gold sample weights are recorded for today's samples.")
        elif selected_period == "Yesterday":
            yesterday = today - timedelta(days=1)
            st.warning(f"⚠️ No data available for yesterday ({yesterday}). Please select a different time period or ensure that gold sample weights are recorded for yesterday's samples.")
        elif selected_period == "Custom period":
            st.warning(f"⚠️ No data available between {start_date} and {end_date}. Please select a different time period or ensure that gold sample weights are recorded for samples in this date range.")
        else:
            st.warning(f"⚠️ No data available for the selected period ({selected_period}). Please select a different time period or ensure that gold sample weights are recorded for samples in this date range.")
    else:
        # Calculate totals for summary
        total_samples = impact_data['sample_count'].sum()
        total_bar_mass = impact_data['total_bar_mass_kg'].sum()
        
        # Calculate total mass deviations (gains and losses)
        total_mass_deviation = impact_data['total_mass_deviation_g'].sum()
        total_positive_deviation = impact_data['total_positive_deviation_g'].sum()
        total_negative_deviation = impact_data['total_negative_deviation_g'].sum()
        
        # Calculate financial impact
        financial_impact = total_mass_deviation * gold_price_per_gram
        financial_gain = total_positive_deviation * gold_price_per_gram
        financial_loss = total_negative_deviation * gold_price_per_gram
        absolute_financial_impact = impact_data['total_abs_mass_deviation_g'].sum() * gold_price_per_gram
        
        # Display summary cards
        st.markdown("<div class='card-container'>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Samples", f"{total_samples:,}")
        
        with col2:
            st.metric("Total Bar Mass", f"{total_bar_mass:,.2f} kg")
        
        with col3:
            # Standard arrows - positive deviation = red down arrow with minus sign
            if total_mass_deviation > 0:
                # Positive deviation = red down arrow with minus sign (negative effect)
                # Sign is negative for giving away gold (down arrow)
                st.metric("Net Mass Effect", f"-{total_mass_deviation:.2f} g", delta=f"-{total_mass_deviation:.2f}g")
            elif total_mass_deviation < 0:
                # Negative deviation = green up arrow with plus sign (positive effect)
                # Sign is positive for gaining gold (up arrow)
                st.metric("Net Mass Effect", f"+{abs(total_mass_deviation):.2f} g", delta=f"+{abs(total_mass_deviation):.2f}g")
            else:
                st.metric("Net Mass Effect", f"{total_mass_deviation:.2f} g", delta="0.00g")
        
        with col4:
            # Financial impact metric with standard arrows
            if financial_impact > 0:
                # Positive financial impact = red down arrow with minus sign (negative effect)
                # Sign is negative for giving away gold (down arrow)
                st.metric("Financial Impact", f"-${financial_impact:.2f}", delta=f"-${financial_impact:.2f}")
            elif financial_impact < 0:
                # Negative financial impact = green up arrow with plus sign (positive effect)
                # Sign is positive for gaining gold (up arrow)
                st.metric("Financial Impact", f"+${abs(financial_impact):.2f}", delta=f"+${abs(financial_impact):.2f}")
            else:
                st.metric("Financial Impact", f"${financial_impact:.2f}", delta="$0.00")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Financial impact summary
        card_class = "negative-card" if total_mass_deviation > 0 else "positive-card" if total_mass_deviation < 0 else "neutral-card"
        metric_class = "negative-metric" if total_mass_deviation > 0 else "positive-metric" if total_mass_deviation < 0 else "neutral-metric"
        
        st.markdown(f"<div class='{card_class}'>", unsafe_allow_html=True)
        
        # Calculate signs for display - positive value means gaining gold (up arrow)
        # negative value means giving away gold (down arrow)
        mass_sign = "+" if total_mass_deviation < 0 else "-" if total_mass_deviation > 0 else ""
        
        # Calculate additional aggregate metrics
        total_absolute_deviation = impact_data['total_abs_mass_deviation_g'].sum()
        
        # Calculate fine gold values (purity/1000 * bar weight)
        # In this case we use the deviation in grams directly
        fine_gold_deviation = total_mass_deviation  # The deviations are already in fine gold
        
        # Calculate financial signs
        financial_sign = "+" if financial_impact < 0 else "-" if financial_impact > 0 else ""
        
        st.markdown(f"""
        <p>Based on the analysis of <strong>{total_samples:,}</strong> samples with a total mass of <strong>{total_bar_mass:,.2f} kg</strong>:</p>
        <p>The net mass effect is <span class='{metric_class}'>{mass_sign}{abs(total_mass_deviation):.2f} grams</span> of gold</p>
        
        <p>Detailed Mass Breakdown:</p>
        <ul>
            <li>Mass Loss: <strong>-{total_positive_deviation:.2f} g</strong></li>
            <li>Mass Gain: <strong>+{total_negative_deviation:.2f} g</strong></li>
        </ul>
        
        <p>Financial Impact (at ${gold_price_per_gram:.2f}/g):</p>
        <ul>
            <li>Net Financial Impact: <span class='{metric_class}'>{financial_sign}${abs(financial_impact):.2f} USD</span></li>
            <li>Financial Loss: <strong>-${financial_gain:.2f} USD</strong></li>
            <li>Financial Gain: <strong>+${financial_loss:.2f} USD</strong></li>
        </ul>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Add a section for fine gold calculation with cards
        st.markdown("<h3 class='sub-header'>Fine Gold Impact</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class='explanation-text'>
            <h4>About Fine Gold Calculation</h4>
            <p>Fine gold is calculated by multiplying the gold purity (in ppt/1000) by the bar weight.</p>
            <p>This effectively converts the total mass to pure gold content.</p>
            <p>Example: A 1kg bar at 995.0 ppt contains 995g of fine gold.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Display financial metrics card
            fin_card_class = "negative-card" if financial_impact > 0 else "positive-card" if financial_impact < 0 else "neutral-card"
            
            st.markdown(f"""
            <div class='{fin_card_class}' style="height: 100%;">
            <h4>Financial Impact Summary</h4>
            <p>Gold Price: <strong>${gold_price_per_gram:.2f}/g</strong></p>
            <p>Net Value Impact: <strong>{financial_sign}${abs(financial_impact):.2f}</strong></p>
            <p>This represents the monetary value of the total fine gold gain/loss.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Display the raw data
        st.markdown("<h3 class='sub-header'>Assayer Impact Details</h3>", unsafe_allow_html=True)
        
        # Format the data for display
        display_data = impact_data.copy()
        
        # Add financial impact columns
        display_data['financial_impact'] = display_data['total_mass_deviation_g'] * gold_price_per_gram
        display_data['financial_gain'] = display_data['total_positive_deviation_g'] * gold_price_per_gram
        display_data['financial_loss'] = display_data['total_negative_deviation_g'] * gold_price_per_gram
        
        # Add + sign to positive deviations for clarity
        display_data['total_mass_deviation_g'] = display_data['total_mass_deviation_g'].apply(
            lambda x: f"+{x:.2f}" if x > 0 else f"{x:.2f}"
        )
        
        # Add + sign to positive deviations and - sign to negative deviations for clarity
        display_data['total_positive_deviation_g'] = display_data['total_positive_deviation_g'].apply(
            lambda x: f"+{x:.2f}" if x > 0 else f"{x:.2f}"
        )
        display_data['total_negative_deviation_g'] = display_data['total_negative_deviation_g'].apply(
            lambda x: f"-{x:.2f}" if x > 0 else f"{x:.2f}"
        )
        
        # Format financial impact columns with dollar signs
        display_data['financial_impact'] = display_data['financial_impact'].apply(
            lambda x: f"+${x:.2f}" if x > 0 else f"-${abs(x):.2f}" if x < 0 else f"${x:.2f}"
        )
        display_data['financial_gain'] = display_data['financial_gain'].apply(
            lambda x: f"+${x:.2f}" if x > 0 else f"${x:.2f}"
        )
        display_data['financial_loss'] = display_data['financial_loss'].apply(
            lambda x: f"-${x:.2f}" if x > 0 else f"${x:.2f}"
        )
        
        # Format additional columns for display
        for col in ['total_abs_mass_deviation_g']:
            if col in display_data.columns:
                display_data[col] = display_data[col].apply(lambda x: f"{x:.2f}")
        
        # Create readable column names
        column_names = {
            'assayer_name': 'Assayer',
            'sample_count': 'Samples',
            'avg_deviation_ppt': 'Avg Deviation (ppt)',
            'std_deviation_ppt': 'Std Dev (ppt)',
            'total_bar_mass_kg': 'Total Mass (kg)',
            'avg_bar_mass_g': 'Avg Bar Size (g)',
            'total_mass_deviation_g': 'Net Mass Effect (g)',
            'total_positive_deviation_g': 'Mass Loss (g)',
            'total_negative_deviation_g': 'Mass Gain (g)',
            'avg_mass_deviation_g': 'Avg Mass Effect (g)',
            'total_abs_mass_deviation_g': 'Total Absolute Dev (g)',
            'financial_impact': 'Financial Impact (USD)',
            'financial_gain': 'Financial Loss (USD)',
            'financial_loss': 'Financial Gain (USD)',
            'deviation_direction': 'Direction'
        }
        
        # Reorder and select columns for better readability with mass-focused metrics
        display_cols = [
            'assayer_name', 'sample_count', 'avg_deviation_ppt', 'std_deviation_ppt',
            'total_bar_mass_kg', 'avg_bar_mass_g', 'total_mass_deviation_g', 
            'total_positive_deviation_g', 'total_negative_deviation_g', 
            'financial_impact', 'financial_gain', 'financial_loss', 'deviation_direction'
        ]
        
        # Display the table with proper column names
        st.dataframe(
            display_data[display_cols].rename(columns=column_names),
            use_container_width=True
        )
        
        # Create visualizations
        st.markdown("<h3 class='sub-header'>Visualizations</h3>", unsafe_allow_html=True)
        
        viz_col1, viz_col2 = st.columns(2)
        
        with viz_col1:
            try:
                # Sorted bar chart for net mass effect by assayer
                fig_bar = px.bar(
                    impact_data.sort_values('total_mass_deviation_g'),
                    x='assayer_name',
                    y='total_mass_deviation_g',
                    title="Net Mass Effect by Assayer (grams)",
                    labels={
                        'assayer_name': 'Assayer',
                        'total_mass_deviation_g': 'Net Mass Effect (g)'
                    },
                    color='deviation_direction',
                    color_discrete_map={
                        'Over': '#B91C1C',   # Red for positive deviations
                        'Under': '#047857',  # Green for negative deviations
                        'Neutral': '#4B5563' # Gray for neutral
                    }
                )
                
                fig_bar.update_layout(
                    height=400,
                    template='plotly_white',
                    xaxis_title='Assayer',
                    yaxis_title='Net Mass Effect (g)'
                )
                
                # Add a horizontal reference line at y=0
                fig_bar.add_shape(
                    type="line",
                    x0=-0.5,
                    x1=len(impact_data)-0.5,
                    y0=0,
                    y1=0,
                    line=dict(color="black", width=1, dash="dash")
                )
                
                st.plotly_chart(fig_bar, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating bar chart: {e}")
        
        with viz_col2:
            try:
                # Create a balance chart showing positive vs negative deviations
                fig_balance = go.Figure()
                
                # Sort by the absolute value of total mass deviation
                sorted_data = impact_data.sort_values(by='total_mass_deviation_g', key=abs, ascending=False)
                
                # Add positive deviations as red bars (representing mass loss when giving away gold)
                fig_balance.add_trace(go.Bar(
                    x=sorted_data['assayer_name'],
                    y=sorted_data['total_positive_deviation_g'],
                    name='Mass Loss (g)',
                    marker_color='#B91C1C'
                ))
                
                # Add negative deviations as green bars (representing mass gain when getting more gold)
                fig_balance.add_trace(go.Bar(
                    x=sorted_data['assayer_name'],
                    y=-sorted_data['total_negative_deviation_g'],
                    name='Mass Gain (g)',
                    marker_color='#047857'
                ))
                
                fig_balance.update_layout(
                    title="Balance of Mass Gain vs Loss by Assayer",
                    barmode='relative',
                    height=400,
                    template='plotly_white',
                    xaxis_title='Assayer',
                    yaxis_title='Mass Effect (g)',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5
                    )
                )
                
                # Add a horizontal reference line at y=0
                fig_balance.add_shape(
                    type="line",
                    x0=-0.5,
                    x1=len(impact_data)-0.5,
                    y0=0,
                    y1=0,
                    line=dict(color="black", width=1, dash="dash")
                )
                
                st.plotly_chart(fig_balance, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating balance chart: {e}")
        
        # Add financial impact visualization
        st.markdown("<h3 class='sub-header'>Financial Impact Visualization</h3>", unsafe_allow_html=True)
        
        try:
            # Add financial data to impact_data
            financial_data = impact_data.copy()
            financial_data['financial_impact'] = financial_data['total_mass_deviation_g'] * gold_price_per_gram
            
            # Invert the sign for hover display - match our sign convention
            # Positive deviation (red bars) should show negative value
            # Negative deviation (green bars) should show positive value
            financial_data['financial_impact_display'] = -financial_data['financial_impact']
            financial_data['financial_impact_abs'] = financial_data['financial_impact'].abs()
            
            # Sort by financial impact
            sorted_financial = financial_data.sort_values('financial_impact')
            
            # Create financial impact chart
            fig_financial = px.bar(
                sorted_financial,
                x='assayer_name',
                y='financial_impact',
                title=f"Financial Impact by Assayer (USD at ${gold_price_per_gram:.2f}/g)",
                labels={
                    'assayer_name': 'Assayer',
                    'financial_impact': 'Financial Impact (USD)'
                },
                color='deviation_direction',
                color_discrete_map={
                    'Over': '#B91C1C',   # Red for positive impact
                    'Under': '#047857',  # Green for negative impact
                    'Neutral': '#4B5563' # Gray for neutral
                },
                custom_data=['financial_impact_display']  # Use our display value for hover
            )
            
            # Update hover template to show the correct sign
            fig_financial.update_traces(
                hovertemplate='<b>%{x}</b><br>Financial Impact: $%{customdata[0]:.2f}<extra></extra>'
            )
            
            # Format the y-axis to show dollar signs
            fig_financial.update_layout(
                height=400,
                template='plotly_white',
                xaxis_title='Assayer',
                yaxis_title='Financial Impact (USD)',
                yaxis=dict(
                    tickprefix="$",
                    tickformat=",.2f"
                )
            )
            
            # Add a horizontal reference line at y=0
            fig_financial.add_shape(
                type="line",
                x0=-0.5,
                x1=len(financial_data)-0.5,
                y0=0,
                y1=0,
                line=dict(color="black", width=1, dash="dash")
            )
            
            st.plotly_chart(fig_financial, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating financial impact chart: {e}")
            
except Exception as e:
    st.warning(f"Unable to analyze mass impact data: {e}. Please ensure a benchmark assayer is set and that bar weights are recorded in the system.")