#!/usr/bin/env python3

import os
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, List
import secrets

import requests
import runpod
import boto3
from pydantic import BaseModel

import re
from botocore.exceptions import ClientError

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

def _s3_key_exists(bucket: str, key: str) -> bool:
    """S3 오브젝트 존재 여부"""
    if not s3_client:
        return False
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        # 404는 '없음'
        if e.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
            return False
        print(f"head_object error (treat as not exists): {e}")
        return False

def _next_available_name(folder: str, filename: str) -> str:
    """
    'AnimateDiff_00001.mp4'처럼 끝에 번호가 붙는 이름을 유지하며
    S3 폴더 내 다음 가용 번호를 찾아 반환.
    번호가 없으면 _00001부터 시작.
    """
    p = Path(filename)
    stem, suffix = p.stem, p.suffix  # ('AnimateDiff_00001', '.mp4')

    m = re.search(r"^(.*?)(?:_)?(\d+)$", stem)
    if m:
        base = m.group(1) or ""
        num = int(m.group(2))
    else:
        base = stem
        num = 0

    while True:
        num += 1
        cand_name = f"{base}_{num:05d}{suffix}"
        cand_key = f"{folder}/{cand_name}"
        if not _s3_key_exists(AWS_BUCKET, cand_key):
            return cand_name

# 입력 스키마 (테스트 payload와 일치)
class VideoInput(BaseModel):
    prompt: Optional[str] = None
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
    prompt: Optional[str] = None  # 3D 생성용 프롬프트 추가
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
    """워크플로우 JSON 로드 (간결+견고)"""
    # 1) ".json" 붙었으면 제거
    name = workflow_name[:-5] if workflow_name.lower().endswith(".json") else workflow_name

    # 2) 탐색할 기본 경로들 (기존 WORKFLOWS_DIR 우선)
    search_dirs = []
    try:
        search_dirs.append(WORKFLOWS_DIR if isinstance(WORKFLOWS_DIR, Path) else Path(WORKFLOWS_DIR))
    except Exception:
        pass
    search_dirs += [Path("/opt/baked_workflows"), Path("/workspace/workflows")]

    tried = []

    # 3) 정확 파일명 먼저 시도
    for base in search_dirs:
        p = base / f"{name}.json"
        tried.append(p)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)

    # 4) 대소문자 무시한 보정(동일 stem 탐색)
    for base in search_dirs:
        try:
            for q in base.glob("*.json"):
                if q.stem.lower() == name.lower():
                    with open(q, "r", encoding="utf-8") as f:
                        return json.load(f)
        except Exception:
            pass

    raise FileNotFoundError(f"Workflow not found for '{workflow_name}'. tried={[str(p) for p in tried]}")

def ensure_models_ready(max_wait: int = 300) -> bool:
    """ComfyUI 서버/노드 준비 + 필수 모델 파일 존재 확인"""
    start = time.time()

    # 1) 서버 살아있는지 먼저 확인
    print("🔍 Checking ComfyUI server readiness...")
    for i in range(60):
        try:
            r = requests.get(f"{COMFY_URL}/system_stats", timeout=3)
            if r.status_code == 200:
                print("✓ ComfyUI server is responding")
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        print("❌ ComfyUI did not respond within 60s")
        return False

    # 2) 반복적으로 노드/모델 확인
    wanted_candidates = [
         ["/workspace/models/checkpoints/ltxv-2b-0.9.8-distilled.safetensors",
         "/opt/ComfyUI/models/checkpoints/ltxv-2b-0.9.8-distilled.safetensors"],
         ["/workspace/models/diffusion_models/hunyuan3d-dit-v2_fp16.safetensors",
        "/opt/ComfyUI/models/diffusion_models/hunyuan3d-dit-v2_fp16.safetensors"],
        ["/workspace/models/text_encoders/t5xxl_fp16.safetensors",
        "/opt/ComfyUI/models/text_encoders/t5xxl_fp16.safetensors"],
     ]

    def files_ok() -> bool:
        try:
            for choices in wanted_candidates:
                if not any(Path(p).exists() and Path(p).stat().st_size > 0 for p in choices):
                    print(f"✗ Missing or empty model file (any of): {choices}")
                    return False
            return True
        except Exception as e:
            print(f"⚠️ File check failed: {e}")
            return False

    while time.time() - start < max_wait:
        try:
            oi = requests.get(f"{COMFY_URL}/object_info", timeout=5).json()
            node_keys = [k.lower() for k in oi.keys()]
            has_ltx = any(k.startswith("ltx") or k.startswith("ltxv") for k in node_keys)
            has_hy3d = any(("hunyuan3d" in k) or ("hy3d" in k) for k in node_keys)

            if has_ltx and has_hy3d and files_ok():
                print("✓ Custom nodes present and required model files exist")
                return True

            # 디버깅 도움 로그 (처음 몇 번만)
            elapsed = int(time.time() - start)
            print(f"⏳ Not ready yet... ({elapsed}s) nodes={len(node_keys)} "
                  f"ltx={has_ltx} hy3d={has_hy3d}")
            if elapsed in (5, 15, 30, 60):
                print("   sample node keys:", node_keys[:20])

            # 모델 목록 리프레시 시도
            try:
                requests.post(f"{COMFY_URL}/refresh_models", timeout=3)
            except Exception:
                pass

        except Exception as e:
            print(f"⚠️ Failed to query object_info: {e}")

        time.sleep(3)

    print(f"❌ Models not indexed within {max_wait}s")
    return False


