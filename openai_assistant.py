import json
import os
import pandas as pd
from typing import Dict, List

# The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# Do not change this unless explicitly requested by the user
from openai import OpenAI

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = None

# Only initialize if API key is available
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_with_openai(prompt, system_prompt="", max_tokens=800):
    """
    Use OpenAI to analyze data based on a prompt
    
    Args:
        prompt: The user prompt to send to OpenAI
        system_prompt: Optional system prompt for context
        max_tokens: Maximum number of tokens in the response
        
    Returns:
        str: OpenAI's response
    """
    try:
        if not OPENAI_API_KEY or not openai_client:
            raise ValueError("OpenAI API key not configured")
            
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.2
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error with OpenAI API: {str(e)}")
        raise e

def analyze_deviation_data(deviations_df, time_period="Last 30 days"):
    """
    Analyze deviations data and provide AI-generated insights
    
    Args:
        deviations_df: DataFrame containing deviation data
        time_period: Time period for context in the analysis
        
    Returns:
        str: AI-generated analysis of the data
    """
    try:
        if deviations_df.empty:
            return "No deviation data available for analysis."
            
        # Calculate summary statistics
        summary_stats = {
            "total_samples": len(deviations_df),
            "unique_samples": deviations_df['sample_id'].nunique(),
            "assayer_count": deviations_df['assayer_name'].nunique(),
            "date_range": f"{deviations_df['test_date'].min().strftime('%Y-%m-%d')} to {deviations_df['test_date'].max().strftime('%Y-%m-%d')}",
            "average_deviation": deviations_df['percentage_deviation'].mean(),
            "median_deviation": deviations_df['percentage_deviation'].median(),
            "std_deviation": deviations_df['percentage_deviation'].std(),
            "max_deviation": deviations_df['percentage_deviation'].max(),
            "min_deviation": deviations_df['percentage_deviation'].min()
        }
        
        # Get per-assayer statistics
        assayer_stats = deviations_df.groupby('assayer_name')['percentage_deviation'].agg(['mean', 'std', 'count']).reset_index()
        assayer_stats.columns = ['assayer_name', 'avg_deviation', 'std_deviation', 'sample_count']
        
        # Format the assayer statistics for the prompt
        assayer_data = ""
        for _, row in assayer_stats.iterrows():
            assayer_data += f"- {row['assayer_name']}: Average Deviation = {row['avg_deviation']:.4f}%, Standard Deviation = {row['std_deviation']:.4f}%, Samples = {row['sample_count']}\n"
        
        prompt = f"""
Analyze this gold assay deviation data covering {time_period}.

Summary Statistics:
- Total samples: {summary_stats['total_samples']}
- Unique sample IDs: {summary_stats['unique_samples']}
- Number of assayers: {summary_stats['assayer_count']}
- Date range: {summary_stats['date_range']}
- Average deviation: {summary_stats['average_deviation']:.4f}%
- Median deviation: {summary_stats['median_deviation']:.4f}%
- Standard deviation: {summary_stats['std_deviation']:.4f}%
- Maximum deviation: {summary_stats['max_deviation']:.4f}%
- Minimum deviation: {summary_stats['min_deviation']:.4f}%

Per-assayer statistics:
{assayer_data}

Task: Provide a brief, data-focused analysis of these deviations in gold assay testing. 
Focus on explaining what the data means, not recommendations. 
Analyze patterns, notable outliers, and how to interpret these figures.
Keep your explanation clear and concise (maximum 100 words).
"""

        system_prompt = """
You are a data analyst for a gold testing laboratory. 
Your task is to provide objective analysis of deviation data, explaining what the numbers represent.
Avoid making recommendations - only interpret what the data shows.
Use simple, direct language focusing on facts.
Highlight key insights that help lab managers understand testing accuracy.
"""

        # Call OpenAI API
        analysis = analyze_with_openai(prompt, system_prompt, max_tokens=300)
        return analysis
    
    except Exception as e:
        # Return a fallback statistical analysis
        return generate_statistical_analysis(deviations_df)

