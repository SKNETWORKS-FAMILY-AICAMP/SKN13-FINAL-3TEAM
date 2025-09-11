#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime
import os, sys, json, time, uuid, mimetypes, argparse, pathlib, shutil

# ──────────────────────────────────────────────────────────────────────────────
# LLM / 메시지 타입 (앞단 패턴 유지)
# ──────────────────────────────────────────────────────────────────────────────
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

# ──────────────────────────────────────────────────────────────────────────────
# 이미지 생성 유틸 (앞단 패턴 유지)
# ──────────────────────────────────────────────────────────────────────────────
from PIL import Image
from diffusers.utils import load_image
# 실제 이미지 모델(Flux 등)을 직접 붙일 경우에만 사용
# from diffusers import FluxKontextPipeline
# import torch

# ──────────────────────────────────────────────────────────────────────────────
# 외부/옵션 라이브러리
# ──────────────────────────────────────────────────────────────────────────────
import requests
try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv(*_, **__): return False

try:
    import boto3
except Exception:
    boto3 = None  # S3 비활성화 허용

# ──────────────────────────────────────────────────────────────────────────────
# 공통 설정 (ENV)
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv()

COMFY_URL = os.getenv("COMFY_URL", "http://127.0.0.1:8188").rstrip("/")
WORKDIR    = pathlib.Path(os.getenv("WORKDIR", "/workspace"))
OUTPUT_DIR = pathlib.Path(os.getenv("OUTPUT_DIR", str(WORKDIR / "outputs")))
# ASSETS_DIR 제거 (더 이상 사용 안 함)
WF_DIR     = WORKDIR / "ComfyUI" / "user" / "default" / "workflows"

# S3: 네가 쓰는 이름과 정확히 일치
S3_ENABLE  = os.getenv("S3_ENABLE", "false").lower() in ("1", "true", "yes")
S3_BUCKET  = os.getenv("AWS_STORAGE_BUCKET_NAME")
AWS_KEY    = os.getenv("ACCESS_KEY_ID")
AWS_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_S3_REGION_NAME")
# S3 경로 고정 (babsim-media 사용)
S3_PREFIX_IMG = "babsim-media/images"
S3_PREFIX_VID = "babsim-media/videos"
S3_PREFIX_3D  = "babsim-media/models"

# 로컬 분류 디렉토리
LOCAL_IMG_DIR = OUTPUT_DIR / "images"
LOCAL_VID_DIR = OUTPUT_DIR / "videos"
LOCAL_3D_DIR  = OUTPUT_DIR / "models"

for d in (OUTPUT_DIR, ASSETS_DIR, LOCAL_IMG_DIR, LOCAL_VID_DIR, LOCAL_3D_DIR):
    d.mkdir(parents=True, exist_ok=True)

PipelineState = Dict[str, Any]

# ──────────────────────────────────────────────────────────────────────────────
# 유틸
# ──────────────────────────────────────────────────────────────────────────────
def _now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def _job_id(n: int = 8) -> str:
    return uuid.uuid4().hex[:n]

def _content_type(path: str) -> str:
    p = path.lower()
    if p.endswith(".glb"): return "model/gltf-binary"
    if p.endswith(".png"): return "image/png"
    # JPG/JPEG 지원 제거 (PNG만 사용)
    if p.endswith(".mp4"): return "video/mp4"
    c, _ = mimetypes.guess_type(path)
    return c or "application/octet-stream"

def _category_for_ext(path: str) -> str:
    ext = pathlib.Path(path).suffix.lower()
    if ext in (".png",): return "image"
    if ext in (".mp4",): return "video"
    if ext in (".glb",): return "model"
    return "other"

