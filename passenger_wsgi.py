import sys
import os

# cPanel's Passenger usually sets the cwd to the application root.
# However, to be safe, we can add it to the path.
sys.path.append(os.getcwd())

from app import create_app

# The 'application' object is what Passenger looks for
application = create_app()