def analyze_heatmap(deviations_df, time_period="Last 30 days"):
    """
    Analyze the deviation heatmap and provide insights
    
    Args:
        deviations_df: DataFrame containing deviation data
        time_period: Time period for context in the analysis
        
    Returns:
        str: AI-generated analysis of the heatmap
    """
    try:
        if deviations_df.empty:
            return "No data available for heatmap analysis."
            
        # Create a summary of what the heatmap is showing
        pivot_ready = deviations_df.copy()
        pivot_ready['test_date'] = pd.to_datetime(pivot_ready['test_date']).dt.date
        
        # Group by assayer and date, calculating mean deviation
        heatmap_data = pivot_ready.groupby(['assayer_name', 'test_date'])['percentage_deviation'].mean().reset_index()
        
        # Calculate overall statistics for different time periods
        overall_avg = heatmap_data['percentage_deviation'].mean()
        overall_max = heatmap_data['percentage_deviation'].max()
        overall_min = heatmap_data['percentage_deviation'].min()
        
        # Identify assayers with highest and lowest average deviations
        assayer_avg = heatmap_data.groupby('assayer_name')['percentage_deviation'].mean()
        highest_assayer = assayer_avg.idxmax()
        highest_avg = assayer_avg.max()
        lowest_assayer = assayer_avg.idxmin()
        lowest_avg = assayer_avg.min()
        
        # Find dates with highest deviation
        date_avg = heatmap_data.groupby('test_date')['percentage_deviation'].mean()
        if not date_avg.empty:
            highest_date = date_avg.idxmax()
            highest_date_avg = date_avg.max()
        else:
            highest_date = "No data"
            highest_date_avg = 0
            
        # Create prompt for OpenAI
        prompt = f"""
Analyze this gold assay deviation heatmap data covering {time_period}.

The heatmap shows percentage deviations from benchmark assayer across different dates and assayers.

Key statistics:
- Overall average deviation: {overall_avg:.4f}%
- Maximum deviation: {overall_max:.4f}%
- Minimum deviation: {overall_min:.4f}%
- Assayer with highest average deviation: {highest_assayer} ({highest_avg:.4f}%)
- Assayer with lowest average deviation: {lowest_assayer} ({lowest_avg:.4f}%)
- Date with highest average deviation: {highest_date} ({highest_date_avg:.4f}%)

Number of assayers: {len(deviations_df['assayer_name'].unique())}
Date range: {deviations_df['test_date'].min().strftime('%Y-%m-%d')} to {deviations_df['test_date'].max().strftime('%Y-%m-%d')}

Task: Provide a brief, data-focused analysis of what the heatmap visualization shows. 
Explain what the colors represent and how to interpret the patterns. 
Focus only on explaining what the data means, not recommendations.
Keep your explanation clear and concise (maximum 100 words).
"""

        system_prompt = """
You are a data visualization expert for a gold testing laboratory. 
Your task is to provide objective analysis of heatmap data, explaining what the visualization shows.
Avoid making recommendations - only interpret what the data shows.
Use simple, direct language focusing on facts.
Explain what the colors and patterns in a heatmap mean in this context.
"""

        # Call OpenAI API
        analysis = analyze_with_openai(prompt, system_prompt, max_tokens=300)
        return analysis
    
    except Exception as e:
        # Return a fallback analysis
        return generate_heatmap_analysis(deviations_df)

