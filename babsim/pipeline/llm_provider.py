from __future__ import annotations
import os
import json
import torch
from typing import Optional
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
from peft import PeftModel
import requests
from django.http import StreamingHttpResponse
from django.conf import settings

def _env(path_key: str, default: Optional[str] = None) -> Optional[str]:
    p = os.getenv(path_key, default)
    return p if p and os.path.exists(p) else default

class _KananaChat:
    def __init__(self):
        # 로컬 모델 로딩 로직을 제거하여 앱 시작 시 에러 방지
        pass

    def _build_prompt(self, prompt: str) -> str:
        system = "당신은 현대자동차/자동차 지식에 특화된 한국어 어시스턴트입니다. 반드시 한국어로 답하세요."
        return f"[SYSTEM]\n{system}\n\n[USER]\n{prompt}\n\n[ASSISTANT]\n"

    @torch.inference_mode()
    def generate_response(self, prompt: str, max_length: int = 512, temperature: float = 0.7) -> str:
        # 기존 로컬 추론 대신, vLLM 서버를 호출하는 함수를 사용
        return generate_vllm_response(prompt, max_length=max_length, temperature=temperature)

kanana_llm_model = _KananaChat()

def generate_vllm_response_text(prompt: str, max_length: int = 512) -> str:
    """
    RunPod의 vLLM API 서버를 호출하여 모델의 응답을 문자열로 생성합니다.
    (파이프라인 중간 과정용)
    """
    # URL에 v1/chat/completions/ 자동 추가
    base_url = settings.VLLM_API_URL.rstrip('/')
    api_url = f"{base_url}/v1/chat/completions"
    model_name = settings.VLLM_MODEL_NAME
    
    # 디버깅: 실제 URL 확인
    print(f"🔍 vLLM API URL: {api_url}")
    print(f"🔍 Model Name: {model_name}")

    headers = {"Content-Type": "application/json"}
    
    # OpenAI 호환 API 형식에 맞게 데이터 구성
    data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "당신은 현대자동차/자동차 지식에 특화된 한국어 어시스턴트입니다. 반드시 한국어로 답하세요."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_length,
        "temperature": temperature,
    }

    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(data), timeout=180)
        response.raise_for_status()
        
        # 디버깅: 응답 정보 확인
        print(f"🔍 Text 응답 상태 코드: {response.status_code}")
        print(f"🔍 Text 응답 Content-Type: {response.headers.get('content-type', '')}")
        print(f"🔍 Text 응답 내용 (처음 500자): {response.text[:500]}...")
        
        # 응답에서 텍스트 추출
        try:
            result = response.json()
            print(f"🔍 JSON 파싱 성공: {result}")
            
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content'].strip()
                print(f"🔍 추출된 내용: {content}")
                return content
            else:
                print("🔍 choices가 없거나 비어있음")
                return "응답을 생성할 수 없습니다."
        except Exception as e:
            print(f"🔍 JSON 파싱 오류: {e}")
            print(f"🔍 응답 내용: {response.text}")
            return "응답을 파싱하는 데 실패했습니다."
    
    except requests.exceptions.RequestException as e:
        print(f"vLLM API 호출 오류: {e}")
        return "모델 응답을 가져오는 데 실패했습니다."

    except (KeyError, IndexError) as e:
        print(f"vLLM API 응답 처리 오류: {e}")
        return "모델 응답을 처리하는 데 실패했습니다."

