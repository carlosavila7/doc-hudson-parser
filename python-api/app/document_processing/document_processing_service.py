import io
import os
import shutil
import logging
import imagehash
import re
import sys

from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat, DocumentStream
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import ImageRefMode
from collections import Counter
from pathlib import Path
from PIL import Image

from app.supabase.supabase_service import SupabaseService
from app.qwen_api.qwen_api_service import QwenApiService 

logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    level=logging.INFO 
)

class DocumentProcessingService:
    def __init__(self):
        self.supabase_service = SupabaseService()
        self.qwen_service = QwenApiService()
        self.logger = logging.getLogger(__name__)

    def append_image_description(self, md_file_path: Path):
        if (not md_file_path.exists()):
            raise FileNotFoundError(f"File not found: {md_file_path}")

        with open(md_file_path, 'r') as f:
            content = f.read()

        image_tag_pattern = r'!\[.*?\]\((.*?)\)'

        def handle_image_reference(match):
            image_tag = match.group(0)
            image_path = Path('temp') / Path(match.group(1))

            image_description = self.qwen_service.get_image_caption(
                image_path)
            
            image_tag_with_description = f'{image_tag}\n<!-- {image_description} -->'

            return image_tag_with_description

        updated_content = re.sub(
            image_tag_pattern, handle_image_reference, content)
        
        with open(md_file_path, 'w') as f:
            f.write(updated_content)

        self.logger.info(
            f'Image descriptions have been generated and added to the markdown file.')
        

    def handle_image_references(self, artifacts_folder_path: Path, md_file_path: Path):
        """Updates markdown image links and cleans up redundant image files.

        This method first identifies visually similar (repeated) images in the 
        artifacts folder. It then parses the Markdown file to:
        1. Remove any image tags (`![]()`) that reference these repeated images.
        2. Convert valid image references from absolute paths to relative paths
        (preserving only the last two path segments, e.g., './parent/image.png').

        After updating the Markdown content, it permanently deletes the detected 
        repeated image files from the filesystem.

        Args:
            artifacts_folder_path (Path): The directory containing the images to analyze.
            md_file_path (Path): The Markdown file to read and modify.

        Raises:
            FileNotFoundError: If the md_file_path does not exist.
        """
        repeated_images = self.get_repeated_images(artifacts_folder_path)

        repeated_filenames = [path.name for path in repeated_images]

        if (not md_file_path.exists()):
            raise FileNotFoundError(f"File not found: {md_file_path}")

        with open(md_file_path, 'r') as f:
            content = f.read()

        image_tag_pattern = r'!\[.*?\]\((.*?)\)'

        def handle_image_reference(match):
            image_path = match.group(1)
            filename = image_path.split('/')[-1]

            if filename in repeated_filenames:  # remove image
                return ''
            else:  # update to relative path
                relative_path = "/".join(match.group(1).split('/')[-2:])
                image_tag = f'![Image](./{relative_path})'
                self.logger.info(f'Update imgage tag to ${image_tag}')
                return image_tag

        updated_content = re.sub(
            image_tag_pattern, handle_image_reference, content)

        self.logger.info(
            f'References to repeated images removed from .md file.')

        with open(md_file_path, 'w') as f:
            f.write(updated_content)

        for repeated_image in repeated_images:
            Path(repeated_image).unlink()
            self.logger.info(f'Deleted {repeated_image}')

    def get_repeated_images(self, target_path: Path):
        """Scans a directory for visually similar PNG images using perceptual hashing.

        This method recursively searches the target path for .png files and groups
        them based on visual similarity (pHash Hamming distance < 10). It identifies
        clusters of duplicates and returns a flattened list of all images involved
        in these clusters.

        Args:
            target_path (Path): The root directory to recursively search for images.

        Returns:
            list[Path]: A flat list containing all file paths that are part of a 
            similarity cluster. This includes both the "originals" and their 
            duplicates.

        Raises:
            FileNotFoundError: If the provided target_path does not exist.
        """
        similarity_threshold = 10

        if not target_path.exists():
            raise FileNotFoundError(f"Folder not found: {target_path}")

        images = sorted(target_path.rglob("*.png"))
        unique_images = []

        for image in images:
            if (len(unique_images) == 0):
                unique_images.append([image])
                continue

            has_similar = False

            for unique_image in unique_images:
                img_a = unique_image[0]
                img_b = image

                hash_a = imagehash.phash(Image.open(img_a))
                hash_b = imagehash.phash(Image.open(img_b))

                hamming_distance = hash_a - hash_b

                are_images_similar = hamming_distance < similarity_threshold

                if (are_images_similar):
                    unique_image.append(img_b)
                    has_similar = True
                    break

            if (not has_similar):
                unique_images.append([image])

        repeated_images = [r for r in unique_images if len(r) > 1]
        repeated_images = [
            s for sub in repeated_images for s in sub]  # flat list

        unique_images = [u for u in unique_images if len(u) == 1]

        self.logger.info(
            f'{len(repeated_images)} repeated images have been found ({len(unique_images)} unique image(s) to keep).')

        return repeated_images

    def parse_pdf_to_markdown(self, path: str, start_page: int = None, end_page: int = None, bucket: str = 'pdf-files'):
        """Downloads a PDF from storage and converts it to a Markdown file.

        This method retrieves a PDF file from the specified Supabase S3 bucket,
        configures the pipeline to handle image extraction and scaling, and 
        saves the resulting Markdown content to a local temporary directory.

        Args:
            path (str): The file path relative to the root of the S3 bucket.
            start_page (int, optional): The starting page number for conversion 
                (inclusive). Defaults to None.
            end_page (int, optional): The ending page number for conversion 
                (inclusive). Defaults to None.
            bucket (str, optional): The name of the storage bucket to download 
                from. Defaults to 'pdf-files'.

        Returns:
            Path: A pathlib object pointing to the generated local Markdown file.
        """
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

    def process_pdf_to_markdown_and_upload(self, file_path: str, start_page: int = None, end_page: int = None, bucket: str = 'pdf-files', output_bucket: str = 'processed-files'):
        """Processes a PDF file from Supabase, converts to markdown, adds image descriptions, and uploads results.

        This method orchestrates the complete document processing pipeline:
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
            dict: A dictionary containing:
                - 'markdown_path': The path to the uploaded markdown file in Supabase
                - 'artifacts_path': The path to the uploaded artifacts folder in Supabase
                - 'status': 'success' or 'error'
                - 'message': A descriptive message about the operation

        Raises:
            FileNotFoundError: If the markdown file or artifacts folder is not created properly.
            Exception: For any errors during file processing or upload operations.
        """
        try:
            md_file_path = self.parse_pdf_to_markdown(
                file_path, start_page=start_page, end_page=end_page, bucket=bucket
            )
            
            pdf_path = Path(file_path)
            artifacts_folder_path = Path("temp") / f"{md_file_path.stem}_artifacts"
            doc_filename = f"{pdf_path.parent.name[:-1]}_{md_file_path.stem}"
            
            if artifacts_folder_path.exists():
                self.logger.info(f'Handling image references for {doc_filename}')
                self.handle_image_references(artifacts_folder_path, md_file_path)
            
                self.logger.info(f'Adding image descriptions for {doc_filename}')
                self.append_image_description(md_file_path)
                
            self.logger.info(f'Uploading markdown file to Supabase')
            markdown_upload_path = f"{doc_filename}/{doc_filename}.md"
            with open(md_file_path, 'rb') as f:
                markdown_content = f.read()
            
            self.supabase_service.client.storage.from_(output_bucket).upload(
                path=markdown_upload_path,
                file=markdown_content,
                file_options={"content-type": "text/markdown"}
            )
            self.logger.info(f'Markdown file uploaded to {markdown_upload_path}')
            
            artifacts_uploaded = False
            if artifacts_folder_path.exists() and artifacts_folder_path.is_dir():
                self.logger.info(f'Uploading artifacts for {doc_filename}')
                artifacts_upload_path = f"{doc_filename}/{doc_filename}_artifacts"
                
                for image_file in artifacts_folder_path.iterdir():
                    if image_file.is_file():
                        with open(image_file, 'rb') as f:
                            image_content = f.read()
                        
                        upload_path = f"{artifacts_upload_path}/{image_file.name}"
                        self.supabase_service.client.storage.from_(output_bucket).upload(
                            path=upload_path,
                            file=image_content,
                            file_options={"content-type": "image/png"}
                        )
                        self.logger.info(f'Artifact uploaded to {upload_path}')
                
                artifacts_uploaded = True
            
            self.flush_temp()
            
            result = {
                'status': 'success',
                'markdown_path': markdown_upload_path,
                'artifacts_path': f"{doc_filename}/{doc_filename}_artifacts" if artifacts_uploaded else None,
                'message': f'Successfully processed and uploaded {doc_filename}'
            }
            
            self.logger.info(result['message'])
            return result
            
        except Exception as e:
            self.logger.error(f'Error during PDF processing and upload: {str(e)}')
            self.flush_temp()
            return {
                'status': 'error',
                'message': f'Failed to process PDF: {str(e)}'
            }

    def flush_temp(self):
        """
        Deletes all files and subdirectories within a specific folder.
        """
        folder_path = "temp/"

        if not os.path.exists(folder_path):
            self.logger.error(f"The folder '{folder_path}' does not exist.")
            return

        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)

            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)

                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)

            except Exception as e:
                self.logger.error(f"Failed to delete {item_path}. Reason: {e}")

        self.logger.info(f'{folder_path} folder has been flushed')

    
    def get_markdown_headers(self, bucket: str, path: str):
        file = self.supabase_service.download_file_from_s3(bucket, path)
        file_content = file.decode()

        header_pattern = r'^(#{1,6}\s+.+)$'
        all_headers = re.findall(header_pattern, file_content, re.MULTILINE)

        counts = Counter(all_headers)

        unique_headers = [h for h in all_headers if counts[h] == 1]

        return unique_headers
