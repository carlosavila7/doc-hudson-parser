from typing import List, Dict, Any
from fastapi import UploadFile, HTTPException
from ..dependencies import get_supabase_client


class SupabaseService:
    def __init__(self):
        self.client = get_supabase_client()

    def download_file_from_s3(self, bucket_name: str, file_path: str) -> bytes:
        """Downloads a file from Supabase Storage (S3)."""
        res = self.client.storage.from_(bucket_name).download(file_path)
        return res

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

    def get_files_from_bucket(self, bucket: str, path: str = None, search: str = None):
        res = self.client.storage.from_(
            bucket).list(path, {"search": search})
        return res

    def create_signed_url(self, bucket: str, path: str, expires_in: int = 3600):
        """Creates a signed URL for a file in Supabase Storage."""
        res = self.client.storage.from_(bucket).create_signed_url(
            path,
            expires_in
        )
        return res

    def get_recruitment_offer(self, offer_id: str):
        response = self.client.table("recruitment_offers").select(
            "*, examining_boards(*)").eq("id", offer_id).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Offer not found")
        return response.data

    def get_exams(self, recruitment_offer_id: str):
        response = self.client.table("exams").select(
            "*").eq("recruitment_offer_id", recruitment_offer_id).execute()
        return response.data

    def get_topics(self, exam_id: str):
        # This joins exam_topics with topics to get the actual topic data
        response = self.client.table("exam_topics") \
            .select("topic_id, topics(id, name, created_at)") \
            .eq("exam_id", exam_id) \
            .execute()
        # Flatten the response to return a list of topics
        return [item['topics'] for item in response.data if item.get('topics')]

    def get_subtopics(self, exam_id: str, topic_id: str):
        exam_topic = self.client.table("exam_topics") \
            .select("id") \
            .eq("exam_id", exam_id) \
            .eq("topic_id", topic_id) \
            .single() \
            .execute()

        exam_topic_id = exam_topic.data['id']

        if not exam_topic_id:
            return []

        response = self.client.table("exam_subtopics") \
            .select("*, topics!inner(*)") \
            .eq("exam_topic_id", exam_topic_id) \
            .execute()

        return [{**item.pop("topics")} for item in response.data]

    def get_offices(self, exam_id: str):
        # Joining exam_offices with the offices table
        response = self.client.table("exam_offices") \
            .select("office_id, offices(id, name, created_at)") \
            .eq("exam_id", exam_id) \
            .execute()
        return [item['offices'] for item in response.data if item.get('offices')]

    def get_job_roles(self, exam_id: str):
        response = self.client.table("job_roles").select(
            "*").eq("exam_id", exam_id).execute()
        return response.data
