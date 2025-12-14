from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import boto3
from botocore.client import BaseClient

from app.core.config import Settings


@dataclass
class ObjectStore:
    bucket: str
    client: BaseClient

    @classmethod
    def from_settings(cls, settings: Settings) -> "ObjectStore":
        client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
        )
        return cls(bucket=settings.s3_bucket, client=client)

    def upload_file(self, file_path: Path, object_key: str) -> None:
        self.client.upload_file(str(file_path), self.bucket, object_key)

    def presigned_url(self, object_key: str, expires_in: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": object_key},
            ExpiresIn=expires_in,
        )