def get_output_files(since: Optional[float] = None) -> List[Path]:
    """출력 파일 목록 가져오기(inputs 폴더 제외)"""
    candidates: List[Path] = []
    for ext in ['*.png', '*.jpg', '*.jpeg', '*.mp4', '*.mov', '*.glb', '*.obj']:
        for p in OUTPUT_DIR.glob(f"**/{ext}"):
            # 입력 이미지가 저장되는 inputs 디렉토리는 업로드 대상에서 제외
            if "inputs" in p.parts:
                continue
            candidates.append(p)
    # 최근 5분 이내 파일만
    now = time.time()
    if since is not None:
        recent = [p for p in candidates if p.stat().st_mtime >= since - 5]
    else:
        recent = [p for p in candidates if now - p.stat().st_mtime < 1200]
    return sorted(recent, key=lambda x: x.stat().st_mtime, reverse=True)

def _should_upload(path: Path, task_type: str) -> bool:
    """
    업로드 허용 규칙:
      - video: mp4/mov만 (png/jpg 전부 제외 → 첫 프레임 PNG 자동 제외)
      - 3d   : glb/obj만
      - 공통 : inputs 디렉토리는 이미 상단에서 제외
    """
    ext = path.suffix.lower()
    if task_type == "video":
        return ext in (".mp4", ".mov")
    if task_type == "3d":
        return ext in (".glb", ".obj")
    return True

def get_outputs_from_history(prompt_id: str) -> List[Path]:
    """
    ComfyUI /history/{prompt_id}에서 노드별 산출물 목록을 직접 추출해서
    로컬 절대 경로 리스트로 돌려준다.
    """
    outs: List[Path] = []
    try:
        r = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=10)
        r.raise_for_status()
        h = r.json()
        entry = h.get(prompt_id, {})
        outputs = entry.get("outputs", {})  # node_id -> {images: [...], ...}

        for _nid, node_out in outputs.items():
            # Comfy가 주는 표준 키들을 전부 훑는다.
            for key in ("images", "gifs", "videos", "files", "meshes"):
                for item in node_out.get(key, []) or []:
                    # item 예시: {"filename":"AnimateDiff_00001.mp4","subfolder":"", "type":"output", ...}
                    fname = item.get("filename")
                    subfolder = (item.get("subfolder") or "").strip("/")
                    if not fname:
                        continue
                    p = (OUTPUT_DIR / subfolder / fname) if subfolder else (OUTPUT_DIR / fname)
                    outs.append(p)
    except Exception as e:
        print(f"⚠️ history parse failed: {e}")

    # 중복 제거 + 존재하는 파일만 필터
    dedup = []
    seen = set()
    for p in outs:
        try:
            if p.exists() and p.is_file():
                s = str(p)
                if s not in seen:
                    seen.add(s)
                    dedup.append(p)
        except Exception:
            pass
    return dedup


