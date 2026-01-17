import os
import logging

from openai import OpenAI


class DeepSeekApiService:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com"
        )

        self.logger = logging.getLogger(__name__)

    def chat_completion(self, system_prompt: str, user_prompt: str, model: str = "deepseek-chat", response_format: str = 'json_object'):
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={
                'type': response_format
            }
        )

        self.logger.info(
            f'{response.usage.completion_tokens=} {response.usage.total_tokens=}')

        return response