def _move_to_local_category(path: str) -> str:
    """ComfyUI가 outputs 루트에 저장해둔 파일을
       outputs/images|videos|models 로 '이동'하여 정리."""
    cat = _category_for_ext(path)
    src = pathlib.Path(path)
    if not src.exists():
        return path
    if cat == "image":
        dest_dir = LOCAL_IMG_DIR
    elif cat == "video":
        dest_dir = LOCAL_VID_DIR
    elif cat == "model":
        dest_dir = LOCAL_3D_DIR
    else:
        # 기타는 그냥 outputs 그대로 둠
        return path
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if str(dest.resolve()) == str(src.resolve()):
        return str(dest)
    # 동일 파일명이 있으면 접미사 추가
    if dest.exists():
        stem, ext = dest.stem, dest.suffix
        dest = dest_dir / f"{stem}_{_now_ts()}{ext}"
    shutil.move(str(src), str(dest))
    return str(dest)

def _ensure_s3():
    if not S3_ENABLE:
        return None
    if not boto3:
        raise RuntimeError("boto3 미설치: pip install boto3 python-dotenv")
    if not all([S3_BUCKET, AWS_KEY, AWS_SECRET, AWS_REGION]):
        raise RuntimeError("S3 환경변수 부족: AWS_STORAGE_BUCKET_NAME / ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_S3_REGION_NAME")
    session = boto3.session.Session(
        aws_access_key_id=AWS_KEY,
        aws_secret_access_key=AWS_SECRET,
        region_name=AWS_REGION
    )
    return session.client("s3")

def _s3_dir_markers(s3c):
    for pref in (S3_PREFIX_IMG, S3_PREFIX_VID, S3_PREFIX_3D):
        s3c.put_object(Bucket=S3_BUCKET, Key=pref.rstrip("/") + "/")

def _s3_key_for(local_path: str, output_prefix: Optional[str]) -> str:
    fn = pathlib.Path(local_path).name
    ext = fn.lower().split(".")[-1]
    base = {
        "png": S3_PREFIX_IMG,
        "mp4": S3_PREFIX_VID,
        "glb": S3_PREFIX_3D,
    }.get(ext, S3_PREFIX_IMG)  # 기본값: images, 확장자는 png만 지원
    if output_prefix:
        return f"{base}/{output_prefix.strip('/')}/{fn}"
    return f"{base}/{fn}"

def _s3_upload(s3c, local_path: str, key: str) -> Dict[str, str]:
    ct = _content_type(local_path)
    s3c.upload_file(local_path, S3_BUCKET, key, ExtraArgs={"ContentType": ct})
    url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
    return {"bucket": S3_BUCKET, "key": key, "url": url, "content_type": ct}

# ──────────────────────────────────────────────────────────────────────────────
# ComfyUI REST 헬퍼
# ──────────────────────────────────────────────────────────────────────────────
def _comfy_get(path: str, **kw):
    return requests.get(f"{COMFY_URL}{path}", timeout=kw.pop("timeout", 60), **kw)

def _comfy_post(path: str, **kw):
    return requests.post(f"{COMFY_URL}{path}", timeout=kw.pop("timeout", 60), **kw)

def _load_workflow(name: str) -> dict:
    wf = WF_DIR / f"{name}.json"
    if not wf.exists():
        raise FileNotFoundError(f"workflow json not found: {wf}")
    return json.loads(wf.read_text(encoding="utf-8"))

def _inject_simple_inputs(graph: dict, params: dict) -> dict:
    g = json.loads(json.dumps(graph))  # deep copy
    img_path = params.get("image_path")
    pos = params.get("prompt")
    neg = params.get("negative_prompt")

    nodes = g.get("nodes")
    if isinstance(nodes, dict):
        nodes = list(nodes.values())
    if not isinstance(nodes, list):
        nodes = []

    for n in nodes:
        cls = str(n.get("class_type", ""))
        ins = n.setdefault("inputs", {})

        if "loadimage" in cls.lower() and "image" in ins and img_path:
            ins["image"] = img_path

        if "text" in ins:
            if any(k in cls for k in ("Text", "Prompt", "CLIPText")) and "negative" not in cls.lower() and pos is not None:
                ins["text"] = pos
            if "negative" in cls.lower() and neg is not None:
                ins["text"] = neg

        for k in ("steps", "seed", "tex_res", "width", "height", "num_frames", "fps"):
            if k in ins and k in params:
                ins[k] = params[k]

        if "filename_prefix" in ins and params.get("_job_id"):
            ins["filename_prefix"] = f"{ins['filename_prefix']}_{params['_job_id']}"

    return g

