import os
import sys

# Ensure the root directory is in python path for serverless environment imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

app = create_app()
