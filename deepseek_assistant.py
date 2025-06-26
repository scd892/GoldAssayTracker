import os
import json
import pandas as pd
import sys
from deepseek_ai import DeepSeekAI
from datetime import datetime, timedelta

# Initialize DeepSeek client
try:
    deepseek_client = DeepSeekAI(api_key=os.environ.get("DEEPSEEK_API_KEY"))
except Exception as e:
    print(f"Error initializing DeepSeek client: {str(e)}")
    deepseek_client = None

def analyze_with_deepseek(prompt, system_prompt="", max_tokens=800):
    """
    Use DeepSeek to analyze data based on a prompt
    
    Args:
        prompt: The user prompt to send to DeepSeek
        system_prompt: Optional system prompt for context
        max_tokens: Maximum number of tokens in the response
        
    Returns:
        str: DeepSeek's response
    """
    # For now, fallback to the statistical analysis functions
    # The actual analysis will be handled by the specific analysis functions
    # like generate_statistical_analysis, generate_heatmap_analysis, etc.
    return None

def analyze_deviation_data(deviations_df, time_period="Last 30 days"):
    """
    Analyze deviations data and provide AI-generated insights
    
    Args:
        deviations_df: DataFrame containing deviation data
        time_period: Time period for context in the analysis
        
    Returns:
        str: AI-generated analysis of the data
    """
    if deviations_df is None or deviations_df.empty:
        return "No data available for analysis during this period."
    
    try:
        # Prepare a summary of the data for the AI
        assayer_stats = deviations_df.groupby('assayer_name').agg({
            'absolute_deviation': ['mean', 'std', 'count', 'min', 'max'],
            'percentage_deviation': ['mean', 'std', 'min', 'max']
        }).reset_index()
        
        # Flatten the multi-level columns
        assayer_stats.columns = ['_'.join(col).strip('_') for col in assayer_stats.columns.values]
        
        # Calculate overall statistics
        total_samples = len(deviations_df)
        num_assayers = deviations_df['assayer_name'].nunique()
        avg_deviation = deviations_df['percentage_deviation'].mean()
        max_deviation = deviations_df['percentage_deviation'].abs().max()
        
        # Get top performing and underperforming assayers
        top_assayer = assayer_stats.loc[assayer_stats['percentage_deviation_mean'].abs().idxmin()]
        bottom_assayer = assayer_stats.loc[assayer_stats['percentage_deviation_mean'].abs().idxmax()]
        
        # Identify any assayers with high standard deviation (inconsistent)
        consistency_threshold = assayer_stats['percentage_deviation_std'].median() * 1.5
        inconsistent_assayers = assayer_stats[assayer_stats['percentage_deviation_std'] > consistency_threshold]
        
        # Check for any trends over time
        deviations_df['test_date'] = pd.to_datetime(deviations_df['test_date'])
        deviations_df = deviations_df.sort_values('test_date')
        
        # Detect if there's any trend in the recent days
        recent_trend = "neutral"
        if len(deviations_df) > 10:
            recent_data = deviations_df.tail(10)
            early_avg = recent_data.iloc[:5]['percentage_deviation'].mean()
            late_avg = recent_data.iloc[5:]['percentage_deviation'].mean()
            if late_avg > early_avg * 1.1:
                recent_trend = "worsening"
            elif late_avg < early_avg * 0.9:
                recent_trend = "improving"
        
        # Prepare data summary for AI
        data_summary = {
            "time_period": time_period,
            "total_samples": int(total_samples),
            "num_assayers": int(num_assayers),
            "avg_deviation_percentage": float(round(avg_deviation, 2)),
            "max_deviation_percentage": float(round(max_deviation, 2)),
            "top_performer": {
                "name": top_assayer['assayer_name'],
                "avg_deviation": float(round(top_assayer['percentage_deviation_mean'], 2)),
                "samples_tested": int(top_assayer['absolute_deviation_count']),
                "consistency": float(round(top_assayer['percentage_deviation_std'], 2))
            },
            "bottom_performer": {
                "name": bottom_assayer['assayer_name'],
                "avg_deviation": float(round(bottom_assayer['percentage_deviation_mean'], 2)),
                "samples_tested": int(bottom_assayer['absolute_deviation_count']),
                "consistency": float(round(bottom_assayer['percentage_deviation_std'], 2))
            },
            "inconsistent_assayers": [
                {
                    "name": row['assayer_name'],
                    "std_deviation": float(round(row['percentage_deviation_std'], 2)),
                    "samples_tested": int(row['absolute_deviation_count'])
                } 
                for _, row in inconsistent_assayers.iterrows()
            ],
            "recent_trend": recent_trend,
            "assayer_details": [
                {
                    "name": row['assayer_name'],
                    "avg_deviation": float(round(row['percentage_deviation_mean'], 2)),
                    "std_deviation": float(round(row['percentage_deviation_std'], 2)),
                    "samples_tested": int(row['absolute_deviation_count']),
                    "min_deviation": float(round(row['percentage_deviation_min'], 2)),
                    "max_deviation": float(round(row['percentage_deviation_max'], 2))
                }
                for _, row in assayer_stats.iterrows()
            ]
        }
        
        # Check if DeepSeek client is available
        if deepseek_client is None:
            # Provide a fallback statistical analysis without using the API
            return generate_statistical_analysis(data_summary)
        
        # Prepare the system prompt for DeepSeek
        system_prompt = """You are an expert gold assay analyst providing insights about laboratory technicians (assayers) performance.
        Analyze the data and provide a detailed but concise interpretation focusing on:
        1. Overall performance summary
        2. Top and bottom performers with specific insights
        3. Consistency issues among assayers
        4. Recent trends (improving, worsening, or stable)
        5. Actionable recommendations for laboratory management
        
        Write in a professional tone. Use specific numbers and percentages from the data.
        Mention assayers by name and provide specific insights about their performance.
        Focus only on the data provided and avoid making assumptions beyond what's in the data.
        
        Your analysis should be 3-4 paragraphs and include specific data points.
        """
        
        # Prepare the user prompt for DeepSeek
        user_prompt = f"""Here is the gold assay deviation data for {time_period}:
        {json.dumps(data_summary, indent=2)}
        
        Provide a comprehensive analysis of this data.
        """
        
        # Get analysis from DeepSeek - currently returns None, so we use fallback
        ai_response = analyze_with_deepseek(user_prompt, system_prompt, max_tokens=800)
        
        # Always use the fallback for now until AI is properly connected
        return generate_statistical_analysis(data_summary)
        
    except Exception as e:
        # Log the error but provide a statistical fallback
        print(f"Error in AI analysis: {str(e)}")
        
        # If we've already calculated the data summary, use it for the fallback
        if 'data_summary' in locals():
            return generate_statistical_analysis(data_summary)
        else:
            return f"An error occurred while analyzing the data: {str(e)}"
            
