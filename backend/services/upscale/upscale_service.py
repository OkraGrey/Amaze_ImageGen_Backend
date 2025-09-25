import requests
from PIL import Image
from io import BytesIO
from backend.config.settings import PICSART_API_KEY, PICSART_UPSCALE_URL
from backend.services.storage.base import FileStorage
from backend.utils.logger import app_logger

class PicsartUpscaleService:
    def __init__(self, storage_service: FileStorage):
        self.storage_service = storage_service
        if not PICSART_API_KEY:
            raise ValueError("Picsart API key is not configured.")
        self.api_key = PICSART_API_KEY
        self.upscale_url = PICSART_UPSCALE_URL

    def upscale_image(self, image_identifier: str, upscale_factor: int) -> tuple[str, str, str]:
        app_logger.info(f"Starting image upscaling for identifier: {image_identifier} with factor: {upscale_factor}")

        try:
            try:
                image_content = self.storage_service.get_result_content(image_identifier)
                app_logger.info(f"Found image in results for identifier: {image_identifier}")
            except FileNotFoundError:
                app_logger.info(f"Image not found in results, trying uploads for identifier: {image_identifier}")
                image_content = self.storage_service.get_upload_content(image_identifier)
                app_logger.info(f"Found image in uploads for identifier: {image_identifier}")

        except FileNotFoundError:
            app_logger.error(f"Image not found for identifier: {image_identifier}")
            raise FileNotFoundError(f"Image with identifier {image_identifier} not found.")
        
        # Get input image resolution
        input_image = Image.open(BytesIO(image_content))
        input_resolution = f"{input_image.width}x{input_image.height}"
        app_logger.info(f"Input image resolution: {input_resolution}")

        headers = {
            "accept": "application/json",
            "X-Picsart-API-Key": self.api_key,
        }
        data = {
            "upscale_factor": str(upscale_factor),
            "format": "PNG",
        }
        files = {"image": image_content}

        app_logger.info(f"Sending request to Picsart API for upscaling.")
        response = requests.post(self.upscale_url, headers=headers, data=data, files=files, timeout=90)
        response.raise_for_status()
        
        resp_json = response.json()
        result_url = resp_json["data"]["url"]
        app_logger.info(f"Successfully received upscaled image URL from Picsart API.")

        app_logger.info(f"Downloading upscaled image from: {result_url}")
        r = requests.get(result_url, timeout=90)
        r.raise_for_status()
        upscaled_image_content = r.content
        app_logger.info(f"Upscaled image downloaded successfully.")

        # Get upscaled image resolution
        upscaled_image = Image.open(BytesIO(upscaled_image_content))
        upscaled_resolution = f"{upscaled_image.width}x{upscaled_image.height}"
        app_logger.info(f"Upscaled image resolution: {upscaled_resolution}")

        app_logger.info(f"Saving upscaled image to storage.")
        new_identifier = self.storage_service.save_result(upscaled_image_content, extension="png")
        app_logger.info(f"Upscaled image saved with new identifier: {new_identifier}")

        return new_identifier, input_resolution, upscaled_resolution
