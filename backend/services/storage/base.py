from abc import ABC, abstractmethod
from fastapi import UploadFile

class FileStorage(ABC):
    @abstractmethod
    def save_upload(self, file: UploadFile) -> str:
        """
        Saves an uploaded file and returns a unique identifier for it.
        """
        pass

    @abstractmethod
    def save_result(self, image_data: bytes, extension: str = 'png') -> str:
        """
        Saves a generated image and returns a unique identifier for it.
        """
        pass

    @abstractmethod
    def get_results_uri(self, identifier: str) -> str:
        """
        Returns a URI for accessing the result file.
        """
        pass
    
    @abstractmethod
    def get_upload_content(self, identifier: str) -> bytes:
        """
        Gets the content of an uploaded file as bytes.
        """
        pass

    @abstractmethod
    def get_result_content(self, identifier: str) -> bytes:
        """
        Gets the content of a result file as bytes.
        """
        pass