def analyze_heatmap(deviations_df, time_period="Last 30 days"):
    """
    Analyze the deviation heatmap and provide insights
    
    Args:
        deviations_df: DataFrame containing deviation data
        time_period: Time period for context in the analysis
        
    Returns:
        str: AI-generated analysis of the heatmap
    """
    if deviations_df is None or deviations_df.empty:
        return "No data available for heatmap analysis during this period."
    
    try:
        # Extract information from the dataframe for heatmap analysis
        # For heatmap we need to look at deviation patterns by assayer and over time
        
        # Convert test_date to datetime if it's not already
        deviations_df['test_date'] = pd.to_datetime(deviations_df['test_date'])
        
        # Create date groups (by week)
        deviations_df['week'] = deviations_df['test_date'].dt.strftime('%Y-%U')
        
        # Get weekly average deviations by assayer
        weekly_avg = deviations_df.groupby(['week', 'assayer_name'])['percentage_deviation'].mean().reset_index()
        
        # Identify hot spots (high deviation areas)
        hot_spots = weekly_avg[weekly_avg['percentage_deviation'].abs() > 5]
        
        # Find consistent patterns
        assayer_consistency = deviations_df.groupby('assayer_name')['percentage_deviation'].std().reset_index()
        consistent_assayers = assayer_consistency.sort_values('percentage_deviation').head(3)
        inconsistent_assayers = assayer_consistency.sort_values('percentage_deviation', ascending=False).head(3)
        
        # Prepare data summary for DeepSeek
        heatmap_summary = {
            "time_period": time_period,
            "total_weeks": weekly_avg['week'].nunique(),
            "total_assayers": weekly_avg['assayer_name'].nunique(),
            "hot_spots": [
                {
                    "week": row['week'],
                    "assayer": row['assayer_name'],
                    "deviation": float(round(row['percentage_deviation'], 2))
                }
                for _, row in hot_spots.iterrows()
            ],
            "most_consistent_assayers": [
                {
                    "name": row['assayer_name'],
                    "std_deviation": float(round(row['percentage_deviation'], 2))
                }
                for _, row in consistent_assayers.iterrows()
            ],
            "most_inconsistent_assayers": [
                {
                    "name": row['assayer_name'],
                    "std_deviation": float(round(row['percentage_deviation'], 2))
                }
                for _, row in inconsistent_assayers.iterrows()
            ],
            "weekly_patterns": weekly_avg.to_dict(orient='records')
        }
        
        # Check if DeepSeek client is available
        if deepseek_client is None:
            # Provide a fallback heatmap analysis without using the API
            return generate_heatmap_analysis(heatmap_summary)
        
        # Prepare the system prompt for DeepSeek
        system_prompt = """You are an expert gold assay analyst interpreting a heatmap of assayer deviations.
        The heatmap shows deviations over time (by week) for different assayers.
        
        Analyze the data and provide insights on:
        1. Time-based patterns (any specific weeks with high deviations across multiple assayers)
        2. Assayer-specific patterns (consistent over/under performance)
        3. Notable hotspots (specific assayer-week combinations with very high deviations)
        4. Consistency patterns (which assayers are most consistent/inconsistent)
        
        Write in a professional tone. Use specific numbers and percentages.
        Focus on what the heatmap visualization would reveal to a laboratory manager.
        Your analysis should be 2-3 paragraphs and include specific data points.
        """
        
        # Prepare the user prompt for DeepSeek
        user_prompt = f"""Here is data extracted from a heatmap visualization of gold assay deviations for {time_period}:
        {json.dumps(heatmap_summary, indent=2)}
        
        Provide an interpretation of what patterns would be visible in this heatmap visualization.
        """
        
        # Get analysis from DeepSeek - currently returns None, so we use fallback
        ai_response = analyze_with_deepseek(user_prompt, system_prompt, max_tokens=600)
        
        # Always use the fallback for now until AI is properly connected
        return generate_heatmap_analysis(heatmap_summary)
        
    except Exception as e:
        # Log the error but provide a statistical fallback
        print(f"Error in heatmap analysis: {str(e)}")
        
        # If we've already calculated the data summary, use it for the fallback
        if 'heatmap_summary' in locals():
            return generate_heatmap_analysis(heatmap_summary)
        else:
            return f"An error occurred while analyzing the heatmap: {str(e)}"

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
    if deviations_df is None or deviations_df.empty:
        return "No data available for trend analysis during this period."
    
    try:
        # Convert test_date to datetime if it's not already
        deviations_df['test_date'] = pd.to_datetime(deviations_df['test_date'])
        deviations_df = deviations_df.sort_values('test_date')
        
        # Calculate moving averages by assayer
        trend_data = []
        
        for assayer in deviations_df['assayer_name'].unique():
            assayer_df = deviations_df[deviations_df['assayer_name'] == assayer]
            if len(assayer_df) >= ma_window:
                # Get daily average first
                daily_avg = assayer_df.groupby(assayer_df['test_date'].dt.date)['percentage_deviation'].mean()
                # Calculate moving average if enough data points
                if len(daily_avg) >= ma_window:
                    ma_series = daily_avg.rolling(window=ma_window).mean()
                    # Convert to records
                    for date, value in zip(daily_avg.index[-10:], ma_series.iloc[-10:]):
                        if pd.notna(value):
                            trend_data.append({
                                "assayer": assayer,
                                "date": date.strftime('%Y-%m-%d'),
                                "ma_value": float(round(value, 2))
                            })
        
        # Calculate overall trend direction for each assayer
        assayer_trends = {}
        for assayer in deviations_df['assayer_name'].unique():
            assayer_points = [p for p in trend_data if p['assayer'] == assayer]
            if len(assayer_points) >= 3:
                first_values = [p['ma_value'] for p in assayer_points[:min(3, len(assayer_points))]]
                last_values = [p['ma_value'] for p in assayer_points[-min(3, len(assayer_points)):]]
                
                first_avg = sum(first_values) / len(first_values)
                last_avg = sum(last_values) / len(last_values)
                
                if last_avg < first_avg * 0.8:
                    trend = "strongly improving"
                elif last_avg < first_avg * 0.95:
                    trend = "improving"
                elif last_avg > first_avg * 1.2:
                    trend = "strongly worsening"
                elif last_avg > first_avg * 1.05:
                    trend = "worsening"
                else:
                    trend = "stable"
                
                assayer_trends[assayer] = {
                    "trend": trend,
                    "first_value": float(round(first_avg, 2)),
                    "last_value": float(round(last_avg, 2)),
                    "change_percentage": float(round((last_avg - first_avg) / first_avg * 100, 2))
                }
        
        # Prepare data summary for DeepSeek
        trend_summary = {
            "time_period": time_period,
            "moving_average_window": ma_window,
            "assayer_trends": [
                {
                    "assayer": assayer,
                    "trend_direction": data["trend"],
                    "first_value": data["first_value"],
                    "last_value": data["last_value"], 
                    "change_percentage": data["change_percentage"]
                }
                for assayer, data in assayer_trends.items()
            ],
            "recent_data_points": trend_data[-30:] if len(trend_data) > 30 else trend_data
        }
        
        # Check if DeepSeek client is available
        if deepseek_client is None:
            # Provide a fallback trend analysis without using the API
            return generate_trend_analysis(trend_summary)
        
        # Prepare the system prompt for DeepSeek
        system_prompt = f"""You are an expert gold assay analyst interpreting a {ma_window}-day moving average trend chart.
        The chart shows how assayer deviations have changed over time.
        
        Analyze the data and provide insights on:
        1. Overall trends across all assayers (improving, worsening, or stable)
        2. Specific assayer trends (which ones are improving or worsening)
        3. Notable patterns or anomalies in the trend data
        4. Potential causes for observed trends (based solely on the data)
        
        Write in a professional tone. Use specific numbers and percentages.
        Focus on interpreting the moving average visualization for a laboratory manager.
        Your analysis should be 2-3 paragraphs and include specific data points.
        """
        
        # Prepare the user prompt for DeepSeek
        user_prompt = f"""Here is data extracted from a {ma_window}-day moving average trend chart of gold assay deviations for {time_period}:
        {json.dumps(trend_summary, indent=2)}
        
        Provide an interpretation of what patterns would be visible in this trend chart visualization.
        """
        
        # Get analysis from DeepSeek - currently returns None, so we use fallback
        ai_response = analyze_with_deepseek(user_prompt, system_prompt, max_tokens=600)
        
        # Always use the fallback for now until AI is properly connected
        return generate_trend_analysis(trend_summary)
        
    except Exception as e:
        # Log the error but provide a statistical fallback
        print(f"Error in trend analysis: {str(e)}")
        
        # If we've already calculated the data summary, use it for the fallback
        if 'trend_summary' in locals():
            return generate_trend_analysis(trend_summary)
        else:
            return f"An error occurred while analyzing the trend chart: {str(e)}"

