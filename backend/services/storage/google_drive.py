import os
import uuid
import tempfile
from fastapi import UploadFile
from backend.services.storage.base import FileStorage
from backend.config.settings import GOOGLE_DRIVE_APP_FOLDER_ID
from backend.utils.google_drive_utils import (
    get_drive_service,
    get_or_create_folder,
    upload_file_content,
    download_file,
    make_file_public
)

class GoogleDriveStorage(FileStorage):
    def __init__(self):
        if not GOOGLE_DRIVE_APP_FOLDER_ID:
            raise ValueError("GOOGLE_DRIVE_APP_FOLDER_ID is not set in your .env file.")
        
        self.service = get_drive_service()
        self.uploads_folder_id = get_or_create_folder(self.service, "uploads", parent_id=GOOGLE_DRIVE_APP_FOLDER_ID)
        self.results_folder_id = get_or_create_folder(self.service, "results", parent_id=GOOGLE_DRIVE_APP_FOLDER_ID)
        self.temp_dir = tempfile.mkdtemp()

    def save_upload(self, file: UploadFile) -> str:
        content = file.file.read()
        filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_id = upload_file_content(
            self.service,
            content,
            filename,
            self.uploads_folder_id,
            file.content_type
        )
        return file_id

    def save_result(self, image_data: bytes, extension: str = 'png') -> str:
        filename = f"generated_{uuid.uuid4().hex}.{extension}"
        file_id = upload_file_content(
            self.service,
            image_data,
            filename,
            self.results_folder_id,
            f'image/{extension}'
        )
        return file_id

    def get_upload_path(self, identifier: str) -> str:
        temp_path = os.path.join(self.temp_dir, identifier)
        download_file(self.service, identifier, temp_path)
        return temp_path

    def get_result_path(self, identifier: str) -> str:
        temp_path = os.path.join(self.temp_dir, identifier)
        download_file(self.service, identifier, temp_path)
        return temp_path

    def file_exists(self, path: str) -> bool:
        return os.path.exists(path)

    def get_results_uri(self, identifier: str) -> str:
        return make_file_public(self.service, identifier)