def analyze_trend_chart(deviations_df, ma_window=7, time_period="Last 90 days"):
    """
    Analyze the moving average trend chart and provide insights
    
    Args:
        deviations_df: DataFrame containing deviation data
        ma_window: Size of the moving average window
        time_period: Time period for context in the analysis
        
    Returns:
        str: AI-generated analysis of the trend chart
    """
    try:
        if deviations_df.empty:
            return "No data available for trend analysis."
            
        # Create a summary of the trend data
        trend_data = deviations_df.copy()
        trend_data['test_date'] = pd.to_datetime(trend_data['test_date'])
        
        # Sort by date for proper trend analysis
        trend_data = trend_data.sort_values('test_date')
        
        # Calculate overall trend statistics
        start_date = trend_data['test_date'].min().strftime('%Y-%m-%d')
        end_date = trend_data['test_date'].max().strftime('%Y-%m-%d')
        
        # Calculate moving average for overall data
        overall_daily = trend_data.groupby(trend_data['test_date'].dt.date)['percentage_deviation'].mean()
        
        # Check if we have enough data for moving average
        if len(overall_daily) >= ma_window:
            overall_ma = overall_daily.rolling(window=ma_window).mean()
            
            # Calculate trend direction
            first_valid_ma = overall_ma.dropna().iloc[0] if not overall_ma.dropna().empty else 0
            last_ma = overall_ma.iloc[-1] if not overall_ma.empty else 0
            trend_direction = "improving" if last_ma < first_valid_ma else "worsening" if last_ma > first_valid_ma else "stable"
            trend_change = abs(last_ma - first_valid_ma)
            
            # Calculate volatility
            volatility = overall_daily.std()
            
            # Detect any pattern changes
            ma_diff = overall_ma.diff()
            sign_changes = ((ma_diff > 0) != (ma_diff.shift(1) > 0)).sum()
            has_pattern_changes = sign_changes > 2
            
            prompt = f"""
Analyze this gold assay moving average trend chart data covering {time_period}.

The chart shows a {ma_window}-day moving average of percentage deviations from the benchmark assayer.

Trend statistics:
- Date range: {start_date} to {end_date}
- Overall trend direction: {trend_direction}
- Change magnitude: {trend_change:.4f}%
- Volatility (standard deviation): {volatility:.4f}%
- Number of trend direction changes: {sign_changes}
- Pattern stability: {"Multiple changes detected" if has_pattern_changes else "Relatively stable"}

Task: Provide a brief, data-focused analysis of what the moving average trend chart shows. 
Explain what the line represents and how to interpret its movement over time.
Focus only on explaining what the data means, not recommendations.
Keep your explanation clear and concise (maximum 100 words).
"""
        else:
            prompt = f"""
Analyze this gold assay data covering {time_period}.

Not enough data points ({len(overall_daily)}) for a {ma_window}-day moving average trend chart.
Date range: {start_date} to {end_date}

Task: Provide a brief, data-focused explanation about what a moving average trend chart would show
if there were sufficient data, and how it would be useful for monitoring gold assay deviations.
Focus only on explaining what the data would mean, not recommendations.
Keep your explanation clear and concise (maximum 100 words).
"""

        system_prompt = """
You are a time-series data analyst for a gold testing laboratory. 
Your task is to provide objective analysis of trend chart data, explaining what the visualization shows.
Avoid making recommendations - only interpret what the data shows.
Use simple, direct language focusing on facts.
Explain what the movement in a trend line means in this context.
"""

        # Call OpenAI API
        analysis = analyze_with_openai(prompt, system_prompt, max_tokens=300)
        return analysis
    
    except Exception as e:
        # Return a fallback analysis
        return generate_trend_analysis(deviations_df, ma_window)

def analyze_distribution_chart(deviations_df, time_period="Last 90 days"):
    """
    Analyze the deviation distribution chart and provide insights
    
    Args:
        deviations_df: DataFrame containing deviation data
        time_period: Time period for context in the analysis
        
    Returns:
        str: AI-generated analysis of the distribution chart
    """
    try:
        if deviations_df.empty:
            return "No data available for distribution analysis."
            
        # Create a summary of the distribution data
        distribution_data = deviations_df.copy()
        
        # Calculate overall statistics
        overall_mean = distribution_data['percentage_deviation'].mean()
        overall_median = distribution_data['percentage_deviation'].median()
        overall_std = distribution_data['percentage_deviation'].std()
        overall_min = distribution_data['percentage_deviation'].min()
        overall_max = distribution_data['percentage_deviation'].max()
        
        # Calculate per-assayer statistics
        assayer_stats = distribution_data.groupby('assayer_name')['percentage_deviation'].agg(['mean', 'median', 'std', 'min', 'max']).reset_index()
        
        # Find assayers with highest and lowest standard deviations
        if not assayer_stats.empty:
            most_consistent_idx = assayer_stats['std'].idxmin()
            most_consistent = assayer_stats.iloc[most_consistent_idx]
            
            least_consistent_idx = assayer_stats['std'].idxmax()
            least_consistent = assayer_stats.iloc[least_consistent_idx]
            
            # Get number of assayers with high/low standard deviations
            high_std_count = (assayer_stats['std'] > overall_std).sum()
            low_std_count = (assayer_stats['std'] <= overall_std).sum()
            
            # Create assayer details for the prompt
            assayer_details = f"""
Most consistent assayer: {most_consistent['assayer_name']}
- Mean: {most_consistent['mean']:.4f}%
- Median: {most_consistent['median']:.4f}%
- Standard Deviation: {most_consistent['std']:.4f}%
- Range: {most_consistent['min']:.4f}% to {most_consistent['max']:.4f}%

Least consistent assayer: {least_consistent['assayer_name']}
- Mean: {least_consistent['mean']:.4f}%
- Median: {least_consistent['median']:.4f}%
- Standard Deviation: {least_consistent['std']:.4f}%
- Range: {least_consistent['min']:.4f}% to {least_consistent['max']:.4f}%

- Number of assayers with above-average spread: {high_std_count}
- Number of assayers with below-average spread: {low_std_count}
"""
        else:
            assayer_details = "Insufficient data for per-assayer statistics."
            
        prompt = f"""
Analyze this gold assay deviation distribution chart data covering {time_period}.

The chart shows the distribution of deviations from the benchmark assayer.

Overall statistics:
- Mean deviation: {overall_mean:.4f}%
- Median deviation: {overall_median:.4f}%
- Standard deviation: {overall_std:.4f}%
- Range: {overall_min:.4f}% to {overall_max:.4f}%

Assayer-specific insights:
{assayer_details}

Task: Provide a brief, data-focused analysis of what the distribution chart shows.
Explain what the box plots represent and how to interpret the spread and central tendencies.
Focus only on explaining what the data means, not recommendations.
Keep your explanation clear and concise (maximum 100 words).
"""

        system_prompt = """
You are a statistical analyst for a gold testing laboratory. 
Your task is to provide objective analysis of distribution data, explaining what the visualization shows.
Avoid making recommendations - only interpret what the data shows.
Use simple, direct language focusing on facts.
Explain what box plots tell us about data distributions in this context.
"""

        # Call OpenAI API
        analysis = analyze_with_openai(prompt, system_prompt, max_tokens=300)
        return analysis
    
    except Exception as e:
        # Return a fallback analysis
        return generate_distribution_analysis(deviations_df)

