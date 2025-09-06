import os
import shutil
import subprocess
from pathlib import Path
from typing import List
from huggingface_hub import snapshot_download

# --- 경로 설정 ---
WORKDIR     = Path(os.getenv("WORKDIR", "/workspace"))
COMFY_DIR   = WORKDIR / "ComfyUI"
MODELS_DIR  = Path(os.getenv("MODELSDIR", "/workspace/models"))
CUSTOMDIR   = Path(os.getenv("CUSTOMDIR", "/workspace/custom_nodes"))

HF_TOKEN    = os.getenv("HF_TOKEN", "").strip()

# 기본 모델 레포 (ENV로 대체 가능)
HUNYUAN3D_REPO = os.getenv("HUNYUAN3D_DIFFUSERS_REPO", "tencent/Hunyuan3D-2").strip()
LTXV_REPO      = os.getenv("LTXV_REPO", "Lightricks/LTX-Video").strip()

# 필요 시 단일 URL 사용 옵션 (미사용이면 빈 값)
HUNYUAN3D_PAINT_URL = os.getenv("HUNYUAN3D_PAINT_URL", "").strip()
HUNYUAN3D_SHAPE_URL = os.getenv("HUNYUAN3D_SHAPE_URL", "").strip()
LTXV_URL            = os.getenv("LTXV_URL", "").strip()

# ComfyUI 표준 폴더
CFY_CKPT_DIR   = COMFY_DIR / "models" / "checkpoints"
CFY_TXTENC_DIR = COMFY_DIR / "models" / "text_encoders"
CFY_DIFF_DIR   = COMFY_DIR / "models" / "diffusers"

def ensure_dirs():
    for p in [MODELS_DIR, CFY_CKPT_DIR, CFY_TXTENC_DIR, CFY_DIFF_DIR]:
        p.mkdir(parents=True, exist_ok=True)

def hf_download(repo_id: str, out_dir: Path):
    print(f"[HF] downloading {repo_id} -> {out_dir}")
    kwargs = dict(repo_id=repo_id, local_dir=out_dir, local_dir_use_symlinks=False, revision=None)
    if HF_TOKEN:
        kwargs["token"] = HF_TOKEN
    snapshot_download(**kwargs)

def download_url(url: str, dst: Path):
    import requests
    print(f"[URL] {url} -> {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=1200) as r:
        r.raise_for_status()
        with open(dst, "wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)

def repo_tail(repo: str) -> str:
    # "org/name" -> "name"
    return repo.strip("/").split("/")[-1]

def find_files(root: Path, patterns: List[str]) -> List[Path]:
    out = []
    for pat in patterns:
        out.extend(root.rglob(pat))
    return out

def symlink_safe(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        try:
            if dst.is_symlink() or dst.is_file():
                dst.unlink()
            else:
                shutil.rmtree(dst)
        except Exception:
            pass
    try:
        dst.symlink_to(src)
        print(f"[LINK] {dst} -> {src}")
    except OSError:
        # 파일시스템/권한 이슈면 copy로 대체
        if src.is_file():
            shutil.copy2(src, dst)
            print(f"[COPY] {dst} <- {src}")
        elif src.is_dir():
            shutil.copytree(src, dst)
            print(f"[COPYTREE] {dst} <- {src}")

def link_diffusers_tree(local_dir: Path, name: str):
    # diffusers 계열은 디렉토리 전체를 링크
    target = CFY_DIFF_DIR / name
    symlink_safe(local_dir, target)

def link_ckpt_safetensors(local_dir: Path):
    # safetensors를 checkpoints에 링크
    for sf in find_files(local_dir, ["*.safetensors"]):
        dst = CFY_CKPT_DIR / sf.name
        symlink_safe(sf, dst)

def link_text_encoders_if_any(local_dir: Path):
    # 흔한 텍스트 인코더 파일 링크 (필요시)
    for sf in find_files(local_dir, ["*t5*.safetensors", "*text*encoder*.safetensors"]):
        dst = CFY_TXTENC_DIR / sf.name
        symlink_safe(sf, dst)

def build_custom_rasterizer():
    cr_path = CUSTOMDIR / "ComfyUI-Hunyuan3DWrapper" / "hy3dgen" / "texgen" / "custom_rasterizer"
    if cr_path.exists():
        print("[custom_rasterizer] building from source (pip install -v)")
        subprocess.run(["pip", "install", "-v", str(cr_path)], check=True)
    else:
        print("[WARN] custom_rasterizer source not found; skip")

def main():
    ensure_dirs()

    # --- Hunyuan3D ---
    if HUNYUAN3D_REPO:
        hy_local = MODELS_DIR / repo_tail(HUNYUAN3D_REPO)
        if not hy_local.exists() or not any(hy_local.iterdir()):
            hf_download(HUNYUAN3D_REPO, hy_local)
        # diffusers 트리 전체를 ComfyUI/diffusers/<name> 으로 링크
        link_diffusers_tree(hy_local, repo_tail(HUNYUAN3D_REPO))
        # 혹시 safetensors가 포함되어 있으면 checkpoints에도 링크
        link_ckpt_safetensors(hy_local)

    # 단일 URL(옵션)
    if HUNYUAN3D_PAINT_URL:
        download_url(HUNYUAN3D_PAINT_URL, MODELS_DIR / "hunyuan3d_paint.safetensors")
        link_ckpt_safetensors(MODELS_DIR)
    if HUNYUAN3D_SHAPE_URL:
        download_url(HUNYUAN3D_SHAPE_URL, MODELS_DIR / "hunyuan3d_shape.safetensors")
        link_ckpt_safetensors(MODELS_DIR)

    # --- LTX-Video ---
    if LTXV_REPO:
        ltx_local = MODELS_DIR / repo_tail(LTXV_REPO)
        if not ltx_local.exists() or not any(ltx_local.iterdir()):
            hf_download(LTXV_REPO, ltx_local)
        # 보통은 safetensors가 checkpoint로 쓰임
        link_ckpt_safetensors(ltx_local)
        link_text_encoders_if_any(ltx_local)
    if LTXV_URL:
        download_url(LTXV_URL, MODELS_DIR / "ltxv.safetensors")
        link_ckpt_safetensors(MODELS_DIR)

    # custom_rasterizer (리눅스) 소스 빌드
    build_custom_rasterizer()

    print("[bootstrap] complete")

if __name__ == "__main__":
    main()
