from fastapi import APIRouter, HTTPException, Query
from app.extractor.extractor_service import ExtractorService
import json

router = APIRouter(prefix="/extractor", tags=["extractor"])

extractor_service = ExtractorService()


@router.get("/base-entities")
def get_base_entities(
    file_bucket: str = Query(..., description="The S3 bucket name"),
    file_path: str = Query(..., description="The S3 file path"),
    header_filter: str = Query(None,
                               description="Header filters which contains relevant data"),
    model: str = Query("deepseek-chat", description="The model to use for extraction")
):
    """
    Extract base entities from the document.
    """
    if isinstance(header_filter, str):
        header_filter = json.loads(header_filter)

    try:
        result = extractor_service.populate_base_entities(
            file_bucket, file_path, header_filter, model)
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exam-subtopics/{exam_id}")
def get_exam_subtopics(
    exam_id: str,
    file_bucket: str = Query(..., description="The S3 bucket name"),
    file_key: str = Query(..., description="The S3 file key"),
    identified_exams: str = Query(...,
                                  description="JSON string of identified exams"),
    header_filter: str = Query(None,
                               description="Header filters which contains relevant data"),
    model: str = Query("deepseek-chat", description="The model to use for extraction")
):
    """
    Extract exam subtopics for a specific exam index.
    """
    if isinstance(header_filter, str):
        header_filter = json.loads(header_filter)

    try:
        identified_exams_parsed = json.loads(identified_exams)
        result = extractor_service.populate_exam_subtopics(
            file_bucket, file_key, identified_exams_parsed, exam_id, header_filter, model)
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job-roles/{exam_id}")
def get_job_roles(
    exam_id: str,
    file_bucket: str = Query(..., description="The S3 bucket name"),
    file_key: str = Query(..., description="The S3 file key"),
    identified_exams: str = Query(...,
                                  description="JSON string of identified exams"),
    header_filter: str = Query(None,
                               description="Header filters which contains relevant data"),
    model: str = Query("deepseek-chat", description="The model to use for extraction")
):
    """
    Extract job roles for a specific exam index.
    """
    if isinstance(header_filter, str):
        header_filter = json.loads(header_filter)

    try:
        identified_exams_parsed = json.loads(identified_exams)
        result = extractor_service.populate_job_roles(
            file_bucket, file_key, identified_exams_parsed, exam_id, header_filter, model)
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/offices/{exam_id}")
def get_offices(
    exam_id: str,
    file_bucket: str = Query(..., description="The S3 bucket name"),
    file_key: str = Query(..., description="The S3 file key"),
    identified_exams: str = Query(...,
                                  description="JSON string of identified exams"),
    header_filter: str = Query(None,
                               description="Header filters which contains relevant data"),
    model: str = Query("deepseek-chat", description="The model to use for extraction")
):
    """
    Extract offices for a specific exam index.
    """
    if isinstance(header_filter, str):
        header_filter = json.loads(header_filter)

    try:
        identified_exams_parsed = json.loads(identified_exams)
        result = extractor_service.populate_offices(
            file_bucket, file_key, identified_exams_parsed, exam_id, header_filter, model)
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
