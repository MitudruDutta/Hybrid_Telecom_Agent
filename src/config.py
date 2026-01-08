import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    groq_api_key: str
    hf_token: str = ""
    aws_region: str = "ap-south-1"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_model: str = "openai/gpt-oss-120b"
    data_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    
    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache
def get_settings() -> Settings:
    return Settings()
