from typing import List, Dict, Any
from fastapi import UploadFile
from ..dependencies import get_supabase_client


class SupabaseService:
    def __init__(self):
        self.client = get_supabase_client()

    # 1. Access files from S3
    def download_file_from_s3(self, bucket_name: str, file_path: str) -> bytes:
        """Downloads a file from Supabase Storage (S3)."""
        # Note: Supabase uses bucket/path, not just path
        res = self.client.storage.from_(bucket_name).download(file_path)
        return res

    # 2. Post data to PostgreSQL
    def insert_data_to_postgres(self, table_name: str, data: List[Dict[str, Any]]):
        """Inserts processed data into a PostgreSQL table."""
        # Using the postgrest client accessible via .table()
        res = self.client.table(table_name).insert(data).execute()
        # res.data will contain the inserted row data on success
        return res.data

    async def upload_file_to_s3(self, bucket: str, path: str, upload_file: UploadFile):
        content = await upload_file.read()

        if ("." not in path):
            path = path + \
                upload_file.filename if (path.endswith("/")) else path

        res = self.client.storage.from_(bucket).upload(
            path=path,
            file=content,
            file_options={"content-type": upload_file.content_type}
        )

        await upload_file.close()

        return res

    def list_buckets(self):
        res = self.client.storage.list_buckets()
        return res

    def get_files_from_bucket(self, bucket: str):
        res = self.client.storage.from_(bucket).list()
        return res
