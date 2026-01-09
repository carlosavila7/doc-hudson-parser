from fastapi import APIRouter, HTTPException, Query
from app.extractor.extractor_service import ExtractorService
import json

router = APIRouter(prefix="/extractor", tags=["extractor"])

extractor_service = ExtractorService()

@router.get("/base-entities")
def get_base_entities(
    file_bucket: str = Query(..., description="The S3 bucket name"),
    file_path: str = Query(..., description="The S3 file path")
):
    """
    Extract base entities from the document.
    """
    try:
        result = extractor_service.populate_base_entities(file_bucket, file_path)
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/exam-subtopics/{exam_index}")
def get_exam_subtopics(
    exam_index: int,
    file_bucket: str = Query(..., description="The S3 bucket name"),
    file_key: str = Query(..., description="The S3 file key"),
    identified_exams: str = Query(..., description="JSON string of identified exams")
):
    """
    Extract exam subtopics for a specific exam index.
    """
    try:
        file = extractor_service.supabase_service.download_file_from_s3(file_bucket, file_key)
        file_content = file.decode('utf-8')
        identified_exams_parsed = json.loads(identified_exams)
        result = extractor_service.populate_exam_subtopics(file_content, identified_exams_parsed, exam_index)
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/job-roles/{exam_index}")
def get_job_roles(
    exam_index: int,
    file_bucket: str = Query(..., description="The S3 bucket name"),
    file_key: str = Query(..., description="The S3 file key"),
    identified_exams: str = Query(..., description="JSON string of identified exams")
):
    """
    Extract job roles for a specific exam index.
    """
    try:
        file = extractor_service.supabase_service.download_file_from_s3(file_bucket, file_key)
        file_content = file.decode('utf-8')
        identified_exams_parsed = json.loads(identified_exams)
        result = extractor_service.populate_job_roles(file_content, identified_exams_parsed, exam_index)
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/offices/{exam_index}")
def get_offices(
    exam_index: int,
    file_bucket: str = Query(..., description="The S3 bucket name"),
    file_key: str = Query(..., description="The S3 file key"),
    identified_exams: str = Query(..., description="JSON string of identified exams")
):
    """
    Extract offices for a specific exam index.
    """
    try:
        file = extractor_service.supabase_service.download_file_from_s3(file_bucket, file_key)
        file_content = file.decode('utf-8')
        identified_exams_parsed = json.loads(identified_exams)
        result = extractor_service.populate_offices(file_content, identified_exams_parsed, exam_index)
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
