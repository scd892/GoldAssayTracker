import os
import json
import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI
from datetime import datetime, timedelta

# Initialize OpenAI client
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
try:
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
except Exception as e:
    print(f"Error initializing OpenAI client: {str(e)}")
    client = None

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
        
        # Prepare data summary for GPT
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
        
        # Check if OpenAI client is available
        if client is None:
            # Provide a fallback statistical analysis without using the API
            return generate_statistical_analysis(data_summary)
        
        # Prepare the prompt for GPT
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
        
        user_prompt = f"""Here is the gold assay deviation data for {time_period}:
        {json.dumps(data_summary, indent=2)}
        
        Provide a comprehensive analysis of this data.
        """
        
        # Make API call to GPT
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,
            max_tokens=800
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        # Log the error but provide a statistical fallback
        print(f"Error in AI analysis: {str(e)}")
        
        # If we've already calculated the data summary, use it for the fallback
        if 'data_summary' in locals():
            return generate_statistical_analysis(data_summary)
        else:
            return f"An error occurred while analyzing the data: {str(e)}"
            
# Helper function to generate a basic analysis based on statistics when API is unavailable
def generate_statistical_analysis(data):
    """Generate a basic statistical analysis when the AI API is unavailable"""
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
        
        # Build a readable analysis
        analysis = f"## Statistical Analysis for {time_period}\n\n"
        
        # Overall summary
        analysis += f"### Overall Summary\n"
        analysis += f"During {time_period}, {total_samples} samples were analyzed by {num_assayers} assayers. "
        analysis += f"The average percentage deviation was {avg_deviation}%, with a maximum deviation of {max_deviation}%. "
        
        if recent_trend == "improving":
            analysis += f"Recent data shows an improving trend in assayer accuracy.\n\n"
        elif recent_trend == "worsening":
            analysis += f"Recent data shows a concerning trend with increasing deviations.\n\n"
        else:
            analysis += f"Recent results show stable performance with no significant trend changes.\n\n"
        
        # Top and bottom performers
        analysis += f"### Performance Highlights\n"
        analysis += f"**Top performer:** {top_performer['name']} with an average deviation of {top_performer['avg_deviation']}% "
        analysis += f"across {top_performer['samples_tested']} samples and a consistency score of {top_performer['consistency']}.\n\n"
        
        analysis += f"**Needs improvement:** {bottom_performer['name']} with an average deviation of {bottom_performer['avg_deviation']}% "
        analysis += f"across {bottom_performer['samples_tested']} samples and a consistency score of {bottom_performer['consistency']}.\n\n"
        
        # Consistency issues
        if inconsistent_assayers:
            analysis += f"### Consistency Concerns\n"
            analysis += f"The following assayers showed higher than normal variation in their results:\n"
            for assayer in inconsistent_assayers[:3]:  # Limit to top 3
                analysis += f"- {assayer['name']}: standard deviation of {assayer['std_deviation']}% across {assayer['samples_tested']} samples\n"
            analysis += "\n"
        
        # Recommendations
        analysis += f"### Recommendations\n"
        analysis += f"1. Provide additional training to {bottom_performer['name']} to improve accuracy\n"
        if inconsistent_assayers:
            analysis += f"2. Review testing procedures with {inconsistent_assayers[0]['name']} to improve consistency\n"
        analysis += f"3. Consider recognizing {top_performer['name']} for exceptional performance\n"
        analysis += f"4. Implement regular calibration checks for all testing equipment\n"
        
        return analysis
        
    except Exception as e:
        return f"Statistical analysis failed: {str(e)}\n\nPlease check your data and try again."

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
        
        # Prepare data summary for GPT
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
        
        # Check if OpenAI client is available
        if client is None:
            # Provide a fallback heatmap analysis without using the API
            return generate_heatmap_analysis(heatmap_summary)
        
        # Prepare the prompt for GPT
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
        
        user_prompt = f"""Here is data extracted from a heatmap visualization of gold assay deviations for {time_period}:
        {json.dumps(heatmap_summary, indent=2)}
        
        Provide an interpretation of what patterns would be visible in this heatmap visualization.
        """
        
        # Make API call to GPT
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,
            max_tokens=600
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        # Log the error but provide a statistical fallback
        print(f"Error in heatmap analysis: {str(e)}")
        
        # If we've already calculated the data summary, use it for the fallback
        if 'heatmap_summary' in locals():
            return generate_heatmap_analysis(heatmap_summary)
        else:
            return f"An error occurred while analyzing the heatmap: {str(e)}"
            