def generate_performance_recommendations(deviations_df, time_period="Last 90 days"):
    """
    Generate specific recommendations for improving assayer performance
    
    Args:
        deviations_df: DataFrame containing deviation data
        time_period: Time period for context in the analysis
        
    Returns:
        str: AI-generated recommendations
    """
    try:
        if deviations_df.empty:
            return "No data available for performance analysis."
            
        # Calculate per-assayer statistics
        assayer_stats = deviations_df.groupby('assayer_name')['percentage_deviation'].agg(['mean', 'std', 'count', 'min', 'max']).reset_index()
        
        # Calculate overall statistics
        overall_stats = {
            'mean': deviations_df['percentage_deviation'].mean(),
            'std': deviations_df['percentage_deviation'].std(),
            'count': len(deviations_df),
            'min': deviations_df['percentage_deviation'].min(),
            'max': deviations_df['percentage_deviation'].max(),
        }
        
        # Identify assayers with various performance characteristics
        if not assayer_stats.empty:
            high_bias = assayer_stats[assayer_stats['mean'].abs() > overall_stats['mean'] * 1.5]
            high_variance = assayer_stats[assayer_stats['std'] > overall_stats['std'] * 1.5]
            low_sample_count = assayer_stats[assayer_stats['count'] < assayer_stats['count'].median() / 2]
            
            # Create statistics summaries for the prompt
            assayer_details = f"""
Overall Statistics:
- Average deviation: {overall_stats['mean']:.4f}%
- Overall standard deviation: {overall_stats['std']:.4f}%
- Range: {overall_stats['min']:.4f}% to {overall_stats['max']:.4f}%
- Total samples: {overall_stats['count']}

Performance Categories:
- Assayers with high bias: {len(high_bias)} assayers
- Assayers with high variance: {len(high_variance)} assayers
- Assayers with low sample counts: {len(low_sample_count)} assayers
"""
            
            # Add specific assayer details
            assayer_details += "\nTop 3 assayers by performance metrics:\n"
            
            # Sort by absolute mean (lowest bias)
            best_accuracy = assayer_stats.iloc[assayer_stats['mean'].abs().argsort()[:3]]
            for _, row in best_accuracy.iterrows():
                assayer_details += f"- {row['assayer_name']}: mean dev = {row['mean']:.4f}%, std dev = {row['std']:.4f}%, samples = {row['count']}\n"
                
            # Sort by std (lowest first - most consistent)
            best_consistency = assayer_stats.iloc[assayer_stats['std'].argsort()[:3]]
            assayer_details += "\nMost consistent assayers:\n"
            for _, row in best_consistency.iterrows():
                assayer_details += f"- {row['assayer_name']}: std dev = {row['std']:.4f}%, mean dev = {row['mean']:.4f}%, samples = {row['count']}\n"
        else:
            assayer_details = "Insufficient data for per-assayer statistics."
            
        prompt = f"""
Analyze gold assay performance data covering {time_period}.

{assayer_details}

Task: Analyze this performance data and provide specific suggestions for:
1. Practical steps to improve overall assayer accuracy
2. Techniques to improve consistency among assayers
3. Potential training needs based on the observed patterns

Focus on clear explanations of what the data means for the laboratory's operations.
Provide concise, actionable insights based on data patterns (200-250 words).
"""

        system_prompt = """
You are a gold testing laboratory quality specialist.
Your task is to provide data-centric analysis and practical suggestions for improvement.
Use direct language focusing on clear explanations of what the data shows.
Offer practical ideas that would help lab managers improve testing processes.
Balance between explanation and actionable insights.
"""

        # Call OpenAI API
        recommendations = analyze_with_openai(prompt, system_prompt, max_tokens=500)
        return recommendations
    
    except Exception as e:
        # Return a fallback analysis
        return generate_recommendation_fallback(deviations_df)

