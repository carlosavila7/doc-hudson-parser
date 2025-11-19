from fastapi import APIRouter
from .supabase_service import SupabaseService


supabase_router = APIRouter(
    prefix="/supabase",
    tags=["Supabase"]
)


def get_storage_service():
    """Provides the SupabaseService instance."""
    return SupabaseService()


@supabase_router.get("/buckets")
async def get_bucket_list(
):
    """Endpoint to retrieve a file from Supabase S3."""
    service: SupabaseService = get_storage_service()

    return service.list_buckets()

@supabase_router.get("/{bucket}")
async def get_files_by_bucket(
    bucket: str
):
    """Endpoint to retrieve a file from Supabase S3."""
    service: SupabaseService = get_storage_service()

    return service.get_files_from_bucket(bucket)