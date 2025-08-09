# BABSIM/config/views.py
from django.shortcuts import render

def index(request):
    """홈페이지(index.html)를 보여주는 뷰"""
    return render(request, 'home.html')

# BABSIM/config/views.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from JJACKLETTE import llm # 방금 만든 llm 모듈 import
# ... 기존 index 뷰 ...

@csrf_exempt
async def chatbot_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message')
        if not user_message:
            return JsonResponse({'error': '메시지가 비어있습니다.'}, status=400)

        # 로컬 모델을 사용하여 응답 생성
        bot_message = llm.generate_text(user_message)
        return JsonResponse({'reply': bot_message})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)