# Fallback analysis functions for when API is unavailable

def generate_statistical_analysis(data):
    """Generate a basic statistical analysis focused on data interpretation, no recommendations"""
    try:
        if data.empty:
            return "No data available for analysis."
            
        # Basic statistics
        mean_dev = data['percentage_deviation'].mean()
        median_dev = data['percentage_deviation'].median()
        std_dev = data['percentage_deviation'].std()
        max_dev = data['percentage_deviation'].max()
        min_dev = data['percentage_deviation'].min()
        sample_count = len(data)
        assayer_count = data['assayer_name'].nunique()
        
        # Calculate per assayer stats
        assayer_stats = data.groupby('assayer_name')['percentage_deviation'].agg(['mean', 'std']).reset_index()
        best_assayer = assayer_stats.iloc[assayer_stats['mean'].abs().idxmin()]['assayer_name']
        worst_assayer = assayer_stats.iloc[assayer_stats['mean'].abs().idxmax()]['assayer_name']
        
        return f"""
## Statistical Analysis of Gold Testing Deviations

The data shows variations in gold content measurements across {assayer_count} assayers with {sample_count} total samples.

**Key Statistics:**
- Average deviation: {mean_dev:.4f}%
- Median deviation: {median_dev:.4f}%
- Standard deviation: {std_dev:.4f}%
- Range: {min_dev:.4f}% to {max_dev:.4f}%

**Assayer Performance:**
- Lowest average deviation: {best_assayer}
- Highest average deviation: {worst_assayer}

This data provides a snapshot of testing accuracy across the laboratory. The deviations represent how far each assayer's measurements differ from the benchmark standard.
"""
    except Exception as e:
        return f"Unable to generate analysis due to an error: {str(e)}"

def generate_heatmap_analysis(data):
    """Generate a basic heatmap analysis focused on data interpretation, no recommendations"""
    try:
        if data.empty:
            return "No data available for heatmap analysis."
            
        # Calculate basic statistics for the heatmap
        assayer_count = data['assayer_name'].nunique()
        date_min = data['test_date'].min()
        date_max = data['test_date'].max()
        date_range = pd.to_datetime(date_max) - pd.to_datetime(date_min)
        
        # Assayer with highest and lowest average deviation
        assayer_stats = data.groupby('assayer_name')['percentage_deviation'].mean().reset_index()
        best_assayer = assayer_stats.iloc[assayer_stats['percentage_deviation'].abs().idxmin()]['assayer_name']
        worst_assayer = assayer_stats.iloc[assayer_stats['percentage_deviation'].abs().idxmax()]['assayer_name']
        
        # Check for patterns across time
        has_date_range = date_range.days > 7 if hasattr(date_range, 'days') else False
        
        return f"""
## Heatmap Analysis of Gold Testing Deviations

The heatmap visualizes deviation patterns across {assayer_count} assayers over time.

**What This Shows:**
- Each row represents an assayer
- Each column represents a date
- Colors indicate deviation magnitude (darker colors = larger deviations)
- Blank areas indicate no data for that assayer/date

**Key Observations:**
- Most consistent assayer: {best_assayer}
- Least consistent assayer: {worst_assayer}
- Date range: {date_range.days if has_date_range else "Limited"} days

This visualization helps identify patterns of deviation across both assayers and time periods, making it easier to spot problematic areas or improvements.
"""
    except Exception as e:
        return f"Unable to generate heatmap analysis due to an error: {str(e)}"

