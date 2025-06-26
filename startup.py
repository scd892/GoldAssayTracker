#!/usr/bin/env python3
"""
Startup script that ensures proper deployment health checks for Streamlit
"""
import subprocess
import sys
import time
import threading
import socket

def check_port_available(port):
    """Check if a port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('', port))
        sock.close()
        return True
    except:
        sock.close()
        return False

def start_streamlit():
    """Start Streamlit application"""
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port", "5000",
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false"
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process

if __name__ == "__main__":
    # Start Streamlit
    print("Starting AEG labsync Monitor...")
    
    # Ensure port 5000 is available
    if not check_port_available(5000):
        print("Port 5000 is already in use, attempting to start anyway...")
    
    # Start the application
    streamlit_process = start_streamlit()
    
    try:
        # Wait for the process
        streamlit_process.wait()
    except KeyboardInterrupt:
        print("Shutting down...")
        streamlit_process.terminate()
        streamlit_process.wait()