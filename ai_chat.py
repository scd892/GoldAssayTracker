import os
import pandas as pd
from typing import Dict, List

# Initialize AI models
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Only import and initialize if API keys are available
deepseek = None
openai_client = None
anthropic_client = None

if DEEPSEEK_API_KEY:
    from deepseek_ai import DeepSeekAI
    deepseek = DeepSeekAI(api_key=DEEPSEEK_API_KEY)

if OPENAI_API_KEY:
    from openai import OpenAI
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    
if ANTHROPIC_API_KEY:
    from anthropic import Anthropic
    anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

def answer_data_query(query: str, deviations_df: pd.DataFrame) -> str:
    """
    Answer user queries about the deviation data and assayer profiles using AI
    
    Args:
        query: The user's question
        deviations_df: DataFrame containing deviation data
        
    Returns:
        str: AI-generated answer
    """
    # Check if query is about assayer profiles
    if any(keyword in query.lower() for keyword in ['when did', 'join', 'experience', 'profile', 'who is', 'work history']):
        return answer_profile_query(query)
        
    try:
        # Fallback to statistical analysis if all APIs are unavailable
        if (DEEPSEEK_API_KEY is None or not DEEPSEEK_API_KEY) and \
           (OPENAI_API_KEY is None or not OPENAI_API_KEY) and \
           (ANTHROPIC_API_KEY is None or not ANTHROPIC_API_KEY):
            return generate_data_answer_fallback(query, deviations_df)
        
        # Prepare data summary
        data_summary = {
            "total_samples": len(deviations_df),
            "unique_samples": deviations_df['sample_id'].nunique(),
            "assayer_count": deviations_df['assayer_name'].nunique(),
            "date_range": f"{deviations_df['test_date'].min().strftime('%Y-%m-%d')} to {deviations_df['test_date'].max().strftime('%Y-%m-%d')}",
            "assayer_list": deviations_df['assayer_name'].unique().tolist(),
        }
        
        # Calculate key metrics for each assayer
        assayer_metrics = {}
        for assayer in data_summary["assayer_list"]:
            assayer_data = deviations_df[deviations_df['assayer_name'] == assayer]
            assayer_metrics[assayer] = {
                "sample_count": len(assayer_data),
                "avg_deviation": assayer_data['percentage_deviation'].mean(),
                "max_deviation": assayer_data['percentage_deviation'].max(),
                "min_deviation": assayer_data['percentage_deviation'].min(),
                "std_deviation": assayer_data['percentage_deviation'].std()
            }
        
        # Prepare overall metrics
        metrics = {
            "avg_deviation": deviations_df['percentage_deviation'].mean(),
            "max_deviation": deviations_df['percentage_deviation'].max(),
            "min_deviation": deviations_df['percentage_deviation'].min(),
            "std_deviation": deviations_df['percentage_deviation'].std()
        }
        
        # Find assayers with metrics matching specific criteria
        best_assayer = min(assayer_metrics.items(), key=lambda x: abs(x[1]['avg_deviation']))
        worst_assayer = max(assayer_metrics.items(), key=lambda x: abs(x[1]['avg_deviation']))
        most_consistent = min(assayer_metrics.items(), key=lambda x: x[1]['std_deviation'])
        least_consistent = max(assayer_metrics.items(), key=lambda x: x[1]['std_deviation'])
        
        # Count assayers with deviations above/below thresholds
        above_01 = sum(1 for _, v in assayer_metrics.items() if abs(v['avg_deviation']) > 0.1)
        above_05 = sum(1 for _, v in assayer_metrics.items() if abs(v['avg_deviation']) > 0.5)
        above_1 = sum(1 for _, v in assayer_metrics.items() if abs(v['avg_deviation']) > 1.0)
        
        # Create a context for the AI with all this information
        context = f"""
You are an AI assistant for a gold testing laboratory. The data shows deviations of assayers from a benchmark assayer.
Below is information about the current dataset:

DATA SUMMARY:
- Total samples: {data_summary['total_samples']}
- Unique sample IDs: {data_summary['unique_samples']}
- Number of assayers: {data_summary['assayer_count']}
- Date range: {data_summary['date_range']}

OVERALL METRICS:
- Average percentage deviation: {metrics['avg_deviation']:.2f}%
- Maximum percentage deviation: {metrics['max_deviation']:.2f}%
- Minimum percentage deviation: {metrics['min_deviation']:.2f}%
- Standard deviation: {metrics['std_deviation']:.2f}%

KEY FINDINGS:
- Assayer with lowest average deviation: {best_assayer[0]} ({best_assayer[1]['avg_deviation']:.2f}%)
- Assayer with highest average deviation: {worst_assayer[0]} ({worst_assayer[1]['avg_deviation']:.2f}%)
- Most consistent assayer: {most_consistent[0]} (std dev: {most_consistent[1]['std_deviation']:.2f}%)
- Least consistent assayer: {least_consistent[0]} (std dev: {least_consistent[1]['std_deviation']:.2f}%)
- Number of assayers with absolute deviation > 0.1%: {above_01}
- Number of assayers with absolute deviation > 0.5%: {above_05}
- Number of assayers with absolute deviation > 1.0%: {above_1}

ASSAYER METRICS:
"""
        # Add individual assayer metrics to the context
        for assayer, metrics in assayer_metrics.items():
            context += f"- {assayer}: samples={metrics['sample_count']}, avg_dev={metrics['avg_deviation']:.2f}%, std_dev={metrics['std_deviation']:.2f}%\n"
        
        # Append the user query to the context
        prompt = f"{context}\n\nUser question: {query}\n\nAnswer:"
        system_prompt = "You are a data analysis assistant for a gold testing laboratory."
        
        # Try OpenAI first if available
        if openai_client is not None:
            try:
                response = openai_client.chat.completions.create(
                    # The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
                    # do not change this unless explicitly requested by the user
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.2
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"OpenAI API error: {str(e)}")
                # If OpenAI fails, try other options
        
        # Try Anthropic if available and OpenAI failed or isn't available
        if anthropic_client is not None:
            try:
                # The newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                # do not change this unless explicitly requested by the user
                response = anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=500,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text
            except Exception as e:
                print(f"Anthropic API error: {str(e)}")
                # If Anthropic fails, try DeepSeek next if available
                
        # Try DeepSeek if available and other options failed or aren't available
        if deepseek is not None:
            try:
                response = deepseek.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.2
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"DeepSeek API error: {str(e)}")
                # If all APIs fail, fall back to statistical analysis
                
        # If we reach here, all API attempts failed
        return generate_data_answer_fallback(query, deviations_df)
        
    except Exception as e:
        return f"Sorry, I couldn't answer that question: {str(e)}\n\nPlease try a different question or check your data."


