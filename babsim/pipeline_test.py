#!/usr/bin/env python3
"""
Babsim 파이프라인 테스트 스크립트
사용자가 직접 프롬프트를 입력하여 파이프라인을 테스트할 수 있습니다.
"""

import sys
import os
from pathlib import Path

# babsim 프로젝트 루트를 Python 경로에 추가
BABSIM_ROOT = Path(__file__).parent
sys.path.append(str(BABSIM_ROOT))

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Django 초기화
import django
django.setup()

# 파이프라인 import
from pipeline.text_pipeline import text_pipeline, PipelineState
from pipeline.services import babsim_pipeline_service

def print_pipeline_flow():
    """파이프라인 플로우 설명"""
    print("=" * 80)
    print("🚀 BABSIM 파이프라인 플로우")
    print("=" * 80)
    print()
    print("1️⃣  의도 분류 (classify_intent)")
    print("   └─ 사용자 질문의 의도를 분류 (text_generation 또는 image_modification)")
    print()
    print("2️⃣  쿼리 재작성 (rewrite_query)")
    print("   └─ HyDE 기법으로 사용자 질문을 확장하고 재작성")
    print()
    print("3️⃣  RAG 응답 생성 (generate_rag_response)")
    print("   └─ Kanana 모델 + RAG로 답변 생성")
    print()
    print("4️⃣  답변 평가 (evaluate_answer)")
    print("   └─ 생성된 답변의 관련성과 적절성 평가")
    print()
    print("5️⃣  재시도/확정 (retry_or_accept)")
    print("   └─ 평가 점수가 낮으면 재시도, 높으면 다음 단계로")
    print()
    print("6️⃣  폼 완성 확인 (check_form_completion)")
    print("   └─ 자동차 디자인 요구사항이 충분히 수집되었는지 확인")
    print()
    print("7️⃣  이미지 쿼리 생성 (generate_image_query)")
    print("   └─ 폼이 완성되면 Stable Diffusion용 프롬프트 생성")
    print()
    print("8️⃣  대화 지속 (continue_conversation)")
    print("   └─ 폼이 미완성이면 추가 질문으로 대화 지속")
    print()
    print("=" * 80)

def test_pipeline_interactive():
    """대화형 파이프라인 테스트"""
    print("🎯 대화형 파이프라인 테스트를 시작합니다!")
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.")
    print()
    
    # 테스트용 사용자 ID
    test_user_id = "test_user_001"
    
    while True:
        try:
            # 사용자 입력 받기
            user_input = input("\n💬 질문을 입력하세요: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '종료']:
                print("👋 테스트를 종료합니다.")
                break
            
            if not user_input:
                print("❌ 빈 입력입니다. 다시 입력해주세요.")
                continue
            
            print(f"\n🔄 파이프라인 처리 중...")
            print("-" * 50)
            
            # 파이프라인 실행
            result = babsim_pipeline_service.process_user_message(test_user_id, user_input)
            
            # 결과 출력
            if 'error' in result:
                print(f"❌ 오류: {result['error']}")
            else:
                print(f"✅ 의도: {result.get('intent', 'N/A')}")
                print(f"📝 응답: {result.get('response', 'N/A')}")
                print(f"📋 폼 완성: {'완료' if result.get('is_form_complete') else '미완성'}")
                
                if result.get('image_query'):
                    print(f"🎨 이미지 쿼리: {result.get('image_query')}")
                
                print(f"🆔 세션 ID: {result.get('session_id', 'N/A')}")
            
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n👋 테스트를 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")

def test_pipeline_direct():
    """직접 파이프라인 테스트 (Django 없이)"""
    print("🎯 직접 파이프라인 테스트를 시작합니다!")
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.")
    print()
    
    while True:
        try:
            # 사용자 입력 받기
            user_input = input("\n💬 질문을 입력하세요: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '종료']:
                print("👋 테스트를 종료합니다.")
                break
            
            if not user_input:
                print("❌ 빈 입력입니다. 다시 입력해주세요.")
                continue
            
            print(f"\n🔄 파이프라인 처리 중...")
            print("-" * 50)
            
            # 초기 상태 설정
            initial_state: PipelineState = {
                "user_query": user_input,
                "intent": "",
                "chat_history": [],
                "response": "",
                "image_query": "",
                "is_form_complete": False,
                "messages_summarized": False,
                "rewritten": False,
                "retried": False,
                "eval": {}
            }
            
            # 파이프라인 실행
            result = text_pipeline.invoke(initial_state)
            
            # 결과 출력
            print(f"✅ 의도: {result.get('intent', 'N/A')}")
            print(f"📝 응답: {result.get('response', 'N/A')}")
            print(f"📋 폼 완성: {'완료' if result.get('is_form_complete') else '미완성'}")
            
            if result.get('image_query'):
                print(f"🎨 이미지 쿼리: {result.get('image_query')}")
            
            if result.get('eval'):
                eval_data = result.get('eval', {})
                print(f"📊 평가 점수: 관련성={eval_data.get('relevance', 0):.2f}, 적절성={eval_data.get('adequacy', 0):.2f}")
            
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n👋 테스트를 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            import traceback
            traceback.print_exc()

def show_sample_queries():
    """샘플 쿼리 보여주기"""
    print("=" * 80)
    print("📝 샘플 쿼리 예시")
    print("=" * 80)
    print()
    print("🚗 자동차 디자인 관련:")
    print("   • '현대자동차의 디자인 철학에 대해 알려주세요'")
    print("   • '아이오닉 6의 디자인 특징은 무엇인가요?'")
    print("   • '자동차 공기역학에 대해 설명해주세요'")
    print()
    print("🎨 이미지 생성 관련:")
    print("   • '미래형 전기차를 디자인해주세요'")
    print("   • '스포츠카 디자인을 만들어주세요'")
    print("   • 'SUV 디자인을 생성해주세요'")
    print()
    print("🔧 기술적 질문:")
    print("   • '자동차 차체 구조 설계 원리는?'")
    print("   • '인간공학적 자동차 설계는 어떻게 하나요?'")
    print()
    print("=" * 80)

def main():
    """메인 함수"""
    print_pipeline_flow()
    show_sample_queries()
    
    print("\n🎯 테스트 모드를 선택하세요:")
    print("1. Django 연동 테스트 (데이터베이스 저장)")
    print("2. 직접 파이프라인 테스트 (메모리만 사용)")
    print("3. 종료")
    
    while True:
        try:
            choice = input("\n선택 (1-3): ").strip()
            
            if choice == '1':
                test_pipeline_interactive()
                break
            elif choice == '2':
                test_pipeline_direct()
                break
            elif choice == '3':
                print("👋 프로그램을 종료합니다.")
                break
            else:
                print("❌ 잘못된 선택입니다. 1-3 중에서 선택해주세요.")
                
        except KeyboardInterrupt:
            print("\n👋 프로그램을 종료합니다.")
            break

if __name__ == "__main__":
    main()
