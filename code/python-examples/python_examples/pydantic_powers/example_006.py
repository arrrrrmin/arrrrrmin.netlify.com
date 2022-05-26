import os
from typing import Optional

from pydantic import BaseSettings


class S3Settings(BaseSettings):
    REGION: Optional[str] = os.getenv("REGION") or "eu-central-1"
    MAIN_BUCKET: Optional[str] = os.getenv("MAIN_BUCKET") or None
    USER_BUCKET: Optional[str] = os.getenv("USER_BUCKET") or None

    class Config:
        env_file = ".env.dev.s3"
        env_file_encoding = "utf-8"
