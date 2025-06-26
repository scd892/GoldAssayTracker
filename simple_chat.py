import streamlit as st
import pandas as pd
import sqlite3
from database import get_deviations_from_benchmark
from ai_chat import answer_data_query

def display_chat_widget():
    """
    Display a simple AI chat widget in the sidebar
    """
    # Get the page name to create unique widget keys
    import inspect
    import os
    page_name = os.path.basename(inspect.stack()[1].filename).replace(".py", "")
    
    # Initialize session state for chat
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "ai", "content": "Hello! I'm your AI Assistant. Ask me questions about the assay data, like 'Who is the assayer with the minimum deviation?' or 'How many assayers have deviation above 0.1%?'"}
        ]
    
    # Check if a chat session is active
    if "chat_active" not in st.session_state:
        st.session_state.chat_active = False
    
    # Add a simple button to toggle chat session
    with st.sidebar:
        st.write("## AI Chat Assistant")
        if st.button("💬 Open Chat", key=f"open_chat_{page_name}", use_container_width=True):
            st.session_state.chat_active = True
    
    # If chat is active, show the chat interface in an expander
    if st.session_state.chat_active:
        with st.sidebar.expander("AI Chat Assistant", expanded=True):
            # Display previous messages
            for message in st.session_state.chat_messages:
                if message["role"] == "user":
                    st.markdown(f"**You:** {message['content']}")
                else:
                    st.markdown(f"**🤖 AI:** {message['content']}")
            
            # Control buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Clear Chat", key=f"clear_chat_{page_name}", use_container_width=True):
                    st.session_state.chat_messages = [
                        {"role": "ai", "content": "Hello! I'm your AI Assistant. Ask me questions about the assay data, like 'Who is the assayer with the minimum deviation?' or 'How many assayers have deviation above 0.1%?'"}
                    ]
                    st.rerun()
            with col2:
                if st.button("Close Chat", key=f"close_chat_{page_name}", use_container_width=True):
                    st.session_state.chat_active = False
                    st.rerun()
            
            # Input area
            user_input = st.text_input("Ask me about the data:", key=f"chat_input_{page_name}", placeholder="Type your question here...")
            if st.button("Send", key=f"send_chat_{page_name}", use_container_width=True) and user_input:
                # Add user message to chat history
                st.session_state.chat_messages.append({"role": "user", "content": user_input})
                
                # Get the data for AI response
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
                    if deviations_df is None or deviations_df.empty:
                        deviations_df = None
                else:
                    deviations_df = None
                
                conn.close()
                
                # Generate AI response based on data availability
                if deviations_df is not None and not deviations_df.empty:
                    with st.spinner("Thinking..."):
                        ai_response = answer_data_query(user_input, deviations_df)
                elif benchmark_df.empty:
                    ai_response = "No benchmark assayer has been set. Please go to the Daily Monitoring page to set a benchmark assayer before I can analyze deviations."
                elif not has_assay_data:
                    ai_response = "There are no assay results in the database yet. Please add some data in the Data Entry page."
                else:
                    ai_response = "I don't have enough comparative data to answer that question. Please make sure you have multiple assayers testing the same samples."
                
                # Add AI response to chat history
                st.session_state.chat_messages.append({"role": "ai", "content": ai_response})
                
                # Refresh the UI
                st.rerun()