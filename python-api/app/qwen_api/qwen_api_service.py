import os
import sys
import logging
import base64

from openai import OpenAI

logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    level=logging.INFO
)


class QwenApiService:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('OPEN_ROUTER_API_KEY'),
            base_url="https://openrouter.ai/api/v1"
        )

        self.logger = logging.getLogger(__name__)

    def get_image_caption(self, image_path: str) -> str:
        """
        Get a caption for an image using the qwen3-vl-flash model.

        Args:
            image_path: Path to the image file (local file path)

        Returns:
            The model's caption response as a string
        """
        prompt = 'The following image has been extracted from an PDF file. It may be a relevant image that corresponds to part of the document`s content or it may be (less likely) a page decoration or a useless artifact. Please generate a brief description of the image. Only describe what is in the image. DO NOT try to predict what it means or in what context it is inserted.'

        try:
            # Read and encode the image
            with open(image_path, "rb") as image_file:
                image_data = base64.standard_b64encode(
                    image_file.read()).decode("utf-8")

            # Determine image type from file extension
            image_ext = os.path.splitext(image_path)[1].lower()
            media_type_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp"
            }
            media_type = media_type_map.get(image_ext, "image/jpeg")

            # Make the API request
            response = self.client.chat.completions.create(
                model="qwen/qwen3-vl-8b-instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{image_data}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            caption = response.choices[0].message.content
            self.logger.info(
                f"Successfully generated caption for {image_path}")
            return caption

        except FileNotFoundError:
            self.logger.error(f"Image file not found: {image_path}")
            raise
        except Exception as e:
            self.logger.error(f"Error generating caption: {str(e)}")
            raise