def answer_profile_query(query: str) -> str:
    """
    Answer queries about assayer profiles
    
    Args:
        query: The user's question about assayer profiles
        
    Returns:
        str: Answer about assayer profiles
    """
    from database import get_all_assayer_profiles, get_assayer_profile_with_stats
    import re
    
    try:
        # Get all assayer profiles
        all_profiles = get_all_assayer_profiles()
        
        if all_profiles.empty:
            return "No assayer profiles are available in the database."
        
        # Extract assayer name from the query
        assayer_name = None
        
        # Check for specific assayer mention
        name_match = re.search(r"(?:about|of|for|did|when|is|work)\s+([A-Za-z\s.]+?)[\s?.,]", query)
        if name_match:
            potential_name = name_match.group(1).strip()
            # Find the closest match in assayer names
            for idx, row in all_profiles.iterrows():
                if potential_name.lower() in row['name'].lower():
                    assayer_name = row['name']
                    assayer_id = row['assayer_id']
                    break
        
        # If we found an assayer, get their detailed profile
        if assayer_name:
            profile = get_assayer_profile_with_stats(assayer_id)
            
            # Format joining date
            joining_date = profile['joining_date'].strftime('%B %d, %Y') if pd.notna(profile['joining_date']) else "Unknown"
            
            # Calculate years of experience
            years_exp = profile.get('years_experience', None)
            years_exp_str = f"{years_exp:.1f} years" if years_exp is not None else "Unknown"
            
            # General profile info
            if "when did" in query.lower() or "join" in query.lower():
                return f"{assayer_name} joined the laboratory on {joining_date} ({years_exp_str} of experience)."
            
            elif "experience" in query.lower() or "work history" in query.lower():
                work_exp = profile.get('work_experience', '')
                if work_exp:
                    return f"{assayer_name}'s work experience: {work_exp}"
                else:
                    return f"No detailed work history is available for {assayer_name}."
            
            elif "who is" in query.lower() or "profile" in query.lower():
                work_exp = profile.get('work_experience', '')
                exp_info = f" Their work experience includes: {work_exp}" if work_exp else ""
                
                # Include performance metrics if available
                perf_info = ""
                if 'avg_deviation' in profile and pd.notna(profile['avg_deviation']):
                    perf_info = f" Their average deviation is {profile['avg_deviation']:.2f} ppt."
                
                return f"{assayer_name} is a laboratory assayer who joined on {joining_date} ({years_exp_str} of experience).{exp_info}{perf_info}"
            
            else:
                # General profile summary
                return f"{assayer_name} is an assayer who joined the laboratory on {joining_date} and has {years_exp_str} of experience."
        
        else:
            # General information about all assayers if no specific one is mentioned
            total_assayers = len(all_profiles)
            avg_exp = all_profiles['years_experience'].mean() if 'years_experience' in all_profiles.columns else None
            
            if "how many" in query.lower() and "assayer" in query.lower():
                return f"There are {total_assayers} assayers in the database."
                
            elif "experience" in query.lower():
                if avg_exp:
                    return f"The average work experience of assayers is {avg_exp:.1f} years."
                else:
                    return "Work experience data is not available for the assayers."
                    
            elif "join" in query.lower() or "when" in query.lower():
                # Find the most recent and oldest assayers
                if 'joining_date' in all_profiles.columns:
                    newest = all_profiles.loc[all_profiles['joining_date'].idxmax()]
                    oldest = all_profiles.loc[all_profiles['joining_date'].idxmin()]
                    return f"The most recent assayer to join is {newest['name']} on {newest['joining_date'].strftime('%B %d, %Y')}. The longest-serving assayer is {oldest['name']} who joined on {oldest['joining_date'].strftime('%B %d, %Y')}."
                else:
                    return "Joining date information is not available for the assayers."
            
            else:
                # List all assayers with their experience
                assayer_list = "\n".join([f"- {row['name']}: {row.get('years_experience', 'Unknown'):.1f} years experience" 
                                         if 'years_experience' in row and pd.notna(row['years_experience']) 
                                         else f"- {row['name']}: Experience unknown" 
                                         for _, row in all_profiles.iterrows()])
                
                return f"Here are all {total_assayers} assayers in the laboratory:\n{assayer_list}"
                
    except Exception as e:
        return f"I couldn't process that profile question: {str(e)}. Please check if assayer profiles are properly set up in the database."


