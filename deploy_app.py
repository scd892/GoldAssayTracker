#!/usr/bin/env python3
"""
Deployment wrapper for AEG labsync Monitor Streamlit application
This script provides proper health check endpoints for deployment systems
"""

import os
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
import signal
import socket

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Health check endpoint
        if self.path in ['/', '/health', '/healthz']:
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress health check logs
        pass

def check_streamlit_ready(port=5000, timeout=60):
    """Check if Streamlit is ready to serve requests"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            if result == 0:
                return True
        except:
            pass
        time.sleep(1)
    return False

def start_health_server(port=8080):
    """Start health check server"""
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        print(f"Health check server started on port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"Health check server error: {e}")

def start_streamlit():
    """Start the Streamlit application"""
    env = os.environ.copy()
    env['STREAMLIT_SERVER_PORT'] = '5000'
    env['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
    env['STREAMLIT_SERVER_HEADLESS'] = 'true'
    
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.port', '5000',
        '--server.address', '0.0.0.0',
        '--server.headless', 'true'
    ]
    
    return subprocess.Popen(cmd, env=env)

def main():
    """Main deployment entry point"""
    print("Starting AEG labsync Monitor deployment...")
    
    # Start Streamlit application
    streamlit_process = start_streamlit()
    
    # Wait for Streamlit to be ready
    if check_streamlit_ready():
        print("Streamlit application is ready")
    else:
        print("Warning: Streamlit may not be fully ready")
    
    # Start health check server in a separate thread
    health_thread = threading.Thread(
        target=start_health_server, 
        args=(8080,), 
        daemon=True
    )
    health_thread.start()
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print("Shutting down...")
        streamlit_process.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Keep the main process alive
        streamlit_process.wait()
    except KeyboardInterrupt:
        print("Received interrupt signal")
    finally:
        streamlit_process.terminate()
        streamlit_process.wait()

if __name__ == "__main__":
    main()