def _queue_prompt(graph: dict, client_id: str) -> str:
    r = _comfy_post("/prompt", json={"prompt": graph, "client_id": client_id})
    r.raise_for_status()
    return r.json()["prompt_id"]

def _wait_done(prompt_id: str, timeout_sec: int = 1800) -> dict:
    t0 = time.time()
    while True:
        h = _comfy_get(f"/history/{prompt_id}")
        if h.status_code == 200:
            data = h.json()
            item = data.get(prompt_id) or data
            st = (item or {}).get("status", {})
            if st.get("completed"): return item
            if st.get("error"): raise RuntimeError(st["error"])
        if time.time() - t0 > timeout_sec:
            raise TimeoutError("timeout waiting for prompt")
        time.sleep(2)

def _collect_outputs(history: dict) -> List[str]:
    out = []
    outputs = history.get("outputs") or {}
    for _, v in outputs.items():
        for img in v.get("images", []):
            fn  = img.get("filename")
            sub = img.get("subfolder") or ""
            if not fn: 
                continue
            folder = OUTPUT_DIR if not sub else OUTPUT_DIR / sub
            out.append(str(folder / fn))
    return out

def _categorize_and_upload(files: List[str], output_prefix: Optional[str]) -> Dict[str, List[Dict[str, Any]]]:
    """로컬: outputs/images|videos|models 로 이동 + S3 업로드(옵션)"""
    s3c = _ensure_s3() if S3_ENABLE else None
    if s3c: _s3_dir_markers(s3c)

    results = {"images": [], "videos": [], "models": [], "others": []}

    for fp in files:
        if not os.path.exists(fp): 
            continue
        # 1) 로컬 분류 이동
        new_fp = _move_to_local_category(fp)
        cat = _category_for_ext(new_fp)

        # 2) S3 업로드(있다면)
        s3_info = None
        if s3c:
            key = _s3_key_for(new_fp, output_prefix)
            s3_info = _s3_upload(s3c, new_fp, key)

        item = {"local": new_fp, "s3": s3_info}
        if cat == "image":   results["images"].append(item)
        elif cat == "video": results["videos"].append(item)
        elif cat == "model": results["models"].append(item)
        else:                results["others"].append(item)
    return results

# ──────────────────────────────────────────────────────────────────────────────
# (앞단 그대로) 이미지 저장
# ──────────────────────────────────────────────────────────────────────────────
def save_image(image: Image.Image, filepath: str):
    """생성된 이미지를 저장합니다"""
    try:
        image.save(filepath)
    except Exception as e:
        print(f"이미지 저장 중 오류 발생: {e}")
        raise

