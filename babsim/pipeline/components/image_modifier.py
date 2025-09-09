"""
이미지 수정 컴포넌트
기존 이미지를 기반으로 수정 요청을 처리하고 새로운 이미지 생성
"""

import os
import json
import requests
import boto3
import io
from typing import Dict, Any, Optional
from django.conf import settings
from langgraph.graph import StateGraph, END
from ..text_pipeline import PipelineState


def modify_image(state: PipelineState) -> PipelineState:
    """
    기존 이미지를 기반으로 수정 요청을 처리하여 새로운 이미지 생성
    """
    try:
        # 이미지 쿼리와 기존 이미지 가져오기
        image_query = state.get("image_query", "")
        input_image = state.get("generated_image", None)
        
        if not image_query:
            state["error"] = "이미지 수정 쿼리가 없습니다."
            return state
        
        print(f"✏️ 이미지 수정 시작: {image_query}")
        
        # 기존 이미지가 있는지 확인
        if input_image is None:
            print("⚠️ 기존 이미지가 없어서 새로 생성합니다.")
            return generate_new_image(state)
        
        # 문자열(경로)이면 PIL.Image로 변환
        if isinstance(input_image, str):
            if os.path.exists(input_image):
                from PIL import Image
                input_image = Image.open(input_image)
            else:
                print("⚠️ 이미지 파일을 찾을 수 없어서 새로 생성합니다.")
                return generate_new_image(state)
        
        # RunPod 이미지 수정 API 호출
        modified_image_url = call_runpod_image_modification(image_query, input_image)
        
        if modified_image_url:
            # S3에 업로드
            s3_url = upload_to_s3(modified_image_url, f"modified_{state.get('session_id', 'unknown')}")
            
            # 결과 저장
            state.update({
                "generated_image": s3_url,
                "image_generation_status": "completed",
                "image_type": "modified",
                "response": f"이미지 수정이 완료되었습니다! 🎨\n\n수정된 이미지: {s3_url}"
            })
            
            print(f"✅ 이미지 수정 완료: {s3_url}")
        else:
            state["error"] = "이미지 수정에 실패했습니다."
            
    except Exception as e:
        print(f"❌ 이미지 수정 오류: {e}")
        state["error"] = f"이미지 수정 중 오류가 발생했습니다: {str(e)}"
    
    return state


def generate_new_image(state: PipelineState) -> PipelineState:
    """
    새로운 이미지 생성 (기존 이미지가 없을 때)
    """
    try:
        image_query = state.get("image_query", "")
        print(f"📸 새 이미지 생성 중: {image_query}")
        
        # RunPod 새 이미지 생성 API 호출
        new_image_url = call_runpod_image_generation(image_query)
        
        if new_image_url:
            # S3에 업로드
            s3_url = upload_to_s3(new_image_url, f"new_{state.get('session_id', 'unknown')}")
            
            # 결과 저장
            state.update({
                "generated_image": s3_url,
                "image_generation_status": "completed",
                "image_type": "new",
                "response": f"새로운 이미지가 생성되었습니다! 🎨\n\n생성된 이미지: {s3_url}"
            })
            
            print(f"✅ 새 이미지 생성 완료: {s3_url}")
        else:
            state["error"] = "이미지 생성에 실패했습니다."
            
    except Exception as e:
        print(f"❌ 이미지 생성 오류: {e}")
        state["error"] = f"이미지 생성 중 오류가 발생했습니다: {str(e)}"
    
    return state


def call_runpod_image_modification(prompt: str, input_image) -> Optional[str]:
    """
    RunPod을 통해 이미지 수정 API 호출
    """
    try:
        # RunPod API 설정
        api_url = getattr(settings, 'RUNPOD_IMAGE_API_URL', 'https://your-runpod-endpoint.com')
        
        # 이미지를 base64로 인코딩
        import base64
        from io import BytesIO
        
        buffer = BytesIO()
        input_image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        # API 요청 데이터
        data = {
            "input": {
                "prompt": prompt,
                "image": img_str,
                "guidance_scale": 4.5,
                "num_inference_steps": 20
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {getattr(settings, 'RUNPOD_API_KEY', '')}"
        }
        
        response = requests.post(api_url, json=data, headers=headers, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("status") == "COMPLETED":
            return result.get("output", {}).get("image_url")
        else:
            print(f"RunPod API 오류: {result}")
            return None
            
    except Exception as e:
        print(f"RunPod 이미지 수정 API 호출 오류: {e}")
        return None


def call_runpod_image_generation(prompt: str) -> Optional[str]:
    """
    RunPod을 통해 새 이미지 생성 API 호출
    """
    try:
        # RunPod API 설정
        api_url = getattr(settings, 'RUNPOD_IMAGE_API_URL', 'https://your-runpod-endpoint.com')
        
        # API 요청 데이터
        data = {
            "input": {
                "prompt": prompt,
                "guidance_scale": 30,
                "num_inference_steps": 20
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {getattr(settings, 'RUNPOD_API_KEY', '')}"
        }
        
        response = requests.post(api_url, json=data, headers=headers, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("status") == "COMPLETED":
            return result.get("output", {}).get("image_url")
        else:
            print(f"RunPod API 오류: {result}")
            return None
            
    except Exception as e:
        print(f"RunPod 이미지 생성 API 호출 오류: {e}")
        return None


def upload_to_s3(image_url: str, filename: str) -> str:
    """
    이미지를 S3에 업로드하고 URL 반환
    """
    try:
        # S3 설정
        s3_client = boto3.client(
            's3',
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', ''),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''),
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'ap-northeast-2')
        )
        
        bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'babsim-images')
        
        # 이미지 다운로드
        response = requests.get(image_url)
        response.raise_for_status()
        
        # S3에 업로드
        s3_key = f"generated_images/{filename}.png"
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=response.content,
            ContentType='image/png'
        )
        
        # S3 URL 생성
        s3_url = f"https://{bucket_name}.s3.{getattr(settings, 'AWS_S3_REGION_NAME', 'ap-northeast-2')}.amazonaws.com/{s3_key}"
        
        return s3_url
        
    except Exception as e:
        print(f"S3 업로드 오류: {e}")
        return image_url  # 원본 URL 반환
