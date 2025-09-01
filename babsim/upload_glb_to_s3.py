
import os
import boto3
from dotenv import load_dotenv

def upload_glb_files():
    """frontend/build/models 폴더의 .glb 파일들을 S3에 업로드합니다."""
    load_dotenv()

    bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME')
    aws_access_key_id = os.getenv('ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    region_name = os.getenv('AWS_S3_REGION_NAME')

    if not all([bucket_name, aws_access_key_id, aws_secret_access_key, region_name]):
        print("오류: .env 파일에 AWS 설정이 모두 필요합니다.")
        return

    local_directory = 'frontend/build/models'
    if not os.path.isdir(local_directory):
        print(f"오류: 로컬 디렉토리를 찾을 수 없습니다 - {local_directory}")
        return

    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )

    print(f"'{local_directory}'의 .glb 파일 업로드를 시작합니다...")
    for filename in os.listdir(local_directory):
        if filename.endswith('.glb'):
            local_path = os.path.join(local_directory, filename)
            s3_key = f"models/{filename}"

            print(f" - '{local_path}' -> s3://{bucket_name}/{s3_key}")
            try:
                s3_client.upload_file(
                    local_path, 
                    bucket_name, 
                    s3_key,
                    ExtraArgs={'ContentType': 'model/gltf-binary'}
                )
                file_url = f"https://{bucket_name}.s3.{region_name}.amazonaws.com/{s3_key}"
                print(f"   성공. URL: {file_url}")
            except Exception as e:
                print(f"   실패: {e}")

    print("업로드 작업이 완료되었습니다.")

if __name__ == "__main__":
    upload_glb_files()
