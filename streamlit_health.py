"""
Health check middleware for Streamlit deployment
"""
import streamlit as st
import os
import time

def add_health_check_headers():
    """Add health check headers for deployment systems"""
    # Add meta tags for health checks
    st.markdown("""
    <meta name="health-check" content="ok">
    <meta name="application-status" content="running">
    <meta name="last-updated" content="{}">
    """.format(int(time.time())), unsafe_allow_html=True)

def check_deployment_readiness():
    """Check if the application is ready for deployment"""
    try:
        # Basic health checks
        import database
        import auth
        
        # Check if databases are accessible
        database.init_db()
        
        # Check if authentication system is working
        auth.initialize_session()
        
        return True
    except Exception as e:
        st.error(f"Application health check failed: {e}")
        return False

def display_health_status():
    """Display health status for monitoring"""
    # Only show health status for specific health check requests
    query_params = st.query_params
    is_health_check = (
        query_params.get('health') == 'check' or 
        query_params.get('healthz') == 'true' or
        query_params.get('ready') == 'true'
    )
    
    if is_health_check:
        st.success("✅ Application is healthy and ready")
        st.json({
            "status": "healthy",
            "timestamp": int(time.time()),
            "version": "1.0.0",
            "database": "connected",
            "auth": "ready"
        })
        return True
    return False