import io
import os
import shutil

from pathlib import Path
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat, DocumentStream
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import ImageRefMode

from ..supabase.supabase_service import SupabaseService


class DocumentProcessingService:
    def __init__(self):
        self.supabase_service = SupabaseService()

    def parse_pdf_to_markdown(self, path: str, start_page: int = None, end_page: int = None, bucket: str = 'pdf-files'):
        output_dir = Path("temp/").resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        file = self.supabase_service.download_file_from_s3(bucket, path)

        file_stream = io.BytesIO(file)
        file_name = path.split('/')[-1]

        custom_range = (
            start_page,
            end_page
        ) if start_page is not None and end_page is not None else None

        input_source = DocumentStream(name=file_name, stream=file_stream)

        options = PdfPipelineOptions()
        options.images_scale = 2.0
        options.generate_picture_images = True

        converter = DocumentConverter(format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=options),
        })

        res = converter.convert(
            input_source, page_range=custom_range) if custom_range is not None else converter.convert(input_source)

        doc_filename = res.input.file.stem

        md_path = output_dir / f"{doc_filename}.md"

        res.document.save_as_markdown(
            str(md_path), image_mode=ImageRefMode.REFERENCED)

        return md_path

    def flush_temp(self):
        """
        Deletes all files and subdirectories within a specific folder.
        """
        folder_path = "temp/"

        if not os.path.exists(folder_path):
            print(f"The folder '{folder_path}' does not exist.")
            return

        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)

            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)

                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)

            except Exception as e:
                print(f"Failed to delete {item_path}. Reason: {e}")

