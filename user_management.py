"""
User management component for administrators
"""
import streamlit as st
import pandas as pd
from auth import USERS, get_current_user, has_permission
from typing import Dict, List

def display_user_management():
    """Display user management interface for administrators"""
    current_user = get_current_user()
    
    # Check if user has admin permissions
    if not current_user or not has_permission(current_user, "user_management"):
        st.error("You don't have permission to access user management.")
        return
    
    st.markdown("<h2 class='sub-header'>👥 User Management</h2>", unsafe_allow_html=True)
    
    # Display current users in a table
    st.markdown("### Current Users")
    
    # Convert users to DataFrame for display
    users_data = []
    for username, user_info in USERS.items():
        users_data.append({
            "Username": username,
            "Role": user_info["role"],
            "Permissions Count": len(user_info["permissions"]),
            "Status": "Active"
        })
    
    users_df = pd.DataFrame(users_data)
    st.dataframe(users_df, use_container_width=True)
    
    # User details section
    st.markdown("### User Details")
    
    selected_user = st.selectbox("Select a user to view details:", list(USERS.keys()))
    
    if selected_user:
        user_info = USERS[selected_user]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Username:** {selected_user}")
            st.markdown(f"**Role:** {user_info['role']}")
            st.markdown(f"**Total Permissions:** {len(user_info['permissions'])}")
        
        with col2:
            st.markdown("**Permissions:**")
            permissions_text = ""
            for perm in user_info['permissions']:
                permissions_text += f"• {perm.replace('_', ' ').title()}\n"
            st.text(permissions_text)
    
    # Password reset section
    st.markdown("---")
    st.markdown("### Security Information")
    
    st.info("""
    **Security Notes:**
    - All user accounts are pre-configured with specific roles and permissions
    - Passwords are stored securely and cannot be viewed
    - Only administrators can access this user management section
    - User roles determine which pages and features are accessible
    """)
    
    # Role descriptions
    st.markdown("### Role Descriptions")
    
    roles_info = {
        "Administrator": {
            "description": "Complete access to all features including user management",
            "pages": "All pages including user management"
        },
        "Management": {
            "description": "Access to all operational features except user management", 
            "pages": "All pages except user management"
        },
        "HR": {
            "description": "Access to monitoring, analytics, and evaluation features",
            "pages": "Home, Daily Monitoring, Analytics, AI Assistant, Assayer Profiles, Interlab Comparisons, Gold Type Analysis, Trainee Evaluation"
        },
        "Monitoring": {
            "description": "Access to data entry and monitoring features",
            "pages": "Home, Data Entry, Daily Monitoring, Analytics, Assayer Profiles, AI Assistant, Gold Type Analysis"
        },
        "Laboratory": {
            "description": "Basic access for data entry and profile viewing",
            "pages": "Home, Data Entry, Assayer Profiles only"
        }
    }
    
    # Use markdown instead of nested expanders to avoid the error
    for role, info in roles_info.items():
        st.markdown(f"**{role}:**")
        st.markdown(f"- Description: {info['description']}")
        st.markdown(f"- Accessible Pages: {info['pages']}")
        st.markdown("---")

def display_access_control_info():
    """Display information about access control system"""
    st.markdown("### Access Control System")
    
    st.markdown("""
    The application uses a role-based access control system:
    
    1. **Authentication Required**: All users must log in to access the application
    2. **Role-Based Permissions**: Each role has specific permissions for different features
    3. **Page-Level Access Control**: Users can only access pages they have permissions for
    4. **Secure Sessions**: User sessions are managed securely with Streamlit session state
    """)
    
    # Display permission matrix
    st.markdown("#### Permission Matrix")
    
    # Create permission matrix
    pages = [
        "Home", "Data Entry", "Daily Monitoring", "Analytics", "Data Export",
        "AI Assistant", "Settings", "Assayer Profiles", "Interlab Comparisons",
        "Gold Type Analysis", "Mass Impact Analysis", "Trainee Evaluation", "User Management"
    ]
    
    roles = ["Administrator", "Management", "HR", "Monitoring", "Laboratory"]
    
    # Permission mapping for display
    role_permissions = {
        "Administrator": [True] * len(pages),
        "Management": [True] * (len(pages)-1) + [False],  # All except user management
        "HR": [True, False, True, True, False, True, False, True, True, True, False, True, False],
        "Monitoring": [True, True, True, True, False, True, False, True, False, True, False, False, False],
        "Laboratory": [True, True, False, False, False, False, False, True, False, False, False, False, False]
    }
    
    # Create matrix DataFrame
    matrix_data = {}
    for role in roles:
        matrix_data[role] = ["✅" if perm else "❌" for perm in role_permissions[role]]
    
    matrix_df = pd.DataFrame(matrix_data, index=pages)
    st.dataframe(matrix_df, use_container_width=True)