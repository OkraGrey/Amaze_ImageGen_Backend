import os
import uuid
from fastapi import UploadFile
from backend.services.storage.base import FileStorage
from backend.utils.logger import app_logger
from backend.config.settings import GOOGLE_DRIVE_APP_FOLDER_ID
from backend.utils.google_drive_utils import (
    get_drive_service,
    get_or_create_folder,
    upload_file_content,
    download_file,
    make_file_public,
    download_file_content
)

class GoogleDriveStorage(FileStorage):
    def __init__(self):
        if not GOOGLE_DRIVE_APP_FOLDER_ID:
            raise ValueError("GOOGLE_DRIVE_APP_FOLDER_ID is not set in your .env file.")
        
        self.service = get_drive_service()
        self.uploads_folder_id = get_or_create_folder(self.service, "uploads", parent_id=GOOGLE_DRIVE_APP_FOLDER_ID)
        self.results_folder_id = get_or_create_folder(self.service, "results", parent_id=GOOGLE_DRIVE_APP_FOLDER_ID)

    def save_upload(self, file: UploadFile) -> str:
        app_logger.info(f"ENTERING SAVE UPLOAD FUNCTION FOR GCP")
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

    def get_results_uri(self, identifier: str) -> str:
        return make_file_public(self.service, identifier)

    def get_upload_content(self, identifier: str) -> bytes:
        return download_file_content(self.service, identifier)

    def get_result_content(self, identifier: str) -> bytes:
        return download_file_content(self.service, identifier)
