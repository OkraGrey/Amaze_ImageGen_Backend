from openai import OpenAI
import base64
import os
from backend.services.generation_service.base_service import BaseImageGenerationService
from PIL import Image
from io import BytesIO
import os
import uuid
from pathlib import Path
from backend.config.settings import RESULT_DIR
from backend.utils.logger import app_logger
from backend.config.settings import OPENAI_API_KEY, OPENAI_MODEL

class OpenAIService(BaseImageGenerationService):    
    def __init__(self):
        app_logger.info(f"INITIALIZING OPENAI SERVICE WITH MODEL: {OPENAI_MODEL}")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL
    
    def generate_image(self, prompt, image_path=None):

        app_logger.info(f"RECIEVED PROMPT: {prompt}")
        try:
            result = None
            if image_path and os.path.exists(image_path):
                app_logger.info(f"RECIEVED IMAGE PATH")
                result = self.client.images.edit(
                    model=self.model,
                    image=[open(image_path, "rb")],
                    prompt=prompt,
                    input_fidelity="high",
                    quality="high"
                )
            else:
                app_logger.info(f"NO IMAGE PATH PROVIDED. ATTEMPTING GENERATION WITH PROMPT ONLY")
                
                result = self.client.images.generate(
                    model=self.model,
                    prompt=prompt,
                    quality="high"
                )
            
            app_logger.info(f"SAVING THE GENERATED IMAGE")
            result_path = None
            image_base64 = result.data[0].b64_json
            image_bytes = base64.b64decode(image_base64)
            # Generate a unique filename
            filename = f"generated_{uuid.uuid4().hex}.png"
            result_path = os.path.join(RESULT_DIR, filename)
            with open(result_path, "wb") as f:
                f.write(image_bytes)
            app_logger.info(f"IMAGE SAVED SUCCESSFULLY AT: {result_path}")
            return result_path
        except Exception as e:
            app_logger.error(f"ERROR GENERATING IMAGE WITH OPENAI SERVICE: {str(e)}")
            raise
