import os
import uuid
from pathlib import Path
import http.client
import mimetypes
from backend.config.settings import ALLOWED_EXTENSIONS
from PIL import Image
from dotenv import load_dotenv
from backend.utils.logger import app_logger
# Load environment variables
load_dotenv()

def allowed_file(filename):

    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
