import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# 1. Configuration Class
class Settings(BaseSettings):
    """Configuration loaded from environment variables."""
    # model_config = SettingsConfigDict(env_file='.env', extra='ignore') # If you use Pydantic V2

    # Supabase Credentials
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")

    # LLM API Key (Example for Gemini)
    # GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

# Load configuration
settings = Settings()

# 2. Supabase Client
def get_supabase_client() -> Client:
    """Returns a Supabase client instance."""
    supabase_client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return supabase_client

# 3. LLM Client/API Key (Used in your main logic later)
# For now, we'll just expose the key, but this function will grow
# def get_llm_api_key() -> str:
#     """Returns the LLM API Key."""
#     return settings.GEMINI_API_KEY