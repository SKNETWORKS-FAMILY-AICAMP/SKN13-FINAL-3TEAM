#!/usr/bin/env python3
"""
BABSIM Pipeline 통합 테스트 스크립트
JJACKLETTE Views와 Pipeline의 완전한 통합 테스트
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

from django.conf import settings
from pipeline.services import babsim_pipeline_service
from pipeline.config import config
from JJACKLETTE.models import Users, ChatSession
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

def test_config_consistency():
    """설정 일관성 테스트"""
    print("=== 1. 설정 일관성 테스트 ===")
    
    try:
        # LLM 모델 설정 확인
        jjacklette_model_path = getattr(settings, "EXAONE_MODEL_PATH", "/app/models/exaone_4.0_1.2b")
        pipeline_llm_model = config.LLM_MODEL
        
        print(f"JJACKLETTE 모델 경로: {jjacklette_model_path}")
        print(f"Pipeline LLM 모델: {pipeline_llm_model}")
        
        if "exaone_4.0_1.2b" in jjacklette_model_path and pipeline_llm_model == "exaone_4.0_1.2b":
            print("✅ LLM 모델 설정 일치")
        else:
            print("❌ LLM 모델 설정 불일치")
            return False
        
        # Embedding 모델 설정 확인
        jjacklette_embedding = getattr(settings, "EMBEDDING_MODEL_NAME", "BAAI/bge-m3")
        pipeline_embedding = config.EMBEDDING_MODEL
        
        print(f"JJACKLETTE Embedding: {jjacklette_embedding}")
        print(f"Pipeline Embedding: {pipeline_embedding}")
        
        if jjacklette_embedding == pipeline_embedding:
            print("✅ Embedding 모델 설정 일치")
        else:
            print("❌ Embedding 모델 설정 불일치")
            return False
        
        # Qdrant 설정 확인
        jjacklette_qdrant_host = getattr(settings, "QDRANT_HOST", "localhost")
        pipeline_qdrant_host = config.QDRANT_HOST
        
        print(f"JJACKLETTE Qdrant Host: {jjacklette_qdrant_host}")
        print(f"Pipeline Qdrant Host: {pipeline_qdrant_host}")
        
        if jjacklette_qdrant_host == pipeline_qdrant_host:
            print("✅ Qdrant 설정 일치")
        else:
            print("❌ Qdrant 설정 불일치")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 설정 테스트 실패: {e}")
        return False

def test_embedding_model():
    """Embedding 모델 로딩 및 테스트"""
    print("\n=== 2. Embedding 모델 테스트 ===")
    
    try:
        embedding_model = HuggingFaceBgeEmbeddings(
            model_name=config.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        test_query = "현대자동차의 디자인 철학"
        embedding = embedding_model.embed_query(test_query)
        
        print(f"✅ Embedding 모델 로딩 성공")
        print(f"   모델: {config.EMBEDDING_MODEL}")
        print(f"   임베딩 차원: {len(embedding)}")
        print(f"   테스트 쿼리: '{test_query}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding 모델 테스트 실패: {e}")
        return False

def test_pipeline_components():
    """Pipeline 컴포넌트 테스트"""
    print("\n=== 3. Pipeline 컴포넌트 테스트 ===")
    
    try:
        # Pipeline 서비스 초기화 테스트
        print("Pipeline 서비스 초기화...")
        service = babsim_pipeline_service
        print("✅ Pipeline 서비스 초기화 성공")
        
        # 컴포넌트 import 테스트
        from pipeline.components.intent_classifier import intent_classifier
        from pipeline.components.rag_generator import rag_generator
        from pipeline.components.chat_manager import chat_manager
        from pipeline.components.image_query_generator import image_query_generator
        from pipeline.models.exaone_llm_model import exaone_llm_model
        
        print("✅ 모든 Pipeline 컴포넌트 import 성공")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline 컴포넌트 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pipeline_integration():
    """Pipeline 통합 테스트"""
    print("\n=== 4. Pipeline 통합 테스트 ===")
    
    try:
        # 테스트 사용자 생성
        test_email = "pipeline_test@example.com"
        user, created = Users.objects.get_or_create(
            email=test_email,
            defaults={'password': 'testpass123'}
        )
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"✅ 테스트 사용자 생성: {test_email}")
        else:
            print(f"✅ 기존 테스트 사용자 사용: {test_email}")
        
        # 테스트 메시지들
        test_messages = [
            "안녕하세요",
            "현대자동차의 디자인 철학에 대해 알려주세요",
            "센슈어스 스포티니스가 뭔가요?",
            "아이오닉 5의 디자인 특징은?"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n--- 테스트 {i}: '{message}' ---")
            
            try:
                result = babsim_pipeline_service.process_user_message(test_email, message)
                
                if 'error' in result:
                    print(f"❌ 처리 실패: {result['error']}")
                    continue
                
                print(f"✅ 응답 생성 성공")
                print(f"   응답 길이: {len(result.get('response', ''))}")
                print(f"   의도: {result.get('intent', 'N/A')}")
                print(f"   폼완성: {result.get('is_form_complete', False)}")
                print(f"   이미지쿼리: {result.get('image_query', 'N/A')}")
                
                # 응답 내용 미리보기
                response_preview = result.get('response', '')[:100]
                if len(result.get('response', '')) > 100:
                    response_preview += "..."
                print(f"   응답 미리보기: {response_preview}")
                
            except Exception as e:
                print(f"❌ 메시지 처리 실패: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chat_session():
    """채팅 세션 테스트"""
    print("\n=== 5. 채팅 세션 테스트 ===")
    
    try:
        test_email = "session_test@example.com"
        
        # 사용자 생성
        user, created = Users.objects.get_or_create(
            email=test_email,
            defaults={'password': 'testpass123'}
        )
        if created:
            user.set_password('testpass123')
            user.save()
        
        # 세션 생성
        session = ChatSession.objects.create(user=user)
        print(f"✅ 채팅 세션 생성: {session.session_id}")
        
        # 세션 기록 조회
        history = babsim_pipeline_service.get_session_history(test_email)
        print(f"✅ 세션 기록 조회: {len(history)}개 세션")
        
        # 세션 종료
        success = babsim_pipeline_service.clear_session(test_email)
        print(f"✅ 세션 종료: {success}")
        
        return True
        
    except Exception as e:
        print(f"❌ 채팅 세션 테스트 실패: {e}")
        return False

def interactive_test():
    """대화형 테스트"""
    print("\n=== 6. 대화형 테스트 ===")
    print("종료하려면 'quit', 'exit', 또는 '종료'를 입력하세요.")
    print()
    
    try:
        email = input("이메일을 입력하세요 (기본값: interactive_test@example.com): ").strip()
        if not email:
            email = "interactive_test@example.com"
        
        print(f"채팅 시작: {email}")
        print("-" * 50)
        
        while True:
            user_input = input("사용자: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '종료']:
                print("채팅을 종료합니다.")
                break
            
            if not user_input:
                continue
            
            try:
                result = babsim_pipeline_service.process_user_message(email, user_input)
                
                if 'error' in result:
                    print(f"시스템 오류: {result['error']}")
                else:
                    print(f"AI: {result['response']}")
                    if result.get('image_query'):
                        print(f"[이미지 쿼리 생성됨]: {result['image_query']}")
                
                print()
                
            except Exception as e:
                print(f"처리 오류: {e}")
                print()
                
    except Exception as e:
        print(f"대화형 테스트 실패: {e}")

def main():
    """메인 테스트 함수"""
    print("🚗 BABSIM Pipeline 통합 테스트")
    print("=" * 60)
    
    # 각 테스트 실행
    tests = [
        ("설정 일관성", test_config_consistency),
        ("Embedding 모델", test_embedding_model),
        ("Pipeline 컴포넌트", test_pipeline_components),
        ("Pipeline 통합", test_pipeline_integration),
        ("채팅 세션", test_chat_session)
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
        print("🎉 모든 테스트 통과! Pipeline이 정상적으로 작동합니다.")
        
        # 대화형 테스트 옵션 제공
        choice = input("\n대화형 테스트를 실행하시겠습니까? (y/n): ").strip().lower()
        if choice in ['y', 'yes', '예']:
            interactive_test()
    else:
        print("⚠️  일부 테스트가 실패했습니다. 설정을 확인해주세요.")

if __name__ == "__main__":
    main()
