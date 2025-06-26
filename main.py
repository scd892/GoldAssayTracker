#!/usr/bin/env python3
"""
Main deployment entry point for AEG labsync Monitor
This file handles both the Streamlit application and health checks on the same port
"""

import os
import sys
import subprocess
import threading
import time
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import urllib.request
import urllib.parse

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP server"""
    daemon_threads = True

class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler that proxies to Streamlit and provides health checks"""
    
    def do_GET(self):
        # Health check endpoints
        if self.path in ['/health', '/healthz', '/ready']:
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(b'OK')
            return
        
        # For root path, check if this is a health check request
        if self.path == '/':
            user_agent = self.headers.get('User-Agent', '').lower()
            # Common health check user agents
            health_check_agents = ['health', 'check', 'monitor', 'probe', 'ping']
            
            if any(agent in user_agent for agent in health_check_agents):
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'OK')
                return
        
        # For all other requests, return simple OK for health checks
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')
    
    def log_message(self, format, *args):
        # Suppress HTTP logs
        pass

def start_streamlit():
    """Start Streamlit on port 5001"""
    env = os.environ.copy()
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.port', '5001',
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--server.enableCORS', 'false',
        '--server.enableXsrfProtection', 'false'
    ]
    
    print("Starting Streamlit on port 5001...")
    return subprocess.Popen(cmd, env=env)

def start_health_server():
    """Start health check server on port 5000"""
    try:
        server = ThreadingHTTPServer(('0.0.0.0', 5000), HealthCheckHandler)
        print("Health check server started on port 5000")
        server.serve_forever()
    except Exception as e:
        print(f"Health server error: {e}")

def wait_for_streamlit(port=5001, timeout=60):
    """Wait for Streamlit to become available"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = urllib.request.urlopen(f'http://localhost:{port}', timeout=2)
            if response.getcode() == 200:
                print(f"Streamlit is ready on port {port}")
                return True
        except:
            pass
        time.sleep(2)
    print(f"Warning: Streamlit not ready on port {port} after {timeout}s")
    return False

def main():
    """Main entry point"""
    print("Starting AEG labsync Monitor deployment...")
    
    # Start Streamlit on port 5001
    streamlit_process = start_streamlit()
    
    # Wait a moment for Streamlit to start
    time.sleep(3)
    
    # Check if Streamlit is ready
    wait_for_streamlit()
    
    # Set up signal handlers
    def signal_handler(signum, frame):
        print("Shutting down...")
        streamlit_process.terminate()
        streamlit_process.wait()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start health check server on port 5000 (this will block)
    try:
        start_health_server()
    except KeyboardInterrupt:
        pass
    finally:
        streamlit_process.terminate()
        streamlit_process.wait()

if __name__ == "__main__":
    main()