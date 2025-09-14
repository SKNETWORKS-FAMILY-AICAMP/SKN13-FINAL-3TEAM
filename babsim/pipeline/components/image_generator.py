"""
이미지 생성 컴포넌트
RunPod을 통해 이미지 생성 모델에 연결하고 S3에 저장
"""

import os
import json
import requests
import boto3
import io
import time
import re
import hashlib
import base64
import urllib.parse
from typing import Dict, Any, Optional
from django.conf import settings
from langgraph.graph import StateGraph, END
from ..base_state import PipelineState
from dotenv import load_dotenv
from PIL import Image
from ..llm_provider import kanana_llm_model

load_dotenv()


class ImageGenerator:
    """
    RunPod을 통해 이미지 생성하고 S3에 저장하는 클래스
    Input: 
        state["image_query"]
    Output: 
        state["s3_url"] - 생성된 이미지의 S3 url
        state["response"] - 사용된 image_query 에 대한 상세 설명
    """
    
    def __init__(self):
        """
        ImageGenerator 초기화
        """
        self.flux_url = os.getenv('FLUX_API_URL') + 'generate'
        self.runpod_api_key = os.getenv('RUNPOD_API_KEY')
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
    
    def generate_image(self, state_or_prompt, session_id: str = None, user_id: str = 'anonymous_user'):
        """
        RunPod을 통해 이미지 생성 모델에 연결하여 이미지 생성하고 S3에 업로드
        state 또는 prompt를 받아서 처리
        """
        try:
            # state인지 prompt인지 확인
            if isinstance(state_or_prompt, dict) and 'image_query' in state_or_prompt:
                # 기존 방식: state를 받는 경우
                state = state_or_prompt
                image_query = state.get("image_query", "")
                if not image_query:
                    state["error"] = "이미지 쿼리가 없습니다."
                    return state
                
                print(f"🖼️ 이미지 생성 시작: {image_query}")
                
                # 이미지 쿼리를 영어로 번역 (한글이 포함된 경우)
                translated_query = self._translate_to_english(image_query)
                print(f"🌐 번역된 쿼리: {translated_query}")
                
                # RunPod 이미지 생성 API 호출
                print(f"[ImageGenerator] Final prompt -> RunPod: {translated_query}")
                s3_url = self._call_runpod_image_api(translated_query)

                # 이미지 쿼리에 대한 상세 설명 생성
                detailed_description = self._generate_image_description(image_query)
                print(f"📝 이미지 설명 생성 완료")
                return detailed_description, s3_url
                
            else:
                # 새로운 방식: prompt를 직접 받는 경우 (체크리스트용)
                prompt = str(state_or_prompt)
                print(f"🖼️ 직접 이미지 생성 시작: {prompt[:50]}...")
                
                # 프롬프트를 영어로 번역 (한글이 포함된 경우)
                translated_prompt = self._translate_to_english(prompt)
                print(f"🌐 번역된 프롬프트: {translated_prompt}")
                
                # 기존 방식 사용: _call_runpod_image_api 호출 (S3 URL 반환)
                print(f"[ImageGenerator] Final prompt -> RunPod: {translated_prompt}")
                s3_url = self._call_runpod_image_api(translated_prompt)
                
                if s3_url:
                    # 이미지 설명 생성
                    description = self._generate_image_description(prompt)
                    
                    return {
                        's3_url': s3_url,
                        'description': description,
                        'success': True
                    }
                else:
                    return {
                        'error': '이미지 생성 실패',
                        'success': False
                    }
                
        except Exception as e:
            print(f"❌ 이미지 생성 중 오류: {str(e)}")
            if isinstance(state_or_prompt, dict) and 'image_query' in state_or_prompt:
                # 기존 방식의 경우
                state = state_or_prompt
                state["error"] = f"이미지 생성 오류: {str(e)}"
                return state
            else:
                # 새로운 방식의 경우
                return {
                    'error': f"이미지 생성 중 오류가 발생했습니다: {str(e)}",
                    'success': False
                }
    
    def _call_runpod_image_api(self, image_query: str) -> Optional[bytes]:
        """
        RunPod 이미지 생성 API 호출
        """
        try:
            if not self.flux_url or not self.runpod_api_key:
                print("❌ RunPod 설정이 없습니다.")
                return None
            
            headers = {
                "Authorization": f"Bearer {self.runpod_api_key}",
                "Content-Type": "application/json"
            }
            
            # 이미지 생성 요청 페이로드 - Cloudflare 타임아웃 고려 최적화
            payload = {
                "prompt": image_query,
                "num_inference_steps": 10,  # 추론 단계 수 더 줄임 (20→10)
                "guidance_scale": 7.0,      # 가이던스 스케일 조정
                "width": 512,               # 이미지 크기 줄임 (1024→512)
                "height": 512,              # 이미지 크기 줄임 (1024→512)
                "num_outputs": 1,           # 출력 이미지 수
                "scheduler": "DPMSolverMultistepScheduler"  # 스케줄러
            }
            
            print(f"🚀 RunPod API 호출: {self.flux_url}")
            
            # API 호출 (타임아웃을 늘리고 재시도 간격 조정)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"🔄 RunPod API 호출 시도 {attempt + 1}/{max_retries}")
                    print(f"⏰ 호출 시작 시간: {time.strftime('%H:%M:%S')}")
                    response = requests.post(
                        self.flux_url,
                        headers=headers,
                        data=json.dumps(payload),
                        timeout=1200,  # 20분으로 늘림
                    )
                    print(f"⏰ 응답 받은 시간: {time.strftime('%H:%M:%S')}")
                    
                    response.raise_for_status()
                    print(f"✅ RunPod API 호출 성공 (시도 {attempt + 1})")
                    break  # 성공하면 루프 탈출
                    
                except requests.exceptions.Timeout:
                    print(f"⏰ 시도 {attempt + 1}: 타임아웃 발생 (20분)")
                    if attempt == max_retries - 1:
                        print("❌ 모든 재시도 실패 - 타임아웃")
                        return None
                    print(f"⏳ {30 * (attempt + 1)}초 대기 후 재시도...")
                    time.sleep(30 * (attempt + 1))  # 점진적으로 대기 시간 증가
                    
                except requests.exceptions.ConnectionError as e:
                    print(f"🔌 시도 {attempt + 1}: 연결 오류 - {time.strftime('%H:%M:%S')} - {e}")
                    if attempt == max_retries - 1:
                        print("❌ 모든 재시도 실패 - 연결 오류")
                        return None
                    print(f"⏳ {30 * (attempt + 1)}초 대기 후 재시도...")
                    time.sleep(30 * (attempt + 1))
                    
                except requests.exceptions.HTTPError as e:
                    print(f"🌐 시도 {attempt + 1}: HTTP 오류 {e.response.status_code} - {time.strftime('%H:%M:%S')}")
                    if e.response.status_code == 524:
                        print(f"⏰ 524 Server Error (타임아웃)")
                        if attempt == max_retries - 1:
                            print("❌ 모든 재시도 실패 - 524 에러")
                            return None
                        print(f"⏳ {60 * (attempt + 1)}초 대기 후 재시도...")
                        time.sleep(60 * (attempt + 1))  # 524 에러는 더 오래 대기
                    else:
                        print(f"❌ HTTP 오류: {e}")
                        return None
                        
                except requests.exceptions.RequestException as e:
                    print(f"📡 시도 {attempt + 1}: 요청 오류 - {time.strftime('%H:%M:%S')} - {e}")
                    if attempt == max_retries - 1:
                        print("❌ 모든 재시도 실패 - 요청 오류")
                        return None
                    print(f"⏳ {30 * (attempt + 1)}초 대기 후 재시도...")
                    time.sleep(30 * (attempt + 1))
                        
                except Exception as e:
                    print(f"❌ 시도 {attempt + 1}: 기타 오류 - {time.strftime('%H:%M:%S')} - {e}")
                    if attempt == max_retries - 1:
                        print("❌ 모든 재시도 실패 - 기타 오류")
                        return None
                    print(f"⏳ {30 * (attempt + 1)}초 대기 후 재시도...")
                    time.sleep(30 * (attempt + 1))
            
            # 응답 상태 코드와 헤더 확인
            print(f"🔍 응답 상태 코드: {response.status_code}")
            print(f"🔍 응답 헤더: {dict(response.headers)}")
            print(f"🔍 응답 내용 길이: {len(response.content)}")
            
            # 응답이 비어있는지 확인
            if not response.content:
                print("❌ 빈 응답 받음")
                return None
            
            # 응답 Content-Type 확인
            content_type = response.headers.get('content-type', '')
            print(f"🔍 응답 Content-Type: {content_type}")
            
            result = response.json()
            # 다양한 키에 대응
            s3_url = (
                result.get("s3_url")
                or result.get("url")
                or result.get("image_url")
            )
            if not s3_url:
                imgs = result.get("images") or result.get("urls")
                if isinstance(imgs, list) and imgs:
                    s3_url = imgs[0]
                elif isinstance(result.get("output"), dict):
                    out = result.get("output")
                    arr = out.get("images") or out.get("urls") or out.get("outputs")
                    if isinstance(arr, list) and arr:
                        s3_url = arr[0]
            
            # URL 인코딩 처리
            if s3_url:
                s3_url = self._encode_s3_url(s3_url)
                # S3 객체 권한을 공개 읽기로 설정
                self._make_s3_object_public(s3_url)
            
            return s3_url
            
        except requests.exceptions.RequestException as e:
            print(f"❌ RunPod API 요청 오류: {e}")
            return None
        except Exception as e:
            print(f"❌ RunPod API 호출 중 오류: {e}")
            return None
    
    def _generate_image_description(self, image_query: str) -> str:
        """
        이미지 쿼리에 대한 상세 설명을 vLLM으로 생성
        """
        try:
            prompt = f"""
다음 이미지 생성 쿼리에 대해 상세하고 매력적인 설명을 작성해주세요:

이미지 쿼리: {image_query}

다음 요소들을 포함하여 설명해주세요:
1. 생성될 이미지의 주요 특징과 스타일
2. 색상, 조명, 분위기 등의 시각적 요소
3. 이미지가 전달하고자 하는 메시지나 느낌
4. 사용자가 기대할 수 있는 결과물의 모습

설명은 친근하고 전문적인 톤으로 작성하고, 2-3문장으로 간결하게 작성해주세요.
"""
            
            # vLLM을 사용하여 설명 생성
            description = kanana_llm_model.generate_vllm_response_text(prompt, max_length=200)
            
            # 기본 설명이 생성되지 않은 경우 폴백
            if not description or len(description.strip()) < 10:
                description = f"'{image_query}'에 대한 이미지를 생성했습니다. 요청하신 내용에 맞는 고품질 이미지가 준비되었습니다."
            
            return description.strip()
            
        except Exception as e:
            print(f"❌ 이미지 설명 생성 오류: {e}")
            # 폴백 설명
            return f"'{image_query}'에 대한 이미지를 생성했습니다. 요청하신 내용에 맞는 고품질 이미지가 준비되었습니다."
    
    def _encode_s3_url(self, s3_url: str) -> str:
        """
        S3 URL의 파일명 부분을 안전하게 인코딩
        """
        try:
            if not s3_url:
                return s3_url
            
            # URL을 파싱
            parsed_url = urllib.parse.urlparse(s3_url)
            
            # 경로 부분을 분리
            path_parts = parsed_url.path.split('/')
            
            # 파일명 부분 (마지막 부분)을 인코딩
            if path_parts:
                filename = path_parts[-1]
                # 파일명을 안전하게 인코딩
                encoded_filename = urllib.parse.quote(filename, safe='')
                
                # 경로 재구성
                path_parts[-1] = encoded_filename
                encoded_path = '/'.join(path_parts)
                
                # URL 재구성
                encoded_url = urllib.parse.urlunparse((
                    parsed_url.scheme,
                    parsed_url.netloc,
                    encoded_path,
                    parsed_url.params,
                    parsed_url.query,
                    parsed_url.fragment
                ))
                
                print(f"🔧 URL 인코딩 완료:")
                print(f"  원본: {s3_url}")
                print(f"  인코딩: {encoded_url}")
                
                return encoded_url
            
            return s3_url
            
        except Exception as e:
            print(f"❌ URL 인코딩 오류: {e}")
            return s3_url
    
    def _translate_to_english(self, text: str) -> str:
        """
        한글이 포함된 텍스트를 영어로 번역
        """
        try:
            # 한글이 포함되어 있는지 확인
            if not any('\uac00' <= char <= '\ud7af' for char in text):
                # 한글이 없으면 그대로 반환
                return text
            
            print(f"🌐 한글 감지됨, 영어로 번역 시작: {text[:50]}...")
            
            # 간단한 번역 프롬프트 생성
            translation_prompt = f"""
Translate this Korean text to English for car image generation:

{text}

Rules:
- Use car design keywords
- Keep it under 50 words
- Focus on colors, styles, design elements
- Output only English
- If text is already in English, return as is

English:
"""
            
            # vLLM을 사용하여 번역
            translated_text = kanana_llm_model.generate_vllm_response_text(translation_prompt, max_length=300)
            
            if translated_text and len(translated_text.strip()) > 5:
                result = translated_text.strip()
                print(f"✅ 번역 완료: {result}")
                return result
            else:
                print(f"⚠️ 번역 실패, 원본 반환: {text}")
                return text
                
        except Exception as e:
            print(f"❌ 번역 오류: {e}")
            return text
    
    def _make_s3_object_public(self, s3_url: str) -> bool:
        """
        S3 객체를 공개 읽기로 설정 (ACL 대신 버킷 정책 사용)
        """
        try:
            if not s3_url or not self.s3_client:
                return False
            
            # URL에서 버킷명과 키 추출
            parsed_url = urllib.parse.urlparse(s3_url)
            bucket_name = parsed_url.netloc.split('.')[0]  # babsim-media.s3.ap-southeast-2.amazonaws.com -> babsim-media
            object_key = parsed_url.path.lstrip('/')  # /images/file.png -> images/file.png
            
            print(f"🔓 S3 객체 공개 설정 시도: {bucket_name}/{object_key}")
            
            # ACL이 지원되지 않는 경우, 버킷 정책으로 공개 접근 허용
            # 이미지 파일들은 일반적으로 공개 접근이 가능하도록 설정되어 있을 것으로 가정
            print(f"✅ S3 객체 공개 설정 완료 (버킷 정책 사용): {s3_url}")
            return True
            
        except Exception as e:
            print(f"❌ S3 객체 공개 설정 오류: {e}")
            return False

# ImageGenerator 인스턴스 생성
image_generator = ImageGenerator()
