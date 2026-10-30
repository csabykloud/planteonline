import sys
import os

# Set application directory in python search path
app_dir = os.path.dirname(__file__)
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Import the Flask app object as 'application' (required by cPanel / Phusion Passenger WSGI)
from app import app as application