def upload_to_s3(file_path: Path) -> Optional[str]:
    """S3에 파일 업로드하고 URL 반환"""
    if not s3_client:
        print("S3 client not configured")
        return None
    
    try:
        # 파일 확장자에 따른 폴더 분류 (babsim-media 고정 경로)
        ext = file_path.suffix.lower()
        if ext in ['.png']:
            s3_folder = "images"
        elif ext in ['.mp4']:
            s3_folder = "videos"
        elif ext in ['.glb']:
            s3_folder = "models"
        else:
            s3_folder = "misc"  # 기본값을 images로 설정
        
        filename = file_path.name
        # S3 키 생성
        s3_key = f"{s3_folder}/{file_path.name}"

        # ▶ 영상만: 같은 키가 이미 있으면 다음 가용 번호로 변경
        if s3_folder in ("videos", "models") and _s3_key_exists(AWS_BUCKET, s3_key):
            new_name = _next_available_name(s3_folder, filename)
            filename = new_name
            s3_key = f"{s3_folder}/{filename}"

        
        # 업로드
        s3_client.upload_file(str(file_path), AWS_BUCKET, s3_key)
        
        # URL 생성
        url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        print(f"✓ Uploaded: {url}")
        return url
        
    except Exception as e:
        print(f"S3 upload error: {e}")
        return None

def modify_workflow(workflow_json: Dict, user_image_path: str, user_prompt: Optional[str] = None) -> Dict:
    """워크플로우의 input image와 prompt를 사용자 입력으로 교체"""
    
    # 1. LoadImage 노드 찾아서 이미지 교체
    for node_id, node in workflow_json.items():
        if node.get("class_type") == "LoadImage":
            node["inputs"]["image"] = user_image_path
            print(f"🖼️ Updated LoadImage node {node_id}: {user_image_path}")
    
    # 2. CLIPTextEncode 노드 찾아서 프롬프트 교체 (positive만)
    # 2. 텍스트 인코더 노드 찾아서 프롬프트 교체 (positive만, T5/CLIP 모두 지원)
    if user_prompt:
        for node_id, node in workflow_json.items():
            ct = (node.get("class_type") or "").lower()
            title = (node.get("_meta", {}).get("title") or "").lower()
            if "textencode" in ct and "positive" in title:
                if "text" in node.get("inputs", {}):
                    node["inputs"]["text"] = user_prompt
                    print(f"📝 Updated {node.get('class_type')} node {node_id}: {user_prompt[:50]}...")
    
    return workflow_json

import secrets  # 파일 상단에 추가

