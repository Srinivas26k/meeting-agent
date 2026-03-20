"""Job status endpoints."""
from fastapi import APIRouter, HTTPException
from typing import Optional

router = APIRouter()

# In-memory job storage (replace with Redis/Celery in production)
jobs_db = {}


@router.get("/{job_id}")
async def get_job_status(job_id: str):
    """
    Get processing job status.
    
    Returns current status and progress information.
    """
    # TODO: Query Celery task status
    # For now, return mock status
    
    if job_id not in jobs_db:
        # Mock response
        return {
            "job_id": job_id,
            "status": "processing",
            "progress": 0.5,
            "current_step": "transcription",
            "message": "Transcribing audio..."
        }
    
    return jobs_db[job_id]


@router.delete("/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a processing job."""
    # TODO: Cancel Celery task
    
    return {
        "job_id": job_id,
        "status": "cancelled",
        "message": "Job cancelled successfully"
    }