def analyze_distribution_chart(deviations_df, time_period="Last 90 days"):
    """
    Analyze the deviation distribution chart and provide insights
    
    Args:
        deviations_df: DataFrame containing deviation data
        time_period: Time period for context in the analysis
        
    Returns:
        str: AI-generated analysis of the distribution chart
    """
    if deviations_df is None or deviations_df.empty:
        return "No data available for distribution analysis during this period."
    
    try:
        # Calculate distribution statistics by assayer
        distribution_stats = deviations_df.groupby('assayer_name')['percentage_deviation'].agg([
            'mean', 'median', 'std', 'min', 'max', 
            lambda x: x.quantile(0.25), 
            lambda x: x.quantile(0.75),
            'count'
        ]).reset_index()
        
        # Rename the columns
        distribution_stats.columns = ['assayer_name', 'mean', 'median', 'std', 'min', 'max', 'q25', 'q75', 'count']
        
        # Calculate interquartile range (IQR)
        distribution_stats['iqr'] = distribution_stats['q75'] - distribution_stats['q25']
        
        # Calculate skewness indicator (mean - median)
        distribution_stats['skew_indicator'] = distribution_stats['mean'] - distribution_stats['median']
        
        # Determine distribution shape for each assayer
        distribution_shapes = []
        
        for _, row in distribution_stats.iterrows():
            # Calculate coefficient of variation to gauge spread
            cv = abs(row['std'] / row['mean']) if row['mean'] != 0 else float('inf')
            
            # Skewness check
            skew_ratio = row['skew_indicator'] / row['std'] if row['std'] != 0 else 0
            
            if abs(skew_ratio) < 0.2:
                skew_type = "approximately symmetric"
            elif skew_ratio > 0:
                skew_type = "right-skewed (positive skew)"
            else:
                skew_type = "left-skewed (negative skew)"
            
            # Determine spread description
            if cv < 0.5:
                spread = "narrow"
            elif cv < 1.0:
                spread = "moderate"
            else:
                spread = "wide"
            
            distribution_shapes.append({
                "assayer": row['assayer_name'],
                "shape": skew_type,
                "spread": spread,
                "mean": float(round(row['mean'], 2)),
                "median": float(round(row['median'], 2)),
                "std": float(round(row['std'], 2)),
                "iqr": float(round(row['iqr'], 2)),
                "sample_count": int(row['count'])
            })
        
        # Prepare data summary for DeepSeek
        distribution_summary = {
            "time_period": time_period,
            "assayer_distributions": distribution_shapes,
            "detailed_stats": distribution_stats.drop(['q25', 'q75'], axis=1).to_dict(orient='records')
        }
        
        # Check if DeepSeek client is available
        if deepseek_client is None:
            # Provide a fallback distribution analysis without using the API
            return generate_distribution_analysis(distribution_summary)
        
        # Prepare the system prompt for DeepSeek
        system_prompt = """You are an expert gold assay analyst interpreting a distribution chart of assayer deviations.
        The chart shows the statistical distribution of deviations for each assayer.
        
        Analyze the data and provide insights on:
        1. Distribution shapes (symmetric, skewed) and what they indicate about assayer performance
        2. Spread of distributions (wide vs. narrow) and implications for consistency
        3. Comparisons between different assayers' distributions
        4. Recommendations based on distribution analysis
        
        Write in a professional tone. Use specific numbers and percentages.
        Focus on interpreting what the distribution visualization would show a laboratory manager.
        Your analysis should be 2-3 paragraphs and include specific data points.
        """
        
        # Prepare the user prompt for DeepSeek
        user_prompt = f"""Here is data extracted from a distribution chart of gold assay deviations for {time_period}:
        {json.dumps(distribution_summary, indent=2)}
        
        Provide an interpretation of what patterns would be visible in this distribution chart visualization.
        """
        
        # Get analysis from DeepSeek - currently returns None, so we use fallback
        ai_response = analyze_with_deepseek(user_prompt, system_prompt, max_tokens=600)
        
        # Always use the fallback for now until AI is properly connected
        return generate_distribution_analysis(distribution_summary)
        
    except Exception as e:
        # Log the error but provide a statistical fallback
        print(f"Error in distribution analysis: {str(e)}")
        
        # If we've already calculated the data summary, use it for the fallback
        if 'distribution_summary' in locals():
            return generate_distribution_analysis(distribution_summary)
        else:
            return f"An error occurred while analyzing the distribution chart: {str(e)}"