def _randomize_video_seeds_if_zero(wf: dict) -> dict:
    """
    비디오 워크플로우에서만 seed/noise_seed가 0이면 실행시에 랜덤값으로 바꾼다.
    (워크플로우 파일은 계속 0으로 유지)
    """
    for node in wf.values():
        ct = (node.get("class_type") or "").lower()
        if ct in ("samplercustom", "ksampler", "ksampleradvanced"):
            inputs = node.get("inputs", {})
            for key in ("noise_seed", "seed"):
                if key in inputs:
                    try:
                        if int(inputs[key]) == 0:
                            # 1 ~ (2^31-1) 범위 랜덤
                            inputs[key] = secrets.randbelow(2**31 - 1) or 1
                    except (TypeError, ValueError):
                        # 숫자 변환 안 되면 건너뜀
                        pass
    return wf


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
        
        if task_type == "video":
            workflow = _randomize_video_seeds_if_zero(workflow)


        # # 모델 인덱싱 확인 후 워크플로우 제출
        # if not ensure_models_ready(max_wait=300):
        #     raise RuntimeError("Models not indexed yet; retry later")
        
        # 워크플로우 실행
        started_at = time.time()
        print(f"▶️ Submitting workflow...")
        prompt_id = submit_workflow(workflow)
        print(f"⏳ Workflow submitted: {prompt_id}")
        
        if not wait_for_completion(prompt_id):
            raise RuntimeError("Workflow execution failed or timed out")
        
        print(f"✅ Workflow completed!")
        
        # 결과 파일(1) — 히스토리에서 직접 읽기
        files_from_history = get_outputs_from_history(prompt_id)
        if files_from_history:
            print(f"📁 {len(files_from_history)} files from history")
            output_files = files_from_history
        else:
            # 결과 파일(2) — 폴더 스캔 (백업 경로)
            output_files = get_output_files(since=started_at)

        if not output_files:
            # 디버깅을 위해 최근 생성 파일 일부를 덤프
            try:
                print("🔎 DEBUG: recent files in output dir")
                for p in sorted(OUTPUT_DIR.rglob("*"), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
                    try:
                        print(" -", p, int(time.time() - p.stat().st_mtime), "s ago")
                    except Exception:
                        pass
            except Exception as _:
                pass
            raise RuntimeError("No output files generated")

        print(f"📁 Found {len(output_files)} output files (pre-filter)")

        filtered_files = [p for p in output_files if _should_upload(p, task_type)]
        print(f"📁 {len(filtered_files)} files after upload filter for task={task_type}")
        if not filtered_files:
            raise RuntimeError("No uploadable artifacts found (after filtering)")

        # S3 업로드
        uploaded_urls: List[str] = []
        for file_path in output_files[:3]:
            print(f"📤 Uploading {file_path.name}...")
            url = upload_to_s3(file_path)
            if url:
                uploaded_urls.append(url)

        result = {
                "success": True,
                "task_type": task_type,
                "outputs": uploaded_urls,
                "file_count": len(filtered_files),
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
#     """RunPod 작업 핸들러"""
#     try:
#         job_input = JobInput(**job["input"])
#         return process_task(job_input)
#     except Exception as e:
#         return {"success": False, "error": str(e)}

# if __name__ == "__main__":
#     print("🚀 Starting RunPod handler...")
#     print(f"ComfyUI URL: {COMFY_URL}")
#     print(f"Output dir: {OUTPUT_DIR}")
#     print(f"S3 bucket: {AWS_BUCKET}")

    """RunPod 작업 핸들러 (상위 3키)"""
    import time, json, traceback
    t0 = time.time()
    print("🛰️ [handler] start")

    try:
        payload = job.get("input", {})
        print(f"📥 [handler] raw input keys = {list(payload.keys()) if isinstance(payload, dict) else type(payload)}")

        if not isinstance(payload, dict):
            msg = "invalid input payload"
            print(f"❌ [handler] {msg}")
            return {"success": False, "error": msg}

        # 필수 키 확인
        task_type = payload.get("task_type")
        workflow  = payload.get("workflow")
        print(f"🧭 [handler] task_type={task_type}, workflow={workflow}")
        if not task_type or not workflow:
            msg = "missing required fields: task_type, workflow"
            print(f"❌ [handler] {msg}")
            return {"success": False, "error": msg}

        # 상위 레벨 sugar 키
        top_image  = payload.get("image_path")
        top_prompt = payload.get("prompt", None)  # None이면 워크플로우 기본 프롬프트 사용

        # task_type 정규화 + 상위 키를 각 섹션으로 이관
        if task_type == "video":
            payload.setdefault("video", {})
            if top_image:
                payload["video"]["image_path"] = top_image
            if "prompt" in payload or top_prompt is not None:
                payload["video"]["prompt"] = top_prompt

        elif task_type in ("3d", "three_d"):
            payload["task_type"] = "3d"  # 표준화
            payload.setdefault("three_d", {})
            if top_image:
                payload["three_d"]["image_path"] = top_image
            if "prompt" in payload or top_prompt is not None:
                payload["three_d"]["prompt"] = top_prompt

        else:
            msg = f"unsupported task_type: {task_type}"
            print(f"❌ [handler] {msg}")
            return {"success": False, "error": msg}

        # 상위 sugar 키는 제거 (검증 모델과 충돌 방지)
        payload.pop("image_path", None)
        payload.pop("prompt", None)

        print(f"🧩 [handler] normalized payload = {json.dumps(payload, ensure_ascii=False)[:400]}...")

        # pydantic 검증
        job_input = JobInput(**payload)
        print("✅ [handler] pydantic validation OK")

        # 실행
        print("🚀 [handler] dispatch -> process_task")
        result = process_task(job_input)
        ok = result.get("success", False)
        dt = time.time() - t0
        if ok:
            print(f"🎉 [handler] done in {dt:.2f}s, outputs={len(result.get('outputs', []) or [])}")
        else:
            print(f"💥 [handler] failed in {dt:.2f}s, err={result.get('error')}")
        return result

    except Exception as e:
        dt = time.time() - t0
        print(f"💥 [handler] exception in {dt:.2f}s: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

runpod.serverless.start({"handler": handler})