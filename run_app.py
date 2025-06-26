#!/usr/bin/env python3
"""
Production deployment runner for AEG labsync Monitor
Handles proper startup and health check responses for deployment systems
"""

import os
import sys
import subprocess
import signal
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import socket

class DeploymentHealthHandler(BaseHTTPRequestHandler):
    """Handle health check requests for deployment systems"""
    
    def do_GET(self):
        if self.path in ['/', '/health', '/healthz', '/ready']:
            # Check if Streamlit is responding
            try:
                response = urllib.request.urlopen('http://localhost:5000', timeout=5)
                if response.getcode() == 200:
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    self.send_header('Cache-Control', 'no-cache')
                    self.end_headers()
                    self.wfile.write(b'OK - Streamlit app is running')
                else:
                    self.send_error(503, 'Streamlit app not ready')
            except Exception:
                self.send_error(503, 'Streamlit app not responding')
        else:
            self.send_error(404, 'Not found')
    
    def log_message(self, format, *args):
        # Suppress logs to keep output clean
        pass

def start_health_server():
    """Start health check server on port 8080"""
    try:
        server = HTTPServer(('0.0.0.0', 8080), DeploymentHealthHandler)
        print("Health check server started on port 8080")
        server.serve_forever()
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print("Port 8080 already in use, trying port 8081")
            try:
                server = HTTPServer(('0.0.0.0', 8081), DeploymentHealthHandler)
                print("Health check server started on port 8081")
                server.serve_forever()
            except Exception as e2:
                print(f"Health server error on port 8081: {e2}")
        else:
            print(f"Health server error: {e}")
    except Exception as e:
        print(f"Health server error: {e}")

def wait_for_streamlit(timeout=60):
    """Wait for Streamlit to become available"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = urllib.request.urlopen('http://localhost:5000', timeout=2)
            if response.getcode() == 200:
                print("Streamlit is ready")
                return True
        except:
            pass
        time.sleep(2)
    return False

def main():
    """Main deployment entry point"""
    print("Starting AEG labsync Monitor for deployment...")
    
    # Start health check server in background
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Start Streamlit
    env = os.environ.copy()
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.port', '5000',
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--server.enableCORS', 'false',
        '--server.enableXsrfProtection', 'false'
    ]
    
    streamlit_process = subprocess.Popen(cmd, env=env)
    
    # Wait for Streamlit to be ready
    if wait_for_streamlit():
        print("Application is ready for deployment")
    else:
        print("Warning: Application may not be fully ready")
    
    # Handle shutdown signals
    def signal_handler(signum, frame):
        print("Shutting down gracefully...")
        streamlit_process.terminate()
        streamlit_process.wait()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        streamlit_process.wait()
    except KeyboardInterrupt:
        pass
    finally:
        streamlit_process.terminate()

if __name__ == "__main__":
    main()