def generate_performance_recommendations(deviations_df, time_period="Last 90 days"):
    """
    Generate specific recommendations for improving assayer performance
    
    Args:
        deviations_df: DataFrame containing deviation data
        time_period: Time period for context in the analysis
        
    Returns:
        str: AI-generated recommendations
    """
    if deviations_df is None or deviations_df.empty:
        return "No data available to generate recommendations."
    
    try:
        # Calculate key performance metrics by assayer
        assayer_metrics = deviations_df.groupby('assayer_name').agg({
            'percentage_deviation': ['mean', 'std', 'count', 'min', 'max'],
            'gold_content': ['mean', 'count']
        }).reset_index()
        
        # Flatten the multi-level columns
        assayer_metrics.columns = ['_'.join(col).strip('_') for col in assayer_metrics.columns.values]
        
        # Identify performance categories
        high_bias_threshold = 2.0  # Assayers with avg deviation > 2%
        high_variance_threshold = 1.5  # Assayers with std > 1.5%
        
        high_bias_assayers = []
        high_variance_assayers = []
        low_experience_assayers = []
        well_performing_assayers = []
        
        for _, row in assayer_metrics.iterrows():
            assayer_info = {
                "name": row['assayer_name'],
                "avg_deviation": float(round(row['percentage_deviation_mean'], 2)),
                "std_deviation": float(round(row['percentage_deviation_std'], 2)),
                "sample_count": int(row['percentage_deviation_count'])
            }
            
            # Check for high bias (consistently off from benchmark)
            if abs(row['percentage_deviation_mean']) > high_bias_threshold:
                high_bias_assayers.append(assayer_info)
            
            # Check for high variance (inconsistent results)
            if row['percentage_deviation_std'] > high_variance_threshold:
                high_variance_assayers.append(assayer_info)
            
            # Check for low experience (few samples tested)
            if row['percentage_deviation_count'] < assayer_metrics['percentage_deviation_count'].median() / 2:
                low_experience_assayers.append(assayer_info)
            
            # Identify well-performing assayers (low bias, low variance)
            if (abs(row['percentage_deviation_mean']) < high_bias_threshold / 2 and 
                row['percentage_deviation_std'] < high_variance_threshold / 2 and
                row['percentage_deviation_count'] >= assayer_metrics['percentage_deviation_count'].median()):
                well_performing_assayers.append(assayer_info)
        
        # Prepare data summary for DeepSeek
        performance_summary = {
            "time_period": time_period,
            "high_bias_assayers": high_bias_assayers,
            "high_variance_assayers": high_variance_assayers,
            "low_experience_assayers": low_experience_assayers,
            "well_performing_assayers": well_performing_assayers,
            "overall_metrics": {
                "total_assayers": int(len(assayer_metrics)),
                "avg_deviation_across_all": float(round(deviations_df['percentage_deviation'].mean(), 2)),
                "avg_std_across_all": float(round(assayer_metrics['percentage_deviation_std'].mean(), 2))
            }
        }
        
        # Check if DeepSeek client is available
        if deepseek_client is None:
            # Provide a fallback recommendations without using the API
            return generate_recommendation_fallback(performance_summary)
        
        # Prepare the system prompt for DeepSeek
        system_prompt = """You are an expert gold assay laboratory consultant providing specific recommendations for improving assayer performance.
        
        Based on the data provided, generate specific, actionable recommendations for:
        1. Overall laboratory quality improvement
        2. Training and development for specific assayers
        3. Process standardization recommendations
        4. Quality control measures
        5. Individual recommendations for problematic assayers
        
        Write in a professional tone with actionable, specific recommendations.
        Mention assayers by name when making specific recommendations.
        Recommendations should be practical and directly related to the performance data.
        """
        
        # Prepare the user prompt for DeepSeek
        user_prompt = f"""Here is performance data for gold assayers over {time_period}:
        {json.dumps(performance_summary, indent=2)}
        
        Provide specific, actionable recommendations for improving laboratory performance.
        """
        
        # Get recommendations from DeepSeek - currently returns None, so we use fallback
        ai_response = analyze_with_deepseek(user_prompt, system_prompt, max_tokens=750)
        
        # Always use the fallback for now until AI is properly connected
        return generate_recommendation_fallback(performance_summary)
        
    except Exception as e:
        # Log the error but provide a statistical fallback
        print(f"Error generating recommendations: {str(e)}")
        
        # If we've already calculated the data summary, use it for the fallback
        if 'performance_summary' in locals():
            return generate_recommendation_fallback(performance_summary)
        else:
            return f"An error occurred while generating recommendations: {str(e)}"

