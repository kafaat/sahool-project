"""
Storage Service - Sahool Agricultural Platform
Handles file storage with MinIO/S3 and local filesystem
Supports image uploads, satellite data, and document management
"""

import os
import io
import hashlib
from typing import Optional, BinaryIO, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import logging
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


class StorageConfig:
    """Storage configuration"""
    
    def __init__(self):
        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.minio_access_key = os.getenv("MINIO_ROOT_USER", "minioadmin")
        self.minio_secret_key = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
        self.minio_secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        self.default_bucket = os.getenv("STORAGE_BUCKET", "sahool-data")
        self.local_storage_path = Path(os.getenv("LOCAL_STORAGE_PATH", "/data/storage"))


class StorageService:
    """Main storage service for file management"""
    
    def __init__(self, config: Optional[StorageConfig] = None):
        self.config = config or StorageConfig()
        self.client = self._init_minio_client()
        self._ensure_bucket_exists()
    
    def _init_minio_client(self) -> Minio:
        """Initialize MinIO client"""
        try:
            client = Minio(
                self.config.minio_endpoint,
                access_key=self.config.minio_access_key,
                secret_key=self.config.minio_secret_key,
                secure=self.config.minio_secure
            )
            logger.info(f"MinIO client initialized: {self.config.minio_endpoint}")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            raise
    
    def _ensure_bucket_exists(self):
        """Ensure default bucket exists"""
        try:
            if not self.client.bucket_exists(self.config.default_bucket):
                self.client.make_bucket(self.config.default_bucket)
                logger.info(f"Created bucket: {self.config.default_bucket}")
        except S3Error as e:
            logger.error(f"Failed to create bucket: {e}")
    
    def upload_file(
        self,
        file_data: BinaryIO,
        object_name: str,
        bucket: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload file to storage
        
        Args:
            file_data: File-like object or bytes
            object_name: Object name/path in storage
            bucket: Bucket name (uses default if not specified)
            content_type: MIME type
            metadata: Additional metadata
        
        Returns:
            Object name/path
        """
        bucket = bucket or self.config.default_bucket
        
        try:
            # Get file size
            file_data.seek(0, 2)
            file_size = file_data.tell()
            file_data.seek(0)
            
            # Upload
            self.client.put_object(
                bucket,
                object_name,
                file_data,
                file_size,
                content_type=content_type,
                metadata=metadata
            )
            
            logger.info(f"Uploaded file: {bucket}/{object_name} ({file_size} bytes)")
            return object_name
            
        except S3Error as e:
            logger.error(f"Failed to upload file: {e}")
            raise
    
    def download_file(
        self,
        object_name: str,
        bucket: Optional[str] = None
    ) -> bytes:
        """
        Download file from storage
        
        Args:
            object_name: Object name/path
            bucket: Bucket name
        
        Returns:
            File content as bytes
        """
        bucket = bucket or self.config.default_bucket
        
        try:
            response = self.client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"Downloaded file: {bucket}/{object_name}")
            return data
            
        except S3Error as e:
            logger.error(f"Failed to download file: {e}")
            raise
    
    def get_presigned_url(
        self,
        object_name: str,
        bucket: Optional[str] = None,
        expires: int = 3600
    ) -> str:
        """
        Get presigned URL for temporary access
        
        Args:
            object_name: Object name/path
            bucket: Bucket name
            expires: Expiration time in seconds
        
        Returns:
            Presigned URL
        """
        bucket = bucket or self.config.default_bucket
        
        try:
            url = self.client.presigned_get_object(
                bucket,
                object_name,
                expires=timedelta(seconds=expires)
            )
            logger.debug(f"Generated presigned URL for: {bucket}/{object_name}")
            return url
            
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def delete_file(
        self,
        object_name: str,
        bucket: Optional[str] = None
    ) -> bool:
        """
        Delete file from storage
        
        Args:
            object_name: Object name/path
            bucket: Bucket name
        
        Returns:
            True if deleted successfully
        """
        bucket = bucket or self.config.default_bucket
        
        try:
            self.client.remove_object(bucket, object_name)
            logger.info(f"Deleted file: {bucket}/{object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    def list_files(
        self,
        prefix: str = "",
        bucket: Optional[str] = None,
        recursive: bool = True
    ) -> List[dict]:
        """
        List files in storage
        
        Args:
            prefix: Object name prefix filter
            bucket: Bucket name
            recursive: List recursively
        
        Returns:
            List of file info dicts
        """
        bucket = bucket or self.config.default_bucket
        
        try:
            objects = self.client.list_objects(
                bucket,
                prefix=prefix,
                recursive=recursive
            )
            
            files = []
            for obj in objects:
                files.append({
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag
                })
            
            logger.info(f"Listed {len(files)} files from {bucket}/{prefix}")
            return files
            
        except S3Error as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    def file_exists(
        self,
        object_name: str,
        bucket: Optional[str] = None
    ) -> bool:
        """Check if file exists"""
        bucket = bucket or self.config.default_bucket
        
        try:
            self.client.stat_object(bucket, object_name)
            return True
        except S3Error:
            return False
    
    def get_file_info(
        self,
        object_name: str,
        bucket: Optional[str] = None
    ) -> Optional[dict]:
        """Get file metadata"""
        bucket = bucket or self.config.default_bucket
        
        try:
            stat = self.client.stat_object(bucket, object_name)
            return {
                "name": object_name,
                "size": stat.size,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "metadata": stat.metadata
            }
        except S3Error as e:
            logger.error(f"Failed to get file info: {e}")
            return None


class ImageStorage:
    """Specialized storage for images"""
    
    def __init__(self, storage: StorageService):
        self.storage = storage
        self.bucket = "sahool-images"
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """Ensure images bucket exists"""
        try:
            if not self.storage.client.bucket_exists(self.bucket):
                self.storage.client.make_bucket(self.bucket)
                logger.info(f"Created images bucket: {self.bucket}")
        except S3Error as e:
            logger.error(f"Failed to create images bucket: {e}")
    
    def upload_image(
        self,
        image_data: bytes,
        filename: str,
        field_id: Optional[int] = None,
        image_type: str = "satellite"
    ) -> Tuple[str, str]:
        """
        Upload image with automatic path generation
        
        Args:
            image_data: Image bytes
            filename: Original filename
            field_id: Field ID for organization
            image_type: Type (satellite, ndvi, rgb, etc.)
        
        Returns:
            Tuple of (object_name, presigned_url)
        """
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(image_data).hexdigest()[:8]
        ext = Path(filename).suffix
        
        if field_id:
            object_name = f"fields/{field_id}/{image_type}/{timestamp}_{file_hash}{ext}"
        else:
            object_name = f"{image_type}/{timestamp}_{file_hash}{ext}"
        
        # Upload
        file_obj = io.BytesIO(image_data)
        self.storage.upload_file(
            file_obj,
            object_name,
            bucket=self.bucket,
            content_type=f"image/{ext[1:]}",
            metadata={
                "field_id": str(field_id) if field_id else "",
                "image_type": image_type,
                "upload_time": timestamp
            }
        )
        
        # Get URL
        url = self.storage.get_presigned_url(object_name, bucket=self.bucket, expires=86400)
        
        return (object_name, url)
    
    def get_field_images(
        self,
        field_id: int,
        image_type: Optional[str] = None
    ) -> List[dict]:
        """Get all images for a field"""
        prefix = f"fields/{field_id}/"
        if image_type:
            prefix += f"{image_type}/"
        
        return self.storage.list_files(prefix=prefix, bucket=self.bucket)


class SatelliteDataStorage:
    """Specialized storage for satellite data"""
    
    def __init__(self, storage: StorageService):
        self.storage = storage
        self.bucket = "sahool-satellite"
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """Ensure satellite bucket exists"""
        try:
            if not self.storage.client.bucket_exists(self.bucket):
                self.storage.client.make_bucket(self.bucket)
                logger.info(f"Created satellite bucket: {self.bucket}")
        except S3Error as e:
            logger.error(f"Failed to create satellite bucket: {e}")
    
    def store_sentinel_scene(
        self,
        scene_data: bytes,
        scene_id: str,
        band: str,
        field_id: int
    ) -> str:
        """Store Sentinel-2 scene data"""
        object_name = f"sentinel2/{field_id}/{scene_id}/{band}.tif"
        
        file_obj = io.BytesIO(scene_data)
        self.storage.upload_file(
            file_obj,
            object_name,
            bucket=self.bucket,
            content_type="image/tiff",
            metadata={
                "scene_id": scene_id,
                "band": band,
                "field_id": str(field_id),
                "satellite": "sentinel2"
            }
        )
        
        return object_name
    
    def get_scene_url(self, scene_id: str, band: str, field_id: int) -> str:
        """Get presigned URL for scene"""
        object_name = f"sentinel2/{field_id}/{scene_id}/{band}.tif"
        return self.storage.get_presigned_url(object_name, bucket=self.bucket)


# Global storage instance
_storage_service: Optional[StorageService] = None


def get_storage() -> StorageService:
    """Get global storage service instance"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service


__all__ = [
    "StorageConfig",
    "StorageService",
    "ImageStorage",
    "SatelliteDataStorage",
    "get_storage"
]
