#!/usr/bin/env python3
"""
BABSIM Pipeline 기본 테스트 스크립트
Docker 서비스 없이도 실행 가능한 기본 테스트
"""

import os
import sys
import django
from pathlib import Path

# Django 설정
BABSIM_ROOT = Path(__file__).parent
sys.path.append(str(BABSIM_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from pipeline.config import config
from pipeline.models.exaone_llm_model import exaone_llm_model

def test_basic_config():
    """기본 설정 테스트"""
    print("=== 1. 기본 설정 테스트 ===")
    
    try:
        print(f"LLM 모델: {config.LLM_MODEL}")
        print(f"Embedding 모델: {config.EMBEDDING_MODEL}")
        print(f"Qdrant Host: {config.QDRANT_HOST}")
        print(f"Qdrant Port: {config.QDRANT_PORT}")
        print("✅ 기본 설정 로드 성공")
        return True
    except Exception as e:
        print(f"❌ 기본 설정 테스트 실패: {e}")
        return False

def test_exaone_model():
    """Exaone 모델 테스트"""
    print("\n=== 2. Exaone 모델 테스트 ===")
    
    try:
        print(f"Inference URL: {exaone_llm_model.INFERENCE_URL}")
        print("✅ Exaone 모델 초기화 성공")
        return True
    except Exception as e:
        print(f"❌ Exaone 모델 테스트 실패: {e}")
        return False

def test_pipeline_components():
    """Pipeline 컴포넌트 테스트 (임베딩 제외)"""
    print("\n=== 3. Pipeline 컴포넌트 테스트 ===")
    
    try:
        from pipeline.components.intent_classifier import intent_classifier
        from pipeline.components.chat_manager import chat_manager
        from pipeline.components.image_query_generator import image_query_generator
        
        print("✅ 기본 컴포넌트 import 성공")
        return True
    except Exception as e:
        print(f"❌ Pipeline 컴포넌트 테스트 실패: {e}")
        return False

def test_pipeline_import():
    """Pipeline 전체 import 테스트"""
    print("\n=== 4. Pipeline 전체 Import 테스트 ===")
    
    try:
        # RAG 생성기는 임베딩 모델 때문에 제외
        from pipeline.services import babsim_pipeline_service
        print("✅ Pipeline 서비스 import 성공")
        return True
    except Exception as e:
        print(f"❌ Pipeline import 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚗 BABSIM Pipeline 기본 테스트")
    print("=" * 50)
    
    # 각 테스트 실행
    tests = [
        ("기본 설정", test_basic_config),
        ("Exaone 모델", test_exaone_model),
        ("Pipeline 컴포넌트", test_pipeline_components),
        ("Pipeline Import", test_pipeline_import)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        success = test_func()
        results.append((test_name, success))
    
    # 결과 요약
    print("\n📊 테스트 결과 요약")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ 통과" if success else "❌ 실패"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n총 {len(results)}개 테스트 중 {passed}개 통과")
    
    if passed == len(results):
        print("🎉 모든 기본 테스트 통과! Pipeline이 정상적으로 설정되었습니다.")
        print("\n다음 단계:")
        print("1. Docker Desktop 실행")
        print("2. docker compose up -d postgres qdrant inference-server")
        print("3. python test_pipeline_complete.py")
    else:
        print("⚠️  일부 테스트가 실패했습니다.")

if __name__ == "__main__":
    main()
