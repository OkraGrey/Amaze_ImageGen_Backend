from abc import ABC, abstractmethod

class BaseImageGenerationService(ABC):

    @abstractmethod
    def generate_image(self, prompt: str, image_path: str = None) -> str:
        pass

