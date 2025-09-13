"""
3D 모델 생성 컴포넌트
RunPod을 통해 3D 모델 생성하고 S3에 저장
"""

import os
import json
import requests
import json
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
import uuid
import os


class Generator3D:
    """3D 생성기 클래스 - RunPod Serverless를 사용하여 3D 모델 생성"""
    
    def __init__(self):
        self.serverless_url = os.getenv("3D_ENDPOINT_ID", "https://api.runpod.ai/v2/your-3d-endpoint")
        self.api_key = os.getenv("RUNPOD_API_KEY", "your-api-key")
        self.s3_client = boto3.client('s3')
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'babsim-bucket')
        
    def generate_3d_model(self, image_url: str, prompt: str = "") -> Dict[str, Any]:
        """
        3D 모델 생성
        
        Args:
            image_url: 입력 이미지 URL
            prompt: 추가 프롬프트 (선택사항)
            
        Returns:
            Dict containing s3_url_3d, generation_type, status, error
        """
        try:
            print(f"[3D 생성기] 3D 모델 생성 시작 - 이미지: {image_url}")
            
            # RunPod Serverless API 호출
            payload = {
                "input": {
                    "image_url": image_url,
                    "prompt": prompt or "Generate a high-quality 3D model of this car",
                    "quality": "high",
                    "format": "glb"
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # RunPod API 호출
            response = requests.post(
                f"{self.serverless_url}/run",
                headers=headers,
                json=payload,
                timeout=300  # 5분 타임아웃
            )
            
            if response.status_code != 200:
                return {
                    "error": f"RunPod API 호출 실패: {response.status_code} - {response.text}",
                    "generation_type": "3d",
                    "s3_url_3d": None
                }
            
            result = response.json()
            
            # 작업 ID 추출
            job_id = result.get("id")
            if not job_id:
                return {
                    "error": "RunPod에서 작업 ID를 받지 못했습니다.",
                    "generation_type": "3d", 
                    "s3_url_3d": None
                }
            
            print(f"[3D 생성기] 작업 ID: {job_id}")
            
            # 작업 완료 대기 및 결과 조회
            final_result = self._wait_for_completion(job_id)
            
            if "error" in final_result:
                return final_result
            
            # 3D 모델 파일을 S3에 업로드
            s3_url = self._upload_to_s3(final_result["output"], "3d_model.glb")
            
            if not s3_url:
                return {
                    "error": "3D 모델을 S3에 업로드하는데 실패했습니다.",
                    "generation_type": "3d",
                    "s3_url_3d": None
                }
            
            print(f"[3D 생성기] 3D 모델 생성 완료: {s3_url}")
            
            return {
                "s3_url_3d": s3_url,
                "generation_type": "3d",
                "status": "success",
                "error": None
            }
            
        except Exception as e:
            print(f"[3D 생성기] 오류 발생: {str(e)}")
            return {
                "error": f"3D 모델 생성 중 오류: {str(e)}",
                "generation_type": "3d",
                "s3_url_3d": None
            }
    
    def _wait_for_completion(self, job_id: str, max_wait_time: int = 600) -> Dict[str, Any]:
        """작업 완료까지 대기"""
        import time
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = requests.get(
                    f"{self.serverless_url}/status/{job_id}",
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code != 200:
                    return {"error": f"상태 조회 실패: {response.status_code}"}
                
                result = response.json()
                status = result.get("status")
                
                if status == "COMPLETED":
                    return result
                elif status == "FAILED":
                    return {"error": f"작업 실패: {result.get('error', 'Unknown error')}"}
                elif status in ["IN_QUEUE", "IN_PROGRESS"]:
                    print(f"[3D 생성기] 작업 진행 중... (상태: {status})")
                    time.sleep(10)  # 10초 대기
                else:
                    return {"error": f"알 수 없는 상태: {status}"}
                    
            except Exception as e:
                return {"error": f"상태 조회 중 오류: {str(e)}"}
        
        return {"error": "작업 완료 시간 초과"}
    
    def _upload_to_s3(self, file_data: Any, filename: str) -> Optional[str]:
        """3D 모델 파일을 S3에 업로드"""
        try:
            # 고유한 파일명 생성
            unique_filename = f"3d_models/{uuid.uuid4()}_{filename}"
            
            # 파일 데이터가 URL인 경우 다운로드
            if isinstance(file_data, str) and file_data.startswith("http"):
                response = requests.get(file_data)
                file_content = response.content
            else:
                # 바이너리 데이터인 경우
                file_content = file_data
            
            # S3에 업로드
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=unique_filename,
                Body=file_content,
                ContentType="model/gltf-binary"
            )
            
            # S3 URL 생성
            s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{unique_filename}"
            print(f"[3D 생성기] S3 업로드 완료: {s3_url}")
            
            return s3_url
            
        except Exception as e:
            print(f"[3D 생성기] S3 업로드 실패: {str(e)}")
            return None


# 전역 인스턴스 생성
generator_3d = Generator3D()