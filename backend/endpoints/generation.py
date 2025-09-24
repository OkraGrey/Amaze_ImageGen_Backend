import os
import tempfile
from contextlib import contextmanager
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from typing import Optional
from fastapi.responses import JSONResponse
from backend.utils.logger import app_logger
from backend.utils.file_utils import allowed_file
from backend.services.generation_service.service_factory import get_service
from backend.services.storage.storage_factory import get_storage_service
from backend.config.settings import PHOTOTOOM_API_KEY
from backend.services.bg_rem.download_service import process_download_image

router = APIRouter()


@router.post("/generate")
async def generate_image(
    prompt: str = Form(...),
    model: str = Form(...),
    file: Optional[UploadFile] = File(None)
    ):
    """Generate image endpoint."""
    app_logger.info(f"GENERATE IMAGE ENDPOINT ACCESSED", extra={
        "prompt": prompt,
        "model": model,
        "has_file": file is not None,
        "filename": file.filename if file else None
    })
    
    storage_service = get_storage_service()

    try:
        file_path = None
        upload_identifier = None
        if file and file.filename:
            app_logger.info(f"CHECKING IF FILE IS ALLOWED")

            if not allowed_file(file.filename):
                raise HTTPException(status_code=400, detail="FILE TYPE NOT ALLOWED")
            
            app_logger.info(f"SAVING FILE TO STORAGE")
            upload_identifier = storage_service.save_upload(file)
            app_logger.info(f"FILE SAVED SUCCESSFULLY WITH IDENTIFIER: {upload_identifier}")
        
        if not prompt.strip():
            raise HTTPException(status_code=400, detail="PROMPT CANNOT BE EMPTY")

        # Get the appropriate service from the factory
        app_logger.info(f"GETTING SERVICE FROM THE FACTORY WITH MODEL NAME: {model}")
        service = get_service(model)
        result_path = None
        result_filename = None
        
        if service:
            app_logger.info(f"RECIEVED FACTORY OBJECT")
            app_logger.info(f"ACCESSING GENERATE IMAGE ")
            result_identifier = service.generate_image(prompt, upload_identifier)
            result_uri = storage_service.get_results_uri(result_identifier)
            
            return JSONResponse(content={
                "success": True,
                "message": "Image generated successfully",
                "result_path": result_uri,
                "result_identifier": result_identifier
            })
        else:
            raise HTTPException(status_code=400, detail="SERVICE NOT FOUND")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        # Re-raise to let FastAPI return the original status code
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@contextmanager
def temporary_file(content: bytes, suffix: str = ".png"):
    """Context manager for creating a temporary file from content."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        yield temp_file_path
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@router.post("/download")
async def download_image(file_identifier: str = Form(...)):
    app_logger.info(
        "DOWNLOAD IMAGE ENDPOINT ACCESSED",
        extra={
            "file_identifier": file_identifier,
        },
    )
    
    if not PHOTOTOOM_API_KEY:
        app_logger.error("PHOTOTOOM API KEY NOT FOUND IN CONFIG")
        raise HTTPException(status_code=500, detail="PHOTOTOOM API KEY NOT CONFIGURED")

    storage_service = get_storage_service()
    
    try:
        # Get the file content
        image_content = storage_service.get_result_content(file_identifier)
        
        # Use a temporary file for processing
        with temporary_file(image_content) as local_input_path:
            app_logger.info(f"DELEGATING TO THE WORKER FUNCTION FOR BG REMOVAL")
            output_path = process_download_image(input_path=local_input_path, api_key=PHOTOTOOM_API_KEY)

            # Upload the processed file back to storage
            with open(output_path, "rb") as f:
                image_data = f.read()
        
        processed_identifier = storage_service.save_result(image_data, extension='png')
        processed_uri = storage_service.get_results_uri(processed_identifier)

        return JSONResponse(content={
            "success": True,
            "message": "Background removed successfully",
            "result_path": processed_uri,
            "result_identifier": processed_identifier
        })
    except Exception as e:
        app_logger.error(f"FAILED TO REMOVE BACKGROUND USING PHOTOTOOM: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/generate_image_description")
async def generate_image_description(file_identifier: str = Form(...)):
    app_logger.info(
        "IMG DESCRIPTION ENDPOINT ACCESSED",
        extra={
            "file_identifier": file_identifier,
        },
    )
    
    storage_service = get_storage_service()
    try:
        # Delegate to the worker function
        app_logger.info(f"DELEGATING TO THE WORKER FUNCTION FOR IMAGE DESCRIPTION")
        app_logger.info(f"GETTING SERVICE FROM THE FACTORY WITH MODEL NAME: gemini")
        service = get_service() # By default gemini is used
        description = service.generate_image_description(file_identifier)
        app_logger.info(f"IMAGE DESCRIPTION GENERATED SUCCESSFULLY: {description}")
        return description
    except Exception as e:
        app_logger.error(f"FAILED TO GENERATE IMAGE DESCRIPTION: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
