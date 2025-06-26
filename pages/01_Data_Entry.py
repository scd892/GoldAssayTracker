import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import add_assayer, add_assay_result, get_assayers, update_assayer, delete_assayer
from database import get_assay_result, update_assay_result, delete_assay_result
from database_interlab import init_interlab_db, add_external_lab, get_external_labs
from database_interlab import update_external_lab, delete_external_lab, add_interlab_result
from database_interlab import get_interlab_results
from database_trainee import init_trainee_db, add_trainee, get_trainees, add_reference_material
from database_trainee import get_reference_materials, add_trainee_evaluation, get_trainee_evaluations
from auth import require_permission, display_access_denied, check_page_access

# Initialize the database tables
init_interlab_db()
init_trainee_db()

st.set_page_config(page_title="Data Entry", page_icon="📋", layout="wide")

# Check authentication and permissions
if not check_page_access("Data_Entry"):
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
    
    .form-container {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid rgba(212, 175, 55, 0.2);
    }
    
    .entry-header {
        font-size: 1.2rem;
        color: #D4AF37;
        margin-bottom: 20px;
        font-weight: 500;
    }
    
    .small-input {
        max-width: 100px;
    }
    
    /* Custom styling for tabs */
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
    
    /* Remove number input spinners/arrows completely */
    .stNumberInput > div > div > input::-webkit-outer-spin-button,
    .stNumberInput > div > div > input::-webkit-inner-spin-button {
        -webkit-appearance: none;
        margin: 0;
        display: none;
    }
    
    .stNumberInput > div > div > input[type=number] {
        -moz-appearance: textfield;
    }
    
    /* Hide the step buttons in number inputs */
    .stNumberInput button {
        display: none !important;
    }
    
    /* Ensure no spinner controls are visible */
    input[type="number"] {
        -webkit-appearance: textfield;
        -moz-appearance: textfield;
        appearance: textfield;
    }
    
    input[type="number"]::-webkit-inner-spin-button,
    input[type="number"]::-webkit-outer-spin-button {
        -webkit-appearance: none;
        margin: 0;
        display: none;
    }
    
    /* Enable tab navigation through inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div {
        tab-index: auto;
    }
</style>
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Add Enter key navigation for batch entry form
    function addEnterKeyNavigation() {
        const inputs = document.querySelectorAll('input[type="text"], input[type="number"], select');
        inputs.forEach((input, index) => {
            input.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const nextIndex = index + 1;
                    if (nextIndex < inputs.length) {
                        inputs[nextIndex].focus();
                    }
                }
            });
        });
    }
    
    // Run navigation setup after a small delay to ensure elements are loaded
    setTimeout(addEnterKeyNavigation, 1000);
    
    // Re-run when new content is added (for dynamic forms)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length > 0) {
                setTimeout(addEnterKeyNavigation, 500);
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});
</script>
""", unsafe_allow_html=True)

# Main header
st.markdown("<h1 class='main-header'>Data Entry & Management</h1>", unsafe_allow_html=True)

# Create tabs for the different sections
tab1, tab2, tab3, tab4 = st.tabs(["Assayer Management", "Assay Results", "Inter-Lab Data Entry", "Trainee Evaluation"])

# Assayer Management Tab
with tab1:
    st.markdown("<h2 class='sub-header'>Assayer Management</h2>", unsafe_allow_html=True)
    
    # Create two columns for adding new assayers and viewing existing ones
    col1, col2 = st.columns([1, 1])
    
    # Left column: Add new assayer form
    with col1:
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        st.markdown("<p class='entry-header'>📝 Add New Assayer</p>", unsafe_allow_html=True)
        
        with st.form("add_assayer_form"):
            assayer_name = st.text_input("Assayer Name", help="Enter the full name of the assayer")
            employee_id = st.text_input("Employee ID", help="Enter a unique employee ID")
            joining_date = st.date_input("Joining Date", value=datetime.now(), help="When did this assayer join?")
            
            # Optional fields
            st.markdown("##### Additional Information (Optional)")
            profile_picture = st.text_input("Profile Picture URL", help="Enter a URL to the assayer's profile picture (if available)")
            work_experience = st.text_area("Work Experience & Qualifications", help="Enter details about the assayer's background")
            
            submitted = st.form_submit_button("Add Assayer")
            
            if submitted:
                if assayer_name and employee_id:
                    # Convert joining_date to string in YYYY-MM-DD format
                    joining_date_str = joining_date.strftime('%Y-%m-%d')
                    
                    # Add the assayer to the database
                    success = add_assayer(
                        name=assayer_name,
                        employee_id=employee_id,
                        joining_date=joining_date_str,
                        profile_picture=profile_picture,
                        work_experience=work_experience
                    )
                    
                    if success:
                        st.success(f"✅ Successfully added assayer: {assayer_name}")
                    else:
                        st.error(f"❌ Failed to add assayer. Employee ID may already exist.")
                else:
                    st.warning("⚠️ Please enter both Assayer Name and Employee ID.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Right column: View and manage existing assayers
    with col2:
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        st.markdown("<p class='entry-header'>👥 Existing Assayers</p>", unsafe_allow_html=True)
        
        # Get all assayers from the database
        assayers = get_assayers()
        
        if not assayers.empty:
            # Display assayers data in a table
            st.dataframe(assayers[['name', 'employee_id', 'joining_date']], use_container_width=True)
            
            # Create two tabs for edit and delete
            edit_tab, delete_tab = st.tabs(["Edit Assayer", "Delete Assayer"])
            
            # Edit tab - Individual assayer editing
            with edit_tab:
                # Create a dictionary mapping display names to assayer IDs
                assayer_options = {f"{row['name']} ({row['employee_id']})": row['assayer_id'] for _, row in assayers.iterrows()}
                
                if assayer_options:
                    selected_assayer_label = st.selectbox(
                        "Select Assayer to Edit",
                        options=list(assayer_options.keys())
                    )
                    
                    # Get the assayer_id from the selection
                    assayer_id = assayer_options[selected_assayer_label]
                    
                    # Extract information for the selected assayer
                    selected_assayer = assayers[assayers['assayer_id'] == assayer_id].iloc[0]
                    
                    with st.form("edit_assayer_form"):
                        edit_name = st.text_input("Assayer Name", value=selected_assayer['name'])
                        edit_employee_id = st.text_input("Employee ID", value=selected_assayer['employee_id'])
                        
                        # Parse the joining date string to a datetime object
                        joining_date_val = pd.to_datetime(selected_assayer['joining_date']).date() if pd.notna(selected_assayer['joining_date']) else datetime.now().date()
                        edit_joining_date = st.date_input("Joining Date", value=joining_date_val)
                        
                        # Optional fields
                        st.markdown("##### Additional Information (Optional)")
                        edit_profile_picture = st.text_input(
                            "Profile Picture URL", 
                            value=selected_assayer['profile_picture'] if 'profile_picture' in selected_assayer and pd.notna(selected_assayer['profile_picture']) else ""
                        )
                        edit_work_experience = st.text_area(
                            "Work Experience & Qualifications", 
                            value=selected_assayer['work_experience'] if 'work_experience' in selected_assayer and pd.notna(selected_assayer['work_experience']) else ""
                        )
                        
                        update_submitted = st.form_submit_button("Update Assayer")
                        
                        if update_submitted:
                            if edit_name and edit_employee_id:
                                # Convert joining_date to string in YYYY-MM-DD format
                                edit_joining_date_str = edit_joining_date.strftime('%Y-%m-%d')
                                
                                # Update the assayer in the database
                                success = update_assayer(
                                    assayer_id=assayer_id,
                                    name=edit_name,
                                    employee_id=edit_employee_id,
                                    joining_date=edit_joining_date_str,
                                    profile_picture=edit_profile_picture,
                                    work_experience=edit_work_experience
                                )
                                
                                if success:
                                    st.success(f"✅ Successfully updated assayer: {edit_name}")
                                    # Force reloading the page to see the updated data
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to update assayer. Employee ID may already exist.")
                            else:
                                st.warning("⚠️ Please enter both Assayer Name and Employee ID.")
                else:
                    st.info("No assayers available to edit.")
            
            # Delete tab
            with delete_tab:
                st.warning("⚠️ This action will deactivate the selected assayer but preserve their historical data.")
                
                # Create a dictionary mapping display names to assayer IDs for deletion
                assayer_options = {f"{row['name']} ({row['employee_id']})": row['assayer_id'] for _, row in assayers.iterrows()}
                
                if assayer_options:
                    # Initialize session state variables if they don't exist
                    if 'delete_assayer_confirmed' not in st.session_state:
                        st.session_state.delete_assayer_confirmed = False
                    if 'delete_assayer_status' not in st.session_state:
                        st.session_state.delete_assayer_status = None
                    if 'delete_assayer_message' not in st.session_state:
                        st.session_state.delete_assayer_message = ""
                    
                    # Function to handle delete confirmation
                    def toggle_assayer_delete_confirmation():
                        st.session_state.delete_assayer_confirmed = not st.session_state.delete_assayer_confirmed
                    
                    # Function to handle delete operation
                    def delete_selected_assayer():
                        assayer_id = assayer_options[st.session_state.delete_assayer_selection]
                        success, message = delete_assayer(assayer_id)
                        st.session_state.delete_assayer_status = success
                        st.session_state.delete_assayer_message = message
                    
                    # Store the selected assayer in session state
                    selected_assayer_label = st.selectbox(
                        "Select Assayer to Delete",
                        options=list(assayer_options.keys()),
                        key="delete_assayer_selection",
                        on_change=lambda: setattr(st.session_state, 'delete_assayer_confirmed', False)
                    )
                    
                    # Add a confirmation checkbox with callback
                    confirm_delete = st.checkbox(
                        "I understand this action cannot be undone", 
                        value=st.session_state.delete_assayer_confirmed,
                        key="confirm_delete_assayer",
                        on_change=toggle_assayer_delete_confirmation
                    )
                    
                    # Display delete button
                    if st.button("Delete Assayer", 
                                disabled=not st.session_state.delete_assayer_confirmed,
                                on_click=delete_selected_assayer):
                        pass  # The actual deletion happens in the on_click callback
                    
                    # Display status messages
                    if st.session_state.delete_assayer_status is not None:
                        if st.session_state.delete_assayer_status:
                            st.success(f"✅ Successfully removed assayer: {selected_assayer_label.split(' (')[0]}")
                            # Reset status after displaying
                            st.session_state.delete_assayer_status = None
                            st.session_state.delete_assayer_message = ""
                            # Force page refresh to update the data
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to remove assayer: {st.session_state.delete_assayer_message}")
                            # Keep the status to show the error
                else:
                    st.info("No assayers available to delete.")
        else:
            st.info("📌 No assayers in the database. Add some using the form on the left.")
        
        st.markdown("</div>", unsafe_allow_html=True)

# Assay Results Tab
with tab2:
    st.markdown("<h2 class='sub-header'>Assay Results Entry</h2>", unsafe_allow_html=True)
    
    # Create sub-tabs for single and batch entry
    entry_tab1, entry_tab2 = st.tabs(["Single Entry", "Batch Entry"])
    
    # Single Entry Tab
    with entry_tab1:
        # Create columns for adding new results and viewing/editing existing ones
        col1, col2 = st.columns([1, 1])
        
        # Left column: Add new assay result
        with col1:
            st.markdown("<div class='form-container'>", unsafe_allow_html=True)
            st.markdown("<p class='entry-header'>🔬 Add Single Assay Result</p>", unsafe_allow_html=True)
        
        # Get assayers for dropdown
        assayers = get_assayers()
        
        if not assayers.empty:
            with st.form("add_result_form"):
                # Create a dictionary mapping display names to assayer IDs
                assayer_options = {f"{row['name']} ({row['employee_id']})": row['assayer_id'] for _, row in assayers.iterrows()}
                
                # Create the dropdown with display names
                selected_assayer_label = st.selectbox(
                    "Select Assayer",
                    options=list(assayer_options.keys()),
                    help="Choose the assayer who performed this test"
                )
                
                # Get the assayer_id from the selection
                selected_assayer_id = assayer_options[selected_assayer_label]
                
                sample_id = st.text_input("Sample ID", help="Enter a unique identifier for this gold sample")
                
                gold_content = st.number_input(
                    "Gold Purity (ppt)", 
                    min_value=0.0, 
                    max_value=999.9, 
                    value=995.0, 
                    step=0.1, 
                    format="%.1f", 
                    help="Enter gold purity in parts per thousand, e.g., 995.0, 915.5, 805.2"
                )
                
                bar_weight_grams = st.number_input(
                    "Bar Weight (grams)",
                    min_value=0.0,
                    max_value=100000.0,
                    value=1000.0,
                    step=100.0,
                    format="%.1f",
                    help="Enter the physical weight of the gold bar/sample in grams (used for mass impact analysis)"
                )
                
                # Add gold type selection
                gold_type = st.selectbox(
                    "Gold Type",
                    options=["Mine Gold", "Jewelry", "Fine Gold", "Recycled Gold", "Unknown"],
                    index=0,  # Default to "Mine Gold"
                    help="Select the type of gold being tested"
                )
                
                test_date = st.date_input("Test Date", value=datetime.now(), help="When was this test performed?")
                
                notes = st.text_area("Notes (Optional)", help="Any additional information about this test or sample")
                
                submit_col1, submit_col2 = st.columns([4, 1])
                with submit_col2:
                    submitted = st.form_submit_button("Submit Result")
                
                if submitted:
                    if sample_id:
                        # Add the result to the database
                        success = add_assay_result(
                            assayer_id=selected_assayer_id,
                            sample_id=sample_id,
                            gold_content=gold_content,
                            test_date=test_date.strftime('%Y-%m-%d %H:%M:%S'),
                            notes=notes,
                            gold_type=gold_type,
                            bar_weight_grams=bar_weight_grams
                        )
                        
                        if success:
                            st.success(f"✅ Successfully added result for sample {sample_id}")
                        else:
                            st.error(f"❌ Failed to add result. Sample ID might already exist for this assayer.")
                    else:
                        st.warning("⚠️ Please enter a Sample ID.")
        else:
            st.warning("⚠️ No assayers available. Please add assayers first.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Right column: View and edit existing results
    with col2:
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        st.markdown("<p class='entry-header'>🔍 Search and Manage Results</p>", unsafe_allow_html=True)
        
        # Initialize session state for search and edit/delete operations
        if 'search_results' not in st.session_state:
            st.session_state.search_results = None
        if 'selected_result_id' not in st.session_state:
            st.session_state.selected_result_id = None
        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = False
        if 'delete_mode' not in st.session_state:
            st.session_state.delete_mode = False
        if 'delete_confirmed' not in st.session_state:
            st.session_state.delete_confirmed = False
            
        # Search form
        with st.form("search_results_form"):
            search_term = st.text_input("Search Sample ID", help="Enter part of a sample ID to search")
            
            col1, col2 = st.columns(2)
            with col1:
                date_from = st.date_input(
                    "From Date", 
                    value=(datetime.now().date().replace(day=1)),  # First day of current month
                    help="Start date for filtering results"
                )
            
            with col2:
                date_to = st.date_input(
                    "To Date", 
                    value=datetime.now().date(),  # Current date
                    help="End date for filtering results"
                )
            
            # Get assayers for dropdown
            assayers = get_assayers()
            
            if not assayers.empty:
                # Add "All Assayers" option
                assayer_options = {"All Assayers": None}
                assayer_options.update({f"{row['name']} ({row['employee_id']})": row['assayer_id'] for _, row in assayers.iterrows()})
                
                selected_assayer_label = st.selectbox(
                    "Filter by Assayer",
                    options=list(assayer_options.keys()),
                    help="Choose an assayer to filter results"
                )
                
                # Get the assayer_id from the selection (None for "All Assayers")
                selected_assayer_id = assayer_options[selected_assayer_label]
            else:
                selected_assayer_id = None
            
            search_submitted = st.form_submit_button("Search Results")
        
        # Import search function
        from database import search_assay_results
        
        # Handle search
        try:
            # If search was just submitted, perform search and store results in session state
            if search_submitted:
                # Convert dates to string format
                date_from_str = date_from.strftime('%Y-%m-%d')
                date_to_str = date_to.strftime('%Y-%m-%d')
                
                # Search for results
                results = search_assay_results(
                    search_term=search_term if search_term else None,
                    assayer_id=selected_assayer_id,
                    date_from=date_from_str,
                    date_to=date_to_str,
                    limit=100
                )
                
                # Store in session state
                st.session_state.search_results = results
                # Reset any edit/delete state
                st.session_state.edit_mode = False
                st.session_state.delete_mode = False
                st.session_state.selected_result_id = None
                
            # Display results if we have any (either from this search or a previous one)
            if st.session_state.search_results is not None and not st.session_state.search_results.empty:
                results = st.session_state.search_results
                
                # Define highlight function
                def highlight_gold(val):
                    """Custom function to color gold content values"""
                    if isinstance(val, (int, float)):
                        if val >= 995.0:
                            return 'background-color: rgba(212, 175, 55, 0.3); color: #000;'
                        elif val >= 916.0:
                            return 'background-color: rgba(212, 175, 55, 0.2); color: #000;'
                        elif val >= 750.0:
                            return 'background-color: rgba(212, 175, 55, 0.1); color: #000;'
                    return ''
                
                # Format the date column
                results['test_date'] = pd.to_datetime(results['test_date']).dt.strftime('%Y-%m-%d')
                
                # Ensure gold_type exists in results, set default if missing
                if 'gold_type' not in results.columns:
                    results['gold_type'] = 'Unknown'
                
                # Fill empty values with 'Unknown'
                results['gold_type'] = results['gold_type'].fillna('Unknown')
                
                # Apply styling
                styled_results = results.style.applymap(highlight_gold, subset=['gold_content'])
                
                # Display the table with results
                st.subheader("Search Results")
                st.dataframe(styled_results, use_container_width=True)
                
                # Create a selection mechanism for the results
                result_options = {f"Sample: {row['sample_id']} | Assayer: {row['assayer_name']} | Gold: {row['gold_content']} ppt": row['result_id'] 
                                 for _, row in results.iterrows()}
                
                selected_result = st.selectbox(
                    "Select a result to manage:",
                    options=list(result_options.keys()),
                    key="result_selector"
                )
                
                selected_result_id = result_options[selected_result]
                st.session_state.selected_result_id = selected_result_id
                
                # Action buttons row
                col1, col2, spacer = st.columns([1, 1, 4])
                
                with col1:
                    if st.button("✏️ Edit", key="edit_button", use_container_width=True, 
                                help="Edit this result"):
                        st.session_state.edit_mode = True
                        st.session_state.delete_mode = False
                        st.rerun()
                        
                with col2:
                    if st.button("🗑️ Delete", key="delete_button", use_container_width=True,
                                help="Delete this result"):
                        st.session_state.delete_mode = True
                        st.session_state.edit_mode = False
                        st.rerun()
                
                # EDIT MODE
                if st.session_state.edit_mode and st.session_state.selected_result_id is not None:
                    st.markdown("---")
                    st.subheader("✏️ Edit Result")
                    
                    # Get the full result data
                    result_data = get_assay_result(st.session_state.selected_result_id)
                    
                    if result_data is not None:
                        with st.form("edit_result_form"):
                            # Display sample ID and assayer (not editable)
                            st.text_input("Sample ID", value=result_data['sample_id'], disabled=True)
                            st.text_input("Assayer", value=result_data['assayer_name'], disabled=True)
                            st.text_input("Test Date", value=pd.to_datetime(result_data['test_date']).strftime('%Y-%m-%d'), disabled=True)
                            
                            # Editable fields
                            edit_gold_content = st.number_input(
                                "Gold Purity (ppt)", 
                                min_value=0.0, 
                                max_value=999.9, 
                                value=float(result_data['gold_content']),
                                step=0.1,
                                format="%.1f"
                            )
                            
                            # Get existing bar weight or set to default
                            current_bar_weight = result_data.get('bar_weight_grams', 1000.0)
                            if current_bar_weight is None or pd.isna(current_bar_weight) or current_bar_weight == 0:
                                current_bar_weight = 1000.0
                                
                            edit_bar_weight_grams = st.number_input(
                                "Bar Weight (grams)",
                                min_value=0.0,
                                max_value=100000.0,
                                value=float(current_bar_weight),
                                step=100.0,
                                format="%.1f",
                                help="Enter the physical weight of the gold bar/sample in grams (used for mass impact analysis)"
                            )
                            
                            # Check if gold_type exists in the data, use default if not
                            current_gold_type = result_data.get('gold_type', 'Unknown')
                            if current_gold_type is None or pd.isna(current_gold_type):
                                current_gold_type = 'Unknown'
                            
                            # Gold type selection (show the current value if available)
                            gold_types = ["Mine Gold", "Jewelry", "Fine Gold", "Recycled Gold"]
                            default_index = gold_types.index(current_gold_type) if current_gold_type in gold_types else 0
                            
                            edit_gold_type = st.selectbox(
                                "Gold Type",
                                options=gold_types,
                                index=default_index,
                                help="Select the type of gold being tested"
                            )
                            
                            edit_notes = st.text_area(
                                "Notes", 
                                value=result_data['notes'] if result_data['notes'] else ""
                            )
                            
                            col1, col2 = st.columns([1, 3])
                            
                            with col1:
                                cancel = st.form_submit_button("Cancel")
                                if cancel:
                                    st.session_state.edit_mode = False
                                    st.rerun()
                                    
                            with col2:
                                save = st.form_submit_button("Save Changes")
                                if save:
                                    # Update the result
                                    success, message = update_assay_result(
                                        result_id=st.session_state.selected_result_id,
                                        gold_content=edit_gold_content,
                                        notes=edit_notes,
                                        gold_type=edit_gold_type,
                                        bar_weight_grams=edit_bar_weight_grams
                                    )
                                    
                                    if success:
                                        st.success(f"✅ Successfully updated result for sample {result_data['sample_id']}")
                                        # Clear edit mode and refresh the search results
                                        st.session_state.edit_mode = False
                                        
                                        # Re-fetch the search results to show the updated data
                                        date_from_str = date_from.strftime('%Y-%m-%d')
                                        date_to_str = date_to.strftime('%Y-%m-%d')
                                        
                                        updated_results = search_assay_results(
                                            search_term=search_term if search_term else None,
                                            assayer_id=selected_assayer_id,
                                            date_from=date_from_str,
                                            date_to=date_to_str,
                                            limit=100
                                        )
                                        st.session_state.search_results = updated_results
                                        
                                        # Force page refresh
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Failed to update result: {message}")
                
                # DELETE MODE
                if st.session_state.delete_mode and st.session_state.selected_result_id is not None:
                    st.markdown("---")
                    st.subheader("🗑️ Delete Result")
                    
                    # Get the full result data
                    result_data = get_assay_result(st.session_state.selected_result_id)
                    
                    if result_data is not None:
                        # Show result details in a clean format
                        # Get bar weight if available, otherwise display "Not specified"
                        bar_weight = result_data.get('bar_weight_grams', 'Not specified')
                        if bar_weight == 0 or pd.isna(bar_weight):
                            bar_weight = 'Not specified'
                            
                        st.markdown(f"""
                        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px;'>
                            <p><strong>Sample ID:</strong> {result_data['sample_id']}</p>
                            <p><strong>Assayer:</strong> {result_data['assayer_name']}</p>
                            <p><strong>Test Date:</strong> {pd.to_datetime(result_data['test_date']).strftime('%Y-%m-%d')}</p>
                            <p><strong>Gold Content:</strong> {result_data['gold_content']} ppt</p>
                            <p><strong>Gold Type:</strong> {result_data.get('gold_type', 'Unknown')}</p>
                            <p><strong>Bar Weight:</strong> {bar_weight if isinstance(bar_weight, str) else f"{bar_weight:.1f} g"}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.warning("⚠️ Are you sure you want to delete this result? This action cannot be undone.")
                        
                        # Confirmation and action buttons
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            if st.button("Cancel", use_container_width=True):
                                st.session_state.delete_mode = False
                                st.rerun()
                                
                        with col2:
                            confirm_delete = st.checkbox("I confirm deletion")
                            if st.button("Delete Result", disabled=not confirm_delete, use_container_width=True):
                                # Delete the result
                                success, message = delete_assay_result(st.session_state.selected_result_id)
                                
                                if success:
                                    st.success("✅ Result deleted successfully")
                                    
                                    # Clear delete mode and update search results
                                    st.session_state.delete_mode = False
                                    
                                    # Re-fetch the search results to show the updated data
                                    date_from_str = date_from.strftime('%Y-%m-%d')
                                    date_to_str = date_to.strftime('%Y-%m-%d')
                                    
                                    updated_results = search_assay_results(
                                        search_term=search_term if search_term else None,
                                        assayer_id=selected_assayer_id,
                                        date_from=date_from_str,
                                        date_to=date_to_str,
                                        limit=100
                                    )
                                    st.session_state.search_results = updated_results
                                    
                                    # Rerun to update UI
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to delete result: {message}")
            elif search_submitted:
                st.info("📌 No results found matching your search criteria.")
                
        except Exception as e:
            st.error(f"❌ Error searching for results: {e}")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Batch Entry Tab
    with entry_tab2:
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        st.markdown("<p class='entry-header'>📊 Batch Assay Results Entry</p>", unsafe_allow_html=True)
        
        # Get assayers for dropdown
        assayers = get_assayers()
        
        if not assayers.empty:
            # Initialize session state for batch entry
            if 'batch_samples' not in st.session_state:
                st.session_state.batch_samples = []
            if 'batch_benchmark_assayer' not in st.session_state:
                st.session_state.batch_benchmark_assayer = None
            if 'batch_test_date' not in st.session_state:
                st.session_state.batch_test_date = datetime.now().date()
            
            # Step 1: Select benchmark assayer and date (one time setup for the batch)
            st.markdown("### 📋 Batch Setup")
            col1, col2 = st.columns(2)
            
            with col1:
                # Create a dictionary mapping display names to assayer IDs
                assayer_options = {f"{row['name']} ({row['employee_id']})": row['assayer_id'] for _, row in assayers.iterrows()}
                
                # Benchmark assayer selection
                benchmark_assayer_label = st.selectbox(
                    "Select Benchmark Assayer",
                    options=list(assayer_options.keys()),
                    help="Choose the benchmark assayer for this batch",
                    key="batch_benchmark_select"
                )
                st.session_state.batch_benchmark_assayer = assayer_options[benchmark_assayer_label]
            
            with col2:
                # Test date selection
                batch_test_date = st.date_input(
                    "Test Date for Batch", 
                    value=st.session_state.batch_test_date,
                    help="All samples in this batch will use this date",
                    key="batch_test_date"
                )
            
            st.markdown("---")
            
            # Step 2: Batch sample entry interface
            st.markdown("### 📝 Sample Entry (Excel-style)")
            
            # Create a form for batch entry
            with st.form("batch_entry_form"):
                # Display current batch info
                st.info(f"Benchmark Assayer: {benchmark_assayer_label} | Test Date: {batch_test_date}")
                
                # Create 20 sample input rows
                num_samples = 20
                batch_data = []
                
                # Header row
                col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 2, 1.5, 1.5, 1.5, 1.5, 1.5])
                col1.markdown("**Assayer**")
                col2.markdown("**Sample ID**")
                col3.markdown("**Bar Weight (g)**")
                col4.markdown("**Gold Type**")
                col5.markdown("**Assayer Result**")
                col6.markdown("**Benchmark Result**")
                col7.markdown("**Notes**")
                
                # Create input rows
                for i in range(num_samples):
                    col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 2, 1.5, 1.5, 1.5, 1.5, 1.5])
                    
                    with col1:
                        # Assayer selection for this sample
                        sample_assayer_label = st.selectbox(
                            "",
                            options=[""] + list(assayer_options.keys()),
                            key=f"sample_assayer_{i}",
                            label_visibility="collapsed"
                        )
                        sample_assayer_id = assayer_options.get(sample_assayer_label, None) if sample_assayer_label else None
                    
                    with col2:
                        # Sample ID
                        sample_id = st.text_input(
                            "",
                            key=f"sample_id_{i}",
                            placeholder=f"Sample {i+1}",
                            label_visibility="collapsed"
                        )
                    
                    with col3:
                        # Bar weight
                        bar_weight = st.number_input(
                            "",
                            min_value=0.0,
                            max_value=100000.0,
                            value=None,
                            step=100.0,
                            format="%.1f",
                            key=f"bar_weight_{i}",
                            label_visibility="collapsed"
                        )
                    
                    with col4:
                        # Gold type
                        gold_type = st.selectbox(
                            "",
                            options=["", "Mine Gold", "Jewelry", "Fine Gold", "Recycled Gold", "Unknown"],
                            key=f"gold_type_{i}",
                            label_visibility="collapsed"
                        )
                    
                    with col5:
                        # Assayer result
                        assayer_result = st.number_input(
                            "",
                            min_value=0.0,
                            max_value=999.9,
                            value=None,
                            step=0.1,
                            format="%.1f",
                            key=f"assayer_result_{i}",
                            label_visibility="collapsed"
                        )
                    
                    with col6:
                        # Benchmark result
                        benchmark_result = st.number_input(
                            "",
                            min_value=0.0,
                            max_value=999.9,
                            value=None,
                            step=0.1,
                            format="%.1f",
                            key=f"benchmark_result_{i}",
                            label_visibility="collapsed"
                        )
                    
                    with col7:
                        # Notes
                        notes = st.text_input(
                            "",
                            key=f"notes_{i}",
                            placeholder="Optional",
                            label_visibility="collapsed"
                        )
                    
                    # Collect data if fields are filled
                    if sample_id and sample_assayer_id and gold_type and assayer_result is not None and assayer_result > 0:
                        batch_data.append({
                            'assayer_id': sample_assayer_id,
                            'sample_id': sample_id,
                            'bar_weight_grams': bar_weight if bar_weight is not None and bar_weight > 0 else 1000.0,
                            'gold_type': gold_type,
                            'gold_content': assayer_result,
                            'benchmark_value': benchmark_result if benchmark_result is not None and benchmark_result > 0 else None,
                            'notes': notes
                        })
                
                # Submit button
                st.markdown("---")
                col1, col2, col3 = st.columns([2, 1, 2])
                with col2:
                    submit_batch = st.form_submit_button("💾 Save Batch", use_container_width=True)
                
                if submit_batch:
                    if batch_data:
                        success_count = 0
                        error_count = 0
                        errors = []
                        
                        # Process each sample in the batch
                        for sample in batch_data:
                            try:
                                # Add assayer result
                                success = add_assay_result(
                                    assayer_id=sample['assayer_id'],
                                    sample_id=sample['sample_id'],
                                    gold_content=sample['gold_content'],
                                    test_date=batch_test_date.strftime('%Y-%m-%d %H:%M:%S'),
                                    notes=sample['notes'],
                                    gold_type=sample['gold_type'],
                                    bar_weight_grams=sample['bar_weight_grams']
                                )
                                
                                if success:
                                    # Add benchmark result if provided
                                    if sample['benchmark_value'] is not None:
                                        benchmark_success = add_assay_result(
                                            assayer_id=st.session_state.batch_benchmark_assayer,
                                            sample_id=sample['sample_id'],
                                            gold_content=sample['benchmark_value'],
                                            test_date=batch_test_date.strftime('%Y-%m-%d %H:%M:%S'),
                                            notes=f"Benchmark for {sample['sample_id']}",
                                            gold_type=sample['gold_type'],
                                            bar_weight_grams=sample['bar_weight_grams']
                                        )
                                    success_count += 1
                                else:
                                    error_count += 1
                                    errors.append(f"Sample {sample['sample_id']}: Already exists")
                            except Exception as e:
                                error_count += 1
                                errors.append(f"Sample {sample['sample_id']}: {str(e)}")
                        
                        # Display results
                        if success_count > 0:
                            st.success(f"✅ Successfully saved {success_count} samples")
                        
                        if error_count > 0:
                            st.error(f"❌ Failed to save {error_count} samples")
                            for error in errors:
                                st.warning(f"• {error}")
                        
                        # Clear the form by clearing session state and rerunning
                        if success_count > 0:
                            # Clear all form inputs by removing them from session state
                            keys_to_remove = []
                            for key in list(st.session_state.keys()):
                                if str(key).startswith(('sample_assayer_', 'sample_id_', 'bar_weight_', 
                                                  'gold_type_', 'assayer_result_', 'benchmark_result_', 'notes_')):
                                    keys_to_remove.append(key)
                            
                            for key in keys_to_remove:
                                del st.session_state[key]
                            
                            st.info("✅ Batch saved successfully! Form cleared for next batch...")
                            st.rerun()
                    else:
                        st.warning("⚠️ Please fill in at least one complete sample row (Assayer, Sample ID, Gold Type, and Assayer Result are required)")
                
                # Show current batch summary
                if batch_data:
                    st.markdown("---")
                    st.markdown("### 📊 Current Batch Summary")
                    st.info(f"Ready to save: {len(batch_data)} samples")
                    
                    # Show preview table
                    if st.checkbox("Show preview", key="show_batch_preview"):
                        preview_df = pd.DataFrame(batch_data)
                        preview_df['assayer_name'] = preview_df['assayer_id'].map(
                            {v: k.split(' (')[0] for k, v in assayer_options.items()}
                        )
                        preview_cols = ['sample_id', 'assayer_name', 'gold_content', 'benchmark_value', 'gold_type', 'bar_weight_grams']
                        st.dataframe(preview_df[preview_cols], use_container_width=True)
        else:
            st.warning("⚠️ No assayers available. Please add assayers first.")
        
        st.markdown("</div>", unsafe_allow_html=True)

# Inter-Lab Data Entry Tab
with tab3:
    st.markdown("<h2 class='sub-header'>Inter-Laboratory Comparison Data</h2>", unsafe_allow_html=True)
    
    # Create tabs for the different sections within the interlab tab
    interlab_tab1, interlab_tab2 = st.tabs(["External Labs", "Lab Results Entry"])
    
    # External Labs Management Tab
    with interlab_tab1:
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        st.markdown("<p class='entry-header'>📝 Add New External Laboratory</p>", unsafe_allow_html=True)
        
        with st.form("add_external_lab_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                lab_name = st.text_input("Laboratory Name", help="Enter the name of the external laboratory")
                accreditation = st.text_input("Accreditation", help="Enter the accreditation of the laboratory")
            
            with col2:
                industry_sector = st.text_input("Industry/Sector", help="Enter the industry or sector of the laboratory")
                
            notes = st.text_area("Notes (Optional)", help="Any additional information about this laboratory")
            
            submitted = st.form_submit_button("Add External Laboratory")
            
            if submitted:
                if lab_name:
                    success = add_external_lab(
                        lab_name=lab_name,
                        accreditation=accreditation,
                        industry_sector=industry_sector,
                        notes=notes
                    )
                    
                    if success:
                        st.success(f"✅ Successfully added external laboratory: {lab_name}")
                    else:
                        st.error(f"❌ Failed to add external laboratory.")
                else:
                    st.warning("⚠️ Please enter a laboratory name.")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Display existing external labs
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        st.markdown("<p class='entry-header'>🏢 Existing External Laboratories</p>", unsafe_allow_html=True)
        
        try:
            labs_df = get_external_labs()
            if not labs_df.empty:
                # Display labs data
                st.dataframe(labs_df, use_container_width=True)
                
                # Edit and Delete UI
                st.markdown("<p style='font-weight: 500; margin-top: 15px;'>Edit or Delete External Laboratories</p>", unsafe_allow_html=True)
                
                # Create two tabs for Edit and Delete
                edit_lab_tab, delete_lab_tab = st.tabs(["Edit Laboratory", "Delete Laboratory"])
                
                # Edit tab - Individual lab editing
                with edit_lab_tab:
                    # Select lab to edit
                    lab_options = {f"{row['lab_name']} ({row['accreditation'] if 'accreditation' in row and pd.notna(row['accreditation']) and row['accreditation'] != '' else 'No Accreditation'})": row['lab_id'] for _, row in labs_df.iterrows()}
                    
                    if lab_options:
                        selected_lab_id_label = st.selectbox(
                            "Select Laboratory to Edit",
                            options=list(lab_options.keys()),
                            key="edit_lab_select"
                        )
                        
                        # Get the lab_id from the selection
                        lab_id = lab_options[selected_lab_id_label]
                        
                        # Extract information for the selected lab
                        selected_lab = labs_df[labs_df['lab_id'] == lab_id].iloc[0]
                        
                        with st.form("edit_lab_form"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                edit_lab_name = st.text_input("Laboratory Name", value=selected_lab['lab_name'])
                                edit_accreditation = st.text_input("Accreditation", value=selected_lab['accreditation'] if 'accreditation' in selected_lab and pd.notna(selected_lab['accreditation']) else "")
                            
                            with col2:
                                edit_industry_sector = st.text_input("Industry/Sector", value=selected_lab['industry_sector'] if 'industry_sector' in selected_lab and pd.notna(selected_lab['industry_sector']) else "")
                                
                            edit_notes = st.text_area("Notes", value=selected_lab['notes'] if 'notes' in selected_lab and pd.notna(selected_lab['notes']) else "")
                            
                            edit_submitted = st.form_submit_button("Update Laboratory")
                            
                            if edit_submitted:
                                if edit_lab_name:
                                    success = update_external_lab(
                                        lab_id=lab_id,
                                        lab_name=edit_lab_name,
                                        accreditation=edit_accreditation,
                                        industry_sector=edit_industry_sector,
                                        notes=edit_notes
                                    )
                                    
                                    if success:
                                        st.success(f"✅ Successfully updated laboratory: {edit_lab_name}")
                                        # Force reloading the page to see the updated data
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Failed to update laboratory.")
                                else:
                                    st.warning("⚠️ Please enter a laboratory name.")
                    else:
                        st.info("No laboratories available to edit.")
                
                # Delete tab
                with delete_lab_tab:
                    st.warning("⚠️ This action will deactivate the selected laboratory and cannot be undone.")
                    
                    # Select lab to delete
                    lab_options = {f"{row['lab_name']} ({row['accreditation'] if 'accreditation' in row and pd.notna(row['accreditation']) and row['accreditation'] != '' else 'No Accreditation'})": row['lab_id'] for _, row in labs_df.iterrows()}
                    
                    if lab_options:
                        # Initialize session state variables if they don't exist
                        if 'delete_lab_confirmed' not in st.session_state:
                            st.session_state.delete_lab_confirmed = False
                        if 'delete_lab_status' not in st.session_state:
                            st.session_state.delete_lab_status = None
                        if 'delete_lab_message' not in st.session_state:
                            st.session_state.delete_lab_message = ""
                        
                        # Function to handle delete confirmation
                        def toggle_lab_delete_confirmation():
                            st.session_state.delete_lab_confirmed = not st.session_state.delete_lab_confirmed
                        
                        # Function to handle delete operation
                        def delete_selected_lab():
                            lab_id = lab_options[st.session_state.delete_lab_selection]
                            success, message = delete_external_lab(lab_id)
                            st.session_state.delete_lab_status = success
                            st.session_state.delete_lab_message = message
                        
                        # Store the selected lab in session state
                        selected_lab_id_label = st.selectbox(
                            "Select Laboratory to Delete",
                            options=list(lab_options.keys()),
                            key="delete_lab_selection",
                            on_change=lambda: setattr(st.session_state, 'delete_lab_confirmed', False)
                        )
                        
                        # Add a confirmation checkbox with callback
                        confirmation = st.checkbox(
                            "I understand and want to proceed with deletion of the selected laboratory", 
                            value=st.session_state.delete_lab_confirmed,
                            key="delete_lab_confirm",
                            on_change=toggle_lab_delete_confirmation
                        )
                        
                        # Display delete button
                        if st.button("Delete Laboratory", 
                                    disabled=not st.session_state.delete_lab_confirmed,
                                    on_click=delete_selected_lab):
                            pass  # The actual deletion happens in the on_click callback
                        
                        # Display status messages
                        if st.session_state.delete_lab_status is not None:
                            if st.session_state.delete_lab_status:
                                st.success(f"✅ {st.session_state.delete_lab_message}")
                                # Reset status after displaying
                                st.session_state.delete_lab_status = None
                                st.session_state.delete_lab_message = ""
                                # Force page refresh to update the data
                                st.rerun()
                            else:
                                st.error(f"❌ {st.session_state.delete_lab_message}")
                                # Keep the status to show the error
                    else:
                        st.info("No laboratories available to delete.")
            else:
                st.info("📌 No external laboratories in the database. Add some using the form above.")
        except Exception as e:
            st.error(f"❌ Error retrieving external laboratories: {e}")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Lab Results Entry Tab
    with interlab_tab2:
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        st.markdown("<p class='entry-header'>🔬 Enter External Laboratory Results with Internal Comparison</p>", unsafe_allow_html=True)
        
        # Get list of external labs for the dropdown
        try:
            labs_df = get_external_labs()
            lab_options = {}
            
            if not labs_df.empty:
                for _, row in labs_df.iterrows():
                    accreditation_info = f" ({row['accreditation']})" if 'accreditation' in row and pd.notna(row['accreditation']) and row['accreditation'] != "" else ""
                    lab_options[f"{row['lab_name']}{accreditation_info}"] = row['lab_id']
            else:
                st.warning("⚠️ No external laboratories available. Please add laboratories first.")
        except Exception as e:
            st.error(f"❌ Error retrieving external laboratories: {e}")
            lab_options = {}
            
        # Get list of internal assayers
        try:
            assayers_df = get_assayers()
            assayer_options = {}
            
            if not assayers_df.empty:
                for _, row in assayers_df.iterrows():
                    assayer_options[row['name']] = row['assayer_id']
            else:
                st.warning("⚠️ No internal assayers available. Please add assayers in the Assayer Management tab.")
        except Exception as e:
            st.error(f"❌ Error retrieving assayers: {e}")
            assayer_options = {}
        
        with st.form("external_result_form"):
            st.markdown("### External Laboratory Information")
            col1, col2 = st.columns(2)
            
            with col1:
                lab = st.selectbox(
                    "Select External Laboratory",
                    options=list(lab_options.keys()) if lab_options else [],
                    disabled=(len(lab_options) == 0),
                    help="Choose the external laboratory that performed this gold test"
                )
                
                sample_id = st.text_input("External Sample ID", 
                                         help="A unique identifier for this gold sample from the external lab")
                
                method_used = st.text_input("Testing Method", 
                                          help="The method used for gold purity testing (e.g., Fire Assay, XRF)")
            
            with col2:
                gold_content = st.number_input(
                    "External Gold Purity (ppt)", 
                    min_value=0.0, 
                    max_value=999.9, 
                    value=995.0, 
                    step=0.1, 
                    format="%.1f", 
                    help="Enter gold purity in parts per thousand, e.g., 995.0, 915.5, 805.2"
                )
                
                test_date = st.date_input("Test Date", 
                                         value=datetime.now(),
                                         help="The date when the test was performed")
                
                uncertainty = st.number_input(
                    "Uncertainty (±ppt)", 
                    min_value=0.0, 
                    max_value=10.0, 
                    value=0.2, 
                    step=0.1, 
                    format="%.1f", 
                    help="Enter the measurement uncertainty in parts per thousand (if available)"
                )
            
            st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
            st.markdown("### Internal Comparison Information")
            
            col3, col4 = st.columns(2)
            
            with col3:
                assayer = st.selectbox(
                    "Select Internal Assayer",
                    options=list(assayer_options.keys()) if assayer_options else ["None"],
                    disabled=(len(assayer_options) == 0),
                    help="Choose the internal assayer who tested this sample"
                )
                
                include_internal = st.checkbox("Include internal result", value=True, 
                                             help="Check to include an internal result for comparison")
            
            with col4:
                internal_gold_content = st.number_input(
                    "Internal Gold Purity (ppt)", 
                    min_value=0.0, 
                    max_value=999.9, 
                    value=995.0, 
                    step=0.1, 
                    format="%.1f",
                    disabled=not include_internal,
                    help="Enter the internal gold purity measurement in parts per thousand"
                )
                
                # Calculate the deviation
                if include_internal:
                    deviation = gold_content - internal_gold_content
                    st.metric("Deviation", f"{deviation:.1f} ppt", delta=None)
            
            notes = st.text_area("Notes (Optional)", 
                                help="Any additional information about this test or sample")
            
            submit_col1, submit_col2 = st.columns([4, 1])
            with submit_col2:
                submitted = st.form_submit_button("Submit Result")
            
            if submitted:
                if len(lab_options) == 0:
                    st.error("❌ Please add external laboratories before submitting results.")
                elif not sample_id:
                    st.warning("⚠️ Please enter a Sample ID.")
                else:
                    try:
                        lab_id = lab_options[lab]
                        # Prepare assayer_id and internal_gold_content
                        assayer_id = None if not include_internal or assayer == "None" else assayer_options[assayer]
                        internal_content = internal_gold_content if include_internal else None
                        
                        success = add_interlab_result(
                            lab_id=lab_id,
                            sample_id=sample_id,
                            gold_content=gold_content,
                            assayer_id=assayer_id, 
                            internal_gold_content=internal_content,
                            test_date=test_date.strftime('%Y-%m-%d %H:%M:%S'),
                            method_used=method_used,
                            uncertainty=uncertainty if uncertainty > 0 else None,
                            notes=notes
                        )
                        
                        if success:
                            st.success(f"✅ Successfully added external result for sample {sample_id}")
                        else:
                            st.error("❌ Failed to add result. Sample ID might already exist for this laboratory.")
                    except Exception as e:
                        st.error(f"❌ Error adding result: {e}")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Display recent interlab results
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        st.markdown("<p class='entry-header'>📊 Recent External Lab Results</p>", unsafe_allow_html=True)
        
        try:
            # Get recent interlab results (last 30 days)
            interlab_results = get_interlab_results(days=30)
            
            if not interlab_results.empty:
                # Format for display and add deviation information
                results = interlab_results.copy()
                
                # Format the date column
                results['test_date'] = pd.to_datetime(results['test_date']).dt.strftime('%Y-%m-%d')
                
                # Add calculated deviation when both external and internal measurements exist
                if 'internal_gold_content' in results.columns:
                    mask = ~results['internal_gold_content'].isna()
                    if mask.any():
                        results.loc[mask, 'deviation'] = (
                            results.loc[mask, 'gold_content'] - results.loc[mask, 'internal_gold_content']
                        ).round(1)
                        
                    # Format the column names for display
                    results.rename(columns={
                        'gold_content': 'External Result (ppt)',
                        'internal_gold_content': 'Internal Result (ppt)',
                        'deviation': 'Deviation (ppt)',
                        'lab_name': 'External Lab',
                        'assayer_name': 'Internal Assayer',
                        'method_used': 'Method',
                        'sample_id': 'Sample ID',
                        'test_date': 'Test Date'
                    }, inplace=True)
                
                # Display in a table with formatting
                def highlight_gold(val):
                    """Custom function to color gold content values"""
                    if isinstance(val, (int, float)):
                        if val >= 995.0:
                            return 'background-color: rgba(212, 175, 55, 0.3); color: #000;'
                        elif val >= 916.0:
                            return 'background-color: rgba(212, 175, 55, 0.2); color: #000;'
                        elif val >= 750.0:
                            return 'background-color: rgba(212, 175, 55, 0.1); color: #000;'
                    return ''
                
                def highlight_deviation(val):
                    """Custom function to color deviation values"""
                    if isinstance(val, (int, float)):
                        if abs(val) <= 0.1:
                            return 'background-color: rgba(0, 255, 0, 0.2); color: #000;'  # Good
                        elif abs(val) <= 0.3:
                            return 'background-color: rgba(255, 255, 0, 0.2); color: #000;'  # Warning
                        else:
                            return 'background-color: rgba(255, 0, 0, 0.2); color: #000;'  # Problem
                    return ''
                
                # Apply styling
                if 'External Result (ppt)' in results.columns and 'Deviation (ppt)' in results.columns:
                    styled_results = results.style.applymap(highlight_gold, subset=['External Result (ppt)'])
                    styled_results = styled_results.applymap(highlight_deviation, subset=['Deviation (ppt)'])
                else:
                    styled_results = results.style.applymap(highlight_gold, subset=['gold_content'])
                
                # Select columns for display
                display_columns = [
                    'Sample ID', 'External Lab', 'External Result (ppt)', 
                    'Internal Assayer', 'Internal Result (ppt)', 'Deviation (ppt)',
                    'Method', 'Test Date'
                ]
                
                # Filter columns that actually exist in the dataframe
                display_columns = [col for col in display_columns if col in results.columns]
                
                # Display the table
                st.dataframe(styled_results[display_columns].head(20), use_container_width=True)
                
                with st.expander("View All Results"):
                    st.dataframe(styled_results, use_container_width=True)
            else:
                st.info("📌 No external lab results in the last 30 days. Add some using the form above.")
        except Exception as e:
            st.error(f"❌ Error retrieving external lab results: {e}")
        
        st.markdown("</div>", unsafe_allow_html=True)

# Trainee Evaluation Tab (Tab 4)
with tab4:
    st.markdown("<h2 class='sub-header'>Trainee Evaluation</h2>", unsafe_allow_html=True)
    
    # Create subtabs for different trainee management functions
    trainee_tab1, trainee_tab2, trainee_tab3 = st.tabs(["Trainee Registration", "Reference Materials", "Trainee Evaluation"])
    
    # Trainee Registration Tab
    with trainee_tab1:
        col1, col2 = st.columns([1, 1])
        
        # Left column: Register new trainee
        with col1:
            st.markdown("<div class='form-container'>", unsafe_allow_html=True)
            st.markdown("<p class='entry-header'>🧪 Register New Trainee</p>", unsafe_allow_html=True)
            
            # Get assayers for dropdown
            assayers = get_assayers()
            
            if not assayers.empty:
                with st.form("add_trainee_form"):
                    # Create a dictionary mapping display names to assayer IDs
                    assayer_options = {f"{row['name']} ({row['employee_id']})": row['assayer_id'] for _, row in assayers.iterrows()}
                    
                    # Create the dropdown with display names
                    selected_assayer_label = st.selectbox(
                        "Select Assayer",
                        options=list(assayer_options.keys()),
                        key="trainee_assayer_selection"
                    )
                    
                    # Get the assayer_id from the selection
                    assayer_id = assayer_options[selected_assayer_label]
                    
                    start_date = st.date_input("Training Start Date", value=datetime.now(), help="When did the training begin?")
                    
                    # Training requirements (thresholds)
                    st.markdown("##### Certification Requirements")
                    tolerance = st.number_input("Target Tolerance (ppt)", value=0.3, min_value=0.01, max_value=1.0, step=0.05, help="Maximum acceptable deviation in ppt")
                    min_samples = st.number_input("Minimum Samples Required", value=20, min_value=5, max_value=100, step=5, help="Minimum number of samples evaluated before certification eligibility")
                    min_accuracy = st.number_input("Minimum Accuracy (%)", value=85.0, min_value=50.0, max_value=100.0, step=5.0, help="Percentage of samples that must fall within tolerance")
                    
                    # Notes
                    notes = st.text_area("Notes", help="Additional information about the trainee")
                    
                    submitted = st.form_submit_button("Register Trainee")
                    
                    if submitted:
                        # Convert start_date to string in YYYY-MM-DD format
                        start_date_str = start_date.strftime('%Y-%m-%d')
                        
                        # Add the trainee to the database
                        try:
                            trainee_id = add_trainee(
                                assayer_id=assayer_id,
                                start_date=start_date_str,
                                target_tolerance=tolerance,
                                min_samples_required=min_samples,
                                min_accuracy_percentage=min_accuracy,
                                notes=notes
                            )
                            
                            if trainee_id:
                                st.success(f"✅ Successfully registered trainee: {selected_assayer_label.split(' (')[0]}")
                            else:
                                st.error(f"❌ Failed to register trainee.")
                        except ValueError as e:
                            st.error(f"❌ Error: {e}")
            else:
                st.warning("⚠️ No assayers available. Add assayers first before registering trainees.")
                
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Right column: View existing trainees
        with col2:
            st.markdown("<div class='form-container'>", unsafe_allow_html=True)
            st.markdown("<p class='entry-header'>👥 Existing Trainees</p>", unsafe_allow_html=True)
            
            # Get trainees from the database
            trainees_df = get_trainees()
            
            if not trainees_df.empty:
                # Display trainee information
                display_cols = ['assayer_name', 'employee_id', 'start_date', 'status', 'target_tolerance']
                col_labels = {
                    'assayer_name': 'Trainee Name',
                    'employee_id': 'Employee ID',
                    'start_date': 'Training Started',
                    'status': 'Status',
                    'target_tolerance': 'Target Tol. (ppt)'
                }
                
                # Apply formatting
                def highlight_status(val):
                    if val == 'Certified':
                        return 'background-color: rgba(0, 255, 0, 0.2)'
                    elif val == 'Needs More Training':
                        return 'background-color: rgba(255, 255, 0, 0.2)'
                    else:  # 'Pending'
                        return 'background-color: rgba(173, 216, 230, 0.2)'
                
                styled_trainees = trainees_df[display_cols].style.applymap(
                    highlight_status, subset=['status']
                ).format({
                    'target_tolerance': '{:.2f}'
                })
                
                st.dataframe(styled_trainees, use_container_width=True)
                
                # Option to view detailed information
                with st.expander("Detailed Trainee Information"):
                    detail_cols = [
                        'assayer_name', 'employee_id', 'start_date', 'certification_date',
                        'status', 'target_tolerance', 'min_samples_required', 'min_accuracy_percentage',
                        'notes'
                    ]
                    st.dataframe(trainees_df[detail_cols], use_container_width=True)
            else:
                st.info("📌 No trainees registered. Register some using the form on the left.")
                
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Reference Materials Tab
    with trainee_tab2:
        col1, col2 = st.columns([1, 1])
        
        # Left column: Add new reference material
        with col1:
            st.markdown("<div class='form-container'>", unsafe_allow_html=True)
            st.markdown("<p class='entry-header'>🧪 Add Reference Material</p>", unsafe_allow_html=True)
            
            with st.form("add_reference_material_form"):
                name = st.text_input("Material Name/ID", help="Enter a unique identifier for the reference material")
                gold_content = st.number_input("Certified Gold Content (ppt)", value=995.0, min_value=0.0, max_value=999.9, step=0.1, help="Certified gold content in parts per thousand")
                uncertainty = st.number_input("Uncertainty (ppt)", value=0.1, min_value=0.01, max_value=1.0, step=0.01, help="Uncertainty of the certified value")
                
                material_type = st.selectbox(
                    "Material Type",
                    options=["Standard", "CRM", "In-house", "External"],
                    help="Type of reference material"
                )
                
                source = st.text_input("Source/Provider", help="Where the reference material was obtained from")
                notes = st.text_area("Additional Information", help="Other details about the reference material")
                
                submitted = st.form_submit_button("Add Reference Material")
                
                if submitted:
                    if name and gold_content:
                        try:
                            ref_id = add_reference_material(
                                name=name,
                                gold_content=gold_content,
                                uncertainty=uncertainty,
                                material_type=material_type,
                                source=source,
                                notes=notes
                            )
                            
                            if ref_id:
                                st.success(f"✅ Successfully added reference material: {name}")
                            else:
                                st.error(f"❌ Failed to add reference material.")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                    else:
                        st.warning("⚠️ Please enter a name and gold content for the reference material.")
                
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Right column: View existing reference materials
        with col2:
            st.markdown("<div class='form-container'>", unsafe_allow_html=True)
            st.markdown("<p class='entry-header'>📋 Existing Reference Materials</p>", unsafe_allow_html=True)
            
            # Get reference materials from the database
            materials_df = get_reference_materials()
            
            if not materials_df.empty:
                # Format the dataframe for display
                display_cols = ['name', 'gold_content', 'uncertainty', 'material_type']
                
                # Apply formatting
                def format_gold(val):
                    return f"{val:.1f}"
                
                styled_materials = materials_df[display_cols].style.format({
                    'gold_content': format_gold,
                    'uncertainty': '{:.3f}'
                })
                
                st.dataframe(styled_materials, use_container_width=True)
                
                # Show detailed information in an expander
                with st.expander("Detailed Reference Material Information"):
                    detail_cols = ['reference_id', 'name', 'gold_content', 'uncertainty', 'material_type', 'source', 'notes']
                    st.dataframe(materials_df[detail_cols], use_container_width=True)
            else:
                st.info("📌 No reference materials in the database. Add some using the form on the left.")
                
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Trainee Evaluation Tab
    with trainee_tab3:
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        st.markdown("<p class='entry-header'>🔍 Record Trainee Evaluation</p>", unsafe_allow_html=True)
        
        # Get trainees, assayers, and reference materials
        trainees_df = get_trainees()
        assayers_df = get_assayers()
        materials_df = get_reference_materials()
        
        if not trainees_df.empty:
            # Create a multi-step workflow
            if 'trainee_eval_step' not in st.session_state:
                st.session_state.trainee_eval_step = 1
            
            if 'evaluation_type' not in st.session_state:
                st.session_state.evaluation_type = None
                
            # Step 1: Choose evaluation type
            if st.session_state.trainee_eval_step == 1:
                st.markdown("### Step 1: Select Evaluation Type")
                
                # First select evaluation type
                evaluation_type = st.radio(
                    "Evaluation Type",
                    options=["Accuracy", "Consistency"],
                    horizontal=True,
                    help="Accuracy evaluates against certified values; Consistency evaluates repeatability of measurements"
                )
                
                if st.button("Next", key="step1_next"):
                    st.session_state.evaluation_type = evaluation_type
                    st.session_state.trainee_eval_step = 2
                    st.rerun()
            
            # Step 2: Enter details based on the evaluation type
            elif st.session_state.trainee_eval_step == 2:
                evaluation_type = st.session_state.evaluation_type
                
                st.markdown(f"### Step 2: Enter {evaluation_type} Evaluation Details")
                
                # Back button
                if st.button("← Back", key="step2_back"):
                    st.session_state.trainee_eval_step = 1
                    st.rerun()
                
                # Different forms based on evaluation type
                if evaluation_type == "Accuracy":
                    # ACCURACY WORKFLOW
                    if assayers_df.empty:
                        st.warning("⚠️ No certified assayers available. Add assayers first.")
                    else:
                        with st.form("accuracy_evaluation_form"):
                            # Sample ID
                            sample_id = st.text_input("Sample ID", help="Enter the unique identifier for this sample")
                            
                            # Certified Assayer selection
                            assayer_options = {f"{row['name']} ({row['employee_id']})": row['assayer_id'] for _, row in assayers_df.iterrows()}
                            
                            selected_assayer_label = st.selectbox(
                                "Select Certified Assayer",
                                options=list(assayer_options.keys()),
                                key="accuracy_assayer_selection"
                            )
                            
                            # Get the assayer_id
                            assayer_id = assayer_options[selected_assayer_label]
                            
                            # Certified Assayer result
                            certified_result = st.number_input(
                                "Certified Assayer's Result (ppt)",
                                value=995.0,
                                min_value=0.0,
                                max_value=999.9,
                                step=0.1,
                                help="Gold content measured by the certified assayer"
                            )
                            
                            # Trainee selection
                            trainee_options = {f"{row['assayer_name']} ({row['employee_id']})": row['trainee_id'] for _, row in trainees_df.iterrows()}
                            
                            selected_trainee_label = st.selectbox(
                                "Select Trainee",
                                options=list(trainee_options.keys()),
                                key="accuracy_trainee_selection"
                            )
                            
                            # Get the trainee_id
                            trainee_id = trainee_options[selected_trainee_label]
                            
                            # Trainee's result
                            trainee_result = st.number_input(
                                "Trainee's Result (ppt)",
                                value=certified_result,
                                min_value=0.0,
                                max_value=999.9,
                                step=0.1,
                                help="Gold content measured by the trainee"
                            )
                            
                            # Test date
                            test_date = st.date_input("Test Date", value=datetime.now())
                            
                            # Notes
                            notes = st.text_area("Notes", help="Additional information about this evaluation")
                            
                            submitted = st.form_submit_button("Record Accuracy Evaluation")
                            
                            if submitted:
                                try:
                                    # First, we need to create or find a reference material record for the certified result
                                    reference_name = f"Accuracy Standard - {sample_id} - {selected_assayer_label.split(' (')[0]}"
                                    
                                    # Check if this reference material already exists
                                    existing_refs = get_reference_materials()
                                    ref_exists = False
                                    reference_id = None
                                    
                                    if not existing_refs.empty:
                                        matching_refs = existing_refs[existing_refs['name'] == reference_name]
                                        if not matching_refs.empty:
                                            ref_exists = True
                                            reference_id = matching_refs.iloc[0]['reference_id']
                                    
                                    # If it doesn't exist, create it
                                    if not ref_exists:
                                        reference_id = add_reference_material(
                                            name=reference_name,
                                            gold_content=certified_result,
                                            uncertainty=0.1,  # Default uncertainty
                                            material_type="Standard",
                                            source=f"Certified Assayer: {selected_assayer_label}",
                                            notes=f"Sample ID: {sample_id}, Created for accuracy evaluation"
                                        )
                                    
                                    # Now record the evaluation
                                    test_date_str = test_date.strftime('%Y-%m-%d')
                                    
                                    eval_id = add_trainee_evaluation(
                                        trainee_id=trainee_id,
                                        reference_id=reference_id,
                                        measured_gold_content=trainee_result,
                                        test_date=test_date_str,
                                        sample_id=sample_id,
                                        notes=notes,
                                        evaluation_type="accuracy"
                                    )
                                    
                                    if eval_id:
                                        deviation = trainee_result - certified_result
                                        st.success(f"✅ Successfully recorded accuracy evaluation. Deviation: {deviation:.2f} ppt")
                                        # Reset to step 1
                                        st.session_state.trainee_eval_step = 1
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Failed to record evaluation.")
                                except Exception as e:
                                    st.error(f"❌ Error: {e}")
                
                else:  # Consistency workflow
                    # CONSISTENCY WORKFLOW
                    with st.form("consistency_evaluation_form"):
                        # QC Sample ID
                        qc_sample_id = st.text_input("QC Sample ID", help="Enter the unique identifier for this QC sample")
                        
                        # QC Sample purity
                        qc_purity = st.number_input(
                            "QC Sample Purity (ppt)",
                            value=995.0,
                            min_value=0.0,
                            max_value=999.9,
                            step=0.1,
                            help="Known purity of the QC sample"
                        )
                        
                        # Trainee selection
                        trainee_options = {f"{row['assayer_name']} ({row['employee_id']})": row['trainee_id'] for _, row in trainees_df.iterrows()}
                        
                        selected_trainee_label = st.selectbox(
                            "Select Trainee",
                            options=list(trainee_options.keys()),
                            key="consistency_trainee_selection"
                        )
                        
                        # Get the trainee_id
                        trainee_id = trainee_options[selected_trainee_label]
                        
                        # Trainee's result
                        trainee_result = st.number_input(
                            "Trainee's Result (ppt)",
                            value=qc_purity,
                            min_value=0.0,
                            max_value=999.9,
                            step=0.1,
                            help="Gold content measured by the trainee"
                        )
                        
                        # Test date
                        test_date = st.date_input("Test Date", value=datetime.now())
                        
                        # Notes
                        notes = st.text_area("Notes", help="Additional information about this evaluation")
                        
                        submitted = st.form_submit_button("Record Consistency Evaluation")
                        
                        if submitted:
                            try:
                                # First, we need to create or find a reference material record for the QC sample
                                reference_name = f"QC Standard - {qc_sample_id}"
                                
                                # Check if this reference material already exists
                                existing_refs = get_reference_materials()
                                ref_exists = False
                                reference_id = None
                                
                                if not existing_refs.empty:
                                    matching_refs = existing_refs[existing_refs['name'] == reference_name]
                                    if not matching_refs.empty:
                                        ref_exists = True
                                        reference_id = matching_refs.iloc[0]['reference_id']
                                
                                # If it doesn't exist, create it
                                if not ref_exists:
                                    reference_id = add_reference_material(
                                        name=reference_name,
                                        gold_content=qc_purity,
                                        uncertainty=0.1,  # Default uncertainty
                                        material_type="QC",
                                        source="Internal QC",
                                        notes=f"QC Sample ID: {qc_sample_id}, Created for consistency evaluation"
                                    )
                                
                                # Now record the evaluation
                                test_date_str = test_date.strftime('%Y-%m-%d')
                                
                                eval_id = add_trainee_evaluation(
                                    trainee_id=trainee_id,
                                    reference_id=reference_id,
                                    measured_gold_content=trainee_result,
                                    test_date=test_date_str,
                                    sample_id=qc_sample_id,
                                    notes=notes,
                                    evaluation_type="consistency"
                                )
                                
                                if eval_id:
                                    deviation = trainee_result - qc_purity
                                    st.success(f"✅ Successfully recorded consistency evaluation. Deviation: {deviation:.2f} ppt")
                                    # Reset to step 1
                                    st.session_state.trainee_eval_step = 1
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to record evaluation.")
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
            
            # Reset button at the bottom to restart the flow
            if st.session_state.trainee_eval_step > 1:
                if st.button("Reset Form", key="reset_eval_form"):
                    st.session_state.trainee_eval_step = 1
                    st.session_state.evaluation_type = None
                    st.rerun()
        
        else:
            st.warning("⚠️ No trainees registered. Register trainees first in the Trainee Registration tab.")
        
        # Display recent evaluations
        st.markdown("<p class='entry-header'>📋 Recent Trainee Evaluations</p>", unsafe_allow_html=True)
        
        try:
            # Get recent evaluations (last 30 days)
            recent_evals = get_trainee_evaluations(days=30)
            
            if not recent_evals.empty:
                # Format the dataframe for display
                display_cols = [
                    'assayer_name', 'employee_id', 'reference_name', 
                    'certified_gold_content', 'measured_gold_content', 'deviation_ppt',
                    'test_date', 'evaluation_type'
                ]
                
                col_rename = {
                    'assayer_name': 'Trainee',
                    'employee_id': 'ID',
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
                
                display_df = recent_evals[display_cols].rename(columns=col_rename)
                
                styled_evals = display_df.style.applymap(
                    highlight_deviation, subset=['Deviation (ppt)']
                ).format({
                    'Certified (ppt)': '{:.1f}',
                    'Measured (ppt)': '{:.1f}',
                    'Deviation (ppt)': '{:.2f}'
                })
                
                st.dataframe(styled_evals, use_container_width=True)
            else:
                st.info("📌 No evaluations in the last 30 days. Add some using the form above.")
        except Exception as e:
            st.error(f"❌ Error retrieving evaluations: {e}")
            
        st.markdown("</div>", unsafe_allow_html=True)

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