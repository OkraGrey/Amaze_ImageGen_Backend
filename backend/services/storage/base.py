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
    def get_upload_path(self, identifier: str) -> str:
        """
        Gets the full path for an uploaded file from its identifier.
        """
        pass

    @abstractmethod
    def get_result_path(self, identifier: str) -> str:
        """
        Gets the full path for a result file from its identifier.
        """
        pass
    
    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """
        Checks if a file exists at the given path.
        """
        pass

    @abstractmethod
    def get_results_uri(self, identifier: str) -> str:
        """
        Returns a URI for accessing the result file.
        """
        pass
