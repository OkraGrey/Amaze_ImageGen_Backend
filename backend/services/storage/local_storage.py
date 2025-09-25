import os
import uuid
from fastapi import UploadFile
from backend.services.storage.base import FileStorage
from backend.config.settings import UPLOAD_DIR, RESULT_DIR, MAX_FILE_SIZE
from backend.utils.file_utils import allowed_file

class LocalStorage(FileStorage):
    def _save_upload(self, file: UploadFile) -> str:
        # Check file size
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds the maximum allowed size of {MAX_FILE_SIZE / (1024 * 1024)}MB")
        
        # Generate a unique filename
        original_filename = file.filename
        extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        identifier = f"{uuid.uuid4().hex}.{extension}"
        
        # Save the file
        file_path = os.path.join(UPLOAD_DIR, identifier)
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())
        
        return identifier

    def save_result(self, image_data: bytes, extension: str = 'png') -> str:
        filename = f"generated_{uuid.uuid4().hex}.{extension}"
        file_path = os.path.join(RESULT_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(image_data)
        return filename

    def _get_upload_path(self, identifier: str) -> str:
        return os.path.join(UPLOAD_DIR, identifier)

    def _get_result_path(self, identifier: str) -> str:
        return os.path.join(RESULT_DIR, identifier)

    def get_results_uri(self, identifier: str) -> str:
        return f"/results/{identifier}"

    def get_upload_content(self, identifier: str) -> bytes:
        path = self._get_upload_path(identifier)
        with open(path, "rb") as f:
            return f.read()

    def get_result_content(self, identifier: str) -> bytes:
        path = self._get_result_path(identifier)
        with open(path, "rb") as f:
            return f.read()