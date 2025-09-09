import os, io, json, time, base64, uuid, shutil, requests
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from PIL import Image
import runpod

# ========== 환경설정 ==========
COMFY_URL   = os.getenv("COMFY_URL", "http://127.0.0.1:8188")
WORKDIR     = os.getenv("WORKDIR", "/workspace")
WORKFLOW_DIR= os.path.join(WORKDIR, "workflows")
OUTPUT_DIR  = os.getenv("OUTPUT_DIR", "/workspace/outputs")

# S3 설정
S3_ENABLE = os.getenv("S3_ENABLE", "true").lower() == "true"
S3_BUCKET = os.getenv("AWS_STORAGE_BUCKET_NAME", "")
S3_REGION = os.getenv("AWS_S3_REGION_NAME", "")

if S3_ENABLE:
    import boto3
    S3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=S3_REGION
    )

# ========== 유틸 함수 ==========
def _now_ms(): return int(time.time()*1000)
def _ensure_dir(p: str): os.makedirs(p, exist_ok=True); return p

def _image_from_uri(uri: str) -> Image.Image:
    if uri.startswith("http"):
        return Image.open(requests.get(uri, stream=True, timeout=1200).raw).convert("RGB")
    if "," in uri and ";base64" in uri.split(",", 1)[0]:
        raw = base64.b64decode(uri.split(",",1)[1]); return Image.open(io.BytesIO(raw)).convert("RGB")
    raw = base64.b64decode(uri); return Image.open(io.BytesIO(raw)).convert("RGB")

def _img_to_datauri(img: Image.Image, fmt="PNG", max_side=768) -> str:
    w,h=img.size; s=max_side/max(w,h)
    if s<1: img=img.resize((int(w*s), int(h*s)))
    buf=io.BytesIO(); img.save(buf, fmt)
    return f"data:image/{fmt.lower()};base64,{base64.b64encode(buf.getvalue()).decode()}"

def _guess_ct(path: str) -> str:
    ext=os.path.splitext(path)[1].lower()
    return {
        ".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",
        ".glb":"model/gltf-binary",".gltf":"model/gltf+json",
        ".mp4":"video/mp4"
    }.get(ext,"application/octet-stream")

# S3 디렉토리 분기
def _s3_dir_for(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".png",".jpg",".jpeg",".bmp",".webp"): return "images"
    if ext in (".glb",".gltf"): return "models"
    if ext in (".mp4",".webm",".mov"): return "videos"
    return "artifacts"

def _s3_upload(local: str, key: Optional[str]=None) -> Dict[str,Any]:
    if not key:
        s3_dir = _s3_dir_for(local)
        key = f"{s3_dir}/{os.path.basename(local)}"
    S3.upload_file(local, S3_BUCKET, key, ExtraArgs={"ContentType": _guess_ct(local)})
    return {"bucket": S3_BUCKET, "key": key, "content_type": _guess_ct(local), "size": os.path.getsize(local)}

def _comfy_prompt(workflow: Dict[str,Any], images: Optional[List[Dict[str,str]]]=None, timeout=3600) -> Dict[str,Any]:
    payload = {"prompt": workflow}
    if images: payload["extra_data"] = {"images": images}
    r = requests.post(f"{COMFY_URL}/prompt", json=payload, timeout=timeout); r.raise_for_status()
    pid = r.json()["prompt_id"]
    while True:
        h = requests.get(f"{COMFY_URL}/history/{pid}", timeout=timeout).json()
        if pid in h and "outputs" in h[pid]:
            return h[pid]["outputs"]
        time.sleep(1)

# ========== 워크플로 파라미터 패치 ==========
def _patch_load_image_name(wf: Dict[str,Any], name="input.jpg"):
    for _, n in wf.items():
        if isinstance(n, dict) and n.get("class_type") in ("LoadImage","LoadImageMask","LoadImageFromURL"):
            n.setdefault("inputs",{})["image"]=name

def _patch_hy3d(wf: Dict[str,Any], views=12, steps=28, tex_res=448, mv=512):
    for _, n in wf.items():
        if not isinstance(n,dict): continue
        if "Hy3D" not in n.get("class_type",""): continue
        ins=n.setdefault("inputs",{})
        for k,v in (("views",views),("num_views",views),("steps",steps),
                    ("texture_resolution",tex_res),("texture_res",tex_res),
                    ("width",mv),("height",mv),("render_width",mv),("render_height",mv)):
            if k in ins: ins[k]=v

def _patch_ltxv(wf: Dict[str,Any], frames=48, steps=28, width=640, height=640):
    for _, n in wf.items():
        if not isinstance(n,dict): continue
        ins=n.setdefault("inputs",{})
        for k,v in (("length",frames),("frames",frames),("steps",steps),("width",width),("height",height)):
            if k in ins: ins[k]=v

