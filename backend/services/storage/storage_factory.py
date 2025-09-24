from backend.services.storage.base import FileStorage
from backend.services.storage.local_storage import LocalStorage
from backend.services.storage.google_drive import GoogleDriveStorage
from backend.config.settings import STORAGE_TYPE
from backend.utils.logger import app_logger

# A registry of available services
STORAGE_SERVICES = {
    "local": LocalStorage(),
    "gcp": GoogleDriveStorage(),
}

def get_storage_service() -> FileStorage:
    app_logger.info(f"GETTING STORAGE SERVICE FOR TYPE: {STORAGE_TYPE}")
    service = STORAGE_SERVICES.get(STORAGE_TYPE.lower())
    if not service:
        raise ValueError(f"Unsupported storage type: {STORAGE_TYPE}")
    app_logger.info(f"RETURNING STORAGE SERVICE OBJECT")
    return service
