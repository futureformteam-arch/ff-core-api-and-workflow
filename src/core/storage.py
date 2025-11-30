import boto3
from botocore.exceptions import ClientError
import os

class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "mock_key"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "mock_secret"),
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "futureform-evidence")

    def generate_presigned_url(self, object_name: str, expiration=3600):
        """Generate a presigned URL to share an S3 object"""
        try:
            response = self.s3_client.generate_presigned_url('put_object',
                                                            Params={'Bucket': self.bucket_name,
                                                                    'Key': object_name},
                                                            ExpiresIn=expiration)
        except ClientError as e:
            print(e)
            return None
        return response
