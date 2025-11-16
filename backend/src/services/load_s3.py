import boto3
from botocore.client import Config
from src.config.get_env import EnvConfig

s3 = boto3.client(
    "s3",
    endpoint_url=EnvConfig.S3_ENDPOINT,
    aws_access_key_id=EnvConfig.S3_ACCESS_KEY,
    aws_secret_access_key=EnvConfig.S3_SECRET_KEY,
    region_name=EnvConfig.S3_REGION,
    config=Config(signature_version="s3v4")
)

object_key = "ЛБ1 (1).pdf"

local_filename = "downloaded_test.pdf"

s3.download_file(EnvConfig.S3_BUCKET, object_key, local_filename)

print("✅ Файл скачан:", local_filename)

# import boto3
# from botocore.client import Config

# s3 = boto3.client(
#     "s3",
#     aws_access_key_id=EnvConfig.S3_ACCESS_KEY,
#     aws_secret_access_key=EnvConfig.S3_SECRET_KEY,
#     endpoint_url=EnvConfig.S3_ENDPOINT,
#     region_name=EnvConfig.S3_REGION,
#     config=Config(signature_version="s3v4")
# )

# bucket = "bucket-04559a"

# resp = s3.list_objects_v2(Bucket=bucket)
# for obj in resp.get('Contents', []):
#     print(obj['Key'])
