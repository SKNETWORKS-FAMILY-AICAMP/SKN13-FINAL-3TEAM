"""
4D 모델 생성 컴포넌트
RunPod을 통해 4D 모델 생성하고 S3에 저장
"""

import os
import json
import requests
import boto3
import io
from typing import Dict, Any
from django.conf import settings
from langgraph.graph import StateGraph, END
from ..base_state import PipelineState


def generate_4d_model(state: PipelineState) -> PipelineState:
    """
    RunPod을 통해 4D 모델 생성하고 S3에 업로드
    """
    try:
        # 4D 쿼리 가져오기 (image_query 필드 재사용)
        d4_query = state.get("image_query", "")
        if not d4_query:
            state["error"] = "4D 생성 쿼리가 없습니다."
            return state
        
        print(f"🎯 4D 모델 생성 시작: {d4_query}")
        
        # RunPod 4D 생성 API 호출
        generated_4d = call_runpod_4d_api(d4_query)
        
        if generated_4d:
            # S3에 4D 모델 업로드
            s3_url = upload_4d_to_s3(generated_4d, d4_query)
            
            if s3_url:
                # 답변 타입과 S3 URL만 저장
                state["answer_type"] = "4D"
                state["s3_url"] = s3_url
                print(f"✅ 4D 모델 생성 및 S3 업로드 완료: {s3_url}")
            else:
                state["error"] = "S3 업로드 실패"
        else:
            state["error"] = "4D 모델 생성 실패"
            
    except Exception as e:
        print(f"❌ 4D 모델 생성 중 오류: {str(e)}")
        state["error"] = f"4D 모델 생성 오류: {str(e)}"
    
    return state


def call_runpod_4d_api(d4_query: str) -> bytes:
    """
    RunPod 4D 모델 생성 API 호출
    """
    try:
        # RunPod 엔드포인트 설정
        runpod_endpoint = os.getenv('4D_API_URL')
        runpod_api_key = os.getenv('RUNPOD_API_KEY')
        
        if not runpod_endpoint or not runpod_api_key:
            print("❌ 4D RunPod 설정이 없습니다.")
            return None
        
        headers = {
            "Authorization": f"Bearer {runpod_api_key}",
            "Content-Type": "application/json"
        }
        
        # 4D 모델 생성 요청 페이로드
        payload = {
            "input": {
                "prompt": d4_query,
                "format": "glb",  # 4D 모델 형식
                "quality": "high",
                "num_inference_steps": 100,  # 4D는 더 복잡하므로 더 많은 스텝
                "temporal_resolution": 30  # 4D 특성: 시간 해상도
            }
        }
        
        print(f"🚀 4D RunPod API 호출: {runpod_endpoint}")
        
        # API 호출
        response = requests.post(
            runpod_endpoint,
            headers=headers,
            json=payload,
            timeout=180  # 4D 생성은 가장 오래 걸림
        )
        
        response.raise_for_status()
        result = response.json()
        
        # 응답에서 4D 모델 데이터 추출
        if result.get("status") == "COMPLETED":
            model_data = result.get("output", {}).get("model", [])
            if model_data:
                import base64
                model_bytes = base64.b64decode(model_data[0])
                return model_bytes
        
        print(f"❌ 4D RunPod 응답 오류: {result}")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 4D RunPod API 요청 오류: {e}")
        return None
    except Exception as e:
        print(f"❌ 4D RunPod API 호출 중 오류: {e}")
        return None


def upload_4d_to_s3(model_bytes: bytes, d4_query: str) -> str:
    """
    생성된 4D 모델을 S3에 업로드
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
        safe_query = re.sub(r'[^a-zA-Z0-9_-]', '_', d4_query)[:50]
        query_hash = hashlib.md5(d4_query.encode()).hexdigest()[:8]
        filename = f"{safe_query}_{query_hash}.glb"
        s3_key = f"4d/{filename}"
        
        # S3에 업로드
        s3_client.upload_fileobj(
            io.BytesIO(model_bytes),
            settings.AWS_STORAGE_BUCKET_NAME,
            s3_key,
            ExtraArgs={'ContentType': 'model/gltf-binary'}
        )
        
        # S3 URL 생성
        s3_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"
        
        print(f"📤 4D S3 업로드 완료: {s3_url}")
        return s3_url
        
    except Exception as e:
        print(f"❌ 4D S3 업로드 오류: {e}")
        return None