def generate_vllm_response_streaming(prompt: str, max_length: int = 512) -> StreamingHttpResponse:
    """
    RunPod의 vLLM API 서버를 호출하여 모델의 응답을 스트리밍으로 생성합니다.
    (최종 사용자 응답용) - 완전 동기 방식
    """
    def event_stream():
        # 완전 동기 방식으로 스트리밍 구현
        import requests
        import json
        import time
        
        # URL 설정
        base_url = settings.VLLM_API_URL.rstrip('/')
        api_url = f"{base_url}/v1/chat/completions"
        model_name = settings.VLLM_MODEL_NAME
        
        print(f"🔍 vLLM API URL: {api_url}")
        print(f"🔍 Model Name: {model_name}")
        
        headers = {"Content-Type": "application/json"}
        
        # 스트리밍 요청 데이터
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_length,
            "stream": True,
            "temperature": 0.7
        }
        
        try:
            print("🔍 스트리밍 요청 시작...")
            
            # requests로 스트리밍 요청
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                stream=True,
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"vLLM API 오류: {response.status_code}")
                # 폴백으로 일반 응답을 스트리밍 시뮬레이션
                yield from _fallback_streaming_simulation(prompt, max_length)
                return
            
            print(f"🔍 스트리밍 응답 Content-Type: {response.headers.get('content-type', 'N/A')}")
            
            # 스트리밍 응답 처리
            buffer = ""
            chunk_count = 0
            
            for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                if chunk:
                    buffer += chunk
                    chunk_count += 1
                    
                    # 줄 단위로 처리
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if line.startswith('data: '):
                            data_content = line[6:].strip()
                            
                            # [DONE] 신호 처리
                            if data_content == '[DONE]':
                                print("🔍 스트리밍 완료: [DONE]")
                                return
                            
                            try:
                                # JSON 파싱 시도
                                json_data = json.loads(data_content)
                                if 'choices' in json_data and len(json_data['choices']) > 0:
                                    delta = json_data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        content = delta['content']
                                        print(f"🔍 청크 {chunk_count}: '{content}'")
                                        # 브라우저 버퍼링 우회용 패딩
                                        content = content.ljust(1024, " ")
                                        yield f"data: {json.dumps({'choices': [{'delta': {'content': content}}]})}\n\n"
                            
                            except json.JSONDecodeError as e:
                                print(f"JSON 파싱 오류: {e}")
                                print(f"원본 라인: {line}")
                                continue
            
            print(f"🔍 총 {chunk_count}개 청크 처리 완료")
            
        except Exception as e:
            print(f"스트리밍 API 호출 오류: {e}")
            # 폴백으로 일반 응답을 스트리밍 시뮬레이션
            yield from _fallback_streaming_simulation(prompt, max_length)

    print("SSSSSSSSSStreamingHttpResponse 반환됨 !!!")
    result = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    result["Cache-Control"] = "no-cache"
    result["X-Accel-Buffering"] = "no"
    return result

from django.http import StreamingHttpResponse
import time

def test_stream(prompt):
    def generate():
        for i in range(5):
            yield f"data: chunk {i}\n\n"
            time.sleep(1)
    return StreamingHttpResponse(generate(), content_type="text/event-stream")

def _fallback_streaming_simulation(prompt: str, max_length: int):
    """폴백: 일반 응답을 스트리밍으로 시뮬레이션"""
    print("🔍 폴백 모드: 일반 응답을 스트리밍으로 시뮬레이션")
    
    try:
        import requests
        import json
        import time
        
        # URL 설정
        base_url = settings.VLLM_API_URL.rstrip('/')
        api_url = f"{base_url}/v1/chat/completions"
        model_name = settings.VLLM_MODEL_NAME
        
        headers = {"Content-Type": "application/json"}
        
        # 일반 요청 데이터
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_length,
            "stream": False,
            "temperature": 0.7
        }
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            # 단어별로 스트리밍 시뮬레이션
            words = content.split()
            for i, word in enumerate(words):
                yield f"data: {json.dumps({'choices': [{'delta': {'content': word + ' '}}]})}\n\n"
                
                if i < len(words) - 1:  # 마지막 단어가 아니면
                    time.sleep(0.05)  # 50ms 지연
            
            # 완료 신호
            yield "data: [DONE]\n\n"
        else:
            yield f"data: {json.dumps({'error': 'API 호출 실패'})}\n\n"
            
    except Exception as e:
        yield f"data: {json.dumps({'error': f'폴백 모드 실패: {str(e)}'})}\n\n"

async def _streaming_generator(prompt: str, max_length: int):
    """test_streaming.py 방식의 스트리밍 제너레이터"""
    # 먼저 스트리밍 시도
    try:
        async for chunk in _try_streaming_response(prompt, max_length):
            yield chunk
    except Exception as e:
        print(f"🔍 스트리밍 실패, 폴백 모드로 전환: {e}")
        # 스트리밍 실패 시 일반 응답을 스트리밍으로 시뮬레이션
        async for chunk in _fallback_streaming_response(prompt, max_length):
            yield chunk

