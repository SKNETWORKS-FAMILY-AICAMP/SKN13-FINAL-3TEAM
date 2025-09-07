"""
이미지 생성 컴포넌트
RunPod을 통해 이미지 생성 모델에 연결하고 S3에 저장
"""

import os
import json
import requests
import boto3
import io
from typing import Dict, Any
from django.conf import settings
from langgraph.graph import StateGraph, END
from .base_state import PipelineState


def generate_image(state: PipelineState) -> PipelineState:
    """
    RunPod을 통해 이미지 생성 모델에 연결하여 이미지 생성하고 S3에 업로드
    """
    try:
        # 이미지 쿼리 가져오기
        image_query = state.get("image_query", "")
        if not image_query:
            state["error"] = "이미지 쿼리가 없습니다."
            return state
        
        print(f"🖼️ 이미지 생성 시작: {image_query}")
        
        # RunPod 이미지 생성 API 호출
        generated_image = call_runpod_image_api(image_query)
        
        if generated_image:
            # S3에 이미지 업로드
            s3_url = upload_image_to_s3(generated_image, image_query)
            
            if s3_url:
                # 답변 타입과 S3 URL만 저장 (response는 비워둠)
                state["answer_type"] = "image"
                state["s3_url"] = s3_url
                print(f"✅ 이미지 생성 및 S3 업로드 완료: {s3_url}")
            else:
                state["error"] = "S3 업로드 실패"
        else:
            state["error"] = "이미지 생성 실패"
            
    except Exception as e:
        print(f"❌ 이미지 생성 중 오류: {str(e)}")
        state["error"] = f"이미지 생성 오류: {str(e)}"
    
    return state


def call_runpod_image_api(image_query: str) -> bytes:
    """
    RunPod 이미지 생성 API 호출
    """
    try:
        # RunPod 엔드포인트 설정 (환경변수에서 가져오기)
        flux_url = os.getenv('FLUX_API_URL')
        runpod_api_key = os.getenv('RUNPOD_API_KEY')
        
        if not flux_url or not runpod_api_key:
            print("❌ RunPod 설정이 없습니다.")
            return None
        
        headers = {
            "Authorization": f"Bearer {runpod_api_key}",
            "Content-Type": "application/json"
        }
        
        # 이미지 생성 요청 페이로드
        payload = {
            "input": {
                "prompt": image_query,
                "width": 1024,
                "height": 1024,
                "num_inference_steps": 20,
                "guidance_scale": 7.5,
                "num_images": 1
            }
        }
        
        print(f"🚀 RunPod API 호출: {flux_url}")
        
        # API 호출
        response = requests.post(
            flux_url,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        response.raise_for_status()
        result = response.json()
        
        # 응답에서 이미지 데이터 추출
        if result.get("status") == "COMPLETED":
            # RunPod 응답 구조에 따라 이미지 데이터 추출
            # 실제 RunPod API 응답 구조에 맞게 수정 필요
            image_data = result.get("output", {}).get("images", [])
            if image_data:
                # Base64 디코딩 또는 URL에서 이미지 다운로드
                import base64
                image_bytes = base64.b64decode(image_data[0])
                return image_bytes
        
        print(f"❌ RunPod 응답 오류: {result}")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ RunPod API 요청 오류: {e}")
        return None
    except Exception as e:
        print(f"❌ RunPod API 호출 중 오류: {e}")
        return None


def upload_image_to_s3(image_bytes: bytes, image_query: str) -> str:
    """
    생성된 이미지를 S3에 업로드
    """
    try:
        # S3 클라이언트 생성
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # 파일명 생성 (쿼리 기반)
        import re
        import hashlib
        safe_query = re.sub(r'[^a-zA-Z0-9_-]', '_', image_query)[:50]
        query_hash = hashlib.md5(image_query.encode()).hexdigest()[:8]
        filename = f"{safe_query}_{query_hash}.png"
        s3_key = f"image/{filename}"
        
        # S3에 업로드
        s3_client.upload_fileobj(
            io.BytesIO(image_bytes),
            settings.AWS_STORAGE_BUCKET_NAME,
            s3_key,
            ExtraArgs={'ContentType': 'image/png'}
        )
        
        # S3 URL 생성
        s3_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"
        
        print(f"📤 S3 업로드 완료: {s3_url}")
        return s3_url
        
    except Exception as e:
        print(f"❌ S3 업로드 오류: {e}")
        return None


