"""
pipeline package init
"""
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get API keys from environment
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SERPAPI_KEY = os.getenv('SERPAPI_KEY')
