# -*- coding: utf-8 -*-
"""
파인튜닝에 필요한 패키지 설치 스크립트
"""
import subprocess
import sys

def install_package(package):
    """패키지 설치"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} 설치 완료")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ {package} 설치 실패")
        return False

def main():
    print("=== 파인튜닝 패키지 설치 시작 ===")
    
    # 기본 패키지들
    packages = [
        "torch>=2.0.0",
        "transformers>=4.35.0",
        "datasets>=2.14.0",
        "peft>=0.6.0",
        "accelerate>=0.24.0",
        "bitsandbytes>=0.41.0",
        "huggingface_hub>=0.17.0",
        "pandas>=1.5.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "tqdm>=4.65.0",
        "wandb>=0.15.0",  # 선택사항
    ]
    
    print("필요한 패키지들:")
    for pkg in packages:
        print(f"  - {pkg}")
    
    print("\n설치를 시작합니다...")
    
    success_count = 0
    for package in packages:
        if install_package(package):
            success_count += 1
    
    print(f"\n=== 설치 완료 ===")
    print(f"성공: {success_count}/{len(packages)}개 패키지")
    
    if success_count == len(packages):
        print("🎉 모든 패키지가 성공적으로 설치되었습니다!")
        print("\n다음 단계:")
        print("1. python prepare_finetuning_dataset.py  # 데이터셋 준비")
        print("2. python finetune_kanana.py  # 파인튜닝 실행")
    else:
        print("⚠️  일부 패키지 설치에 실패했습니다. 수동으로 설치해주세요.")

if __name__ == "__main__":
    main()
