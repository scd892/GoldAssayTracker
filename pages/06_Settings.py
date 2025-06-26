import streamlit as st
import os
import sys
import pandas as pd
from dotenv import load_dotenv, set_key, find_dotenv
import time

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_utils import check_ai_providers, get_ai_provider_details
from auth import require_permission, display_access_denied, check_page_access

# Page configuration
st.set_page_config(
    page_title="Settings - AEG labsync- Monitor",
    page_icon="🔶",
    layout="wide"
)

# Check authentication and permissions
if not check_page_access("Settings"):
    display_access_denied()
    st.stop()

# Header
st.markdown("<h1 style='text-align: center; color: #D4AF37;'>AI Settings</h1>", unsafe_allow_html=True)

st.markdown("""
This page allows you to configure the AI providers used in the application. 
The application supports multiple AI providers for redundancy and flexibility. 
If one provider is unavailable, the system will automatically try the next one.

Providers are tried in the following order:
1. OpenAI (GPT-4o)
2. Anthropic (Claude 3.5 Sonnet)
3. DeepSeek (DeepSeek Chat)

If none of the above are configured or available, the application will use a basic statistical analysis fallback.
""")

# Create a 3-column layout
col1, col2, col3 = st.columns(3)

# Load current environment variables
load_dotenv()
env_path = find_dotenv()

# Get provider details
provider_details = get_ai_provider_details()

# Check which providers are configured
provider_status = check_ai_providers()

# Extract API keys (without displaying them)
openai_api_key = os.environ.get("OPENAI_API_KEY", "")
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY", "")

# Display OpenAI settings in the first column
with col1:
    st.subheader("OpenAI Settings")
    
    # Show current status
    if openai_api_key:
        st.success("✅ OpenAI API Key is configured")
        st.info("Model: GPT-4o")
        clear_openai = st.button("Clear OpenAI API Key")
        if clear_openai:
            # Remove API key from environment
            os.environ["OPENAI_API_KEY"] = ""
            # Update .env file
            set_key(env_path, "OPENAI_API_KEY", "")
            st.warning("OpenAI API Key cleared. Reloading...")
            time.sleep(1)
            st.rerun()
    else:
        st.warning("⚠️ OpenAI API Key not configured")
        new_openai_key = st.text_input("Enter OpenAI API Key", type="password")
        if st.button("Save OpenAI API Key"):
            if new_openai_key:
                # Set environment variable
                os.environ["OPENAI_API_KEY"] = new_openai_key
                # Update .env file
                set_key(env_path, "OPENAI_API_KEY", new_openai_key)
                st.success("OpenAI API Key saved. Reloading...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Please enter an API key")

# Display Anthropic settings in the second column
with col2:
    st.subheader("Anthropic Settings")
    
    # Show current status
    if anthropic_api_key:
        st.success("✅ Anthropic API Key is configured")
        st.info("Model: Claude 3.5 Sonnet")
        clear_anthropic = st.button("Clear Anthropic API Key")
        if clear_anthropic:
            # Remove API key from environment
            os.environ["ANTHROPIC_API_KEY"] = ""
            # Update .env file
            set_key(env_path, "ANTHROPIC_API_KEY", "")
            st.warning("Anthropic API Key cleared. Reloading...")
            time.sleep(1)
            st.rerun()
    else:
        st.warning("⚠️ Anthropic API Key not configured")
        new_anthropic_key = st.text_input("Enter Anthropic API Key", type="password")
        if st.button("Save Anthropic API Key"):
            if new_anthropic_key:
                # Set environment variable
                os.environ["ANTHROPIC_API_KEY"] = new_anthropic_key
                # Update .env file
                set_key(env_path, "ANTHROPIC_API_KEY", new_anthropic_key)
                st.success("Anthropic API Key saved. Reloading...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Please enter an API key")

# Display DeepSeek settings in the third column
with col3:
    st.subheader("DeepSeek Settings")
    
    # Show current status
    if deepseek_api_key:
        st.success("✅ DeepSeek API Key is configured")
        st.info("Model: DeepSeek Chat")
        clear_deepseek = st.button("Clear DeepSeek API Key")
        if clear_deepseek:
            # Remove API key from environment
            os.environ["DEEPSEEK_API_KEY"] = ""
            # Update .env file
            set_key(env_path, "DEEPSEEK_API_KEY", "")
            st.warning("DeepSeek API Key cleared. Reloading...")
            time.sleep(1)
            st.rerun()
    else:
        st.warning("⚠️ DeepSeek API Key not configured")
        new_deepseek_key = st.text_input("Enter DeepSeek API Key", type="password")
        if st.button("Save DeepSeek API Key"):
            if new_deepseek_key:
                # Set environment variable
                os.environ["DEEPSEEK_API_KEY"] = new_deepseek_key
                # Update .env file
                set_key(env_path, "DEEPSEEK_API_KEY", new_deepseek_key)
                st.success("DeepSeek API Key saved. Reloading...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Please enter an API key")

# Display overall provider status
st.markdown("---")
st.subheader("Provider Status")

# Create a data table to show all providers
status_data = []
for provider in provider_details:
    status = "✅ Configured" if provider["configured"] else "❌ Not Configured"
    status_data.append({
        "Provider": provider["name"],
        "Model": provider["model"],
        "Status": status,
        "Priority": provider["order"]
    })

# Display as a table
status_df = pd.DataFrame(status_data)
status_df = status_df.sort_values("Priority")
status_df = status_df.drop(columns=["Priority"])

# Use a custom style function
def highlight_status(val):
    color = "#e6ffe6" if "✅" in val else "#ffe6e6"  # Light green or light red
    return f"background-color: {color}"

# Apply styling and display
st.dataframe(status_df.style.applymap(highlight_status, subset=["Status"]), use_container_width=True)

# Display fallback info
st.subheader("Statistical Fallback")
st.info("""
If no AI providers are configured or available, the application will automatically use a built-in statistical analysis system.
This provides basic answers to common questions without requiring any external API calls.
""")

# Add additional information at the bottom
st.markdown("---")
st.markdown("""
### How to obtain API keys:
- **OpenAI API Key**: Sign up at [OpenAI Platform](https://platform.openai.com/)
- **Anthropic API Key**: Sign up at [Anthropic Console](https://console.anthropic.com/)
- **DeepSeek API Key**: Sign up at [DeepSeek AI](https://platform.deepseek.ai/)

### Note on Security:
API keys are stored in the local .env file. They are never shared or transmitted outside the application.
""")

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

# Add the chat component from the shared module
import sys
import os
# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simple_chat import display_chat_widget
display_chat_widget()