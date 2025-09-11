#!/usr/bin/env python3

import os
import requests
from pathlib import Path
from tqdm import tqdm

def download_file(url: str, dst: Path) -> bool:
    """파일 다운로드 (진행률 표시)"""
    try:
        print(f"Downloading {dst.name}...")
        
        with requests.get(url, stream=True, timeout=300) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            
            with open(dst, 'wb') as f, tqdm(
                total=total_size, 
                unit='B', 
                unit_scale=True, 
                desc=dst.name
            ) as pbar:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        print(f"✓ Downloaded {dst.name} ({dst.stat().st_size} bytes)")
        return True
        
    except Exception as e:
        print(f"✗ Download failed: {e}")
        return False

def bootstrap_models():
    """런타임 모델 다운로드"""
    models_dir = Path("/workspace/models")
    
    # 선택적 LTX-Video 체크포인트 다운로드
    ltxv_url = os.getenv("LTXV_CKPT_URL")
    if ltxv_url:
        ltxv_path = models_dir / "checkpoints" / "ltxv-custom.safetensors"
        if not ltxv_path.exists():
            print("Downloading custom LTX-Video checkpoint...")
            download_file(ltxv_url, ltxv_path)
    
    # 선택적 Hunyuan3D 추가 모델
    hy3d_url = os.getenv("HUNYUAN3D_EXTRA_URL")
    if hy3d_url:
        hy3d_path = models_dir / "hunyuan3d" / "extra-model.safetensors"
        hy3d_path.parent.mkdir(exist_ok=True)
        if not hy3d_path.exists():
            print("Downloading extra Hunyuan3D model...")
            download_file(hy3d_url, hy3d_path)
    
    print("✓ Bootstrap completed")

if __name__ == "__main__":
    bootstrap_models()