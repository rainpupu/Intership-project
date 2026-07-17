"""
MinIO 对象存储客户端封装
"""
import io
from datetime import timedelta
from minio import Minio
from minio.error import S3Error
from app.config.settings import settings


class MinIOClient:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket_name = settings.MINIO_BUCKET
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            print(f"MinIO bucket 初始化警告: {e}")

    def upload_file(self, object_name: str, file_path: str) -> str:
        self.client.fput_object(bucket_name=self.bucket_name, object_name=object_name, file_path=file_path)
        return self.get_presigned_url(object_name)

    def upload_bytes(self, object_name: str, data: bytes, content_type: str = "image/jpeg") -> str:
        self.client.put_object(
            bucket_name=self.bucket_name, object_name=object_name,
            data=io.BytesIO(data), length=len(data), content_type=content_type,
        )
        return self.get_presigned_url(object_name)

    def get_presigned_url(self, object_name: str) -> str:
        return self.client.presigned_get_object(
            bucket_name=self.bucket_name, object_name=object_name, expires=timedelta(days=7),
        )

    def delete_file(self, object_name: str):
        self.client.remove_object(bucket_name=self.bucket_name, object_name=object_name)