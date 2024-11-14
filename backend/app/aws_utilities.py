from io import BytesIO
from typing import BinaryIO
import boto3
from util import Utilities

class S3Utilities:
    def __init__(self):
        Utilities.Load_Env()
        # Configure boto3 to use LocalStack endpoint
        self.s3_client = boto3.client(
            's3',
            endpoint_url=Utilities.get_env_variable('ENDPOINT_URL'),  # LocalStack default endpoint
            aws_access_key_id=Utilities.get_env_variable('ACCESS_KEY'),
            aws_secret_access_key=Utilities.get_env_variable('SECRET_KEY'),
            region_name='us-east-1'
        )
        self.bucket_name = 'my-image-bucket'

    def ensure_bucket_exists(self):
        """Ensure the S3 bucket exists, create if it doesn't"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except:
            self.s3_client.create_bucket(Bucket=self.bucket_name)

    def upload_to_s3(self, image: BinaryIO) -> tuple[str, str]:
        """Upload image to S3 and return object key and URL"""
        try:
            self.ensure_bucket_exists()
            
            filename = getattr(image, 'filename', 'uploaded_image')
            content_type = getattr(image, 'content_type', 'image/jpeg')
            
            # Upload to S3
            self.s3_client.upload_fileobj(
                image,
                self.bucket_name,
                filename,
                ExtraArgs={'ContentType': content_type}
            )
            
            # Generate URL
            url = f"http://localhost:4566/{self.bucket_name}/{filename}"
            
            return url
            
        except Exception as error:
            print(f"S3 upload failed: {error}")
            raise