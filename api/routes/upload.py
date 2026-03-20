"""File upload endpoints."""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import shutil
from datetime import datetime
import uuid

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a meeting recording file.
    
    Returns job ID for tracking processing status.
    """
    # Validate file type
    allowed_extensions = {'.mp4', '.mp3', '.wav', '.webm', '.m4a', '.ogg', '.flac'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Generate unique filename
    job_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{job_id}{file_ext}"
    file_path = UPLOAD_DIR / filename
    
    # Save file
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # TODO: Queue processing job with Celery
    # For now, return job ID
    
    return {
        "job_id": job_id,
        "filename": file.filename,
        "file_path": str(file_path),
        "status": "uploaded",
        "message": "File uploaded successfully. Processing will begin shortly."
    }
