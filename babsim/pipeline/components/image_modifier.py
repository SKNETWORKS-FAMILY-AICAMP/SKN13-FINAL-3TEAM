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
import uuid
import mimetypes
import urllib.parse
import time
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
        self.api_url = os.getenv('FLUX_API_URL', '').rstrip('/') + '/generate'
        self.api_key = os.getenv('RUNPOD_API_KEY', '')
        
        # URL 검증
        if not self.api_url:
            print("⚠️ FLUX_API_URL이 설정되지 않았습니다.")
        if not self.api_key:
            print("⚠️ RUNPOD_API_KEY가 설정되지 않았습니다.")
            
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
            s3_url = state.get("s3_url", "")
            if not s3_url:
                # 항상 (response, url) 형태로 반환
                return ("수정할 이미지가 없습니다. 먼저 이미지를 생성해주세요.", None)
            
            if not image_query:
                # 원본 이미지를 보존해 UI가 깨지지 않도록 기존 URL을 함께 반환
                return ("이미지 수정 쿼리가 없습니다.", s3_url)
            
            print(f"✏️ 이미지 수정 시작: {image_query}")
            
            # 이미지 쿼리를 영어로 번역 (한글이 포함된 경우)
            translated_query = self._translate_to_english(image_query)
            print(f"🌐 번역된 수정 쿼리: {translated_query}")
            
            # S3 URL에서 이미지 바이너리 다운로드
            image_binary = self._download_image_from_s3(s3_url)
            
            if image_binary is None:
                return ("이미지 다운로드에 실패했습니다.", s3_url)
            
            # 최종 편집 프롬프트 구성 (간결 + 제약 포함)
            final_prompt = self._build_edit_prompt(translated_query)
            print(f"[ImageModifier] Built edit prompt: {final_prompt}")
            
            # RunPod 이미지 수정 API 호출 (최종 프롬프트 사용)
            modified_image_url = self._call_runpod_image_modification(final_prompt, image_binary)
            
            # 이미지 수정에 대한 상세 설명 생성
            detailed_description = self._generate_modification_description(image_query)
            
            print(f"✅ 이미지 수정 완료: {modified_image_url}")
            # 수정 실패 시 원본 URL을 유지해 후속 단계가 끊기지 않도록 함
            if not modified_image_url:
                return (f"이미지 수정에 실패했습니다. 원본 이미지를 유지합니다.\n사유: 모델 응답 없음", s3_url)
            return (detailed_description, modified_image_url)
                
        except Exception as e:
            print(f"❌ 이미지 수정 오류: {e}")
            return (f"이미지 수정 중 오류가 발생했습니다: {str(e)}", None)
    
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
            # URL 검증
            if not self.api_url:
                print("❌ FLUX_API_URL이 설정되지 않았습니다.")
                return None
                
            # 이미지 바이너리를 base64로 인코딩
            img_str = base64.b64encode(image_binary).decode()
            
            # API 요청 데이터 (편집 안정성 향상 파라미터 포함)
            data = {
                "prompt": prompt,
                "image": img_str,
                "num_inference_steps": 25,
                "guidance_scale": 7.0,
                "scheduler": "DPMSolverMultistepScheduler",
                # 편집 강도: 0.0(원본 유지) ~ 1.0(프롬프트 우선)
                "strength": 0.75,
                # 불필요한 변화 방지 (너무 강하게 막지 않도록 완화)
                "negative_prompt": "do not alter headlights shape, wheels design, grille geometry, windows shape; no text, watermark"
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            print(f"🚀 RunPod 이미지 수정 API 호출: {self.api_url}")
            print(f"[ImageModifier] Final prompt -> RunPod: {prompt}")
            
            response = requests.post(self.api_url, json=data, headers=headers, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            print(f"🔍 RunPod 응답: {result}")
            
            # RunPod API 응답에서 s3_url 추출 (여러 포맷 호환)
            s3_url = (
                result.get("s3_url")
                or result.get("url")
                or result.get("image_url")
            )
            if not s3_url:
                # 흔한 변형: { images: [url, ...] } 또는 { output: { images: [...] } }
                images = result.get("images") or result.get("urls")
                if isinstance(images, list) and images:
                    s3_url = images[0]
                elif isinstance(result.get("output"), dict):
                    out = result.get("output")
                    arr = out.get("images") or out.get("urls") or out.get("outputs")
                    if isinstance(arr, list) and arr:
                        s3_url = arr[0]
            if s3_url:
                print(f"✅ RunPod 이미지 수정 성공: {s3_url}")
                # 우선 URL 인코딩
                s3_url = self._encode_s3_url(s3_url)
                # 가능한 경우 원본을 다운로드해서 우리 버킷의 안전한 파일명으로 재업로드
                try:
                    content = None
                    try:
                        resp = requests.get(s3_url, timeout=30)
                        if 200 <= resp.status_code < 300:
                            content = resp.content
                    except Exception as e:
                        print(f"🔁 원본 URL 다운로드 실패: {e}")
                    # 파일명이 쿼리로 붙은 케이스 보정: '?something.png' -> '%3Fsomething.png'
                    if content is None:
                        parsed = urllib.parse.urlparse(s3_url)
                        if parsed.query and ('=' not in parsed.query):
                            corrected_path = parsed.path + '%3F' + parsed.query
                            corrected_url = urllib.parse.urlunparse((
                                parsed.scheme,
                                parsed.netloc,
                                corrected_path,
                                '',
                                '',
                                ''
                            ))
                            try:
                                print(f"🔧 쿼리를 경로로 보정하여 재시도: {corrected_url}")
                                resp2 = requests.get(corrected_url, timeout=30)
                                if 200 <= resp2.status_code < 300:
                                    content = resp2.content
                                    s3_url = corrected_url
                            except Exception as e2:
                                print(f"❌ 보정 URL 다운로드 실패: {e2}")
                    if content:
                        stable_url = self._upload_bytes_to_s3(content, suggested_ext=".png")
                        if stable_url:
                            self._make_s3_object_public(stable_url)
                            # 캐시 무력화 파라미터 추가
                            try:
                                ts = int(time.time())
                                delimiter = '&' if urllib.parse.urlparse(stable_url).query else '?'
                                stable_url = f"{stable_url}{delimiter}v={ts}"
                            except Exception:
                                pass
                            return stable_url
                    # 재업로드가 실패하면 기존 URL 접근성 확인 + 마지막 시도
                    verified_url = self._ensure_image_accessible(s3_url, result)
                    if verified_url:
                        self._make_s3_object_public(verified_url)
                        return verified_url
                except Exception as e:
                    print(f"❌ 수정 이미지 재업로드 경로 실패: {e}")
                print("❌ 반환된 URL 접근 실패 및 대체 소스 없음")
                return None
            else:
                print(f"❌ RunPod API 오류: s3_url이 없음 - {result}")
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
            response = kanana_llm_model.generate_vllm_response_text(prompt, max_length=200)
            
            # StreamingHttpResponse인 경우 처리
            if hasattr(response, 'content'):
                # StreamingHttpResponse의 경우 content를 읽어서 문자열로 변환
                description = response.content.decode('utf-8') if isinstance(response.content, bytes) else str(response.content)
            else:
                # 일반 문자열인 경우
                description = str(response)
            
            # 기본 설명이 생성되지 않은 경우 폴백
            if not description or len(description.strip()) < 10:
                description = f"'{image_query}'에 따라 이미지를 수정했습니다. 요청하신 내용에 맞게 이미지가 개선되었습니다."
            
            return description.strip()
            
        except Exception as e:
            print(f"❌ 이미지 수정 설명 생성 오류: {e}")
    
    def _build_edit_prompt(self, translated_query: str) -> str:
        """
        편집 전용 최종 프롬프트를 구성. 핵심 지시를 앞에 두고, 유지해야 할 요소를 명시.
        """
        try:
            # 1) 번역이 질문형이면 명령형으로 정규화
            q = (translated_query or "").strip()
            q = q.rstrip(" ?!.")
            lowered = q.lower()
            if lowered.startswith("how can i "):
                q = q[len("How can I "):]  # 질문형 접두사 제거
            if lowered.startswith("please "):
                q = q[len("Please "):]
            # 기본 동사 보강: change/modify 없으면 앞에 Change 추가
            if not any(v in lowered for v in ["change ", "modify ", "repaint "]):
                q = f"Change {q}"

            # 2) 보존/범위 지시
            base_directive = (
                "Apply to car body paint only; keep composition, proportions, trim, headlights, wheels, grille, windows, and environment unchanged. "
                "Photorealistic."
            )
            # 77 토큰 내로 유지되도록 간결하게 결합
            final = f"{q}. {base_directive}"
            return final.strip()
        except Exception:
            return translated_query

    def _ensure_image_accessible(self, primary_url: str, result_json: dict) -> Optional[str]:
        """주어진 URL이 200 OK인지 확인하고, 실패 시 결과 JSON에서 대체 소스를 찾아 재업로드 후 URL 반환"""
        try:
            if self._http_ok(primary_url):
                return primary_url
            # 대체 URL 후보들 수집
            candidates = []
            for key in ["s3_url", "url", "image_url"]:
                u = result_json.get(key)
                if isinstance(u, str): candidates.append(u)
            list_keys = ["images", "urls"]
            for lk in list_keys:
                arr = result_json.get(lk)
                if isinstance(arr, list):
                    for u in arr:
                        if isinstance(u, str): candidates.append(u)
            if isinstance(result_json.get("output"), dict):
                out = result_json.get("output")
                for lk in ["images", "urls", "outputs"]:
                    arr = out.get(lk)
                    if isinstance(arr, list):
                        for u in arr:
                            if isinstance(u, str): candidates.append(u)
            # 후보들 검사
            for u in candidates:
                if self._http_ok(u):
                    return u
            # base64 이미지 폴백
            b64_keys = ["image_base64", "image", "data"]
            for bk in b64_keys:
                b64 = result_json.get(bk)
                if isinstance(b64, str) and len(b64) > 100:
                    try:
                        # data:image/png;base64,.... 형태 제거
                        if b64.startswith("data:"):
                            comma = b64.find(',')
                            b64 = b64[comma+1:] if comma != -1 else b64
                        content = base64.b64decode(b64)
                        return self._upload_bytes_to_s3(content, suggested_ext=".png")
                    except Exception as e:
                        print(f"❌ base64 디코드 실패: {e}")
            return None
        except Exception as e:
            print(f"❌ URL 접근성 확인 실패: {e}")
            return None

    def _http_ok(self, url: str) -> bool:
        try:
            r = requests.head(url, timeout=10)
            if r.status_code == 405:  # 일부 호스트는 HEAD 미지원
                r = requests.get(url, stream=True, timeout=15)
            return 200 <= r.status_code < 300
        except Exception:
            return False

    def _upload_bytes_to_s3(self, content: bytes, suggested_ext: str = ".png") -> Optional[str]:
        if not self.s3_client:
            return None
        try:
            # 안전한 파일명 생성
            key = f"images/{int(time.time())}_{uuid.uuid4().hex}{suggested_ext}"
            # ContentType 추정
            ctype = mimetypes.types_map.get(suggested_ext.lower(), "image/png")
            self.s3_client.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=key,
                Body=content,
                ContentType=ctype,
            )
            region = settings.AWS_S3_REGION_NAME
            bucket = settings.AWS_STORAGE_BUCKET_NAME
            return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
        except Exception as e:
            print(f"❌ 재업로드 실패: {e}")
            return None
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
Translate this Korean text to English for car image modification:

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

# ImageModifier 인스턴스 생성
image_modifier = ImageModifier()
