"""
Authentication and access control module for AEG labsync Monitor
"""
import streamlit as st
import hashlib
from typing import Dict, List, Optional

# User accounts with their roles and access permissions
USERS = {
    "admin": {
        "password": "@Algol025",
        "role": "Administrator",
        "permissions": [
            "app", "data_entry", "daily_monitoring", "analytics", "data_export",
            "ai_assistant", "settings", "assayer_profiles", "interlab_comparisons",
            "gold_type_analysis", "mass_impact_analysis", "trainee_evaluation",
            "user_management"
        ]
    },
    "management": {
        "password": "aegold995",
        "role": "Management",
        "permissions": [
            "app", "data_entry", "daily_monitoring", "analytics", "data_export",
            "ai_assistant", "settings", "assayer_profiles", "interlab_comparisons",
            "gold_type_analysis", "mass_impact_analysis", "trainee_evaluation"
        ]
    },
    "hr": {
        "password": "aeghr025",
        "role": "HR",
        "permissions": [
            "app", "daily_monitoring", "analytics", "ai_assistant", 
            "assayer_profiles", "interlab_comparisons", "gold_type_analysis", 
            "trainee_evaluation"
        ]
    },
    "monitoring": {
        "password": "aeglab3210",
        "role": "Monitoring",
        "permissions": [
            "app", "data_entry", "daily_monitoring", "analytics", 
            "assayer_profiles", "ai_assistant", "gold_type_analysis"
        ]
    },
    "laboratory": {
        "password": "17025",
        "role": "Laboratory",
        "permissions": [
            "app", "data_entry", "assayer_profiles"
        ]
    }
}

# Page mappings to permission names
PAGE_PERMISSIONS = {
    "app.py": "app",
    "Data_Entry": "data_entry",
    "Daily_Monitoring": "daily_monitoring",
    "Analytics": "analytics",
    "Data_Export": "data_export",
    "AI_Assistant": "ai_assistant",
    "Settings": "settings",
    "Assayer_Profiles": "assayer_profiles",
    "Interlab_Comparisons": "interlab_comparisons",
    "Gold_Type_Analysis": "gold_type_analysis",
    "Mass_Impact_Analysis": "mass_impact_analysis",
    "Trainee_Evaluation": "trainee_evaluation"
}

def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a provided password against the stored password"""
    return stored_password == provided_password

def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user with username and password"""
    if username in USERS:
        return verify_password(USERS[username]["password"], password)
    return False

def get_user_role(username: str) -> Optional[str]:
    """Get the role of a user"""
    if username in USERS:
        return USERS[username]["role"]
    return None

def get_user_permissions(username: str) -> List[str]:
    """Get the permissions of a user"""
    if username in USERS:
        return USERS[username]["permissions"]
    return []

def has_permission(username: str, permission: str) -> bool:
    """Check if a user has a specific permission"""
    if username in USERS:
        return permission in USERS[username]["permissions"]
    return False

