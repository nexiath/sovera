"""
File storage service for Sovera using MinIO.
Handles file upload, download, and management for project buckets.
"""

import os
import logging
import mimetypes
from typing import List, Dict, Optional, BinaryIO
from datetime import datetime, timedelta
from urllib.parse import unquote
import uuid

from minio import Minio
from minio.error import S3Error
from fastapi import HTTPException, UploadFile

logger = logging.getLogger(__name__)

class FileStorageError(Exception):
    """Custom exception for file storage operations"""
    pass

class FileStorageService:
    """Service for managing files in MinIO buckets"""
    
    def __init__(self):
        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.minio_access_key = os.getenv("MINIO_ACCESS_KEY")
        self.minio_secret_key = os.getenv("MINIO_SECRET_KEY")
        
        if not all([self.minio_access_key, self.minio_secret_key]):
            raise FileStorageError("MinIO credentials not configured")
        
        # Initialize MinIO client
        self.client = Minio(
            self.minio_endpoint,
            access_key=self.minio_access_key,
            secret_key=self.minio_secret_key,
            secure=False  # HTTP for internal Docker communication
        )
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type from filename"""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove or replace unsafe characters
        unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        sanitized = filename
        for char in unsafe_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Ensure filename is not empty and not too long
        if not sanitized.strip():
            sanitized = f"unnamed_file_{uuid.uuid4().hex[:8]}"
        
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:250] + ext
        
        return sanitized
    
    def _generate_object_key(self, filename: str, folder_path: Optional[str] = None) -> str:
        """Generate object key for MinIO storage"""
        sanitized_filename = self._sanitize_filename(filename)
        
        if folder_path:
            # Sanitize folder path
            folder_path = folder_path.strip('/')
            folder_parts = [self._sanitize_filename(part) for part in folder_path.split('/')]
            folder_path = '/'.join(part for part in folder_parts if part)
            return f"{folder_path}/{sanitized_filename}"
        
        return sanitized_filename
    
    async def upload_file(
        self, 
        bucket_name: str, 
        file: UploadFile, 
        folder_path: Optional[str] = None,
        max_file_size: int = 100 * 1024 * 1024  # 100MB default
    ) -> Dict[str, any]:
        """
        Upload a file to MinIO bucket.
        
        Args:
            bucket_name: Target bucket name
            file: FastAPI UploadFile object
            folder_path: Optional folder path within bucket
            max_file_size: Maximum file size in bytes
            
        Returns:
            Dictionary with file information
            
        Raises:
            FileStorageError: If upload fails
        """
        try:
            # Validate file size
            if hasattr(file, 'size') and file.size and file.size > max_file_size:
                raise FileStorageError(f"File size ({file.size} bytes) exceeds limit ({max_file_size} bytes)")
            
            # Generate object key
            object_key = self._generate_object_key(file.filename, folder_path)
            
            # Get file content
            content = await file.read()
            file_size = len(content)
            
            if file_size > max_file_size:
                raise FileStorageError(f"File size ({file_size} bytes) exceeds limit ({max_file_size} bytes)")
            
            # Get content type
            content_type = file.content_type or self._get_content_type(file.filename)
            
            # Create a BytesIO object for MinIO
            from io import BytesIO
            file_data = BytesIO(content)
            
            # Upload to MinIO
            result = self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_key,
                data=file_data,
                length=file_size,
                content_type=content_type,
                metadata={
                    'original_filename': file.filename,
                    'upload_timestamp': datetime.utcnow().isoformat(),
                    'file_size': str(file_size)
                }
            )
            
            logger.info(f"Successfully uploaded file '{object_key}' to bucket '{bucket_name}'")
            
            return {
                'object_key': object_key,
                'filename': file.filename,
                'content_type': content_type,
                'size_bytes': file_size,
                'etag': result.etag,
                'uploaded_at': datetime.utcnow().isoformat()
            }
            
        except S3Error as e:
            logger.error(f"MinIO error uploading file: {e}")
            raise FileStorageError(f"Failed to upload file: {e}")
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise FileStorageError(f"Failed to upload file: {e}")
    
    async def list_files(self, bucket_name: str, prefix: Optional[str] = None) -> List[Dict[str, any]]:
        """
        List files in a MinIO bucket.
        
        Args:
            bucket_name: Bucket name
            prefix: Optional prefix to filter files
            
        Returns:
            List of file information dictionaries
        """
        try:
            objects = self.client.list_objects(
                bucket_name=bucket_name,
                prefix=prefix,
                recursive=True
            )
            
            files = []
            for obj in objects:
                # Get object metadata
                try:
                    stat = self.client.stat_object(bucket_name, obj.object_name)
                    metadata = stat.metadata or {}
                    
                    files.append({
                        'object_key': obj.object_name,
                        'filename': metadata.get('original_filename', os.path.basename(obj.object_name)),
                        'size_bytes': obj.size,
                        'content_type': stat.content_type,
                        'last_modified': obj.last_modified.isoformat() if obj.last_modified else None,
                        'etag': obj.etag,
                        'metadata': metadata
                    })
                except Exception as e:
                    logger.warning(f"Error getting metadata for object {obj.object_name}: {e}")
                    # Add basic info even if metadata fails
                    files.append({
                        'object_key': obj.object_name,
                        'filename': os.path.basename(obj.object_name),
                        'size_bytes': obj.size,
                        'content_type': 'application/octet-stream',
                        'last_modified': obj.last_modified.isoformat() if obj.last_modified else None,
                        'etag': obj.etag,
                        'metadata': {}
                    })
            
            return files
            
        except S3Error as e:
            logger.error(f"MinIO error listing files: {e}")
            raise FileStorageError(f"Failed to list files: {e}")
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            raise FileStorageError(f"Failed to list files: {e}")
    
    async def delete_file(self, bucket_name: str, object_key: str) -> bool:
        """
        Delete a file from MinIO bucket.
        
        Args:
            bucket_name: Bucket name
            object_key: Object key to delete
            
        Returns:
            True if successful
        """
        try:
            self.client.remove_object(bucket_name, object_key)
            logger.info(f"Successfully deleted file '{object_key}' from bucket '{bucket_name}'")
            return True
            
        except S3Error as e:
            logger.error(f"MinIO error deleting file: {e}")
            raise FileStorageError(f"Failed to delete file: {e}")
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            raise FileStorageError(f"Failed to delete file: {e}")
    
    async def get_file_info(self, bucket_name: str, object_key: str) -> Dict[str, any]:
        """
        Get information about a specific file.
        
        Args:
            bucket_name: Bucket name
            object_key: Object key
            
        Returns:
            File information dictionary
        """
        try:
            stat = self.client.stat_object(bucket_name, object_key)
            metadata = stat.metadata or {}
            
            return {
                'object_key': object_key,
                'filename': metadata.get('original_filename', os.path.basename(object_key)),
                'size_bytes': stat.size,
                'content_type': stat.content_type,
                'last_modified': stat.last_modified.isoformat() if stat.last_modified else None,
                'etag': stat.etag,
                'metadata': metadata
            }
            
        except S3Error as e:
            logger.error(f"MinIO error getting file info: {e}")
            raise FileStorageError(f"File not found: {e}")
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            raise FileStorageError(f"Failed to get file info: {e}")
    
    def generate_presigned_url(
        self, 
        bucket_name: str, 
        object_key: str, 
        expires: timedelta = timedelta(hours=1),
        method: str = "GET"
    ) -> str:
        """
        Generate a presigned URL for file access.
        
        Args:
            bucket_name: Bucket name
            object_key: Object key
            expires: Expiration time
            method: HTTP method (GET, PUT, etc.)
            
        Returns:
            Presigned URL string
        """
        try:
            url = self.client.presigned_url(
                method=method,
                bucket_name=bucket_name,
                object_name=object_key,
                expires=expires
            )
            return url
            
        except S3Error as e:
            logger.error(f"MinIO error generating presigned URL: {e}")
            raise FileStorageError(f"Failed to generate download URL: {e}")
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise FileStorageError(f"Failed to generate download URL: {e}")
    
    async def get_file_content(self, bucket_name: str, object_key: str) -> bytes:
        """
        Get file content as bytes.
        
        Args:
            bucket_name: Bucket name
            object_key: Object key
            
        Returns:
            File content as bytes
        """
        try:
            response = self.client.get_object(bucket_name, object_key)
            content = response.read()
            response.close()
            response.release_conn()
            return content
            
        except S3Error as e:
            logger.error(f"MinIO error getting file content: {e}")
            raise FileStorageError(f"Failed to get file content: {e}")
        except Exception as e:
            logger.error(f"Error getting file content: {e}")
            raise FileStorageError(f"Failed to get file content: {e}")
    
    def check_bucket_exists(self, bucket_name: str) -> bool:
        """Check if bucket exists"""
        try:
            return self.client.bucket_exists(bucket_name)
        except Exception as e:
            logger.error(f"Error checking bucket existence: {e}")
            return False
    
    def get_bucket_stats(self, bucket_name: str) -> Dict[str, any]:
        """Get bucket statistics"""
        try:
            objects = list(self.client.list_objects(bucket_name, recursive=True))
            
            total_size = sum(obj.size for obj in objects)
            total_files = len(objects)
            
            # Group by file type
            file_types = {}
            for obj in objects:
                ext = os.path.splitext(obj.object_name)[1].lower()
                ext = ext if ext else 'no_extension'
                file_types[ext] = file_types.get(ext, 0) + 1
            
            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'file_types': file_types
            }
            
        except Exception as e:
            logger.error(f"Error getting bucket stats: {e}")
            return {
                'total_files': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0,
                'file_types': {}
            }

# Global file storage service instance
file_storage_service = FileStorageService()