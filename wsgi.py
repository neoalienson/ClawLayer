"""WSGI entry point for production servers (gunicorn, uWSGI, etc.)"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clawlayer.app import create_app

# Create Flask app instance
clawlayer_app = create_app(verbose=1)
app = clawlayer_app.app

if __name__ == "__main__":
    # For testing: python wsgi.py
    app.run(port=11435)
