import streamlit as st
import pandas as pd
import sqlite3
from database import get_deviations_from_benchmark
from ai_chat import answer_data_query

def display_chat_widget(hide_on_pages=None):
    """
    Display the AI chat widget on specified pages
    
    Args:
        hide_on_pages: List of page paths where the chat should be hidden
    """
    # Get current page path for creating unique keys
    import inspect
    import os
    import random
    import string
    
    # We need a page-specific session state for the chat widget
    # Get the current page path
    current_page = os.path.basename(inspect.stack()[1].filename).replace(".py", "")
    
    # Create a page-specific key for the chat widget display state
    page_display_key = f"chat_widget_displayed_{current_page}"
    
    # Initialize the page-specific display state if it doesn't exist
    if page_display_key not in st.session_state:
        st.session_state[page_display_key] = True
    
    # Get the calling filename to use as part of the key
    caller_filename = os.path.basename(inspect.stack()[1].filename)
    page_key = caller_filename.replace(".py", "").replace(".", "_").lower()
    
    # Add a random suffix to ensure uniqueness
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    key_suffix = f"{page_key}_{random_suffix}"
    
    # Don't show on specified pages
    if hide_on_pages and st._get_script_run_ctx().page_script_hash in hide_on_pages:
        return
    
    # Initialize session state for chat
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "ai", "content": "Hello! I'm your AI Assistant. Ask me questions about the assay data, like 'Who is the assayer with the minimum deviation?' or 'How many assayers have deviation above 0.1%?'"}
        ]
    
    # Create a page-specific key for the chat visibility
    chat_visible_key = f"chat_visible_{current_page}"
    
    # Initialize the page-specific chat visibility if it doesn't exist
    if chat_visible_key not in st.session_state:
        st.session_state[chat_visible_key] = False
    
    # Add CSS for chat components
    st.markdown("""
    <style>
    .chat-window {
        position: fixed;
        bottom: 90px;
        right: 20px;
        width: 350px;
        max-height: 500px;
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        z-index: 9998;
        overflow: hidden;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .user-message {
        align-self: flex-end;
        background-color: #D4AF37;  /* Gold color for user messages */
        border-radius: 18px 18px 4px 18px;
        padding: 10px 14px;
        margin: 8px 0;
        max-width: 85%;
        font-size: 0.9rem;
        color: white;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        word-wrap: break-word;
    }
    
    .ai-message {
        align-self: flex-start;
        background-color: #4682B4;  /* Steel Blue for AI responses */
        border-radius: 18px 18px 18px 4px;
        padding: 10px 14px;
        margin: 8px 0;
        max-width: 85%;
        font-size: 0.9rem;
        color: white;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        word-wrap: break-word;
    }
    
    /* Style for the streamlit button elements inside our components */
    .stButton button {
        border-radius: 20px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    /* Specific styling for form buttons */
    [data-testid="baseButton-secondaryFormSubmit"] {
        background-color: #D4AF37 !important;
        color: white !important;
        border: none !important;
        padding: 2px 15px !important;
    }
    
    /* Better focus styles for accessibility */
    .stButton button:focus {
        box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.5) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create a container for the chat widget in the sidebar
    chat_container = st.container()
    
    with chat_container:
        # Add fixed-position chat button with custom styling
        st.markdown("""
        <style>
        .floating-chat-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
        }
        
        .floating-chat-btn button {
            width: 60px !important;
            height: 60px !important;
            border-radius: 30px !important;
            background-color: #D4AF37 !important;
            color: white !important;
            font-size: 24px !important;
            border: none !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
            transition: all 0.3s ease !important;
        }
        
        .floating-chat-btn button:hover {
            background-color: #B8860B !important;
            box-shadow: 0 6px 12px rgba(0,0,0,0.3) !important;
        }
        </style>
        <div class="floating-chat-btn">
        """, unsafe_allow_html=True)
        
        chat_button = st.button("💬", key=f"chat_btn_{key_suffix}", help="AI Chat Assistant")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Update chat visibility if button is clicked
        if chat_button:
            st.session_state[chat_visible_key] = not st.session_state[chat_visible_key]
            st.rerun()
        
        # Chat window (conditionally visible)
        if st.session_state[chat_visible_key]:
            # Create a fixed positioned chat window
            st.markdown("""
            <div class="chat-window">
            """, unsafe_allow_html=True)
            
            # Add a styled container for the header
            st.markdown("""
            <div style="background-color: #D4AF37; color: white; padding: 8px 12px; font-weight: bold; 
                      display: flex; justify-content: space-between; align-items: center;">
                <span>AI Chat Assistant</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Add close button
            if st.button("✕ Close", key=f"close_chat_btn_{key_suffix}", help="Close Chat"):
                st.session_state[chat_visible_key] = False
                st.rerun()
            
            # Add a clear chat button
            if st.button("🗑️ Clear Chat", key=f"clear_chat_btn-{key_suffix}", help="Clear all chat messages"):
                st.session_state.chat_messages = [
                    {"role": "ai", "content": "Hello! I'm your AI Assistant. Ask me questions about the assay data, like 'Who is the assayer with the minimum deviation?' or 'How many assayers have deviation above 0.1%?'"}
                ]
                st.rerun()
            
            # Display chat messages
            chat_messages = st.container()
            with chat_messages:
                for message in st.session_state.chat_messages:
                    if message["role"] == "user":
                        st.markdown(f"<div class='user-message'>{message['content']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='ai-message'>{message['content']}</div>", unsafe_allow_html=True)
            
            # Check if we have any data and if benchmark is set
            conn = sqlite3.connect('gold_assay.db')
            
            # Check if benchmark is set
            benchmark_df = pd.read_sql("SELECT assayer_id FROM benchmark_assayers WHERE is_active = 1 LIMIT 1", conn)
            
            # Check if we have any assay results
            assay_count_df = pd.read_sql("SELECT COUNT(*) as count FROM assay_results", conn)
            has_assay_data = assay_count_df.iloc[0]['count'] > 0 if not assay_count_df.empty else False
            
            # Get the data only if benchmark is set
            if not benchmark_df.empty:
                # Get all data from the past year (365 days) to ensure we have data
                deviations_df = get_deviations_from_benchmark(days=365)
                
                # Check if the data is empty after loading
                if deviations_df is None or deviations_df.empty:
                    deviations_df = None
            else:
                deviations_df = None
                
            conn.close()
                
            # Initialize a session state variable to track form submission
            if "chat_submitted" not in st.session_state:
                st.session_state.chat_submitted = False
                
            # Create a form to capture the input properly
            with st.form(key=f"chat_form_{key_suffix}", clear_on_submit=True):
                # Chat input field (using markdown to reduce size)
                st.markdown("<div style='font-size:0.8rem; margin-bottom:-15px;'>Ask me about the data:</div>", unsafe_allow_html=True)
                
                # Input field inside the form
                form_input = st.text_input("Ask me about the data", 
                                key=f"chat_form_input_{key_suffix}",
                                label_visibility="collapsed",
                                placeholder="e.g., Who has the lowest deviation?")
                
                # Submit button (hidden with empty label and small size)
                submitted = st.form_submit_button("Send", help="Send message")
                
                # Process the form submission
                if submitted and form_input:
                    # Set the flag to process this input
                    st.session_state.chat_submitted = True
                    st.session_state.current_input = form_input
            
            # Handle the form submission outside the form
            if st.session_state.chat_submitted:
                # Reset the submission flag
                st.session_state.chat_submitted = False
                
                # Get the input from session state
                current_input = st.session_state.current_input
                
                # Add user message to chat history
                st.session_state.chat_messages.append({"role": "user", "content": current_input})
                
                # Generate AI response based on data availability
                if deviations_df is not None and not deviations_df.empty:
                    with st.spinner("Thinking..."):
                        ai_response = answer_data_query(current_input, deviations_df)
                elif benchmark_df.empty:
                    ai_response = "No benchmark assayer has been set. Please go to the Daily Monitoring page to set a benchmark assayer before I can analyze deviations."
                elif not has_assay_data:
                    ai_response = "There are no assay results in the database yet. Please add some data in the Data Entry page."
                else:
                    ai_response = "I don't have enough comparative data to answer that question. Please make sure you have multiple assayers testing the same samples."
                
                # Add AI response to chat history
                st.session_state.chat_messages.append({"role": "ai", "content": ai_response})
                
                # Rerun to update the chat display
                st.rerun()
                
            # Close the fixed div container
            st.markdown("</div>", unsafe_allow_html=True)