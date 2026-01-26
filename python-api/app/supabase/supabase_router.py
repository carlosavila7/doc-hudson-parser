from fastapi import File, UploadFile, APIRouter, Query
from fastapi.responses import StreamingResponse
from .supabase_service import SupabaseService
from typing import Annotated
import io

router = APIRouter(
    prefix="/supabase",
    tags=["Supabase"]
)


def get_storage_service():
    """Provides the SupabaseService instance."""
    return SupabaseService()


@router.get("/buckets")
async def get_bucket_list(
):
    """Endpoint to retrieve a file from Supabase S3."""
    service: SupabaseService = get_storage_service()

    return service.list_buckets()


@router.get("/storage/{bucket}")
async def get_files_by_bucket(
    bucket: str,
    path: str = None,
    search: str = None
):
    """Endpoint to retrieve a file from Supabase S3."""
    service: SupabaseService = get_storage_service()

    return service.get_files_from_bucket(bucket, path, search)


@router.get("/storage/download-file/{bucket}")
def download_file(
    bucket: str,
    path: str
):
    """Endpoint to download a file from Supabase S3."""
    service: SupabaseService = get_storage_service()

    bytes = service.download_file_from_s3(bucket, path)

    return StreamingResponse(
        content=io.BytesIO(bytes),
        headers={
            "Content-Disposition": f"attachment; filename={path.split('/')[-1]}"
        }
    )


@router.post("/storage/upload-file/{bucket}")
async def upload_file(
    bucket: str,
    path: str,
    file: Annotated[UploadFile, File()]
):
    """Endpoint to upload a file to Supabase S3."""
    service: SupabaseService = get_storage_service()

    return await service.upload_file_to_s3(bucket, path, file)


@router.get("/storage/signed-url/{bucket}")
async def get_signed_url(
    bucket: str,
    path: str,
    expires_in: int = 60
):
    """Endpoint to retrieve a signed URL for a file in Supabase S3."""
    service: SupabaseService = get_storage_service()

    return service.create_signed_url(bucket, path, expires_in)


@router.get("/recruitment-offers/{offer_id}")
async def get_recruitment_offer(offer_id: str):
    service: SupabaseService = get_storage_service()

    return service.get_recruitment_offer(offer_id)


@router.get("/exams")
async def get_exams(offer_id: str = Query(...,
                                          description="The recruitment offer ID")):
    service: SupabaseService = get_storage_service()

    return service.get_exams(offer_id)


@router.get("/topics")
async def get_topics(exam_id: str = Query(...,
                                          description="The exam ID")):
    service: SupabaseService = get_storage_service()

    return service.get_topics(exam_id)


@router.get("/subtopics")
async def get_subtopics(exam_id: str = Query(...,
                                             description="The exam ID"),
                        topic_id: str = Query(...,
                                              description="The exam ID")):
    service: SupabaseService = get_storage_service()

    return service.get_subtopics(exam_id, topic_id)


@router.get("/offices")
async def get_offices(exam_id: str = Query(...,
                                           description="The exam ID")):
    service: SupabaseService = get_storage_service()

    return service.get_offices(exam_id)


@router.get("/job-roles")
async def get_job_roles(exam_id: str = Query(...,
                                             description="The exam ID")):
    service: SupabaseService = get_storage_service()

    return service.get_job_roles(exam_id)