def initialize_session():
    """Initialize session state for authentication"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "role" not in st.session_state:
        st.session_state.role = None
    if "permissions" not in st.session_state:
        st.session_state.permissions = []
    if "login_persistent" not in st.session_state:
        st.session_state.login_persistent = True  # Default to persistent login
    if "login_timestamp" not in st.session_state:
        st.session_state.login_timestamp = None

def is_logged_in() -> bool:
    """Check if user is logged in"""
    initialize_session()
    return st.session_state.authenticated

def get_current_user() -> Optional[str]:
    """Get the current logged-in user"""
    if is_logged_in():
        return st.session_state.get("username")
    return None

def logout():
    """Log out the current user and clear all session data"""
    for key in ["authenticated", "username", "role", "permissions", "login_persistent", "login_timestamp"]:
        if key in st.session_state:
            del st.session_state[key]

def login_user(username: str):
    """Log in a user and set session state with persistence"""
    from datetime import datetime
    st.session_state.authenticated = True
    st.session_state.username = username
    st.session_state.role = get_user_role(username)
    st.session_state.permissions = get_user_permissions(username)
    st.session_state.login_persistent = True
    st.session_state.login_timestamp = datetime.now()

def check_page_access(page_name: str) -> bool:
    """Check if current user has access to a specific page"""
    if not is_logged_in():
        return False
    
    current_user = get_current_user()
    if not current_user:
        return False
    
    # Get the permission name for this page
    permission_name = PAGE_PERMISSIONS.get(page_name)
    if not permission_name:
        return False
    
    return has_permission(current_user, permission_name)

def require_login():
    """Decorator function to require login for a page"""
    if not is_logged_in():
        st.error("You must be logged in to access this page.")
        st.stop()

def require_permission(permission: str):
    """Decorator function to require a specific permission"""
    if not is_logged_in():
        st.error("You must be logged in to access this page.")
        st.stop()
    
    current_user = get_current_user()
    if not current_user or not has_permission(current_user, permission):
        st.error("You don't have permission to access this page.")
        st.stop()

def display_login_form():
    """Display the login form"""
    st.markdown("<h1 class='main-header' style='text-align: center;'>AEG labsync Login</h1>", unsafe_allow_html=True)
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.markdown("### Please log in to continue")
            
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit_button = st.form_submit_button("🔑 Login", use_container_width=True)
            
            if submit_button:
                if username and password:
                    if authenticate_user(username, password):
                        login_user(username)
                        st.success(f"Welcome, {get_user_role(username)}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                else:
                    st.error("Please enter both username and password.")

def display_user_info():
    """Display current user information in sidebar"""
    if is_logged_in():
        current_user = get_current_user()
        role = st.session_state.get("role", "Unknown")
        login_time = st.session_state.get("login_timestamp")
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### User Session")
        
        # User info in a nice container
        with st.sidebar.container():
            st.markdown(f"**User:** {current_user}")
            st.markdown(f"**Role:** {role}")
            
            # Show login time if available
            if login_time:
                from datetime import datetime
                time_str = login_time.strftime("%Y-%m-%d %H:%M")
                st.markdown(f"**Logged in:** {time_str}")
            
            # Session status indicator
            st.success("✅ Session Active")
        
        # Logout button with warning styling
        if st.sidebar.button("🔓 Logout", use_container_width=True, type="secondary"):
            logout()
            st.rerun()

def get_accessible_pages() -> Dict[str, str]:
    """Get list of pages accessible to current user"""
    if not is_logged_in():
        return {}
    
    current_user = get_current_user()
    if not current_user:
        return {}
    
    user_permissions = get_user_permissions(current_user)
    accessible_pages = {}
    
    # Define page titles and their corresponding permission requirements
    page_mapping = {
        "Data_Entry": ("📋 Data Entry", "data_entry"),
        "Daily_Monitoring": ("📊 Daily Monitoring", "daily_monitoring"),
        "Analytics": ("📈 Analytics", "analytics"),
        "Data_Export": ("💾 Data Export", "data_export"),
        "AI_Assistant": ("🤖 AI Assistant", "ai_assistant"),
        "Settings": ("⚙️ Settings", "settings"),
        "Assayer_Profiles": ("👤 Assayer Profiles", "assayer_profiles"),
        "Interlab_Comparisons": ("🔬 Interlab Comparisons", "interlab_comparisons"),
        "Gold_Type_Analysis": ("🥇 Gold Type Analysis", "gold_type_analysis"),
        "Mass_Impact_Analysis": ("⚖️ Mass Impact Analysis", "mass_impact_analysis"),
        "Trainee_Evaluation": ("🎓 Trainee Evaluation", "trainee_evaluation")
    }
    
    for page_key, (page_title, permission) in page_mapping.items():
        if permission in user_permissions:
            accessible_pages[page_key] = page_title
    
    return accessible_pages

def display_access_denied():
    """Display access denied message"""
    st.error("🚫 Access Denied")
    st.markdown("You don't have permission to access this page.")
    
    current_user = get_current_user()
    if current_user:
        role = st.session_state.get("role", "Unknown")
        st.info(f"Your current role: **{role}**")
        
        # Show accessible pages
        accessible_pages = get_accessible_pages()
        if accessible_pages:
            st.markdown("### Pages you can access:")
            for page_key, page_title in accessible_pages.items():
                st.markdown(f"- {page_title}")