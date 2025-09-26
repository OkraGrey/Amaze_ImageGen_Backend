import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PHOTOTOOM_API_KEY = os.getenv("PHOTOTOOM_API_KEY")
PICSART_API_KEY = os.getenv("PICSART_API_KEY")

# Picsart API
PICSART_UPSCALE_URL = "https://api.picsart.io/tools/1.0/upscale"

# Gemini model configuration
GEMINI_IMG_MODEL = "gemini-2.5-flash-image-preview"
GEMINI_DESC_MODEL = "gemini-2.5-flash"

OPENAI_IMG_MODEL = "gpt-image-1"
OPENAI_DESC_MODEL = "gpt-5"

# Check if running on Vercel
if os.getenv("VERCEL") == "1":
    # Use the /tmp directory for uploads and results on Vercel
    UPLOAD_DIR = "/tmp/uploads"
    RESULT_DIR = "/tmp/results"
else:
    # Local setup
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
    RESULT_DIR = os.path.join(BASE_DIR, "results")

# Upload configuration
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Result configuration
os.makedirs(RESULT_DIR, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

# Max file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Storage Type
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "gcp") # gcp for Google Drive

# Google Drive settings
GOOGLE_DRIVE_APP_FOLDER_ID = os.getenv("GOOGLE_DRIVE_APP_FOLDER_ID") 
GOOGLE_CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "client_secret.json")
GOOGLE_TOKEN_FILE = os.path.join(BASE_DIR, "token.json")