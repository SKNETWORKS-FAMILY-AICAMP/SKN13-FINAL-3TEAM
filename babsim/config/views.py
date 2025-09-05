# BABSIM/config/views.py
from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pipeline.services import babsim_pipeline_service

def index(request):
    """홈페이지(index.html)를 보여주는 뷰"""
    return render(request, 'home.html')

@csrf_exempt
async def chatbot_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message')
        user_id = data.get('user_id')  # 기본값 설정
        
        if not user_message:
            return JsonResponse({'error': '메시지가 비어있습니다.'}, status=400)

        # Pipeline 서비스를 사용하여 응답 생성
        result = babsim_pipeline_service.process_user_message(user_id, user_message)
        
        if 'error' in result:
            return JsonResponse({'error': result['error']}, status=500)
        
        return JsonResponse({
            'reply': result['response'],
            'intent': result.get('intent', ''),
            'is_form_complete': result.get('is_form_complete', False),
            'image_query': result.get('image_query', ''),
            'session_id': result.get('session_id', ''),
            'prompt_id': result.get('prompt_id', '')
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