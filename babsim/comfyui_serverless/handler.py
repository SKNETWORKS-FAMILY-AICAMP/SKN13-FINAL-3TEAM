#!/usr/bin/env python3

import os
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, List

import requests
import runpod
import boto3
from pydantic import BaseModel

# 설정
COMFY_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = Path("/workspace/outputs")
WORKFLOWS_DIR = Path("/opt/baked_workflows")

# AWS 설정
AWS_BUCKET = os.getenv("AWS_STORAGE_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_S3_REGION_NAME", "ap-southeast-2") 
AWS_ACCESS_KEY = os.getenv("ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
# S3 경로 고정 (babsim-media 사용)

# S3 클라이언트 초기화
s3_client = boto3.client(
    's3',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
) if all([AWS_BUCKET, AWS_ACCESS_KEY, AWS_SECRET_KEY]) else None

print(f"✓ S3 configured: {s3_client is not None}")

# 입력 스키마 (테스트 payload와 일치)
class VideoInput(BaseModel):
    prompt: str
    image_path: str
    width: int = 768
    height: int = 448
    frames: int = 49
    frame_rate: int = 24
    steps: int = 30
    strength: float = 0.4
    seed: int = 42
    crf: int = 23

class ThreeDInput(BaseModel):
    image_path: str
    prompt: str = ""  # 3D 생성용 프롬프트 추가
    tex_res: int = 1024
    steps: int = 30
    seed: int = 12345
    file_format: str = "glb"

class JobInput(BaseModel):
    task_type: str  # "video" or "3d"
    workflow: str   # workflow filename
    video: Optional[VideoInput] = None
    three_d: Optional[ThreeDInput] = None

# ComfyUI API 함수들
def submit_workflow(workflow: Dict) -> str:
    """워크플로우 제출하고 prompt_id 반환"""
    response = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow})
    response.raise_for_status()
    return response.json()["prompt_id"]

