import sys
import os

# cPanel's Passenger usually sets the cwd to the application root.
# We insert the current directory to the front of the path to ensure
# we import 'app' from this folder, not some system package.
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

# The 'application' object is what Passenger looks for
application = create_app()
