from google import genai
from pathlib import Path
from app.rate_limiter import RateLimiter


class GeminiApiService:
    def __init__(self):
        self.client = genai.Client()
        self.rate_limiter = RateLimiter()

    def generate_image_description(self, image_path: Path):
        image_file = self.client.files.upload(file=image_path)
        prompt = 'The following image has been extracted from an PDF file. It may be a relevant image that corresponds to part of the document`s content or it may be (less likely) a page decoration or a useless artifact. Please generate a brief description of the image. Only describe what is in the image. DO NOT try to predict what it means or in what context it is inserted.'

        contents = [prompt, image_file]

        token_count = self.client.models.count_tokens(
            model='gemini-2.5-flash', contents=contents)

        self.rate_limiter.wait_for_slot_gemini_free_tier(
            tokens=token_count.total_tokens)

        response = self.client.models.generate_content(
            model='gemini-2.5-flash', contents=contents)
        
        return response.text
