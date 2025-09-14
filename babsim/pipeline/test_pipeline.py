#!/usr/bin/env python3
"""
Babsim 파이프라인 테스트 스크립트
"""

import sys
import os
from pathlib import Path

# babsim 디렉토리를 Python 경로에 추가
BABSIM_ROOT = Path(__file__).parent.parent
sys.path.append(str(BABSIM_ROOT))

def test_text_generation():
    """텍스트 생성 테스트"""
    print("=== 텍스트 생성 테스트 ===")
    
    try:
        from pipeline.text_pipeline import text_pipeline
        
        initial_state = {
            "user_query": "현대자동차의 역사에 대해 알려주세요.",
            "intent": "",
            "chat_history": [],
            "response": "",
            "image_query": "",
            "is_form_complete": False,
            "messages_summarized": False
        }
        
        result = text_pipeline.invoke(initial_state)
        
        print(f"✅ 파이프라인 실행 성공")
        print(f"   의도: {result.get('intent', 'N/A')}")
        print(f"   응답: {result.get('response', '')[:100]}...")
        print(f"   폼 완성: {result.get('is_form_complete', False)}")
        print(f"   요약 완료: {result.get('messages_summarized', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 텍스트 생성 테스트 실패: {e}")
        return False

def test_image_modification():
    """이미지 수정 요청 테스트"""
    print("\n=== 이미지 수정 요청 테스트 ===")
    
    try:
        from pipeline.text_pipeline import text_pipeline
        
        initial_state = {
            "user_query": "이 이미지를 수정해주세요.",
            "intent": "",
            "chat_history": [],
            "response": "",
            "image_query": "",
            "is_form_complete": False,
            "messages_summarized": False
        }
        
        result = text_pipeline.invoke(initial_state)
        
        print(f"✅ 파이프라인 실행 성공")
        print(f"   의도: {result.get('intent', 'N/A')}")
        print(f"   응답: {result.get('response', '')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 이미지 수정 테스트 실패: {e}")
        return False

def test_multi_turn_conversation():
    """Multi-turn 대화 테스트"""
    print("\n=== Multi-turn 대화 테스트 ===")
    
    try:
        from pipeline.text_pipeline import text_pipeline
        
        # 첫 번째 메시지
        initial_state = {
            "user_query": "SUV 차량을 디자인하고 싶어요.",
            "intent": "",
            "chat_history": [],
            "response": "",
            "image_query": "",
            "is_form_complete": False,
            "messages_summarized": False
        }
        
        result1 = text_pipeline.invoke(initial_state)
        chat_history = result1.get("chat_history", [])
        
        print(f"✅ 첫 번째 메시지 처리 성공")
        print(f"   응답: {result1.get('response', '')[:100]}...")
        
        # 두 번째 메시지
        state2 = {
            "user_query": "전면부 뷰로 보여주세요.",
            "intent": "",
            "chat_history": chat_history,
            "response": "",
            "image_query": "",
            "is_form_complete": False,
            "messages_summarized": False
        }
        
        result2 = text_pipeline.invoke(state2)
        
        print(f"✅ 두 번째 메시지 처리 성공")
        print(f"   응답: {result2.get('response', '')[:100]}...")
        print(f"   폼 완성: {result2.get('is_form_complete', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Multi-turn 대화 테스트 실패: {e}")
        return False

def test_form_completion():
    """폼 완성 테스트"""
    print("\n=== 폼 완성 테스트 ===")
    
    try:
        from pipeline.text_pipeline import text_pipeline
        
        # 폼 완성을 위한 대화 시나리오
        messages = [
            "SUV 차량을 디자인하고 싶어요.",
            "전면부 뷰로 보여주세요.",
            "검은색으로 해주세요.",
            "LED 조명을 사용해주세요."
        ]
        
        chat_history = []
        
        for i, message in enumerate(messages, 1):
            print(f"메시지 {i}: {message}")
            
            state = {
                "user_query": message,
                "intent": "",
                "chat_history": chat_history,
                "response": "",
                "image_query": "",
                "is_form_complete": False,
                "messages_summarized": False
            }
            
            result = text_pipeline.invoke(state)
            chat_history = result.get("chat_history", [])
            
            print(f"   응답: {result.get('response', '')[:100]}...")
            print(f"   폼 완성: {result.get('is_form_complete', False)}")
            
            if result.get("is_form_complete", False):
                print(f"   이미지 쿼리: {result.get('image_query', '')[:100]}...")
                break
        
        return True
        
    except Exception as e:
        print(f"❌ 폼 완성 테스트 실패: {e}")
        return False

def test_components():
    """개별 컴포넌트 테스트"""
    print("\n=== 개별 컴포넌트 테스트 ===")
    
    try:
        # 의도 분류기 테스트
        from pipeline.components.intent_classifier import intent_classifier
        intent = intent_classifier.classify_intent("안녕하세요")
        print(f"✅ 의도 분류: {intent}")
        
        # RAG 생성기 테스트
        from pipeline.components.rag_generator import rag_generator
        response = rag_generator.generate_response("현대자동차", [])
        print(f"✅ RAG 응답: {response[:100]}...")
        
        # 채팅 매니저 테스트
        from pipeline.components.chat_manager import chat_manager
        history = chat_manager.add_message([], "user", "안녕하세요")
        history = chat_manager.add_message(history, "assistant", "안녕하세요!")
        print(f"✅ 채팅 기록: {len(history)}개 메시지")
        
        # 이미지 쿼리 생성기 테스트
        from pipeline.components.image_query_generator import image_query_generator
        query = image_query_generator.generate_image_query(history)
        print(f"✅ 이미지 쿼리: {query[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 컴포넌트 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚗 Babsim 파이프라인 테스트")
    print("=" * 50)
    
    # 각 테스트 실행
    tests = [
        ("개별 컴포넌트", test_components),
        ("텍스트 생성", test_text_generation),
        ("이미지 수정 요청", test_image_modification),
        ("Multi-turn 대화", test_multi_turn_conversation),
        ("폼 완성", test_form_completion)
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
        print("🎉 모든 테스트 통과! 파이프라인이 정상적으로 작동합니다.")
    else:
        print("⚠️  일부 테스트가 실패했습니다. 설정을 확인해주세요.")

if __name__ == "__main__":
    main()
