import streamlit as st
import pandas as pd
from datetime import datetime
import base64
import io
from PIL import Image
import sqlite3
import time
import random

from database import (
    get_assayers, 
    add_assayer, 
    update_assayer, 
    delete_assayer, 
    get_assayer_profile, 
    get_assayer_profile_with_stats,
    get_all_assayer_profiles
)
from auth import require_permission, display_access_denied, check_page_access

# Import the chat component
from simple_chat import display_chat_widget

# Page config
st.set_page_config(page_title="Assayer Profiles", page_icon="👤", layout="wide")

# Check authentication and permissions
if not check_page_access("Assayer_Profiles"):
    display_access_denied()
    st.stop()

# Display the chat widget
display_chat_widget()

# Custom styling
st.markdown("""
<style>
    .profile-card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        position: relative;
    }
    .profile-header {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
    }
    .profile-image {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        object-fit: cover;
        margin-right: 15px;
        border: 3px solid #D4AF37;
    }
    .profile-name {
        font-size: 1.5rem;
        font-weight: bold;
        margin: 0;
    }
    .profile-title {
        color: #777;
        margin: 0;
    }
    .profile-details {
        display: flex;
        flex-wrap: wrap;
    }
    .profile-detail {
        flex: 1;
        min-width: 200px;
        margin-bottom: 10px;
    }
    .detail-label {
        font-weight: bold;
        color: #555;
    }
    .detail-value {
        color: #333;
    }
    .benchmark-badge {
        position: absolute;
        top: 10px;
        right: 10px;
        background-color: #D4AF37;
        color: white;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .edit-button {
        position: absolute;
        top: 10px;
        right: 120px;
        background-color: #4682B4;
        color: white;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# Page header
st.title("📊 Assayer Profiles")
st.markdown("View and manage detailed profiles for all laboratory assayers")

# Function to convert image to base64
def image_to_base64(img_file):
    if img_file is not None:
        # Open the image using PIL
        img = Image.open(img_file)
        
        # Resize image to a reasonable size for storage
        max_size = (300, 300)
        img.thumbnail(max_size)
        
        # Convert to base64
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
    return ""

# Function to get profile image HTML
def get_profile_image_html(profile_picture):
    if profile_picture:
        return f'<img src="data:image/jpeg;base64,{profile_picture}" class="profile-image" />'
    else:
        # Default image if none is provided
        return '<div class="profile-image" style="background-color: #ccc; display: flex; align-items: center; justify-content: center;"><span style="font-size: 2rem;">👤</span></div>'

# Function to calculate years of experience
def get_years_experience(joining_date):
    if joining_date is None or pd.isna(joining_date):
        return "Unknown"
    
    # Convert to datetime if it's a string
    if isinstance(joining_date, str):
        try:
            joining_date = datetime.strptime(joining_date, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return "Unknown"
    
    try:
        # Calculate years
        years = (datetime.now() - joining_date).days / 365.25
        if years < 0:  # Handle future dates
            return "Unknown"
        return f"{years:.1f} years"
    except (TypeError, ValueError):
        return "Unknown"

# Function to display a profile card
def display_profile_card(profile, is_benchmark=False):
    with st.container():
        # Extract profile data with defaults for missing values
        assayer_id = profile.get('assayer_id', 0)
        name = profile.get('name', 'Unknown')
        employee_id = profile.get('employee_id', 'N/A')
        joining_date = profile.get('joining_date', None)
        profile_picture = profile.get('profile_picture', '')
        years_experience = profile.get('years_experience', None)
        
        # Handle work experience with proper default
        work_experience = profile.get('work_experience', '')
        if not work_experience or pd.isna(work_experience):
            work_experience = 'No work experience information available.'
            
        # Get years experience either from profile or calculate it
        if years_experience is not None and not pd.isna(years_experience):
            years_exp = f"{years_experience} years"
        else:
            years_exp = get_years_experience(joining_date)
        
        # Format joining date for display with careful handling of NaT values
        joining_date_display = "Unknown"
        if joining_date is not None and pd.notna(joining_date):
            try:
                joining_date_display = joining_date.strftime('%B %d, %Y')
            except (ValueError, AttributeError):
                joining_date_display = "Unknown"
        
        # Performance metrics if available
        avg_deviation = profile.get('avg_deviation', None)
        avg_deviation_display = f"{avg_deviation:.2f} ppt" if avg_deviation is not None and not pd.isna(avg_deviation) else "N/A"
        
        sample_count = profile.get('sample_count', 0)
        
        # Create a card with border and padding
        st.markdown("""
        <style>
        .card {
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: #f9f9f9;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: relative;
        }
        .profile-metrics {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 10px;
        }
        .metric-item {
            flex: 1 1 45%;
            background-color: #f0f0f0;
            padding: 8px;
            border-radius: 4px;
            font-size: 0.9em;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Start card
        st.markdown('<div class="card">', unsafe_allow_html=True)
        
        # Profile header with name and badge
        if is_benchmark:
            st.markdown("**🌟 Benchmark Assayer**")
            
        # Display profile picture and basic info
        st.subheader(name)
        st.caption(f"Employee ID: {employee_id}")
        
        if profile_picture:
            st.image(f"data:image/jpeg;base64,{profile_picture}", width=150)
        
        # Display profile metrics using HTML/CSS flexbox instead of columns
        st.markdown("""<div class="profile-metrics">
            <div class="metric-item"><strong>Joining Date:</strong> {0}</div>
            <div class="metric-item"><strong>Experience:</strong> {1}</div>
            <div class="metric-item"><strong>Samples Tested:</strong> {2}</div>
            <div class="metric-item"><strong>Avg Deviation:</strong> {3}</div>
        </div>""".format(
            joining_date_display,
            years_exp,
            sample_count,
            avg_deviation_display
        ), unsafe_allow_html=True)
        
        # Display work experience
        st.markdown("**Work Experience:**")
        st.markdown(work_experience)
        
        # Add edit button
        if st.button("Edit Profile", key=f"edit-{assayer_id}"):
            st.session_state.editing_assayer_id = assayer_id
            st.session_state.show_edit_form = True
            st.rerun()
            
        # End card
        st.markdown('</div>', unsafe_allow_html=True)

# Main/Sidebar layout
tab1, tab2 = st.tabs(["Assayer Profiles", "Manage Assayers"])

# Get current benchmark assayer
conn = sqlite3.connect('gold_assay.db')
benchmark_df = pd.read_sql("""
    SELECT b.assayer_id
    FROM benchmark_assayers b
    WHERE b.is_active = 1
    LIMIT 1
""", conn)
conn.close()

benchmark_id = benchmark_df.iloc[0]['assayer_id'] if not benchmark_df.empty else None

# Initialize session state
if 'show_edit_form' not in st.session_state:
    st.session_state.show_edit_form = False
    
if 'editing_assayer_id' not in st.session_state:
    st.session_state.editing_assayer_id = None

# Profiles tab
with tab1:
    # Get all assayer profiles with stats
    all_profiles = get_all_assayer_profiles()
    
    if all_profiles.empty:
        st.info("No assayers have been added yet. Use the 'Manage Assayers' tab to add assayers.")
    else:
        # Convert joining_date to datetime if needed
        if 'joining_date' in all_profiles.columns:
            all_profiles['joining_date'] = pd.to_datetime(all_profiles['joining_date'])
        
        # Get detailed profiles with stats for each assayer
        detailed_profiles = []
        for _, row in all_profiles.iterrows():
            profile = get_assayer_profile_with_stats(row['assayer_id'])
            if profile is not None:
                detailed_profiles.append(profile)
        
        # Display profiles in a grid
        if detailed_profiles:
            col1, col2 = st.columns(2)
            
            # Shuffle profiles but keep benchmark first
            if benchmark_id is not None:
                benchmark_profile = None
                other_profiles = []
                
                for profile in detailed_profiles:
                    if profile['assayer_id'] == benchmark_id:
                        benchmark_profile = profile
                    else:
                        other_profiles.append(profile)
                
                # Shuffle the non-benchmark profiles
                random.shuffle(other_profiles)
                
                # Display benchmark profile at the top (full width)
                if benchmark_profile is not None:
                    st.markdown("#### 🌟 Benchmark Assayer")
                    display_profile_card(benchmark_profile, is_benchmark=True)
                    st.markdown("#### Other Assayers")
                
                # Display other profiles in two columns
                for i, profile in enumerate(other_profiles):
                    with col1 if i % 2 == 0 else col2:
                        display_profile_card(profile)
            else:
                # No benchmark set, just display all profiles
                random.shuffle(detailed_profiles)
                for i, profile in enumerate(detailed_profiles):
                    with col1 if i % 2 == 0 else col2:
                        display_profile_card(profile)
        else:
            st.warning("Failed to load detailed profiles. Database may be corrupted.")

# Manage Assayers tab
with tab2:
    # Edit assayer form (shown conditionally)
    if st.session_state.show_edit_form and st.session_state.editing_assayer_id is not None:
        st.subheader("Edit Assayer Profile")
        
        # Get the assayer's current data
        current_profile = get_assayer_profile(st.session_state.editing_assayer_id)
        
        if current_profile is not None:
            with st.form(key="edit_assayer_form"):
                name = st.text_input("Name", value=current_profile['name'])
                employee_id = st.text_input("Employee ID", value=current_profile['employee_id'])
                
                # Format the date for date input
                current_date = current_profile['joining_date'].date() if pd.notna(current_profile['joining_date']) else datetime.now().date()
                joining_date = st.date_input("Joining Date", value=current_date)
                
                # Display current profile picture if available
                if current_profile['profile_picture']:
                    st.markdown("Current Profile Picture:")
                    st.markdown(f"<img src='data:image/jpeg;base64,{current_profile['profile_picture']}' style='max-width:150px; max-height:150px;'>", unsafe_allow_html=True)
                
                new_picture = st.file_uploader("Update Profile Picture (optional)", type=['jpg', 'jpeg', 'png'])
                
                work_experience = st.text_area("Work Experience", value=current_profile.get('work_experience', ''), height=150)
                
                update_submitted = st.form_submit_button("Update Assayer")
                cancel_button = st.form_submit_button("Cancel")
                
                if update_submitted:
                    # Process the form data
                    joining_datetime = datetime.combine(joining_date, datetime.min.time())
                    
                    # Convert new picture to base64 if provided, otherwise keep existing
                    if new_picture is not None:
                        profile_picture = image_to_base64(new_picture)
                    else:
                        profile_picture = current_profile['profile_picture']
                    
                    # Update the assayer in the database
                    success = update_assayer(
                        st.session_state.editing_assayer_id,
                        name,
                        employee_id,
                        joining_datetime,
                        profile_picture,
                        work_experience
                    )
                    
                    if success:
                        st.success(f"Assayer '{name}' updated successfully!")
                        time.sleep(1)  # Short delay
                        st.session_state.show_edit_form = False
                        st.session_state.editing_assayer_id = None
                        st.rerun()
                    else:
                        st.error("Failed to update assayer. Employee ID may already be in use.")
                
                if cancel_button:
                    st.session_state.show_edit_form = False
                    st.session_state.editing_assayer_id = None
                    st.rerun()
        else:
            st.error("Could not find the assayer profile to edit.")
            st.session_state.show_edit_form = False
            st.session_state.editing_assayer_id = None
    
    # If not in edit mode, show the add new assayer form
    else:
        st.subheader("Add New Assayer")
        
        with st.form(key="add_assayer_form"):
            name = st.text_input("Name")
            employee_id = st.text_input("Employee ID")
            joining_date = st.date_input("Joining Date", value=datetime.now())
            profile_picture = st.file_uploader("Profile Picture", type=['jpg', 'jpeg', 'png'])
            work_experience = st.text_area("Work Experience", height=150)
            
            submitted = st.form_submit_button("Add Assayer")
            
            if submitted:
                # Process the form data
                joining_datetime = datetime.combine(joining_date, datetime.min.time())
                
                # Convert picture to base64
                picture_base64 = image_to_base64(profile_picture) if profile_picture else ""
                
                # Add assayer to database
                success = add_assayer(
                    name,
                    employee_id,
                    joining_datetime, 
                    picture_base64, 
                    work_experience
                )
                
                if success:
                    st.success(f"Assayer '{name}' added successfully!")
                    # Delay briefly to show success message
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to add assayer. Employee ID may already be in use.")

# Footer with attribution
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 0.8em;'>"
    "Developed by Algo Digital Solutions, powered by Mureri Technologies<br>"
    "All Rights Reserved"
    "</div>",
    unsafe_allow_html=True
)