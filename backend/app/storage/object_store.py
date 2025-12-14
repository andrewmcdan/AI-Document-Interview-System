from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil

import boto3
from botocore.client import BaseClient

from app.core.config import Settings


class ObjectStore:
    def upload_file(self, file_path: Path, object_key: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def presigned_url(self, object_key: str, expires_in: int = 3600) -> str | None:  # pragma: no cover - interface
        raise NotImplementedError

    def delete_prefix(self, prefix: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class S3ObjectStore(ObjectStore):
    bucket: str
    client: BaseClient

    @classmethod
    def from_settings(cls, settings: Settings) -> "S3ObjectStore":
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

    def delete_prefix(self, prefix: str) -> None:
        paginator = self.client.get_paginator("list_objects_v2")
        objects_to_delete = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                objects_to_delete.append({"Key": obj["Key"]})

        if objects_to_delete:
            self.client.delete_objects(Bucket=self.bucket, Delete={"Objects": objects_to_delete})


@dataclass
class LocalObjectStore(ObjectStore):
    base_path: Path

    @classmethod
    def from_settings(cls, settings: Settings) -> "LocalObjectStore":
        base = Path(settings.local_storage_path).expanduser().resolve()
        base.mkdir(parents=True, exist_ok=True)
        return cls(base_path=base)

    def upload_file(self, file_path: Path, object_key: str) -> None:
        dest = self.base_path / object_key
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, dest)

    def presigned_url(self, object_key: str, expires_in: int = 3600) -> str | None:
        _ = expires_in
        dest = self.base_path / object_key
        return str(dest)

    def delete_prefix(self, prefix: str) -> None:
        target = self.base_path / prefix
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
        elif target.exists():
            target.unlink(missing_ok=True)


def get_object_store_provider(settings: Settings):
    if settings.storage_backend.lower() == "local":
        return LocalObjectStore.from_settings
    return S3ObjectStore.from_settings