# Fallback functions for when AI is unavailable
def generate_statistical_analysis(data):
    """Generate a basic statistical analysis focused on data interpretation, no recommendations"""
    try:
        # Extract key data points
        time_period = data["time_period"]
        total_samples = data["total_samples"]
        num_assayers = data["num_assayers"]
        avg_deviation = data["avg_deviation_percentage"]
        max_deviation = data["max_deviation_percentage"]
        top_performer = data["top_performer"]
        bottom_performer = data["bottom_performer"]
        inconsistent_assayers = data["inconsistent_assayers"]
        recent_trend = data["recent_trend"]
        assayer_details = data["assayer_details"]
        
        # Sort assayers by deviation magnitude (absolute value)
        sorted_assayers = sorted(assayer_details, key=lambda x: abs(x["avg_deviation"]))
        
        # Build a readable analysis
        analysis = f"## Data Interpretation for {time_period}\n\n"
        
        # Chart explanation
        analysis += f"This chart displays percentage deviations from benchmark for {num_assayers} assayers across {total_samples} samples.\n\n"
        
        # Axis explanation
        analysis += f"**X-axis:** Represents percentage deviation from benchmark values (0% = perfect match with benchmark).\n"
        analysis += f"**Y-axis:** Shows individual assayer names ordered by their average deviation.\n\n"
        
        # Data interpretation
        analysis += f"### Key Observations\n"
        
        # Highlight precise assayers (closest to zero)
        low_deviation_assayers = [a for a in sorted_assayers[:3]]
        if low_deviation_assayers:
            low_dev_names = ", ".join([a["name"] for a in low_deviation_assayers])
            avg_devs = ", ".join([f"{a['avg_deviation']}%" for a in low_deviation_assayers])
            analysis += f"**Closest to benchmark:** {low_dev_names} with deviations of {avg_devs} respectively.\n\n"
        
        # Highlight assayers with most significant deviations
        high_deviation_assayers = sorted(assayer_details, key=lambda x: abs(x["avg_deviation"]), reverse=True)[:3]
        if high_deviation_assayers:
            high_names = []
            high_devs = []
            for a in high_deviation_assayers:
                high_names.append(a["name"])
                if a["avg_deviation"] > 0:
                    high_devs.append(f"+{a['avg_deviation']}% (higher than benchmark)")
                else:
                    high_devs.append(f"{a['avg_deviation']}% (lower than benchmark)")
                    
            high_dev_names = ", ".join(high_names)
            high_dev_values = ", ".join(high_devs)
            analysis += f"**Largest deviations:** {high_dev_names} with deviations of {high_dev_values} respectively.\n\n"
        
        # Trend information
        if recent_trend == "improving":
            analysis += f"**Trend analysis:** Recent data shows narrowing deviations across most assayers.\n\n"
        elif recent_trend == "worsening":
            analysis += f"**Trend analysis:** Recent data shows widening deviations across most assayers.\n\n"
        else:
            analysis += f"**Trend analysis:** Deviation patterns remain consistent with no significant direction change.\n\n"
        
        return analysis
        
    except Exception as e:
        return f"Data interpretation failed: {str(e)}\n\nPlease check your data and try again."

