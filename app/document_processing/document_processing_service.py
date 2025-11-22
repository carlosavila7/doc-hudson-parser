import io

from pathlib import Path
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat, DocumentStream
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import ImageRefMode

from ..supabase.supabase_service import SupabaseService


class DocumentProcessingService:
    def __init__(self):
        self.supabase_service = SupabaseService()

    def parse_pdf_to_markdown(self, path: str, bucket: str = 'pdf-files'):
        output_dir = Path("temp/").resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        file = self.supabase_service.download_file_from_s3(bucket, path)

        file_stream = io.BytesIO(file)
        file_name = path.split('/')[-1]

        input_source = DocumentStream(name=file_name, stream=file_stream)
        
        options = PdfPipelineOptions()
        options.images_scale = 2.0
        options.generate_picture_images = True

        converter = DocumentConverter(format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=options)
        })

        res = converter.convert(input_source)

        doc_filename = res.input.file.stem

        md_path = output_dir / f"{doc_filename}.md"

        res.document.save_as_markdown(
            str(md_path), image_mode=ImageRefMode.REFERENCED)

        return md_path


def parse_document(input_doc_path, output_path, start_page, end_page):
    output_dir = Path(output_path).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    options = PdfPipelineOptions()

    options.images_scale = 2.0
    options.generate_page_images = False
    options.generate_picture_images = True
    options.do_picture_description = False

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=options)
        }
    )

    page_range_to_pass = {
        "start": start_page,
        "end": end_page
    } if start_page is not None and end_page is not None else None

    print('page_range_to_pass (verified type):',
          page_range_to_pass, type(page_range_to_pass))

    conv_res = converter.convert(
        input_doc_path)

    doc_filename = conv_res.input.file.stem

    md_path = output_dir / f"{doc_filename}.md"

    conv_res.document.save_as_markdown(
        str(md_path), image_mode=ImageRefMode.REFERENCED)
