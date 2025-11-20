from fastapi import FastAPI, File, UploadFile, APIRouter
from .supabase_service import SupabaseService
from typing import Annotated

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

@router.get("/{bucket}")
async def get_files_by_bucket(
    bucket: str
):
    """Endpoint to retrieve a file from Supabase S3."""
    service: SupabaseService = get_storage_service()

    return service.get_files_from_bucket(bucket)

@router.post("/upload-file/{bucket}")
async def get_files_by_bucket(
    bucket: str,
    path: str,
    file: Annotated[UploadFile, File()]
):
    """Endpoint to retrieve a file from Supabase S3."""
    service: SupabaseService = get_storage_service()

    return await service.upload_file_to_s3(bucket, path, file)