def generate_trend_analysis(data, window=7):
    """Generate a basic trend analysis focused on data interpretation, no recommendations"""
    try:
        if data.empty:
            return "No data available for trend analysis."
            
        # Calculate basic statistics for the trend
        date_min = data['test_date'].min()
        date_max = data['test_date'].max()
        
        # Calculate overall average
        mean_dev = data['percentage_deviation'].mean()
        
        # Determine if we have enough data for meaningful trend
        date_range = pd.to_datetime(date_max) - pd.to_datetime(date_min)
        has_enough_data = date_range.days >= window if hasattr(date_range, 'days') else False
        
        if has_enough_data:
            message = f"""
## Moving Average Trend Analysis

The line chart shows a {window}-day moving average of gold testing deviations over time.

**What This Shows:**
- The y-axis represents the average percentage deviation
- The x-axis shows dates
- The line smooths daily fluctuations to reveal the underlying trend
- Upward trend indicates increasing deviations (potentially concerning)
- Downward trend indicates decreasing deviations (potentially improving)

**Key Points:**
- Overall average deviation across period: {mean_dev:.4f}%
- Time period: {date_min} to {date_max}

This trend visualization helps identify whether testing accuracy is improving or deteriorating over time, and can highlight specific time periods of interest.
"""
        else:
            message = f"""
## Trend Analysis (Limited Data)

The chart attempts to show a {window}-day moving average, but there may not be enough consecutive data points for a meaningful trend line.

**What This Would Normally Show:**
- The moving average smooths daily fluctuations to reveal underlying patterns
- Time period available: {date_min} to {date_max}
- Overall average deviation: {mean_dev:.4f}%

With more continuous data collection, this visualization would help identify whether testing accuracy is improving or deteriorating over time.
"""
        
        return message
    except Exception as e:
        return f"Unable to generate trend analysis due to an error: {str(e)}"

def generate_distribution_analysis(data):
    """Generate a basic distribution analysis focused on data interpretation, no recommendations"""
    try:
        if data.empty:
            return "No data available for distribution analysis."
            
        # Calculate basic statistics
        assayer_count = data['assayer_name'].nunique()
        
        # Per-assayer stats
        assayer_stats = data.groupby('assayer_name')['percentage_deviation'].agg(['mean', 'std']).reset_index()
        most_consistent = assayer_stats.iloc[assayer_stats['std'].idxmin()]['assayer_name']
        least_consistent = assayer_stats.iloc[assayer_stats['std'].idxmax()]['assayer_name']
        
        return f"""
## Distribution Analysis of Gold Testing Deviations

The box plot shows the distribution of deviations for each of the {assayer_count} assayers.

**How to Read This Chart:**
- Each box represents one assayer's deviation distribution
- The middle line in each box is the median value
- The box shows the middle 50% of values (interquartile range)
- Whiskers extend to min/max values within 1.5x the interquartile range
- Dots beyond whiskers represent outliers or extreme values

**Key Observations:**
- Most consistent assayer (smallest box): {most_consistent}
- Least consistent assayer (largest box): {least_consistent}
- Boxes centered near zero indicate good accuracy
- Wide boxes indicate inconsistent results

This visualization helps identify both accuracy (how centered around zero) and precision (how narrow the distribution) for each assayer.
"""
    except Exception as e:
        return f"Unable to generate distribution analysis due to an error: {str(e)}"

def generate_recommendation_fallback(data):
    """Generate performance data interpretation instead of recommendations"""
    try:
        if data.empty:
            return "No data available for performance analysis."
            
        # Calculate basic statistics
        mean_dev = data['percentage_deviation'].mean()
        std_dev = data['percentage_deviation'].std()
        
        # Per-assayer stats
        assayer_stats = data.groupby('assayer_name')['percentage_deviation'].agg(['mean', 'std', 'count']).reset_index()
        
        # Find assayers with various characteristics
        above_avg_dev = assayer_stats[assayer_stats['mean'].abs() > abs(mean_dev)]
        above_avg_std = assayer_stats[assayer_stats['std'] > std_dev]
        low_count = assayer_stats[assayer_stats['count'] < assayer_stats['count'].median() / 2]
        
        return f"""
## Gold Testing Performance Analysis

The data provides insight into assayer performance across {len(assayer_stats)} active assayers.

**Performance Categories:**
- Assayers with above-average deviation: {len(above_avg_dev)} assayers
- Assayers with above-average inconsistency: {len(above_avg_std)} assayers
- Assayers with relatively few samples: {len(low_count)} assayers

**Data Interpretation:**
- Higher deviations indicate a potential systematic bias in testing methodology
- Higher standard deviations indicate inconsistent testing results
- Assayers with few samples may need more testing experience

This analysis helps identify patterns in testing performance and highlights areas where further investigation may be beneficial.
"""
    except Exception as e:
        return f"Unable to generate performance analysis due to an error: {str(e)}"