def generate_heatmap_analysis(data):
    """Generate a basic heatmap analysis focused on data interpretation, no recommendations"""
    try:
        # Extract key data points
        time_period = data["time_period"]
        total_weeks = data["total_weeks"]
        total_assayers = data["total_assayers"]
        hot_spots = data["hot_spots"]
        consistent_assayers = data["most_consistent_assayers"]
        inconsistent_assayers = data["most_inconsistent_assayers"]
        
        # Build a readable analysis
        analysis = f"## Heatmap Interpretation for {time_period}\n\n"
        
        # Axis explanation
        analysis += f"**X-axis:** Represents time periods (weeks) from earliest ({time_period}).\n"
        analysis += f"**Y-axis:** Shows individual assayer names.\n"
        analysis += f"**Color intensity:** Indicates magnitude of deviation from benchmark (darker = larger deviation).\n\n"
        
        # Overall summary
        analysis += f"### Key Observations\n"
        analysis += f"This heatmap visualizes deviation patterns across {total_weeks} weeks for {total_assayers} assayers. "
        
        # Pattern explanation
        if hot_spots:
            # Group hotspots by week to identify problematic time periods
            weeks_with_issues = {}
            for spot in hot_spots:
                if spot['week'] not in weeks_with_issues:
                    weeks_with_issues[spot['week']] = []
                weeks_with_issues[spot['week']].append((spot['assayer'], spot['deviation']))
            
            multi_assayer_weeks = {week: assayers for week, assayers in weeks_with_issues.items() if len(assayers) > 1}
            
            if multi_assayer_weeks:
                analysis += f"\n\n**Time-based patterns:** "
                problematic_weeks = list(multi_assayer_weeks.keys())[:2]  # Limit to top 2
                analysis += f"Weeks {', '.join(problematic_weeks)} show deviations across multiple assayers, "
                analysis += f"suggesting possible laboratory-wide factors during these periods.\n\n"
            
            # Identify assayers with multiple hotspots
            assayer_hotspot_count = {}
            for spot in hot_spots:
                if spot['assayer'] not in assayer_hotspot_count:
                    assayer_hotspot_count[spot['assayer']] = 0
                assayer_hotspot_count[spot['assayer']] += 1
            
            repeat_offenders = [(a, c) for a, c in assayer_hotspot_count.items() if c > 1]
            if repeat_offenders:
                analysis += f"**Assayer-specific patterns:** "
                repeat_names = [f"{a} ({c} occurrences)" for a, c in sorted(repeat_offenders, key=lambda x: x[1], reverse=True)[:3]]
                analysis += f"{', '.join(repeat_names)} show recurring deviation patterns.\n\n"
        else:
            analysis += f"The data shows relatively consistent performance with no significant hotspots across the time period.\n\n"
        
        # Consistency information
        if consistent_assayers and inconsistent_assayers:
            analysis += f"**Consistency comparison:** "
            consist_names = [f"{a['name']} (±{a['std_deviation']}%)" for a in consistent_assayers[:2]]
            inconsist_names = [f"{a['name']} (±{a['std_deviation']}%)" for a in inconsistent_assayers[:2]]
            
            analysis += f"{', '.join(consist_names)} maintain the most stable results, while "
            analysis += f"{', '.join(inconsist_names)} show the greatest variability in their measurements.\n\n"
        
        return analysis
        
    except Exception as e:
        return f"Heatmap interpretation failed: {str(e)}\n\nPlease check your data and try again."

