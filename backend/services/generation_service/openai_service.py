from openai import OpenAI
import base64
import os
from backend.services.generation_service.base_service import BaseImageGenerationService
from PIL import Image
from io import BytesIO
import os
import uuid
from pathlib import Path
from backend.utils.logger import app_logger
from backend.config.settings import OPENAI_API_KEY, OPENAI_IMG_MODEL, OPENAI_DESC_MODEL
from backend.services.storage.storage_factory import get_storage_service

class OpenAIService(BaseImageGenerationService):    
    def __init__(self):
        app_logger.info(f"INITIALIZING OPENAI SERVICE")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.img_model = OPENAI_IMG_MODEL
        self.desc_model = OPENAI_DESC_MODEL
        self.storage_service = get_storage_service()
    
    def generate_image(self, prompt, image_path=None):

        app_logger.info(f"RECIEVED PROMPT: {prompt}")
        try:
            result = None
            if image_path and self.storage_service.file_exists(image_path):
                app_logger.info(f"RECIEVED IMAGE PATH")
                result = self.client.images.edit(
                    model=self.img_model,
                    image=[open(image_path, "rb")],
                    prompt=prompt,
                    input_fidelity="high",
                    quality="high"
                )
            else:
                app_logger.info(f"NO IMAGE PATH PROVIDED. ATTEMPTING GENERATION WITH PROMPT ONLY")
                
                result = self.client.images.generate(
                    model=self.img_model,
                    prompt=prompt,
                    quality="high"
                )
            
            app_logger.info(f"SAVING THE GENERATED IMAGE")
            result_identifier = None
            image_base64 = result.data[0].b64_json
            image_bytes = base64.b64decode(image_base64)
            result_identifier = self.storage_service.save_result(image_bytes, extension='png')
            app_logger.info(f"IMAGE SAVED SUCCESSFULLY WITH IDENTIFIER: {result_identifier}")
            return result_identifier
        except Exception as e:
            app_logger.error(f"ERROR GENERATING IMAGE WITH OPENAI SERVICE: {str(e)}")
            raise
