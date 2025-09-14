
import os
import boto3
from dotenv import load_dotenv

def create_s3_folders():
    """S3 버킷에 기본 폴더(images, videos, models)를 생성합니다."""
    load_dotenv()

    bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME')
    aws_access_key_id = os.getenv('ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    region_name = os.getenv('AWS_S3_REGION_NAME')

    if not all([bucket_name, aws_access_key_id, aws_secret_access_key, region_name]):
        print("오류: .env 파일에 AWS 설정이 모두 필요합니다.")
        print("(AWS_STORAGE_BUCKET_NAME, ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_REGION_NAME)")
        return

    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )

    folders_to_create = ['images/', 'videos/', 'models/']

    print(f"'{bucket_name}' 버킷에 폴더 생성을 시작합니다...")
    for folder in folders_to_create:
        try:
            # 폴더가 이미 있는지 확인하지 않고 그냥 생성 요청을 보냅니다.
            # S3는 동일한 이름의 객체를 덮어쓰므로 문제가 없습니다.
            s3_client.put_object(Bucket=bucket_name, Key=folder)
            print(f" - '{folder}' 생성/확인 완료.")
        except Exception as e:
            print(f" - '{folder}' 생성 중 오류 발생: {e}")

    print("폴더 설정이 완료되었습니다.")

if __name__ == "__main__":
    create_s3_folders()
