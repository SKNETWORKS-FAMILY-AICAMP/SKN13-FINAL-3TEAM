"""
이미지 수정 컴포넌트
기존 이미지를 기반으로 수정 요청을 처리하고 새로운 이미지 생성
"""

import os
import json
import requests
import boto3
import io
import base64
import hashlib
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from ..base_state import PipelineState
from django.conf import settings
from PIL import Image
from ..llm_provider import kanana_llm_model


class ImageModifier:
    """
    이미지 수정을 담당하는 클래스
    Input:
        state["image_query"] - 수정 요청 텍스트
        state["s3_url"] - 기존 이미지 S3 URL (필수사항)
    Output:
        state["s3_url"] - 수정된 이미지의 S3 URL
        state["response"] - 수정에 대한 상세 설명
    """
    
    def __init__(self):
        """
        ImageModifier 초기화
        """
        self.api_url = getattr(settings, 'RUNPOD_IMAGE_API_URL', '')
        self.api_key = getattr(settings, 'RUNPOD_API_KEY', '')
        self.s3_client = None
        self._initialize_s3_client()
    
    def _initialize_s3_client(self):
        """
        S3 클라이언트 초기화
        """
        
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
        except Exception as e:
            print(f"❌ S3 클라이언트 초기화 오류: {e}")
            self.s3_client = None
    
    def modify_image(self, state: PipelineState) -> PipelineState:
        """
        기존 이미지를 기반으로 수정 요청을 처리하여 새로운 이미지 생성
        """
        try:
            # 이미지 쿼리와 기존 이미지 가져오기
            image_query = state.get("image_query", "")
            s3_url = state.get("s3_url", "https://babsim-media.s3.ap-southeast-2.amazonaws.com/images/1757566389_hyundai_car_image_generation.png"
        )
            
            if not image_query:
                state["error"] = "이미지 수정 쿼리가 없습니다."
                return state
            
            print(f"✏️ 이미지 수정 시작: {image_query}")
            
            # S3 URL에서 이미지 바이너리 다운로드
            image_binary = self._download_image_from_s3(s3_url)
            
            if image_binary is None:
                state["error"] = "이미지 다운로드에 실패했습니다."
                return state
            
            # RunPod 이미지 수정 API 호출
            modified_image_url = self._call_runpod_image_modification(image_query, image_binary)
            
            # 이미지 수정에 대한 상세 설명 생성
            detailed_description = self._generate_modification_description(image_query)
            
            print(f"✅ 이미지 수정 완료: {modified_image_url}")

            return detailed_description, modified_image_url
                
        except Exception as e:
            print(f"❌ 이미지 수정 오류: {e}")
            state["error"] = f"이미지 수정 중 오류가 발생했습니다: {str(e)}"

        return state
    
    def _download_image_from_s3(self, s3_url: str) -> Optional[bytes]:
        """
        S3 URL에서 이미지 바이너리를 다운로드
        """
        try:
            print(f"📥 S3에서 이미지 다운로드: {s3_url}")
            
            # HTTP 요청으로 이미지 다운로드
            response = requests.get(s3_url, timeout=30)
            response.raise_for_status()
            
            print(f"✅ 이미지 다운로드 완료: {len(response.content)} bytes")
            
            return response.content
            
        except Exception as e:
            print(f"❌ 이미지 다운로드 오류: {e}")
            return None
    
    def _call_runpod_image_modification(self, prompt: str, image_binary: bytes) -> Optional[str]:
        """
        RunPod을 통해 이미지 수정 API 호출
        """
        try:
            # 이미지 바이너리를 base64로 인코딩
            img_str = base64.b64encode(image_binary).decode()
            
            # API 요청 데이터
            data = {
                "prompt": prompt,
                "image": img_str
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            print(f"🚀 RunPod 이미지 수정 API 호출: {self.api_url}")
            
            response = requests.post(self.api_url, json=data, headers=headers, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            print(f"🔍 RunPod 응답: {result}")
            
            if result.get("status") == "COMPLETED":
                return result.get("s3_url")
            else:
                print(f"❌ RunPod API 오류: {result}")
                return None
                
        except Exception as e:
            print(f"❌ RunPod 이미지 수정 API 호출 오류: {e}")
            return None
    
    def _generate_modification_description(self, image_query: str) -> str:
        """
        이미지 수정에 대한 상세 설명을 vLLM으로 생성
        """
        try:
            prompt = f"""
다음 이미지 수정 요청에 대해 상세하고 매력적인 설명을 작성해주세요:

수정 요청: {image_query}

다음 요소들을 포함하여 설명해주세요:
1. 어떤 부분이 수정되었는지
2. 수정된 이미지의 새로운 특징과 변화
3. 수정 후 이미지의 시각적 개선점
4. 사용자가 기대할 수 있는 결과물의 모습

설명은 친근하고 전문적인 톤으로 작성하고, 2-3문장으로 간결하게 작성해주세요.
"""
            
            # vLLM을 사용하여 설명 생성
            description = kanana_llm_model.generate_response(prompt, max_length=200)
            
            # 기본 설명이 생성되지 않은 경우 폴백
            if not description or len(description.strip()) < 10:
                description = f"'{image_query}'에 따라 이미지를 수정했습니다. 요청하신 내용에 맞게 이미지가 개선되었습니다."
            
            return description.strip()
            
        except Exception as e:
            print(f"❌ 이미지 수정 설명 생성 오류: {e}")

# ImageModifier 인스턴스 생성
image_modifier = ImageModifier()
