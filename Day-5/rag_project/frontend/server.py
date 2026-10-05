"""
Frontend Development Server

Serves the Enterprise RAG Assistant Web UI on port 3000.
Run in a separate terminal:
    python server.py
or from project root:
    python -m http.server 3000 --directory frontend
"""

import http.server
import socketserver
import os
import sys

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Enable CORS for local cross-origin API calls if needed
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

if __name__ == "__main__":
    os.chdir(DIRECTORY)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("=" * 65)
        print("  ENTERPRISE RAG ASSISTANT - FRONTEND WEB UI")
        print("=" * 65)
        print(f"  Frontend is running at: http://localhost:{PORT}")
        print("  Connecting to backend:  http://localhost:8000")
        print("=" * 65)
        print("  Press Ctrl+C to stop the server\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nFrontend server stopped.")
            sys.exit(0)
