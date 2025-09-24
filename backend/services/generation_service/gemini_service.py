from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os
import uuid
from pathlib import Path

from backend.config.settings import GEMINI_API_KEY, GEMINI_DESC_MODEL,GEMINI_IMG_MODEL
from backend.services.generation_service.base_service import BaseImageGenerationService
from backend.utils.logger import app_logger
from backend.services.storage.storage_factory import get_storage_service

class GeminiService(BaseImageGenerationService):    
    def __init__(self):
        app_logger.info(f"INITIALIZING GEMINI SERVICE")
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.img_model = GEMINI_IMG_MODEL
        self.desc_model = GEMINI_DESC_MODEL
        self.storage_service = get_storage_service()
    
    def generate_image(self, prompt, image_path=None):
        try:
            contents = [prompt]
            if image_path and self.storage_service.file_exists(image_path):
                app_logger.info(f"RECIEVED IMAGE PATH")
                image = Image.open(image_path)
                contents.append(image)
            else:
                app_logger.info(f"NO IMAGE PATH PROVIDED. GOING FORWARD WITH PROMPT ONLY")
            
            app_logger.info(f"CALLING GEMINI CLIENT")
            response = self.client.models.generate_content(
                model=self.img_model,
                contents=contents
            )
            
            # Save the generated image
            app_logger.info(f"SAVING THE GENERATED IMAGE")
            result_identifier = None
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image_data = part.inline_data.data
                    result_identifier = self.storage_service.save_result(image_data, extension='png')
                    app_logger.info(f"IMAGE SAVED SUCCESSFULLY WITH IDENTIFIER: {result_identifier}")
                    break
            return result_identifier
        except Exception as e:
            print(f"ERROR GENERATING IMAGE: {str(e)}")
            raise
    
    def generate_image_description(self, image_path=None):
        app_logger.info(f"GENERATING IMAGE DESCRIPTION")
        try:
            # Initialized contents with the user prompt
            contents = ["Generate a detailed JSON description of the given image"]
            if image_path and self.storage_service.file_exists(image_path):
                print(f"[INFO]---RECIEVED IMAGE PATH---")
                image = Image.open(image_path)
                contents.append(image)
            else:
                app_logger.error(f"NO IMAGE PATH PROVIDED")
                raise ValueError("IMAGE PATH IS REQUIRED!")
            
            app_logger.info(f"CALLING GEMINI CLIENT")
            response = self.client.models.generate_content(
                model=self.desc_model,
                config=types.GenerateContentConfig(
                    system_instruction="""
                    You are an expert translator that converts images into detailed JSON descriptions for image generation models. Make sure to identify patterns, text, objects, colors explicitly with all other tiny details. 
                    # OUTPUT FORMAT: YOU Should return a JSON object only.
                    """
                ),
                contents=contents
            )
            
            app_logger.info(f"RESPONSE RECIEVED FROM GEMINI CLIENT")
            description = response.text
            if description.startswith("```json"):
                return description[7:-3]
            return description
        except Exception as e:
            print(f"ERROR GENERATING IMAGE DESCRIPTION: {str(e)}")
            raise