# ========== RunPod 핸들러 ==========
def rp_handler(job: Dict[str,Any]) -> Dict[str,Any]:
    """
    input:
    {
      "mode": "3d" | "video",
      "preset": "FAST|BAL|HIGH",
      "image": "<url|data-uri-base64>",
      "input_name": "input.jpg",
      "workflows": {"hy3d":"hy3d_api.json","ltxv":"ltxv_api.json"},
      "params": {...}  # views/steps 등 오버라이드
    }
    """
    t0=_now_ms()
    inp=job.get("input",{})
    mode=(inp.get("mode") or "3d").lower()
    preset=(inp.get("preset") or "BAL").upper()
    input_name = inp.get("input_name","input.jpg")
    wf_files = inp.get("workflows",{})

    # 프리셋
    if preset=="FAST":
        hy3d_cfg={"views":10,"steps":24,"tex_res":448,"mv":512}
        ltxv_cfg={"frames":32,"steps":24,"width":512,"height":512}
    elif preset=="HIGH":
        hy3d_cfg={"views":16,"steps":30,"tex_res":512,"mv":512}
        ltxv_cfg={"frames":64,"steps":30,"width":768,"height":768}
    else:
        hy3d_cfg={"views":12,"steps":28,"tex_res":448,"mv":512}
        ltxv_cfg={"frames":48,"steps":28,"width":640,"height":640}

    params=inp.get("params",{})
    for k,v in list(params.items()):
        if k in hy3d_cfg: hy3d_cfg[k]=v
        if k in ltxv_cfg: ltxv_cfg[k]=v

    # 입력 이미지 준비
    img=_image_from_uri(inp["image"])
    data_uri=_img_to_datauri(img, fmt="PNG", max_side=768)

    # 워크플로 로드
    wf_path = os.path.join(WORKFLOW_DIR, (wf_files.get("ltxv") if mode=="video" else wf_files.get("hy3d")) or ("ltxv_api.json" if mode=="video" else "hy3d_api.json"))
    with open(wf_path,"r",encoding="utf-8") as f: wf=json.load(f)
    if "nodes" in wf and "links" in wf:
        raise ValueError("에디터 저장 JSON입니다. Export(API)로 내보내세요.")

    _patch_load_image_name(wf, input_name)
    if mode=="video": _patch_ltxv(wf, **ltxv_cfg)
    else: _patch_hy3d(wf, **hy3d_cfg)

    outputs = _comfy_prompt(wf, images=[{"name":input_name,"image":data_uri}], timeout=3600)

    # 산출물 모으기
    job_id=str(uuid.uuid4())[:8]
    job_dir=_ensure_dir(os.path.join(OUTPUT_DIR, job_id))
    collected_files, collected_urls = [], []

    for node_id, node_out in outputs.items():
        for _, vals in node_out.items():
            if not isinstance(vals, list): continue
            for v in vals:
                if not isinstance(v, dict): continue
                if v.get("type")=="output" and v.get("subfolder"):
                    src=os.path.join(OUTPUT_DIR, v["subfolder"], v["filename"])
                    if os.path.isfile(src):
                        dst=os.path.join(job_dir, v["filename"])
                        _ensure_dir(os.path.dirname(dst)); shutil.copy2(src,dst)
                        collected_files.append(dst)
                elif v.get("type")=="url" and v.get("data"):
                    collected_urls.append(v["data"])
                elif v.get("type")=="image" and v.get("image"):
                    b64=v["image"].split(",",1)[1] if "," in v["image"] else v["image"]
                    im=Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
                    th=os.path.join(job_dir, f"thumb_{_now_ms()}.png")
                    im.save(th, format="PNG")
                    collected_files.append(th)

    # URL 산출물도 다운로드
    def _dl(u: str)->str:
        name=os.path.basename(urlparse(u).path) or f"artifact_{_now_ms()}.bin"
        r = requests.get(u, stream=True, timeout=1200); r.raise_for_status()
        dst=os.path.join(job_dir, name)
        with open(dst,"wb") as f:
            for c in r.iter_content(1024*1024):
                if c: f.write(c)
        return dst
    for u in set(collected_urls):
        try: collected_files.append(_dl(u))
        except Exception: pass

    # 확장자 유지 + S3 업로드
    result = {"job_id": job_id, "mode": mode, "preset": preset,
              "params":{"hy3d":hy3d_cfg,"ltxv":ltxv_cfg}, "elapsed_ms": 0,
              "outputs":{"files":[], "s3": []}}
    for p in collected_files:
        ext=os.path.splitext(p)[1].lower()
        if ext not in (".jpg",".jpeg",".png",".glb",".gltf",".mp4",".webm",".mov"):
            continue
        if S3_ENABLE:
            meta=_s3_upload(p)  # 디렉토리 자동 분기
            result["outputs"]["s3"].append(meta)
        result["outputs"]["files"].append(p)

    result["elapsed_ms"] = _now_ms() - t0
    return result

# Serverless 엔트리포인트
runpod.serverless.start({"handler": rp_handler})