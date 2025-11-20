from fastapi import File, UploadFile, APIRouter
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

@router.get("/{bucket}")
async def get_files_by_bucket(
    bucket: str
):
    """Endpoint to retrieve a file from Supabase S3."""
    service: SupabaseService = get_storage_service()

    return service.get_files_from_bucket(bucket)

@router.get("/download-file/{bucket}")
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

@router.post("/upload-file/{bucket}")
async def upload_file(
    bucket: str,
    path: str,
    file: Annotated[UploadFile, File()]
):
    """Endpoint to upload a file to Supabase S3."""
    service: SupabaseService = get_storage_service()

    return await service.upload_file_to_s3(bucket, path, file)