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

def remove_bg(input_path):

    app_logger.info(f"STARTING PHOTOTOOM BACKGROUND REMOVAL FOR: {input_path}")

    # Get API key from environment
    api_key = os.getenv('PHOTOTOOM_API_KEY')
    if not api_key:
        app_logger.error(f"PHOTOTOOM API KEY NOT FOUND IN ENVIRONMENT VARIABLES")
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

        app_logger.info(f"Reading image file for PhotoRoom API")

        # Prepare the POST data
        with open(input_path, 'rb') as f:
            image_data = f.read()
        filename = os.path.basename(input_path)

        body = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"image_file\"; filename=\"{filename}\"\r\n"
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode('utf-8') + image_data + f"\r\n--{boundary}--\r\n".encode('utf-8')

        app_logger.info(f"CALLING PHOTOTOOM API FOR BACKGROUND REMOVAL")

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
            app_logger.info(f"PHOTOTOOM BACKGROUND REMOVAL SUCCESSFUL")
            app_logger.info(f"IMAGE SAVED TO: {output_path}")
        else:
            error_msg = f"PhotoRoom API error: {response.status} - {response.reason}"
            app_logger.error(f"ERROR OCCURED: {error_msg}")
            error_body = response.read()
            app_logger.error(f"RESPONSE: {error_body}")
            raise Exception(error_msg)

        # Close the connection
        conn.close()

        return output_path

    except Exception as e:
        app_logger.error(f"FAILED TO REMOVE BACKGROUND USING PHOTOTOOM: {str(e)}")
        raise
