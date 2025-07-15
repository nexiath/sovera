"""
Infrastructure provisioning service for multi-tenant projects.
Creates dedicated PostgreSQL databases and MinIO buckets for each project.
"""

import os
import logging
from typing import Tuple, Optional
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from minio import Minio
from minio.error import S3Error

from models.project import Project, generate_slug

logger = logging.getLogger(__name__)

class ProvisioningError(Exception):
    """Custom exception for provisioning errors"""
    pass

class ProvisioningService:
    def __init__(self):
        # PostgreSQL connection for admin operations
        self.pg_host = os.getenv("POSTGRES_SERVER", "db")
        self.pg_user = os.getenv("POSTGRES_USER", "postgres")
        self.pg_password = os.getenv("POSTGRES_PASSWORD")
        self.pg_admin_db = os.getenv("POSTGRES_DB", "sovera")
        
        # MinIO connection
        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
        self.minio_access_key = os.getenv("MINIO_ACCESS_KEY")
        self.minio_secret_key = os.getenv("MINIO_SECRET_KEY")
        
        # Initialize MinIO client
        self.minio_client = Minio(
            self.minio_endpoint,
            access_key=self.minio_access_key,
            secret_key=self.minio_secret_key,
            secure=False  # HTTP for internal Docker communication
        )

    def generate_project_names(self, project_name: str) -> Tuple[str, str, str]:
        """Generate unique names for project infrastructure"""
        slug = generate_slug(project_name)
        db_name = f"project_{slug.replace('-', '_')}_db"
        bucket_name = f"project-{slug}-bucket"
        
        # Ensure names are valid
        db_name = db_name.lower()[:63]  # PostgreSQL limit
        bucket_name = bucket_name.lower()[:63]  # MinIO limit
        
        return slug, db_name, bucket_name

    def create_postgres_database(self, db_name: str) -> bool:
        """Create a dedicated PostgreSQL database for the project"""
        try:
            # Connect to admin database
            conn = psycopg2.connect(
                host=self.pg_host,
                user=self.pg_user,
                password=self.pg_password,
                database=self.pg_admin_db
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            with conn.cursor() as cursor:
                # Check if database already exists
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (db_name,)
                )
                if cursor.fetchone():
                    logger.warning(f"Database {db_name} already exists")
                    conn.close()
                    return True
                
                # Create database
                cursor.execute(f'CREATE DATABASE "{db_name}"')
                logger.info(f"Created PostgreSQL database: {db_name}")
                
            conn.close()
            
            # Initialize the new database with basic schema
            self._initialize_project_database(db_name)
            return True
            
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL database {db_name}: {e}")
            raise ProvisioningError(f"PostgreSQL provisioning failed: {e}")

    def _initialize_project_database(self, db_name: str):
        """Initialize project database with complete multi-tenant schema"""
        try:
            from database.multi_tenant import multi_tenant_manager
            
            # Use the multi-tenant manager to create complete schema
            multi_tenant_manager.create_project_schema(db_name)
            logger.info(f"Initialized complete schema for database: {db_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database {db_name}: {e}")
            raise ProvisioningError(f"Database initialization failed: {e}")

    def create_minio_bucket(self, bucket_name: str) -> bool:
        """Create a dedicated MinIO bucket for the project"""
        try:
            # Check if bucket already exists
            if self.minio_client.bucket_exists(bucket_name):
                logger.warning(f"Bucket {bucket_name} already exists")
                return True
            
            # Create bucket
            self.minio_client.make_bucket(bucket_name)
            
            # Set bucket policy for private access
            # TODO: Set proper bucket policy based on project settings
            
            logger.info(f"Created MinIO bucket: {bucket_name}")
            return True
            
        except S3Error as e:
            logger.error(f"Failed to create MinIO bucket {bucket_name}: {e}")
            raise ProvisioningError(f"MinIO provisioning failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error creating bucket {bucket_name}: {e}")
            raise ProvisioningError(f"MinIO provisioning failed: {e}")

    def provision_project(self, project_name: str) -> Tuple[str, str, str]:
        """
        Provision complete infrastructure for a new project.
        Returns: (slug, db_name, bucket_name)
        """
        try:
            # Generate unique names
            slug, db_name, bucket_name = self.generate_project_names(project_name)
            
            logger.info(f"Starting provisioning for project: {project_name}")
            logger.info(f"Generated names - Slug: {slug}, DB: {db_name}, Bucket: {bucket_name}")
            
            # Create PostgreSQL database
            if not self.create_postgres_database(db_name):
                raise ProvisioningError("Failed to create PostgreSQL database")
            
            # Create MinIO bucket
            if not self.create_minio_bucket(bucket_name):
                raise ProvisioningError("Failed to create MinIO bucket")
            
            logger.info(f"Successfully provisioned project infrastructure: {project_name}")
            return slug, db_name, bucket_name
            
        except Exception as e:
            logger.error(f"Provisioning failed for project {project_name}: {e}")
            # TODO: Implement cleanup/rollback mechanism
            raise ProvisioningError(f"Complete provisioning failed: {e}")

    def cleanup_project(self, db_name: str, bucket_name: str) -> bool:
        """
        Cleanup project infrastructure (for project deletion).
        WARNING: This will permanently delete all project data!
        """
        success = True
        
        try:
            # Drop PostgreSQL database
            conn = psycopg2.connect(
                host=self.pg_host,
                user=self.pg_user,
                password=self.pg_password,
                database=self.pg_admin_db
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            with conn.cursor() as cursor:
                # Terminate connections to the database
                cursor.execute("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = %s AND pid <> pg_backend_pid()
                """, (db_name,))
                
                # Drop database
                cursor.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
                logger.info(f"Dropped PostgreSQL database: {db_name}")
                
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to cleanup PostgreSQL database {db_name}: {e}")
            success = False
        
        try:
            # Remove MinIO bucket
            if self.minio_client.bucket_exists(bucket_name):
                # Remove all objects first
                objects = self.minio_client.list_objects(bucket_name, recursive=True)
                for obj in objects:
                    self.minio_client.remove_object(bucket_name, obj.object_name)
                
                # Remove bucket
                self.minio_client.remove_bucket(bucket_name)
                logger.info(f"Removed MinIO bucket: {bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup MinIO bucket {bucket_name}: {e}")
            success = False
        
        return success

# Global provisioning service instance
provisioning_service = ProvisioningService()