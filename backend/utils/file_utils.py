import os
import uuid
from pathlib import Path
import http.client
import mimetypes
from backend.config.settings import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def allowed_file(filename):

    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file):
    """
    Save an uploaded file to the upload directory.
    
    Args:
        file: The uploaded file object
        
    Returns:
        str: Path to the saved file
    """
    # Check file size
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File size exceeds the maximum allowed size of {MAX_FILE_SIZE / (1024 * 1024)}MB")
    
    # Generate a unique filename
    original_filename = file.filename
    extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    filename = f"{uuid.uuid4().hex}.{extension}"
    
    # Use tmp subdirectory for test uploads and temporary files
    tmp_dir = os.path.join(UPLOAD_DIR, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    
    # Save the file in tmp directory
    file_path = os.path.join(tmp_dir, filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
    
    return file_path

def remove_bg(input_path):
    """
    Removes the background from an image using PhotoRoom API.

    Args:
        input_path (str): The path to the input image.

    Returns:
        str: The path to the output image with the background removed.
    """
    print(f"[INFO]--- Starting PhotoRoom background removal for: {input_path} ---")

    # Get API key from environment
    api_key = os.getenv('PHOTOTOOM_API_KEY')
    if not api_key:
        print(f"[ERROR]--- PhotoRoom API key not found in environment variables ---")
        raise ValueError("PhotoRoom API key not configured")

    # Create output path with unique suffix
    filename = Path(input_path).stem
    unique_suffix = uuid.uuid4().hex[:8]
    output_path = os.path.join(os.path.dirname(input_path), f"{filename}_no_bg_{unique_suffix}.png")

    try:
        # Define multipart boundary
        boundary = '----------{}'.format(uuid.uuid4().hex)

        # Get mimetype of image
        content_type, _ = mimetypes.guess_type(input_path)
        if content_type is None:
            content_type = 'application/octet-stream'

        print(f"[INFO]--- Reading image file for PhotoRoom API ---")

        # Prepare the POST data
        with open(input_path, 'rb') as f:
            image_data = f.read()
        filename = os.path.basename(input_path)

        body = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"image_file\"; filename=\"{filename}\"\r\n"
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode('utf-8') + image_data + f"\r\n--{boundary}--\r\n".encode('utf-8')

        print(f"[INFO]--- Calling PhotoRoom API for background removal ---")

        # Set up the HTTP connection and headers
        conn = http.client.HTTPSConnection('sdk.photoroom.com')

        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'x-api-key': api_key
        }

        # Make the POST request
        conn.request('POST', '/v1/segment', body=body, headers=headers)
        response = conn.getresponse()

        # Handle the response
        if response.status == 200:
            response_data = response.read()
            with open(output_path, 'wb') as out_f:
                out_f.write(response_data)
            print(f"[INFO]--- PhotoRoom background removal successful ---")
            print(f"[INFO]--- Image saved to: {output_path} ---")
        else:
            error_msg = f"PhotoRoom API error: {response.status} - {response.reason}"
            print(f"[ERROR]--- {error_msg} ---")
            error_body = response.read()
            print(f"[ERROR]--- Response: {error_body} ---")
            raise Exception(error_msg)

        # Close the connection
        conn.close()

        return output_path

    except Exception as e:
        print(f"[ERROR]--- Failed to remove background using PhotoRoom: {str(e)} ---")
        raise