def wait_for_completion(prompt_id: str, timeout: int = 600) -> bool:
    """워크플로우 완료 대기"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{COMFY_URL}/history/{prompt_id}")
            if response.status_code == 200:
                history = response.json()
                if prompt_id in history:
                    status = history[prompt_id].get("status", {})
                    if status.get("completed", False):
                        return True
                    elif "error" in status:
                        print(f"Workflow error: {status['error']}")
                        return False
        except:
            pass
        
        time.sleep(2)
    
    return False

def load_workflow(workflow_name: str) -> Dict:
    """워크플로우 JSON 로드"""
    workflow_path = WORKFLOWS_DIR / f"{workflow_name}.json"
    
    if not workflow_path.exists():
        raise FileNotFoundError(f"Workflow not found: {workflow_path}")
    
    with open(workflow_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_output_files() -> List[Path]:
    """출력 파일 목록 가져오기"""
    output_files = []
    
    for ext in ['*.png', '*.jpg', '*.jpeg', '*.mp4', '*.mov', '*.glb', '*.obj']:
        output_files.extend(OUTPUT_DIR.glob(f"**/{ext}"))
    
    # 최신 파일들만 반환 (최근 5분 이내)
    recent_files = []
    current_time = time.time()
    
    for file_path in output_files:
        if current_time - file_path.stat().st_mtime < 300:  # 5분
            recent_files.append(file_path)
    
    return sorted(recent_files, key=lambda x: x.stat().st_mtime, reverse=True)

def upload_to_s3(file_path: Path) -> Optional[str]:
    """S3에 파일 업로드하고 URL 반환"""
    if not s3_client:
        print("S3 client not configured")
        return None
    
    try:
        # 파일 확장자에 따른 폴더 분류 (babsim-media 고정 경로)
        ext = file_path.suffix.lower()
        if ext in ['.png']:
            s3_folder = "babsim-media/images"
        elif ext in ['.mp4', '.mov']:
            s3_folder = "babsim-media/videos"
        elif ext in ['.glb', '.obj']:
            s3_folder = "babsim-media/models"
        else:
            s3_folder = "babsim-media/images"  # 기본값을 images로 설정
        
        # S3 키 생성
        job_id = str(uuid.uuid4())[:8]
        s3_key = f"{s3_folder}/{job_id}/{file_path.name}"
        
        # 업로드
        s3_client.upload_file(str(file_path), AWS_BUCKET, s3_key)
        
        # URL 생성
        url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        print(f"✓ Uploaded: {url}")
        return url
        
    except Exception as e:
        print(f"S3 upload error: {e}")
        return None

def modify_workflow(workflow_json: Dict, user_image_path: str, user_prompt: str) -> Dict:
    """워크플로우의 input image와 prompt를 사용자 입력으로 교체"""
    
    # 1. LoadImage 노드 찾아서 이미지 교체
    for node_id, node in workflow_json.items():
        if node.get("class_type") == "LoadImage":
            node["inputs"]["image"] = user_image_path
            print(f"🖼️ Updated LoadImage node {node_id}: {user_image_path}")
    
    # 2. CLIPTextEncode 노드 찾아서 프롬프트 교체 (positive만)
    for node_id, node in workflow_json.items():
        if (node.get("class_type") == "CLIPTextEncode" and 
            "positive" in node.get("_meta", {}).get("title", "").lower()):
            node["inputs"]["text"] = user_prompt
            print(f"📝 Updated CLIPTextEncode node {node_id}: {user_prompt[:50]}...")
    
    return workflow_json

def download_input_image(url: str) -> str:
    """입력 이미지를 URL에서 다운로드"""
    try:
        print(f"Downloading input image: {url}")
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # 파일명 생성
        filename = f"input_{int(time.time())}.png"
        local_path = OUTPUT_DIR / "inputs" / filename
        local_path.parent.mkdir(exist_ok=True)
        
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✓ Input image saved: {local_path}")
        return str(local_path)
        
    except Exception as e:
        print(f"✗ Failed to download input image: {e}")
        raise

def process_task(job_input: JobInput) -> Dict[str, Any]:
    """메인 작업 처리 함수"""
    try:
        task_type = job_input.task_type
        print(f"🚀 Processing {task_type} task...")
        
        # 입력 데이터 준비
        if task_type == "video":
            if not job_input.video:
                raise ValueError("video input required for video task")
            
            # 입력 이미지 다운로드
            local_image_path = download_input_image(job_input.video.image_path)
            
            input_data = {
                "image_path": local_image_path,
                "prompt": job_input.video.prompt,
                "width": job_input.video.width,
                "height": job_input.video.height,
                "frames": job_input.video.frames,
                "steps": job_input.video.steps,
                "seed": job_input.video.seed
            }
            workflow_name = job_input.workflow or "LTX_video"
            
        elif task_type == "3d":
            if not job_input.three_d:
                raise ValueError("three_d input required for 3d task")
            
            # 입력 이미지 다운로드
            local_image_path = download_input_image(job_input.three_d.image_path)
            
            input_data = {
                "image_path": local_image_path,
                "tex_res": job_input.three_d.tex_res,
                "steps": job_input.three_d.steps,
                "seed": job_input.three_d.seed
            }
            workflow_name = job_input.workflow or "hunyuan_3d"
        else:
            raise ValueError(f"Unknown task_type: {task_type}")
        
        print(f"📋 Using workflow: {workflow_name}")
        print(f"🖼️ Input image: {input_data['image_path']}")
        
        # 워크플로우 로드 및 파라미터 주입
        workflow = load_workflow(workflow_name)
        
        # 사용자 입력으로 워크플로우 동적 수정
        user_prompt = job_input.video.prompt if task_type == "video" else job_input.three_d.prompt if task_type == "3d" else ""
        workflow = modify_workflow(workflow, input_data['image_path'], user_prompt)
        
        # 워크플로우 실행
        print(f"▶️ Submitting workflow...")
        prompt_id = submit_workflow(workflow)
        print(f"⏳ Workflow submitted: {prompt_id}")
        
        if not wait_for_completion(prompt_id):
            raise RuntimeError("Workflow execution failed or timed out")
        
        print(f"✅ Workflow completed!")
        
        # 결과 파일 수집
        output_files = get_output_files()
        if not output_files:
            raise RuntimeError("No output files generated")
        
        print(f"📁 Found {len(output_files)} output files")
        
        # S3 업로드
        uploaded_urls = []
        for file_path in output_files[:3]:  # 최대 3개 파일
            print(f"📤 Uploading {file_path.name}...")
            url = upload_to_s3(file_path)
            if url:
                uploaded_urls.append(url)

        result = {
                "success": True,
                "task_type": task_type,
                "outputs": uploaded_urls,
                "file_count": len(output_files),
                "workflow": workflow_name
        }
        
        print(f"🎉 Task completed successfully!")
        print(f"📋 Results: {len(uploaded_urls)} files uploaded to S3")
        for url in uploaded_urls:
            print(f"🔗 {url}")
        
        return result       

    except Exception as e:
        print(f"❌ Task failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "task_type": getattr(job_input, 'task_type', 'unknown')
        }

# RunPod 핸들러
def handler(job):
    """RunPod 작업 핸들러"""
    try:
        job_input = JobInput(**job["input"])
        return process_task(job_input)
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    print("🚀 Starting RunPod handler...")
    print(f"ComfyUI URL: {COMFY_URL}")
    print(f"Output dir: {OUTPUT_DIR}")
    print(f"S3 bucket: {AWS_BUCKET}")

runpod.serverless.start({"handler": handler})