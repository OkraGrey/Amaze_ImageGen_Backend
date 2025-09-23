import os
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from typing import Optional
from fastapi.responses import JSONResponse
from backend.utils.logger import app_logger
from backend.utils.file_utils import allowed_file, save_uploaded_file
from backend.services.generation_service.service_factory import get_service

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
    
    try:
        file_path = None
        if file and file.filename:
            app_logger.info(f"CHECKING IF FILE IS ALLOWED")

            if not allowed_file(file.filename):
                raise HTTPException(status_code=400, detail="FILE TYPE NOT ALLOWED")

            file_path = save_uploaded_file(file)
            app_logger.info(f"FILE SAVED SUCCESSFULLY")
        
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
            result_path = service.generate_image(prompt, file_path)

            app_logger.info(f"RESULT PATH RECIEVED FROM SERVICE: {result_path}")
            result_filename = os.path.basename(result_path)
        
            return JSONResponse(content={
                "success": True,
                "message": "Image generated successfully",
                "result_path": f"/results/{result_filename}"
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
