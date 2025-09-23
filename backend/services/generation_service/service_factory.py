from .base_service import BaseImageGenerationService
from .gemini_service import GeminiService
from .openai_service import OpenAIService
from backend.utils.logger import app_logger

# A registry of available services
SERVICES = {
    "gemini": GeminiService(),
    "openai": OpenAIService(),
}

def get_service(model_name: str) -> BaseImageGenerationService:

    app_logger.info(f"RECEIVED MODEL NAME IN GET SERVICE: {model_name}")
    service = SERVICES.get(model_name.lower())
    if not service:
        raise ValueError(f"Unsupported model: {model_name}")
    app_logger.info(f"RETURNING FACTORY OBJECT")
    return service