def generate_data_answer_fallback(query: str, deviations_df: pd.DataFrame) -> str:
    """Generate basic data answers when the AI API is unavailable"""
    try:
        # Simple keyword-based responses for common questions
        query = query.lower()
        
        # Calculate key metrics
        assayer_stats = deviations_df.groupby('assayer_name')['percentage_deviation'].agg(['mean', 'std', 'count']).reset_index()
        assayer_stats.columns = ['assayer_name', 'avg_deviation', 'std_deviation', 'sample_count']
        
        # Find best/worst assayers
        best_assayer = assayer_stats.iloc[assayer_stats['avg_deviation'].abs().idxmin()]
        worst_assayer = assayer_stats.iloc[assayer_stats['avg_deviation'].abs().idxmax()]
        most_consistent = assayer_stats.iloc[assayer_stats['std_deviation'].idxmin()]
        
        # Count assayers above thresholds
        above_01 = sum(assayer_stats['avg_deviation'].abs() > 0.1)
        above_05 = sum(assayer_stats['avg_deviation'].abs() > 0.5)
        above_1 = sum(assayer_stats['avg_deviation'].abs() > 1.0)
        
        # Keyword-based responses
        if "minimum" in query and "deviation" in query or "lowest" in query and "deviation" in query:
            return f"The assayer with the minimum deviation is {best_assayer['assayer_name']} with an average deviation of {best_assayer['avg_deviation']:.2f}%."
        
        elif "maximum" in query and "deviation" in query or "highest" in query and "deviation" in query:
            return f"The assayer with the maximum deviation is {worst_assayer['assayer_name']} with an average deviation of {worst_assayer['avg_deviation']:.2f}%."
        
        elif "consistent" in query:
            return f"The most consistent assayer is {most_consistent['assayer_name']} with a standard deviation of {most_consistent['std_deviation']:.2f}%."
        
        elif "above 0.1" in query:
            return f"There are {above_01} assayers with absolute deviation above 0.1%."
        
        elif "above 0.5" in query:
            return f"There are {above_05} assayers with absolute deviation above 0.5%."
            
        elif "above 1" in query:
            return f"There are {above_1} assayers with absolute deviation above 1.0%."
            
        elif "how many" in query and "assayer" in query:
            return f"There are {assayer_stats.shape[0]} active assayers in the current dataset."
            
        elif "total" in query and "sample" in query:
            return f"There are {deviations_df.shape[0]} total samples in the current dataset."
            
        else:
            return "I'm not sure how to answer that question. Please try asking about minimum/maximum deviations, consistency, or the number of assayers above specific thresholds."
            
    except Exception as e:
        return f"I couldn't process that question: {str(e)}. Please check your data or try a different question."