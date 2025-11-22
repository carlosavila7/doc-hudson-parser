import io
import os
import shutil
import logging
import imagehash
import re

from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat, DocumentStream
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import ImageRefMode
from pathlib import Path
from PIL import Image


from ..supabase.supabase_service import SupabaseService


class DocumentProcessingService:
    def __init__(self):
        self.supabase_service = SupabaseService()
        self.logger = logging.getLogger(__name__)

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
