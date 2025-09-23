import os
import uuid
from pathlib import Path
import mimetypes
from backend.utils.logger import app_logger
import http.client


def process_download_image(input_path: str, api_key: str) -> str:
    filename_stem = Path(input_path).stem
    unique_suffix = uuid.uuid4().hex[:8]
    output_path = os.path.join(
        os.path.dirname(input_path),
        f"{filename_stem}_NO_BG_{unique_suffix}.png"
    )
    app_logger.info("INSIDE PROCESS DOWNLOAD IMAGE FUNCTION")
    try:
        boundary = '----------{}'.format(uuid.uuid4().hex)

        content_type, _ = mimetypes.guess_type(input_path)
        if content_type is None:
            content_type = 'application/octet-stream'

        app_logger.info("READING IMAGE FILE FOR PHOTOTOOM API")
        # Prepare the POST data
        app_logger.info("PREPARING READING IMAGE FILE")
        with open(input_path, 'rb') as f:
            image_data = f.read()
        filename = os.path.basename(input_path)

        body = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"image_file\"; filename=\"{filename}\"\r\n"
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode('utf-8') + image_data + f"\r\n--{boundary}--\r\n".encode('utf-8')

        app_logger.info(
            f"CALLING PHOTOTOOM API FOR BACKGROUND REMOVAL WITH FILE PATH: {input_path}"
        )
        # Set up the HTTP connection and headers
        conn = http.client.HTTPSConnection('sdk.photoroom.com')

        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'x-api-key': api_key,
        }

        # Make the POST request
        conn.request('POST', '/v1/segment', body=body, headers=headers)
        response = conn.getresponse()

        # Handle the response
        if response.status == 200:
            response_data = response.read()
            with open(output_path, 'wb') as out_f:
                out_f.write(response_data)
            app_logger.info("PHOTOTOOM BACKGROUND REMOVAL SUCCESSFUL")
            app_logger.info(f"IMAGE SAVED TO: {output_path}")
        else:
            error_body = response.read()
            error_msg = f"PhotoRoom API error: {response.status} - {response.reason}"
            app_logger.error(error_msg)
            app_logger.error(f"RESPONSE: {error_body}")
            raise Exception(error_msg)

        # Close the connection
        conn.close()
        return output_path

    except Exception as e:
        app_logger.error(f"FAILED TO REMOVE BACKGROUND USING PHOTOTOOM: {str(e)}")
        raise