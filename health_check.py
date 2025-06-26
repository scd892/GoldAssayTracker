#!/usr/bin/env python3
"""
Health check endpoint for deployment verification
"""

import http.server
import socketserver
import threading
import time
import os

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

def start_health_check_server(port=8080):
    """Start a simple health check server on a different port"""
    try:
        with socketserver.TCPServer(("", port), HealthCheckHandler) as httpd:
            print(f"Health check server running on port {port}")
            httpd.serve_forever()
    except Exception as e:
        print(f"Health check server error: {e}")

def run_health_check_daemon():
    """Run health check server in daemon thread"""
    health_thread = threading.Thread(target=start_health_check_server, daemon=True)
    health_thread.start()
    return health_thread

if __name__ == "__main__":
    # For standalone health check testing
    start_health_check_server()