# Helper function to generate a basic heatmap analysis when API is unavailable
def generate_heatmap_analysis(data):
    """Generate a basic heatmap analysis when the AI API is unavailable"""
    try:
        # Extract key data points
        time_period = data["time_period"]
        total_weeks = data["total_weeks"]
        total_assayers = data["total_assayers"]
        hot_spots = data["hot_spots"]
        consistent_assayers = data["most_consistent_assayers"]
        inconsistent_assayers = data["most_inconsistent_assayers"]
        
        # Build a readable analysis
        analysis = f"## Heatmap Analysis for {time_period}\n\n"
        
        # Overall summary
        analysis += f"### Overview\n"
        analysis += f"The heatmap analysis covers {total_weeks} weeks of data across {total_assayers} assayers. "
        
        # Hotspot analysis
        if hot_spots:
            analysis += f"\n\n### Notable Hotspots\n"
            analysis += f"The heatmap reveals {len(hot_spots)} significant deviation hotspots:\n"
            for spot in hot_spots[:5]:  # Limit to top 5
                analysis += f"- Week {spot['week']}: {spot['assayer']} with {spot['deviation']}% deviation\n"
        else:
            analysis += f"No significant hotspots were detected in the data, suggesting relatively stable performance across all time periods.\n"
        
        # Consistency patterns
        analysis += f"\n### Consistency Patterns\n"
        
        if consistent_assayers:
            analysis += f"**Most consistent assayers:**\n"
            for assayer in consistent_assayers:
                analysis += f"- {assayer['name']} (std dev: {assayer['std_deviation']}%)\n"
            analysis += "\n"
        
        if inconsistent_assayers:
            analysis += f"**Most inconsistent assayers:**\n"
            for assayer in inconsistent_assayers:
                analysis += f"- {assayer['name']} (std dev: {assayer['std_deviation']}%)\n"
        
        # Recommendations
        analysis += f"\n### Recommendations\n"
        analysis += f"1. Monitor weeks with multiple hotspots for potential equipment or procedure issues\n"
        
        if inconsistent_assayers:
            analysis += f"2. Provide additional training to {inconsistent_assayers[0]['name']} to improve consistency\n"
        
        if consistent_assayers:
            analysis += f"3. Consider {consistent_assayers[0]['name']}'s methods as a potential best practice template\n"
        
        analysis += f"4. Review the testing methodology during weeks with unusual patterns across multiple assayers\n"
        
        return analysis
        
    except Exception as e:
        return f"Heatmap analysis failed: {str(e)}\n\nPlease check your data and try again."

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
        
        # Prepare data summary for GPT
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
        
        # Prepare the prompt for GPT
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
        
        user_prompt = f"""Here is data extracted from a {ma_window}-day moving average trend chart of gold assay deviations for {time_period}:
        {json.dumps(trend_summary, indent=2)}
        
        Provide an interpretation of what patterns would be visible in this trend chart visualization.
        """
        
        # Make API call to GPT
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,
            max_tokens=600
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
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
        
        # Prepare data summary for GPT
        distribution_summary = {
            "time_period": time_period,
            "assayer_distributions": distribution_shapes,
            "detailed_stats": distribution_stats.drop(['q25', 'q75'], axis=1).to_dict(orient='records')
        }
        
        # Prepare the prompt for GPT
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
        
        user_prompt = f"""Here is data extracted from a distribution chart of gold assay deviations for {time_period}:
        {json.dumps(distribution_summary, indent=2)}
        
        Provide an interpretation of what patterns would be visible in this distribution chart visualization.
        """
        
        # Make API call to GPT
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,
            max_tokens=600
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
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
        
        # Prepare data summary for GPT
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
        
        # Prepare the prompt for GPT
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
        
        user_prompt = f"""Here is performance data for gold assayers over {time_period}:
        {json.dumps(performance_summary, indent=2)}
        
        Provide specific, actionable recommendations for improving laboratory performance.
        """
        
        # Make API call to GPT
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,
            max_tokens=750
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"An error occurred while generating recommendations: {str(e)}"