def generate_trend_analysis(data):
    """Generate a basic trend analysis focused on data interpretation, no recommendations"""
    try:
        # Extract key data points
        time_period = data["time_period"]
        ma_window = data["moving_average_window"]
        assayer_trends = data["assayer_trends"]
        recent_data_points = data["recent_data_points"]
        
        # Count trends by category
        improving = [a for a in assayer_trends if a["trend_direction"] in ["improving", "strongly improving"]]
        worsening = [a for a in assayer_trends if a["trend_direction"] in ["worsening", "strongly worsening"]]
        stable = [a for a in assayer_trends if a["trend_direction"] == "stable"]
        
        # Find most significant changes
        biggest_improvement = None
        biggest_worsening = None
        
        for assayer in assayer_trends:
            if assayer["trend_direction"] in ["improving", "strongly improving"]:
                if biggest_improvement is None or assayer["change_percentage"] < biggest_improvement["change_percentage"]:
                    biggest_improvement = assayer
            elif assayer["trend_direction"] in ["worsening", "strongly worsening"]:
                if biggest_worsening is None or assayer["change_percentage"] > biggest_worsening["change_percentage"]:
                    biggest_worsening = assayer
        
        # Build a readable analysis
        analysis = f"## Trend Chart Interpretation for {time_period}\n\n"
        
        # Axis explanation
        analysis += f"**X-axis:** Represents dates over the {time_period} period.\n"
        analysis += f"**Y-axis:** Shows percentage deviation from benchmark values (0% = perfect match).\n"
        analysis += f"**Lines:** Each line represents a {ma_window}-day moving average for a different assayer.\n\n"
        
        # Direction explanation
        analysis += f"**Downward trends:** Indicate improving precision (moving closer to benchmark).\n"
        analysis += f"**Upward trends:** Indicate decreasing precision (moving away from benchmark).\n"
        analysis += f"**Flat/stable lines:** Indicate consistent precision levels.\n\n"
        
        # Overall trend summary
        analysis += f"### Key Observations\n"
        
        # Category counts
        analysis += f"From {len(assayer_trends)} assayers with sufficient data for trend analysis: "
        analysis += f"{len(improving)} show improving trends, "
        analysis += f"{len(stable)} show stable performance, and "
        analysis += f"{len(worsening)} show worsening trends.\n\n"
        
        # Notable trends
        if biggest_improvement:
            analysis += f"**Most significant improvement:** {biggest_improvement['assayer']} shows a {abs(biggest_improvement['change_percentage'])}% "
            analysis += f"reduction in deviation from {biggest_improvement['first_value']}% to {biggest_improvement['last_value']}%.\n\n"
        
        if biggest_worsening:
            analysis += f"**Most significant degradation:** {biggest_worsening['assayer']} shows a {biggest_worsening['change_percentage']}% "
            analysis += f"increase in deviation from {biggest_worsening['first_value']}% to {biggest_worsening['last_value']}%.\n\n"
            
        # General laboratory trend
        lab_trend = "improving"
        if len(worsening) > len(improving) and len(worsening) > len(stable):
            lab_trend = "worsening"
        elif len(stable) > len(improving) and len(stable) > len(worsening):
            lab_trend = "stable"
            
        analysis += f"**Overall laboratory trend:** The general performance trend is {lab_trend} "
        analysis += f"based on the {ma_window}-day moving average analysis.\n\n"
        
        return analysis
        
    except Exception as e:
        return f"Trend interpretation failed: {str(e)}\n\nPlease check your data and try again."

def generate_distribution_analysis(data):
    """Generate a basic distribution analysis focused on data interpretation, no recommendations"""
    try:
        # Extract key data points
        time_period = data["time_period"]
        distributions = data["assayer_distributions"]
        
        # Categorize distributions
        symmetric = [d for d in distributions if "symmetric" in d["shape"]]
        right_skewed = [d for d in distributions if "right-skewed" in d["shape"]]
        left_skewed = [d for d in distributions if "left-skewed" in d["shape"]]
        
        narrow_spread = [d for d in distributions if d["spread"] == "narrow"]
        wide_spread = [d for d in distributions if d["spread"] == "wide"]
        
        # Build a readable analysis
        analysis = f"## Distribution Chart Interpretation for {time_period}\n\n"
        
        # Axis and chart explanation
        analysis += f"**X-axis:** Represents assayer names ordered alphabetically.\n"
        analysis += f"**Box plots:** Each box shows distribution of percentage deviations from benchmark.\n"
        analysis += f"**Box components:** Middle line = median, box edges = 25th and 75th percentiles, whiskers = min/max (excluding outliers), dots = outliers.\n\n"
        
        # Key interpretation points
        analysis += f"### Key Observations\n"
        
        # Spread comparison
        analysis += f"**Spread comparison:** "
        if narrow_spread and wide_spread:
            narrow_names = [d['assayer'] for d in narrow_spread[:2]]
            wide_names = [d['assayer'] for d in wide_spread[:2]]
            analysis += f"{', '.join(narrow_names)} show narrow boxes (high consistency), while "
            analysis += f"{', '.join(wide_names)} show wide boxes (high variability).\n\n"
        elif narrow_spread:
            narrow_names = [d['assayer'] for d in narrow_spread[:3]]
            analysis += f"{', '.join(narrow_names)} show the narrowest boxes, indicating consistent results.\n\n"
        elif wide_spread:
            wide_names = [d['assayer'] for d in wide_spread[:3]]
            analysis += f"{', '.join(wide_names)} show the widest boxes, indicating variable results.\n\n"
            
        # Box position interpretation
        if distributions:
            # Sort by median values
            sorted_by_median = sorted(distributions, key=lambda x: x['median'])
            lowest_median = sorted_by_median[0]
            highest_median = sorted_by_median[-1]
            centered_median = min(distributions, key=lambda x: abs(x['median']))
            
            analysis += f"**Box position:** "
            analysis += f"{highest_median['assayer']}'s box is positioned highest (median: {highest_median['median']}%), "
            analysis += f"indicating tendency toward higher readings than benchmark. "
            analysis += f"{lowest_median['assayer']}'s box is positioned lowest (median: {lowest_median['median']}%), "
            analysis += f"indicating tendency toward lower readings. "
            analysis += f"{centered_median['assayer']} is most centered (median: {centered_median['median']}%).\n\n"
        
        # Distribution shape explanation
        analysis += f"**Shape interpretation:** "
        if right_skewed:
            r_skewed_names = [d['assayer'] for d in right_skewed[:2]]
            analysis += f"{', '.join(r_skewed_names)} show right-skewed distributions (longer upper whiskers), "
            analysis += f"indicating occasional large positive deviations. "
        if left_skewed:
            l_skewed_names = [d['assayer'] for d in left_skewed[:2]]
            analysis += f"{', '.join(l_skewed_names)} show left-skewed distributions (longer lower whiskers), "
            analysis += f"indicating occasional large negative deviations. "
        if symmetric:
            sym_names = [d['assayer'] for d in symmetric[:2]]
            analysis += f"{', '.join(sym_names)} show symmetric distributions (balanced whiskers), "
            analysis += f"indicating random rather than systematic variation."
        analysis += "\n\n"
        
        # Outlier identification if present
        outlier_info = []
        for d in distributions:
            # Consider a simple outlier detection method - determine if max/min is far from Q3/Q1
            iqr = d['iqr']
            if (d['max'] - d['q75']) > 1.5 * iqr or (d['q25'] - d['min']) > 1.5 * iqr:
                outlier_info.append(d['assayer'])
                
        if outlier_info:
            analysis += f"**Outlier detection:** {', '.join(outlier_info[:3])} show outlier points, "
            analysis += f"indicating occasional unusual measurement results.\n\n"
        
        return analysis
        
    except Exception as e:
        return f"Distribution interpretation failed: {str(e)}\n\nPlease check your data and try again."

