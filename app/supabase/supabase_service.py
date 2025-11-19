from typing import List, Dict, Any
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

    # 3. Upload files to S3
    def upload_file_to_s3(self, bucket_name: str, file_path: str, file_content: bytes, file_type: str = "text/plain"):
        """Uploads a file (e.g., processed output) to Supabase Storage (S3)."""
        res = self.client.storage.from_(bucket_name).upload(
            path=file_path,
            file=file_content,
            file_options={"content-type": file_type}
        )
        return res
    
    def list_buckets(self):
        res = self.client.storage.list_buckets()
        return res
    
    def get_files_from_bucket(self, bucket: str):
        res = self.client.storage.from_(bucket).list()
        return res