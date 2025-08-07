# DRF의 ViewSet 또는 APIView를 활용하여 RESTful API 로직을 작성
# 클라이언트(React.js)로부터 요청을 받아 serializers.py를 통해 데이터를 처리하고,
# models.py를 통해 PostgreSQL과 상호작용하며, services.py의 비즈니스 로직을 호출

# JJACKLETTE/views.py

from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
# from .llm_interface import generate_response

def chatbot_page(request):
    return render(request, 'home.html')

class ChatbotAPIView(APIView):
    """
    챗봇 응답을 처리하는 API (동기 방식)
    """
    def post(self, request, *args, **kwargs):
        message = request.data.get('message')

        if not message:
            return Response(
                {"error": "메시지가 비어있습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        mock_response = f"'{message}' 메시지 잘 받았습니다. (연결 테스트 성공!)"

        return Response({"response": mock_response}, status=status.HTTP_200_OK)