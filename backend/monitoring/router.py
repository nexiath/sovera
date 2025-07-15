import os
import platform
import socket
import subprocess
from datetime import datetime, timedelta

import psutil
from fastapi import APIRouter, Depends, HTTPException
from minio.error import S3Error

from auth.dependencies import get_current_user
from core.config import settings
from core.minio_client import minio_client
from models.user import User

router = APIRouter()

@router.get("/info")
def get_system_info(current_user: User = Depends(get_current_user)):
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time

    return {
        "hostname": socket.gethostname(),
        "uptime": str(uptime),
        "cpu_load": psutil.cpu_percent(interval=1, percpu=True),
        "ram_usage": psutil.virtual_memory()._asdict(),
        "disk_usage": psutil.disk_usage('/')._asdict(),
        "python_version": platform.python_version(),
        "os_version": platform.platform(),
    }

@router.get("/ping")
def ping_hosts(current_user: User = Depends(get_current_user)):
    hosts = ["google.com", "github.com", "franceconnect.gouv.fr"]
    results = {}
    for host in hosts:
        try:
            output = subprocess.check_output(["ping", "-c", "1", host], universal_newlines=True)
            latency = float(output.split("time=")[1].split(" ms")[0])
            results[host] = {"latency_ms": latency, "status": "up"}
        except (subprocess.CalledProcessError, IndexError):
            results[host] = {"latency_ms": None, "status": "down"}
    return results

@router.get("/logs")
def get_system_logs(current_user: User = Depends(get_current_user)):
    try:
        with open("sovera.log", "r") as f:
            lines = f.readlines()
            return {"logs": lines[-50:]}
    except FileNotFoundError:
        return {"logs": []}

@router.post("/backup")
def create_backup(current_user: User = Depends(get_current_user)):
    backup_filename = f"sovera_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.sql"
    backup_path = f"/tmp/{backup_filename}"

    try:
        # Execute pg_dump
        pg_dump_command = [
            "pg_dump",
            "-h", settings.POSTGRES_SERVER,
            "-U", settings.POSTGRES_USER,
            "-d", settings.POSTGRES_DB,
            "-F", "p",
            "-f", backup_path
        ]
        env = os.environ.copy()
        env["PGPASSWORD"] = settings.POSTGRES_PASSWORD

        subprocess.run(pg_dump_command, check=True, env=env)

        # Upload to MinIO
        bucket_name = "backups"
        found = minio_client.bucket_exists(bucket_name)
        if not found:
            minio_client.make_bucket(bucket_name)

        minio_client.fput_object(bucket_name, backup_filename, backup_path)

        # Generate presigned URL
        presigned_url = minio_client.presigned_get_object(
            bucket_name, backup_filename, expires=timedelta(minutes=10)
        )
        return {"message": "Backup created and uploaded", "download_url": presigned_url}

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"pg_dump failed: {str(e)}")
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        if os.path.exists(backup_path):
            os.remove(backup_path)
