from abc import ABC, abstractmethod
from fastapi import UploadFile
from backend.config.settings import MAX_FILE_SIZE
from backend.utils.custom_exceptions import FileTooLargeError

class FileStorage(ABC):
    def save_upload(self, file: UploadFile) -> str:
        # Check file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        if file_size > MAX_FILE_SIZE:
            raise FileTooLargeError(f"File size {file_size} exceeds the limit of {MAX_FILE_SIZE} bytes.")
        
        return self._save_upload(file)

    @abstractmethod
    def _save_upload(self, file: UploadFile) -> str:
        """Platform-specific implementation for saving an uploaded file."""
        pass

    @abstractmethod
    def save_result(self, image_data: bytes, extension: str = "png") -> str:
        """Save the generated image and return its identifier."""
        pass

    @abstractmethod
    def get_upload_content(self, identifier: str) -> bytes:
        """Retrieve the content of an uploaded file."""
        pass

    @abstractmethod
    def get_result_content(self, identifier: str) -> bytes:
        """Retrieve the content of a result file."""
        pass

    @abstractmethod
    def get_results_uri(self, identifier: str) -> str:
        """Get the URI for a result file."""
        pass