async def _try_streaming_response(prompt: str, max_length: int):
    """실제 스트리밍 응답 시도"""
    # URL에 v1/chat/completions/ 자동 추가
    base_url = settings.VLLM_API_URL.rstrip('/')
    api_url = f"{base_url}/v1/chat/completions"
    model_name = settings.VLLM_MODEL_NAME
        
    # 디버깅: 실제 URL 확인
    print(f"🔍 vLLM Streaming API URL: {api_url}")
    print(f"🔍 Model Name: {model_name}")

    headers = {"Content-Type": "application/json"}
    
    # OpenAI 호환 API 형식에 맞게 데이터 구성
    data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "당신은 현대자동차/자동차 지식에 특화된 한국어 어시스턴트입니다. 반드시 한국어로 답하세요."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_length,
        "temperature": 0.7,
        "stream": True,
    }

    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=120)) as response:
            response.raise_for_status()
            
            # Content-Type 확인
            content_type = response.headers.get('content-type', '')
            print(f"🔍 스트리밍 응답 Content-Type: {content_type}")
            
            # vLLM 서버의 스트리밍 응답 처리
            buffer = ""
            chunk_count = 0
            
            async for chunk in response.content.iter_chunked(1024):
                if chunk:
                    buffer += chunk.decode('utf-8', errors='ignore')
                    chunk_count += 1
                    
                    # 줄 단위로 처리
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if line.startswith('data: '):
                            data_content = line[6:].strip()
                            
                            # [DONE] 신호 처리
                            if data_content == '[DONE]':
                                print(f"🔍 스트리밍 완료: [DONE] (총 청크: {chunk_count})")
                                yield f"data: {json.dumps({'choices': [{'delta': {'content': ''}, 'finish_reason': 'stop'}]})}\n\n"
                                break
                            
                            try:
                                # JSON 파싱 시도
                                json_data = json.loads(data_content)
                                if 'choices' in json_data and len(json_data['choices']) > 0:
                                    delta = json_data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        content = delta['content']
                                        print(f"🔍 스트리밍 청크 {chunk_count}: '{content}'")
                                        yield f"data: {json.dumps({'choices': [{'delta': {'content': content}}]})}\n\n"
                                    elif 'finish_reason' in json_data['choices'][0]:
                                        print(f"🔍 스트리밍 완료: {json_data['choices'][0]['finish_reason']}")
                                        yield f"data: {json.dumps({'choices': [{'delta': {'content': ''}, 'finish_reason': json_data['choices'][0]['finish_reason']}]})}\n\n"
                            except json.JSONDecodeError as e:
                                # JSON이 아닌 경우 그대로 전달
                                print(f"🔍 JSON 파싱 오류: {e}")
                                print(f"🔍 원본 라인: {line}")
                                print(f"🔍 데이터 내용: {data_content}")
                                yield f"data: {data_content}\n\n"
                        elif line:
                            # data: 접두사가 없는 경우 추가
                            print(f"🔍 일반 라인: {line}")
                            yield f"data: {line}\n\n"

async def _fallback_streaming_response(prompt: str, max_length: int):
    """스트리밍 실패 시 일반 응답을 스트리밍으로 시뮬레이션"""
    print("🔍 폴백 모드: 일반 응답을 스트리밍으로 시뮬레이션")
    
    # 일반 텍스트 응답 생성
    response_text = generate_vllm_response_text(prompt, max_length)
    print(f"🔍 폴백 모드 응답 텍스트: {response_text[:100]}...")
    
    # 텍스트를 단어 단위로 나누어 스트리밍 시뮬레이션 (test_streaming.py 방식)
    words = response_text.split()
    print(f"🔍 폴백 모드 단어 수: {len(words)}")
    
    for i, word in enumerate(words):
        # 각 단어를 개별 청크로 전송
        content = word + (" " if i < len(words) - 1 else "")
        print(f"🔍 폴백 스트리밍 청크 {i+1}/{len(words)}: '{content}'")
        yield f"data: {json.dumps({'choices': [{'delta': {'content': content}}]})}\n\n"
        
        # 자연스러운 타이핑 효과를 위한 지연
        import asyncio
        await asyncio.sleep(0.05)  # 50ms 지연
    
    # 완료 신호
    print("🔍 폴백 모드 완료")
    yield f"data: {json.dumps({'choices': [{'delta': {'content': ''}, 'finish_reason': 'stop'}]})}\n\n"

# 기존 함수명 유지 (하위 호환성)
def generate_vllm_response(prompt: str, max_length: int = 512) -> str:
    """기존 함수명 유지 - 텍스트 응답 반환"""
    return generate_vllm_response_text(prompt, max_length)


# 전역 모델 인스턴스
kanana_llm_model = _KananaChat()
kanana_llm_model.generate_response("현대차에 대해 설명해줘")