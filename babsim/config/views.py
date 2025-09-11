# BABSIM/config/views.py
from django.shortcuts import render
import json
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from pipeline.services import babsim_pipeline_service

def index(request):
    """홈페이지(index.html)를 보여주는 뷰"""
    return render(request, 'home.html')

@csrf_exempt
def chatbot_api(request, session_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)

    try:
        data = json.loads(request.body)
        # print(data)  # 디버깅을 위한 요청 데이터 출력
        user_message = data.get('message')
        user_id = data.get('user_id', '550e8400-e29b-41d4-a716-446655440000')  # UUID 형식의 기본값 설정
        checklist_data = data.get('checklistData', {})
        completion_status = data.get('completionStatus', {})
        
        # 디버깅: 받은 데이터 확인
        print(f"🔍 config/views.py 디버깅:")
        print(f"  - 받은 user_id: {user_id}")
        print(f"  - user_id 타입: {type(user_id)}")
        print(f"  - 전체 data: {data}")
        
        if not user_message:
            return JsonResponse({'error': '메시지가 비어있습니다.'}, status=400)

        # Pipeline 서비스를 사용하여 응답 생성 (체크리스트 데이터 포함)
        result = babsim_pipeline_service.process_query(
            user_message,
            user_id=user_id,
            session_id=session_id,
            checklist_data=checklist_data,
            completion_status=completion_status,
        )
        
        if 'error' in result:
            return JsonResponse({'error': result['error']}, status=500)
        
        # 스트리밍 응답인 경우 직접 반환
        if 'streaming_response' in result:
            print(f"views.py 가 받은 result : {result}")
            
            return result["streaming_response"]
        
        # 일반 응답인 경우 JsonResponse로 반환
        return JsonResponse({
            'reply': result['response'],
            'intent': result.get('initial_intent', ''),
            'is_form_complete': result.get('is_form_complete', False),
            'image_query': result.get('image_query', ''),
            'session_id': result.get('session_id', ''),
            'prompt_id': result.get('prompt_id', ''),
            'generated_results': result.get('generated_results', []),
            'completion_status': result.get('completion_status', {}),
            'checklist_data': result.get('checklist_data', {})
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
async def chat_history_api(request):
    """사용자의 채팅 기록 조회 API"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)

    try:
        data = json.loads(request.body)
        user_email = data.get('email')
        
        if not user_email:
            return JsonResponse({'error': '이메일이 필요합니다.'}, status=400)

        # Pipeline 서비스를 사용하여 채팅 기록 조회
        history = babsim_pipeline_service.get_session_history(user_email)
        
        return JsonResponse({
            'history': history,
            'user_email': user_email
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
async def clear_session_api(request):
    """사용자의 활성 세션 종료 API"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)

    try:
        data = json.loads(request.body)
        user_email = data.get('email')
        
        if not user_email:
            return JsonResponse({'error': '이메일이 필요합니다.'}, status=400)

        # Pipeline 서비스를 사용하여 세션 종료
        success = babsim_pipeline_service.clear_session(user_email)
        
        return JsonResponse({
            'success': success,
            'user_email': user_email
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)