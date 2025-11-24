from google import genai
from pathlib import Path
from app.rate_limiter import RateLimiter


class GeminiApiService:
    def __init__(self):
        self.client = genai.Client()
        self.rate_limiter = RateLimiter()

    def generate_image_description(self, image_path: Path):
        image_file = self.client.files.upload(file=image_path)
        prompt = 'Generate a brief description of this image'

        contents = [prompt, image_file]

        token_count = self.client.models.count_tokens(
            model='gemini-2.5-flash', contents=contents)

        self.rate_limiter.wait_for_slot_gemini_free_tier(
            tokens=token_count.total_tokens)

        response = self.client.models.generate_content(
            model='gemini-2.5-flash', contents=contents)
        
        return response.text
