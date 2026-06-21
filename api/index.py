import sys
import os

# Append root directory to path to allow importing app.py and its dependencies
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
