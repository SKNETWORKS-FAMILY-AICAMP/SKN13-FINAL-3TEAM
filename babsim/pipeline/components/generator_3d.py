"""
3D 모델 생성 컴포넌트
RunPod을 통해 3D 모델 생성하고 S3에 저장
"""

import os
import json
import requests
import boto3
import io
from typing import Dict, Any
from django.conf import settings
from langgraph.graph import StateGraph, END
from ..text_pipeline import PipelineState


def generate_3d_model(state: PipelineState) -> PipelineState:
    """
    RunPod을 통해 3D 모델 생성하고 S3에 업로드
    """
    try:
        # 3D 쿼리 가져오기 (image_query 필드 재사용)
        d3_query = state.get("image_query", "")
        if not d3_query:
            state["error"] = "3D 생성 쿼리가 없습니다."
            return state
        
        print(f"🎯 3D 모델 생성 시작: {d3_query}")
        
        # RunPod 3D 생성 API 호출
        generated_3d = call_runpod_3d_api(d3_query)
        
        if generated_3d:
            # S3에 3D 모델 업로드
            s3_url = upload_3d_to_s3(generated_3d, d3_query)
            
            if s3_url:
                # 답변 타입과 S3 URL만 저장
                state["answer_type"] = "3D"
                state["s3_url"] = s3_url
                print(f"✅ 3D 모델 생성 및 S3 업로드 완료: {s3_url}")
            else:
                state["error"] = "S3 업로드 실패"
        else:
            state["error"] = "3D 모델 생성 실패"
            
    except Exception as e:
        print(f"❌ 3D 모델 생성 중 오류: {str(e)}")
        state["error"] = f"3D 모델 생성 오류: {str(e)}"
    
    return state


def call_runpod_3d_api(d3_query: str) -> bytes:
    """
    RunPod 3D 모델 생성 API 호출
    """
    try:
        # RunPod 엔드포인트 설정
        runpod_endpoint = os.getenv('3D_API_URL')
        runpod_api_key = os.getenv('RUNPOD_API_KEY')
        
        if not runpod_endpoint or not runpod_api_key:
            print("❌ 3D RunPod 설정이 없습니다.")
            return None
        
        headers = {
            "Authorization": f"Bearer {runpod_api_key}",
            "Content-Type": "application/json"
        }
        
        # 3D 모델 생성 요청 페이로드
        payload = {
            "input": {
                "prompt": d3_query,
                "format": "glb",  # 3D 모델 형식
                "quality": "high",
                "num_inference_steps": 50
            }
        }
        
        print(f"🚀 3D RunPod API 호출: {runpod_endpoint}")
        
        # API 호출
        response = requests.post(
            runpod_endpoint,
            headers=headers,
            json=payload,
            timeout=120  # 3D 생성은 더 오래 걸림
        )
        
        response.raise_for_status()
        result = response.json()
        
        # 응답에서 3D 모델 데이터 추출
        if result.get("status") == "COMPLETED":
            model_data = result.get("output", {}).get("model", [])
            if model_data:
                import base64
                model_bytes = base64.b64decode(model_data[0])
                return model_bytes
        
        print(f"❌ 3D RunPod 응답 오류: {result}")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 3D RunPod API 요청 오류: {e}")
        return None
    except Exception as e:
        print(f"❌ 3D RunPod API 호출 중 오류: {e}")
        return None


def upload_3d_to_s3(model_bytes: bytes, d3_query: str) -> str:
    """
    생성된 3D 모델을 S3에 업로드
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
        safe_query = re.sub(r'[^a-zA-Z0-9_-]', '_', d3_query)[:50]
        query_hash = hashlib.md5(d3_query.encode()).hexdigest()[:8]
        filename = f"{safe_query}_{query_hash}.glb"
        s3_key = f"3d/{filename}"
        
        # S3에 업로드
        s3_client.upload_fileobj(
            io.BytesIO(model_bytes),
            settings.AWS_STORAGE_BUCKET_NAME,
            s3_key,
            ExtraArgs={'ContentType': 'model/gltf-binary'}
        )
        
        # S3 URL 생성
        s3_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"
        
        print(f"📤 3D S3 업로드 완료: {s3_url}")
        return s3_url
        
    except Exception as e:
        print(f"❌ 3D S3 업로드 오류: {e}")
        return None