def generate_recommendation_fallback(data):
    """Generate performance data interpretation instead of recommendations"""
    try:
        # Extract key data points
        time_period = data["time_period"]
        high_bias = data["high_bias_assayers"]
        high_variance = data["high_variance_assayers"]
        low_experience = data["low_experience_assayers"]
        well_performing = data["well_performing_assayers"]
        overall = data["overall_metrics"]
        
        # Build a readable analysis
        analysis = f"## Performance Analysis for {time_period}\n\n"
        
        # Explain what the chart is showing
        analysis += f"This chart aggregates performance metrics for {overall['total_assayers']} assayers "
        analysis += f"with an overall average deviation of {overall['avg_deviation_across_all']}% "
        analysis += f"and average standard deviation of {overall['avg_std_across_all']}%.\n\n"
        
        # Performance categories explanation
        analysis += f"### Performance Categories\n"
        
        # High bias assayers
        if high_bias:
            analysis += f"**Significant bias detected:** "
            bias_names = []
            bias_values = []
            for assayer in high_bias[:3]:
                direction = "higher" if assayer['avg_deviation'] > 0 else "lower"
                bias_names.append(assayer['name'])
                bias_values.append(f"{abs(assayer['avg_deviation'])}% {direction} than benchmark")
            
            analysis += f"{', '.join(bias_names)} consistently report {' and '.join(bias_values)} respectively "
            analysis += f"across their test samples, suggesting possible systematic measurement bias.\n\n"
        
        # High variance assayers
        if high_variance:
            analysis += f"**Significant variability detected:** "
            var_names = [f"{a['name']} (±{a['std_deviation']}%)" for a in high_variance[:3]]
            analysis += f"{', '.join(var_names)} show the highest variability in their measurements, "
            analysis += f"indicating inconsistent testing results compared to peers.\n\n"
        
        # Low experience assayers
        if low_experience:
            analysis += f"**Limited sample assayers:** "
            exp_names = [f"{a['name']} ({a['sample_count']} samples)" for a in low_experience[:3]]
            analysis += f"{', '.join(exp_names)} have tested fewer samples than the median, "
            analysis += f"which may affect the statistical significance of their performance metrics.\n\n"
        
        # Well performing assayers
        if well_performing:
            analysis += f"**High precision performers:** "
            well_names = [f"{a['name']} (±{a['std_deviation']}%, avg: {a['avg_deviation']}%)" for a in well_performing[:3]]
            analysis += f"{', '.join(well_names)} demonstrate both high accuracy (low deviation from benchmark) "
            analysis += f"and high precision (low standard deviation), representing optimal testing performance.\n\n"
        
        # Benchmark comparison summary
        if overall['total_assayers'] > 0:
            # Count assayers above/below/at benchmark
            above_benchmark = len([a for a in high_bias if a['avg_deviation'] > 0])
            below_benchmark = len([a for a in high_bias if a['avg_deviation'] < 0])
            at_benchmark = overall['total_assayers'] - above_benchmark - below_benchmark
            
            analysis += f"### Benchmark Comparison\n"
            analysis += f"Among all assayers: {above_benchmark} tend to report higher values than the benchmark, "
            analysis += f"{below_benchmark} tend to report lower values, and approximately {at_benchmark} "
            analysis += f"report values closely aligned with the benchmark.\n\n"
        
        return analysis
        
    except Exception as e:
        return f"Performance analysis failed: {str(e)}\n\nPlease check your data and try again."