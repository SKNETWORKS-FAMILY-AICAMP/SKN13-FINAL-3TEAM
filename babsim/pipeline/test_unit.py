#!/usr/bin/env python3
"""
Babsim 파이프라인 단위 테스트 스크립트
개별 컴포넌트들을 독립적으로 테스트할 수 있습니다.
"""

import sys
import os
from pathlib import Path

# babsim 디렉토리를 Python 경로에 추가
BABSIM_ROOT = Path(__file__).parent.parent
sys.path.append(str(BABSIM_ROOT))

def test_config():
    """설정 파일 테스트"""
    print("=== 설정 파일 테스트 ===")
    try:
        from pipeline.config import config
        
        print(f"✅ LLM 모델: {config.LLM_MODEL}")
        print(f"✅ 임베딩 모델: {config.EMBEDDING_MODEL}")
        print(f"✅ Qdrant 호스트: {config.QDRANT_HOST}")
        print(f"✅ Qdrant 포트: {config.QDRANT_PORT}")
        print(f"✅ 컬렉션명: {config.QDRANT_COLLECTION_NAME}")
        print(f"✅ 시스템 프롬프트: {config.SYSTEM_PROMPT[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ 설정 테스트 실패: {e}")
        return False

def test_intent_classifier():
    """의도 분류기 테스트"""
    print("\n=== 의도 분류기 테스트 ===")
    try:
        from pipeline.components.intent_classifier import intent_classifier
        
        test_cases = [
            ("안녕하세요", "text_generation"),
            ("현대자동차에 대해 알려주세요", "text_generation"),
            ("이 이미지를 수정해주세요", "image_modification"),
            ("아이오닉 5의 디자인은?", "text_generation")
        ]
        
        for query, expected in test_cases:
            intent = intent_classifier.classify_intent(query)
            status = "✅" if intent == expected else "❌"
            print(f"{status} '{query}' -> {intent} (예상: {expected})")
        
        return True
    except Exception as e:
        print(f"❌ 의도 분류기 테스트 실패: {e}")
        return False

def test_chat_manager():
    """채팅 매니저 테스트"""
    print("\n=== 채팅 매니저 테스트 ===")
    try:
        from pipeline.components.chat_manager import chat_manager
        
        # 빈 대화 기록으로 시작
        history = []
        
        # 메시지 추가
        history = chat_manager.add_message(history, "user", "안녕하세요")
        history = chat_manager.add_message(history, "assistant", "안녕하세요! 무엇을 도와드릴까요?")
        history = chat_manager.add_message(history, "user", "현대자동차에 대해 알려주세요")
        history = chat_manager.add_message(history, "assistant", "현대자동차는 한국의 대표적인 자동차 제조업체입니다.")
        
        print(f"✅ 대화 기록 길이: {len(history)}")
        print(f"✅ 첫 번째 메시지: {history[0]}")
        print(f"✅ 마지막 메시지: {history[-1]}")
        
        # 폼 완성 확인
        is_complete = chat_manager.is_form_complete(history)
        print(f"✅ 폼 완성 여부: {is_complete}")
        
        return True
    except Exception as e:
        print(f"❌ 채팅 매니저 테스트 실패: {e}")
        return False

def test_image_query_generator():
    """이미지 쿼리 생성기 테스트"""
    print("\n=== 이미지 쿼리 생성기 테스트 ===")
    try:
        from pipeline.components.image_query_generator import image_query_generator
        
        # 샘플 대화 기록
        chat_history = [
            {"role": "user", "content": "SUV 차량을 디자인하고 싶어요"},
            {"role": "assistant", "content": "좋습니다! 어떤 종류의 SUV를 원하시나요?"},
            {"role": "user", "content": "전면부 뷰로 보여주세요"},
            {"role": "assistant", "content": "전면부 뷰로 SUV를 디자인하겠습니다."}
        ]
        
        # 폼 데이터 추출 테스트
        form_data = image_query_generator._extract_form_data(chat_history)
        print(f"✅ 추출된 폼 데이터: {form_data}")
        
        # 이미지 쿼리 생성 테스트
        query = image_query_generator.generate_image_query(chat_history)
        print(f"✅ 생성된 이미지 쿼리: {query[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ 이미지 쿼리 생성기 테스트 실패: {e}")
        return False

def test_rag_adapter():
    """RAG 어댑터 테스트"""
    print("\n=== RAG 어댑터 테스트 ===")
    try:
        from pipeline.components.babsim_rag_adapter import babsim_rag_adapter
        
        # 컬렉션 정보 조회
        info = babsim_rag_adapter.get_collection_info()
        print(f"✅ 컬렉션 상태: {info.get('status', 'unknown')}")
        
        if info.get('status') == 'connected':
            print(f"✅ 총 포인트 수: {info.get('total_points', 'unknown')}")
            print(f"✅ 벡터 크기: {info.get('vector_size', 'unknown')}")
            
            # 검색 테스트
            results = babsim_rag_adapter.search_relevant_documents("현대자동차", k=3)
            print(f"✅ 검색 결과 수: {len(results)}")
            
            if results:
                print(f"✅ 첫 번째 결과 점수: {results[0].get('score', 'N/A')}")
        else:
            print("⚠️  Qdrant 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        
        return True
    except Exception as e:
        print(f"❌ RAG 어댑터 테스트 실패: {e}")
        return False

def test_services():
    """서비스 레이어 테스트"""
    print("\n=== 서비스 레이어 테스트 ===")
    try:
        from pipeline.services import babsim_pipeline_service
        
        # 사용자 생성/조회 테스트
        test_email = "test@example.com"
        user = babsim_pipeline_service.get_user_by_email(test_email)
        
        if user:
            print(f"✅ 기존 사용자 조회: {user.email}")
        else:
            print("⚠️  사용자가 존재하지 않습니다. Django 설정을 확인해주세요.")
        
        # 대화 기록 형식 변환 테스트
        sample_history = [
            {"role": "user", "content": "안녕하세요"},
            {"role": "assistant", "content": "안녕하세요!"}
        ]
        
        formatted = babsim_pipeline_service.get_chat_history_for_pipeline(None)
        print(f"✅ 대화 기록 변환: {len(formatted)}개 메시지")
        
        return True
    except Exception as e:
        print(f"❌ 서비스 레이어 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🧪 Babsim 파이프라인 단위 테스트")
    print("=" * 50)
    
    # 각 테스트 실행
    tests = [
        ("설정 파일", test_config),
        ("의도 분류기", test_intent_classifier),
        ("채팅 매니저", test_chat_manager),
        ("이미지 쿼리 생성기", test_image_query_generator),
        ("RAG 어댑터", test_rag_adapter),
        ("서비스 레이어", test_services)
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
        print("🎉 모든 단위 테스트 통과!")
    else:
        print("⚠️  일부 테스트가 실패했습니다.")

if __name__ == "__main__":
    main()
