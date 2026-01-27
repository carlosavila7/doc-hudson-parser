from fastapi import APIRouter
from .document_processing_service import DocumentProcessingService

router = APIRouter(
    prefix="/document-processing",
    tags=["Document Processing"]
)


def get_document_processing_service():
    """Provides the DocumentProcessingService instance."""
    return DocumentProcessingService()


@router.post("/process-pdf")
def process_pdf(
    file_path: str,
    start_page: int = None,
    end_page: int = None,
    bucket: str = 'pdf-files',
    output_bucket: str = 'processed-files'
):
    """Endpoint to process a PDF from Supabase, convert to markdown, add image descriptions, and upload results.

    This endpoint orchestrates the complete document processing pipeline:
    1. Downloads and converts PDF to Markdown with optional page range
    2. Handles image references (removes duplicates, converts to relative paths)
    3. Adds AI-generated descriptions for all images
    4. Uploads the resulting markdown file to Supabase
    5. Uploads all artifact images to a dedicated artifacts folder in Supabase

    Args:
        file_path (str): The file path relative to the root of the S3 bucket (without file extension).
        start_page (int, optional): The starting page number for conversion (inclusive). Defaults to None.
        end_page (int, optional): The ending page number for conversion (inclusive). Defaults to None.
        bucket (str, optional): The name of the source storage bucket. Defaults to 'pdf-files'.
        output_bucket (str, optional): The name of the destination storage bucket. Defaults to 'processed-files'.

    Returns:
        dict: A dictionary containing the processing status and paths to uploaded files.
    """
    if start_page == 0 and end_page == 0:
        start_page = None
        end_page = None

    service: DocumentProcessingService = get_document_processing_service()

    return service.process_pdf_to_markdown_and_upload(
        file_path=file_path,
        start_page=start_page,
        end_page=end_page,
        bucket=bucket,
        output_bucket=output_bucket
    )


@router.get("/file-headers")
def process_pdf(
    file_path: str,
    bucket: str,
):
    service: DocumentProcessingService = get_document_processing_service()

    return service.get_markdown_headers(
        bucket, file_path,
    )