# ──────────────────────────────────────────────────────────────────────────────
# (앞단 유지) + (추가: 3D/비디오)
# ──────────────────────────────────────────────────────────────────────────────
class EnhancedImagePipeline:
    def __init__(self, save_image_fn=save_image):
        self.save_image = save_image_fn
        self.llm = ChatOpenAI(model="gpt-4o-mini")

        # 실제 Flux 등을 붙일 경우(옵션)
        # self.pipe = FluxKontextPipeline.from_pretrained("...")
        # self.pipe.to("cuda" if torch.cuda.is_available() else "cpu")

    # 1) 초기 dictionary 쿼리 → 영어 프롬프트 생성
    def process_initial_query(self, state: Dict[str, Any]) -> Dict[str, Any]:
        dict_query = state["messages"][-1].content  # dictionary
        prompt = f"""
Convert the following structured car design dictionary into a concise English prompt 
for an image generation model (Flux). Use short descriptive words (< 78 CLIP TOKENS).

Dictionary:
{json.dumps(dict_query, ensure_ascii=False)}
"""
        response = self.llm.invoke([HumanMessage(content=prompt)])
        state["generated_query"] = response.content.strip()
        state["original_dict"]  = dict_query
        state["pipeline_step"]  = "query_received"
        print("쿼리 수신 및 변환 완료:", state["generated_query"])
        return state

    # 2) 이미지 생성 (처음이면 새로 생성, 있으면 편집)
    def generate_image(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state["generated_query"]

        # 이전 생성물 확인
        input_image = state.get("generated_image", None)
        if isinstance(input_image, str) and os.path.exists(input_image):
            input_image = load_image(input_image)

        # 실제 이미지 생성부(환경에 맞춰 주석 해제)
        # if input_image is None:
        #     result = self.pipe(prompt=query, guidance_scale=30)
        # else:
        #     result = self.pipe(image=input_image, prompt=query, guidance_scale=4.5)
        # if not result.images:
        #     raise RuntimeError("이미지가 생성되지 않았습니다.")
        # output_image = result.images[0]

        # 데모용(빈 이미지). 운영에서는 위의 실제 모델을 사용하세요.
        output_image = Image.new("RGB", (1024, 576), color=(32, 32, 32))

        ts = _now_ts()
        out_path = str(LOCAL_IMG_DIR / f"generated_image_{ts}.png")
        self.save_image(output_image, out_path)

        state["generated_image"] = output_image         # PIL 객체
        state["generated_image_path"] = out_path        # 3D 입력에도 사용
        state["output_path"]   = out_path
        state["pipeline_step"] = "image_generated"
        print("✅ 이미지 생성 완료:", out_path)
        return state

    # 3) 이미지 설명 (한국어)
    def explain_image(self, state: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
이 이미지는 다음 쿼리를 사용하여 생성되었습니다:
{state["generated_query"]}

원래 사용자가 입력한 사전(dictionary):
{json.dumps(state["original_dict"], ensure_ascii=False)}

위의 정보를 바탕으로, 이 이미지가 어떤 디자인 요소들
(뷰포인트, 차체 유형, 비율, 표면, 조명, 휠, 색상 등)을
고려하여 생성되었는지 한국어로 설명해 주세요.
"""
        response = self.llm.invoke([
            SystemMessage(content="당신은 자동차 디자인 이미지 결과를 설명하는 도우미입니다. 한국어로만 대답하세요."),
            HumanMessage(content=prompt)
        ])
        explanation = response.content.strip()
        print("\n🤖 AI 설명:\n", explanation)

        user_input = input("\n👉 이 이미지가 마음에 드시나요? 수정이 필요하시다면 편하게 말씀해주세요 !: ")
        state["messages"].append(AIMessage(content=explanation))
        state["messages"].append(HumanMessage(content=user_input))
        state["pipeline_step"] = "explanation_generated"
        return state

    # 4) 사용자 피드백 판별
    def process_feedback(self, state: Dict[str, Any]) -> Dict[str, Any]:
        last_user = [m for m in state["messages"] if isinstance(m, HumanMessage)][-1].content
        judge_prompt = f"""
사용자가 이렇게 말했습니다: "{last_user}"
이 발언이 수정을 원한다는 의미면 "modify",
만족이면 "done" — 반드시 한 단어로만 답하세요.
"""
        resp = self.llm.invoke([HumanMessage(content=judge_prompt)])
        decision = resp.content.strip().lower()
        state["pipeline_step"] = f"feedback_{decision}"
        return state

    # 5) 수정 요청 처리
    def handle_modification(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_input = input("\n👉 어떤 부분을 수정하고 싶으신가요?: ")
        state["messages"].append(HumanMessage(content=user_input))

        last_user = [m for m in state["messages"] if isinstance(m, HumanMessage)][-1].content
        prompt = f"""
Translate the following user request into English 
for use as an image generation prompt (< 78 CLIP tokens).

- Use concise and descriptive words.
- Preserve common automotive exterior design terms.
- Keep it edit-friendly.

User request: {last_user}
"""
        response = self.llm.invoke([HumanMessage(content=prompt)])
        state["generated_query"] = response.content.strip()
        state["modification_count"] = state.get("modification_count", 0) + 1
        state["pipeline_step"] = "query_modified"
        return state

    # ──────────────────────────────────────────────────────────────────
    # RunPod 서버리스 연동 기능
    # ──────────────────────────────────────────────────────────────────
    def _call_runpod_serverless(
        self,
        endpoint_url: str,
        payload: Dict[str, Any],
        timeout: int = 600
    ) -> Dict[str, Any]:
        """RunPod 서버리스 엔드포인트 호출"""
        try:
            response = requests.post(
                f"{endpoint_url}/runsync",
                json={"input": payload},
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"RunPod 서버리스 호출 실패: {e}")

    def _upload_image_for_runpod(self, image_path: str) -> str:
        """이미지를 RunPod에서 접근 가능한 URL로 업로드"""
        # S3에 임시 업로드하여 RunPod에서 접근 가능한 URL 생성
        s3c = _ensure_s3()
        if not s3c:
            # S3가 비활성화된 경우 로컬 경로 반환 (RunPod 내부에서만 사용)
            return image_path
        
        # 임시 S3 키 생성
        filename = pathlib.Path(image_path).name
        temp_key = f"temp-inputs/{_job_id()}/{filename}"
        
        # S3 업로드
        s3_info = _s3_upload(s3c, image_path, temp_key)
        return s3_info["url"]

    # ──────────────────────────────────────────────────────────────────
    # (수정) 3D 생성 — RunPod 서버리스 연동
    # ──────────────────────────────────────────────────────────────────
    def generate_3d(
        self,
        state: Dict[str, Any],
        tex_res: int = 1024,
        steps: int = 30,
        seed: int = 12345,
        export_glb: bool = True,
        output_prefix: Optional[str] = None,
        image_path: Optional[str] = None,
        use_runpod: bool = True,
        runpod_endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        img = image_path or state.get("generated_image_path")
        if not img:
            raise FileNotFoundError("3D 입력 이미지 경로가 없습니다.")

        if use_runpod and runpod_endpoint:
            # RunPod 서버리스 모드
            image_url = self._upload_image_for_runpod(img) if os.path.exists(img) else img
            
            payload = {
                "task_type": "3d",
                "workflow": "hunyuan_3d.json",
                "three_d": {
                    "image_path": image_url,
                    "tex_res": tex_res,
                    "steps": steps,
                    "seed": seed,
                    "file_format": "glb" if export_glb else "obj"
                }
            }
            
            print(f"🚀 RunPod 3D 생성 시작: {payload}")
            result = self._call_runpod_serverless(runpod_endpoint, payload)
            
            state["three_d_outputs"] = {
                "runpod_result": result,
                "s3_urls": result.get("outputs", []),
                "job_id": result.get("job_id")
            }
            state["pipeline_step"] = "3d_generated_runpod"
            print("✅ RunPod 3D 생성 완료:", result)
            
        else:
            # 로컬 ComfyUI 모드 (기존 방식)
            if not os.path.exists(img):
                raise FileNotFoundError(f"이미지 파일이 존재하지 않습니다: {img}")
                
            params = {
                "prompt": state.get("generated_query"),
                "negative_prompt": "",
                "image_path": img,
                "tex_res": tex_res,
                "steps": steps,
                "seed": seed,
                "export_glb": export_glb,
                "_job_id": _job_id()
            }
            graph = _load_workflow("hunyuan_3d")
            graph = _inject_simple_inputs(graph, params)
            pid = _queue_prompt(graph, client_id=f"local-{params['_job_id']}")
            hist = _wait_done(pid)
            files = _collect_outputs(hist)

            result = _categorize_and_upload(files, output_prefix)
            state["three_d_outputs"] = result
            state["pipeline_step"] = "3d_generated"
            print("✅ 로컬 3D 생성 완료:", result)
            
        return state

    # ──────────────────────────────────────────────────────────────────
    # (수정) Video 생성 — RunPod 서버리스 연동
    # ──────────────────────────────────────────────────────────────────
    def generate_video(
        self,
        state: Dict[str, Any],
        num_frames: int = 49,
        fps: int = 8,
        width: int = 576,
        height: int = 320,
        seed: int = 42,
        output_prefix: Optional[str] = None,
        image_path: Optional[str] = None,
        use_runpod: bool = True,
        runpod_endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        
        if use_runpod and runpod_endpoint:
            # RunPod 서버리스 모드
            img = image_path or state.get("generated_image_path")
            image_url = None
            
            if img:
                image_url = self._upload_image_for_runpod(img) if os.path.exists(img) else img
            
            payload = {
                "task_type": "video",
                "workflow": "LTX_video.json",
                "video": {
                    "prompt": state.get("generated_query", ""),
                    "image_path": image_url,
                    "width": width,
                    "height": height,
                    "frames": num_frames,
                    "frame_rate": fps,
                    "steps": 30,
                    "strength": 0.4,
                    "seed": seed,
                    "crf": 24
                }
            }
            
            print(f"🚀 RunPod 비디오 생성 시작: {payload}")
            result = self._call_runpod_serverless(runpod_endpoint, payload)
            
            state["video_outputs"] = {
                "runpod_result": result,
                "s3_urls": result.get("outputs", []),
                "job_id": result.get("job_id")
            }
            state["pipeline_step"] = "video_generated_runpod"
            print("✅ RunPod 비디오 생성 완료:", result)
            
        else:
            # 로컬 ComfyUI 모드 (기존 방식)
            params = {
                "prompt": state.get("generated_query"),
                "negative_prompt": "",
                "num_frames": num_frames,
                "fps": fps,
                "width": width,
                "height": height,
                "seed": seed,
                "_job_id": _job_id()
            }
            graph = _load_workflow("LTX_video")
            graph = _inject_simple_inputs(graph, params)
            pid = _queue_prompt(graph, client_id=f"local-{params['_job_id']}")
            hist = _wait_done(pid)
            files = _collect_outputs(hist)

            result = _categorize_and_upload(files, output_prefix)
            state["video_outputs"] = result
            state["pipeline_step"] = "video_generated"
            print("✅ 로컬 비디오 생성 완료:", result)
            
        return state

    # ──────────────────────────────────────────────────────────────────
    # Django 프로젝트 통합을 위한 래퍼 메서드들
    # ──────────────────────────────────────────────────────────────────
    def process_flux_result_for_3d_video(
        self,
        flux_image_path: str,
        user_prompt: str,
        task_type: str,  # "3d" or "video"
        runpod_endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """FLUX에서 생성된 이미지를 받아 3D/비디오 생성하는 메인 메서드"""
        
        # 상태 초기화 (기존 패턴 유지)
        state = {
            "messages": [HumanMessage(content={"prompt": user_prompt})],
            "generated_query": user_prompt,
            "generated_image_path": flux_image_path,
            "pipeline_step": "flux_result_received"
        }
        
        print(f"🎯 FLUX 결과물 처리 시작: {task_type} 생성")
        print(f"📁 입력 이미지: {flux_image_path}")
        print(f"💬 프롬프트: {user_prompt}")
        
        try:
            if task_type.lower() == "3d":
                result = self.generate_3d(
                    state,
                    image_path=flux_image_path,
                    use_runpod=True,
                    runpod_endpoint=runpod_endpoint,
                    **kwargs
                )
                return {
                    "success": True,
                    "task_type": "3d",
                    "result": result.get("three_d_outputs"),
                    "state": result
                }
                
            elif task_type.lower() == "video":
                result = self.generate_video(
                    state,
                    image_path=flux_image_path,
                    use_runpod=True,
                    runpod_endpoint=runpod_endpoint,
                    **kwargs
                )
                return {
                    "success": True,
                    "task_type": "video",
                    "result": result.get("video_outputs"),
                    "state": result
                }
            else:
                raise ValueError(f"지원하지 않는 작업 타입: {task_type}")
                
        except Exception as e:
            print(f"❌ {task_type} 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_type": task_type
            }

# ──────────────────────────────────────────────────────────────────────────────
# (옵션) .glb 디렉토리 일괄 업로드 — models/ 프리픽스 사용
# ──────────────────────────────────────────────────────────────────────────────
def upload_glb_files(dir_path: Optional[str] = None):
    bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME')
    aws_access_key_id = os.getenv('ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    region_name = os.getenv('AWS_S3_REGION_NAME')

    if not all([bucket_name, aws_access_key_id, aws_secret_access_key, region_name]):
        print("오류: .env 파일에 AWS 설정이 모두 필요합니다.")
        return
    if not boto3:
        print("오류: boto3가 필요합니다. pip install boto3")
        return

    local_directory = dir_path or 'react/build/models'
    if not os.path.isdir(local_directory):
        print(f"오류: 로컬 디렉토리를 찾을 수 없습니다 - {local_directory}")
        return

    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )

    print(f"'{local_directory}'의 .glb 파일 업로드를 시작합니다...")
    for filename in os.listdir(local_directory):
        if filename.endswith('.glb'):
            local_path = os.path.join(local_directory, filename)
            s3_key = f"{S3_PREFIX_3D.rstrip('/')}/{filename}"
            print(f" - '{local_path}' -> s3://{bucket_name}/{s3_key}")
            try:
                s3_client.upload_file(
                    local_path, 
                    bucket_name, 
                    s3_key,
                    ExtraArgs={'ContentType': 'model/gltf-binary'}
                )
                file_url = f"https://{bucket_name}.s3.{region_name}.amazonaws.com/{s3_key}"
                print(f"   성공. URL: {file_url}")
            except Exception as e:
                print(f"   실패: {e}")

    print("업로드 작업이 완료되었습니다.")

# ──────────────────────────────────────────────────────────────────────────────
# CLI (개인 Runpod/로컬 검증용) — 운영에선 import만 하세요.
# ──────────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Image pipeline (front) + 3D/Video(ComfyUI) + S3")
    sub = ap.add_subparsers(dest="cmd", required=True)

    # run: 3D / video 생성
    rp = sub.add_parser("run", help="3D/Video 생성 실행")
    rp.add_argument("--task", required=True, choices=["3d", "video", "hunyuan_3d", "ltx_video"])
    rp.add_argument("--prompt", type=str, default="a premium black full-size luxury sedan")
    rp.add_argument("--negative-prompt", dest="negative_prompt", type=str, default="")
    rp.add_argument("--image", dest="image_path", type=str, default=None)  # 3D에서 사용
    rp.add_argument("--steps", type=int, default=30)
    rp.add_argument("--seed", type=int, default=12345)
    rp.add_argument("--tex-res", dest="tex_res", type=int, default=1024)
    rp.add_argument("--width", type=int, default=576)
    rp.add_argument("--height", type=int, default=320)
    rp.add_argument("--num-frames", dest="num_frames", type=int, default=49)
    rp.add_argument("--fps", type=int, default=8)
    rp.add_argument("--output-prefix", dest="output_prefix", type=str, default=None)

    # upload-glb-dir: 산출물 일괄 업로드
    up = sub.add_parser("upload-glb-dir", help=".glb 디렉토리 일괄 업로드 (models/ prefix)")
    up.add_argument("--dir", type=str, default=None, help="기본값: react/build/models")

    args = ap.parse_args()

    if args.cmd == "run":
        # 앞단 패턴 유지: 사용자의 dict를 HumanMessage(content=dict)로 받아 프롬프트 생성
        state: Dict[str, Any] = {"messages": [HumanMessage(content={"prompt": args.prompt})]}
        pipe = EnhancedImagePipeline()
        state = pipe.process_initial_query(state)
        state = pipe.generate_image(state)

        # 분기
        task = "hunyuan_3d" if args.task == "3d" else ("ltx_video" if args.task == "video" else args.task)
        if task in ("3d", "hunyuan_3d"):
            state = pipe.generate_3d(
                state,
                tex_res=args.tex_res,
                steps=args.steps,
                seed=args.seed,
                export_glb=True,
                output_prefix=args.output_prefix,
                image_path=args.image_path
            )
        elif task in ("video", "ltx_video"):
            state = pipe.generate_video(
                state,
                num_frames=args.num_frames,
                fps=args.fps,
                width=args.width,
                height=args.height,
                seed=args.seed,
                output_prefix=args.output_prefix
            )

        print(json.dumps({
            "image": state.get("generated_image_path"),
            "three_d_outputs": state.get("three_d_outputs"),
            "video_outputs": state.get("video_outputs"),
        }, indent=2, ensure_ascii=False))

    elif args.cmd == "upload-glb-dir":
        upload_glb_files(args.dir)

if __name__ == "__main__":
    main()