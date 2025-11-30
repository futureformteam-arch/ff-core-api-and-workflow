import boto3
from botocore.exceptions import ClientError
from src.core.config import settings
import hashlib
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class S3Service:
    """Service for managing evidence file storage in S3"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME
    
    def generate_presigned_upload_url(
        self, 
        assessment_id: int, 
        evidence_type: str,
        file_name: str,
        content_type: str = "application/octet-stream",
        expiration: int = 3600
    ) -> dict:
        """
        Generate presigned URL for secure file upload
        
        Args:
            assessment_id: ID of the assessment
            evidence_type: Type of evidence (financial, uptime, contract, etc.)
            file_name: Original file name
            content_type: MIME type of the file
            expiration: URL expiration time in seconds (default 1 hour)
            
        Returns:
            dict with upload_url, s3_key, and expiration info
        """
        # Generate unique S3 key
        timestamp = datetime.utcnow().isoformat()
        file_hash = hashlib.md5(f"{assessment_id}_{file_name}_{timestamp}".encode()).hexdigest()
        s3_key = f"assessments/{assessment_id}/{evidence_type}/{file_hash}_{file_name}"
        
        try:
            url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key,
                    'ContentType': content_type
                },
                ExpiresIn=expiration
            )
            
            logger.info(f"Generated presigned upload URL for {s3_key}")
            
            return {
                "upload_url": url,
                "s3_key": s3_key,
                "s3_bucket": self.bucket_name,
                "expires_in": expiration
            }
        except ClientError as e:
            logger.error(f"Failed to generate presigned upload URL: {str(e)}")
            raise Exception(f"Failed to generate presigned URL: {str(e)}")
    
    def generate_presigned_download_url(
        self, 
        s3_key: str, 
        expiration: int = 3600
    ) -> str:
        """
        Generate presigned URL for file download
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Presigned download URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            
            logger.info(f"Generated presigned download URL for {s3_key}")
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned download URL: {str(e)}")
            raise Exception(f"Failed to generate download URL: {str(e)}")
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete file from S3
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if successful
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Deleted file: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file {s3_key}: {str(e)}")
            raise Exception(f"Failed to delete file: {str(e)}")
    
    def get_file_metadata(self, s3_key: str) -> dict:
        """
        Get file metadata from S3
        
        Args:
            s3_key: S3 object key
            
        Returns:
            File metadata dict
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return {
                "content_type": response.get('ContentType'),
                "content_length": response.get('ContentLength'),
                "last_modified": response.get('LastModified'),
                "etag": response.get('ETag')
            }
        except ClientError as e:
            logger.error(f"Failed to get file metadata for {s3_key}: {str(e)}")
            raise Exception(f"Failed to get file metadata: {str(e)}")
