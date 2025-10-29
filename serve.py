#!/usr/bin/env python3
"""Simple HTTP server to serve the flashcards application."""

import http.server
import socketserver
import webbrowser
import os

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow local file access
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

def find_available_port(start_port=8000, max_attempts=10):
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            # Try to create a server on this port
            with socketserver.TCPServer(("", port), None) as test_server:
                test_server.allow_reuse_address = True
                return port
        except OSError:
            continue
    raise OSError(f"Could not find available port in range {start_port}-{start_port + max_attempts}")

def main():
    # Change to the directory containing this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    Handler = MyHTTPRequestHandler
    
    # Find available port
    try:
        port = find_available_port(PORT)
    except OSError as e:
        print(f"Error: {e}")
        return
    
    # Allow socket reuse to prevent "address already in use" errors
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", port), Handler) as httpd:
        url = f"http://localhost:{port}/flashcards.html"
        print(f"Server running at {url}")
        if port != PORT:
            print(f"(Port {PORT} was in use, using {port} instead)")
        print("Press Ctrl+C to stop the server")
        
        # Open browser automatically
        webbrowser.open(url)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    main()