"""
Files management router for Sovera projects.
Handles file upload, download, and management using MinIO.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse, Response
from sqlmodel import Session
import logging
from datetime import datetime
import io

from auth.dependencies import get_current_user
from database.session import get_session
from models.user import User
from models.project import Project
from services.file_storage import file_storage_service, FileStorageError
from utils.rbac import require_project_viewer, require_project_editor

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/projects/{project_id}/files/upload")
async def upload_file(
    project_id: int = Path(..., description="Project ID", gt=0),
    file: UploadFile = File(...),
    folder_path: Optional[str] = Form(None, description="Optional folder path within bucket"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    project: Project = Depends(require_project_editor)
):
    """
    Upload a file to the project's MinIO bucket.
    
    **Permissions Required:** Editor or Owner
    
    **Features:**
    - Automatic file type detection
    - File size validation
    - Folder organization support
    - Duplicate name handling
    - Metadata preservation
    
    **File Size Limits:**
    - Default: 100MB per file
    - Configurable per project
    
    **Supported File Types:**
    - Documents: PDF, DOC, DOCX, TXT, MD
    - Images: PNG, JPG, JPEG, GIF, SVG, WEBP
    - Data: JSON, CSV, XML, YAML
    - Archives: ZIP, TAR, GZ
    - Code: JS, TS, PY, SQL, etc.
    """
    try:
        logger.info(f"Uploading file '{file.filename}' to project {project_id}")
        
        # Check file size against project limits
        max_file_size = project.storage_limit_mb * 1024 * 1024  # Convert MB to bytes
        
        # Upload file to project bucket
        result = await file_storage_service.upload_file(
            bucket_name=project.bucket_name,
            file=file,
            folder_path=folder_path,
            max_file_size=max_file_size
        )
        
        # Add project context to response
        response = {
            **result,
            "project_id": project_id,
            "project_name": project.name,
            "bucket_name": project.bucket_name,
            "download_url": f"/projects/{project_id}/files/{result['object_key']}/download"
        }
        
        logger.info(f"Successfully uploaded file '{file.filename}' to project {project_id}")
        return response
        
    except FileStorageError as e:
        logger.warning(f"File upload failed for project {project_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error uploading file to project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during file upload")

@router.get("/projects/{project_id}/files/", response_model=List[Dict[str, Any]])
async def list_files(
    project_id: int = Path(..., description="Project ID", gt=0),
    folder_path: Optional[str] = Query(None, description="Filter by folder path"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    project: Project = Depends(require_project_viewer)
):
    """
    List all files in the project's bucket.
    
    **Permissions Required:** Viewer, Editor, or Owner
    
    **Features:**
    - Folder-based filtering
    - File metadata display
    - Size and type information
    - Upload timestamp
    
    **Response includes:**
    - File name and path
    - File size and type
    - Upload date
    - Download URL
    - File metadata
    """
    try:
        logger.info(f"Listing files for project {project_id}")
        
        # List files from project bucket
        files = await file_storage_service.list_files(
            bucket_name=project.bucket_name,
            prefix=folder_path
        )
        
        # Add project context and download URLs
        result = []
        for file_info in files:
            result.append({
                **file_info,
                "project_id": project_id,
                "download_url": f"/projects/{project_id}/files/{file_info['object_key']}/download",
                "preview_url": f"/projects/{project_id}/files/{file_info['object_key']}/preview" if _is_previewable(file_info['content_type']) else None
            })
        
        logger.info(f"Found {len(result)} files for project {project_id}")
        return result
        
    except FileStorageError as e:
        logger.warning(f"Failed to list files for project {project_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error listing files for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while listing files")

@router.get("/projects/{project_id}/files/{object_key:path}/download")
async def download_file(
    project_id: int = Path(..., description="Project ID", gt=0),
    object_key: str = Path(..., description="File object key"),
    as_attachment: bool = Query(False, description="Download as attachment"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    project: Project = Depends(require_project_viewer)
):
    """
    Download a file from the project's bucket.
    
    **Permissions Required:** Viewer, Editor, or Owner
    
    **Parameters:**
    - `as_attachment`: If true, forces download instead of inline display
    
    **Features:**
    - Secure direct download
    - Content-Type preservation
    - Optional attachment mode
    - Access logging
    """
    try:
        logger.info(f"Downloading file '{object_key}' from project {project_id}")
        
        # Get file info first
        file_info = await file_storage_service.get_file_info(project.bucket_name, object_key)
        
        # Get file content
        content = await file_storage_service.get_file_content(project.bucket_name, object_key)
        
        # Prepare response headers
        headers = {
            "Content-Length": str(len(content))
        }
        
        if as_attachment:
            headers["Content-Disposition"] = f'attachment; filename="{file_info["filename"]}"'
        else:
            headers["Content-Disposition"] = f'inline; filename="{file_info["filename"]}"'
        
        # Create streaming response
        return Response(
            content=content,
            media_type=file_info["content_type"],
            headers=headers
        )
        
    except FileStorageError as e:
        logger.warning(f"File download failed for project {project_id}: {e}")
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Unexpected error downloading file from project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during file download")

@router.get("/projects/{project_id}/files/{object_key:path}/preview")
async def preview_file(
    project_id: int = Path(..., description="Project ID", gt=0),
    object_key: str = Path(..., description="File object key"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    project: Project = Depends(require_project_viewer)
):
    """
    Preview a file (for supported file types).
    
    **Supported preview types:**
    - Text files (TXT, MD, JSON, XML, etc.)
    - Images (PNG, JPG, GIF, SVG, etc.)
    - Small files under 1MB
    
    **Returns:**
    - For text files: JSON with content
    - For images: Direct image response
    - For others: File info only
    """
    try:
        logger.info(f"Previewing file '{object_key}' from project {project_id}")
        
        # Get file info
        file_info = await file_storage_service.get_file_info(project.bucket_name, object_key)
        
        # Check if file is previewable
        if not _is_previewable(file_info["content_type"]):
            raise HTTPException(status_code=400, detail="File type not supported for preview")
        
        # Check file size (limit preview to 1MB)
        if file_info["size_bytes"] > 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large for preview")
        
        # Get file content
        content = await file_storage_service.get_file_content(project.bucket_name, object_key)
        
        # Handle different content types
        if file_info["content_type"].startswith("text/") or file_info["content_type"] in ["application/json", "application/xml"]:
            # Return text content as JSON
            try:
                text_content = content.decode('utf-8')
                return {
                    "type": "text",
                    "content": text_content,
                    "file_info": file_info
                }
            except UnicodeDecodeError:
                return {
                    "type": "binary",
                    "message": "File contains binary data",
                    "file_info": file_info
                }
        
        elif file_info["content_type"].startswith("image/"):
            # Return image directly
            return Response(
                content=content,
                media_type=file_info["content_type"],
                headers={"Content-Length": str(len(content))}
            )
        
        else:
            # Not previewable
            return {
                "type": "not_supported",
                "message": "Preview not supported for this file type",
                "file_info": file_info
            }
        
    except FileStorageError as e:
        logger.warning(f"File preview failed for project {project_id}: {e}")
        raise HTTPException(status_code=404, detail="File not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error previewing file from project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during file preview")

@router.delete("/projects/{project_id}/files/{object_key:path}")
async def delete_file(
    project_id: int = Path(..., description="Project ID", gt=0),
    object_key: str = Path(..., description="File object key"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    project: Project = Depends(require_project_editor)
):
    """
    Delete a file from the project's bucket.
    
    **Permissions Required:** Editor or Owner
    
    **Warning:** This operation is irreversible.
    """
    try:
        logger.info(f"Deleting file '{object_key}' from project {project_id}")
        
        # Delete file from bucket
        success = await file_storage_service.delete_file(project.bucket_name, object_key)
        
        if success:
            logger.info(f"Successfully deleted file '{object_key}' from project {project_id}")
            return {
                "message": f"File '{object_key}' has been successfully deleted",
                "object_key": object_key,
                "project_id": project_id
            }
        else:
            raise HTTPException(status_code=500, detail="File deletion failed")
            
    except FileStorageError as e:
        logger.warning(f"File deletion failed for project {project_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting file from project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during file deletion")

@router.get("/projects/{project_id}/files/{object_key:path}/info")
async def get_file_info(
    project_id: int = Path(..., description="Project ID", gt=0),
    object_key: str = Path(..., description="File object key"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    project: Project = Depends(require_project_viewer)
):
    """
    Get detailed information about a specific file.
    
    **Returns:**
    - File metadata
    - Size and type information
    - Upload details
    - Download URLs
    """
    try:
        logger.info(f"Getting info for file '{object_key}' from project {project_id}")
        
        # Get file info
        file_info = await file_storage_service.get_file_info(project.bucket_name, object_key)
        
        # Add project context
        result = {
            **file_info,
            "project_id": project_id,
            "project_name": project.name,
            "download_url": f"/projects/{project_id}/files/{object_key}/download",
            "preview_url": f"/projects/{project_id}/files/{object_key}/preview" if _is_previewable(file_info['content_type']) else None
        }
        
        return result
        
    except FileStorageError as e:
        logger.warning(f"Failed to get file info for project {project_id}: {e}")
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Unexpected error getting file info for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while getting file info")

@router.get("/projects/{project_id}/files/stats")
async def get_storage_stats(
    project_id: int = Path(..., description="Project ID", gt=0),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    project: Project = Depends(require_project_viewer)
):
    """
    Get storage statistics for the project.
    
    **Returns:**
    - Total files count
    - Total storage used
    - Storage limit
    - File type breakdown
    """
    try:
        logger.info(f"Getting storage stats for project {project_id}")
        
        # Get bucket statistics
        stats = file_storage_service.get_bucket_stats(project.bucket_name)
        
        # Add project limits and usage percentage
        storage_limit_bytes = project.storage_limit_mb * 1024 * 1024
        usage_percentage = (stats['total_size_bytes'] / storage_limit_bytes * 100) if storage_limit_bytes > 0 else 0
        
        result = {
            **stats,
            "project_id": project_id,
            "project_name": project.name,
            "storage_limit_mb": project.storage_limit_mb,
            "storage_limit_bytes": storage_limit_bytes,
            "usage_percentage": round(usage_percentage, 2),
            "remaining_bytes": max(0, storage_limit_bytes - stats['total_size_bytes']),
            "remaining_mb": round(max(0, storage_limit_bytes - stats['total_size_bytes']) / 1024 / 1024, 2)
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting storage stats for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while getting storage stats")

def _is_previewable(content_type: str) -> bool:
    """Check if a file type supports preview"""
    previewable_types = [
        # Text types
        "text/plain", "text/markdown", "text/html", "text/css", "text/javascript",
        # Application types
        "application/json", "application/xml", "application/yaml",
        # Image types
        "image/png", "image/jpeg", "image/gif", "image/svg+xml", "image/webp"
    ]
    
    return content_type in previewable_types or content_type.startswith(("text/", "image/"))