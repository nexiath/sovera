from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from minio.error import S3Error

from auth.dependencies import get_current_user
from core.minio_client import minio_client
from models.user import User

router = APIRouter()

def get_bucket_name(user: User) -> str:
    return f"user-{user.id}"

@router.post("/upload/")
def upload_file(
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...)
):
    bucket_name = get_bucket_name(current_user)
    try:
        found = minio_client.bucket_exists(bucket_name)
        if not found:
            minio_client.make_bucket(bucket_name)
        
        minio_client.put_object(
            bucket_name,
            file.filename,
            file.file,
            length=-1,
            part_size=10*1024*1024
        )
        return {"filename": file.filename}
    except S3Error as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/files/")
def list_files(current_user: User = Depends(get_current_user)):
    bucket_name = get_bucket_name(current_user)
    try:
        objects = minio_client.list_objects(bucket_name, recursive=True)
        return [obj.object_name for obj in objects]
    except S3Error as exc:
        if exc.code == 'NoSuchBucket':
            return []
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/file/{filename}")
def get_file_url(filename: str, current_user: User = Depends(get_current_user)):
    bucket_name = get_bucket_name(current_user)
    try:
        url = minio_client.presigned_get_object(bucket_name, filename)
        return {"url": url}
    except S3Error as exc:
        raise HTTPException(status_code=404, detail="File not found")

@router.delete("/file/{filename}")
def delete_file(filename: str, current_user: User = Depends(get_current_user)):
    bucket_name = get_bucket_name(current_user)
    try:
        minio_client.remove_object(bucket_name, filename)
        return {"ok": True}
    except S3Error as exc:
        raise HTTPException(status_code=404, detail="File not found")
