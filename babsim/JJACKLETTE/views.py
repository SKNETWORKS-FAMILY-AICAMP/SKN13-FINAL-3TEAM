# from django.shortcuts import render

# # DRF의 ViewSet 또는 APIView를 활용하여 RESTful API 로직을 작성
# # 클라이언트(React.js)로부터 요청을 받아 serializers.py를 통해 데이터를 처리하고,
# # models.py를 통해 PostgreSQL과 상호작용하며, services.py의 비즈니스 로직을 호출

# JJACKLETTE/views.py

import os
import requests
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

# -------------------------------------------------------------
# Docker Compose에서 설정한 환경 변수를 불러옵니다.
# VLM_API_URL은 docker-compose.yml 파일에서 정의해야 합니다.
# 예: VLM_API_URL=http://<your-pod-ip>:8000/generate_caption/
# -------------------------------------------------------------
VLM_API_URL = os.environ.get('VLM_API_URL')

class VLMGenerateCaptionView(APIView):
    """
    RunPod의 VLM API를 호출하여 이미지 캡션을 생성하는 API 뷰
    """
    def post(self, request, *args, **kwargs):
        # API URL이 설정되지 않았을 경우 에러 처리
        if not VLM_API_URL:
            return Response({"error": "VLM API URL이 설정되지 않았습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        image_file = request.FILES.get('image_file')
        prompt = request.data.get('prompt', 'Please describe this image.')
        
        if not image_file:
            return Response({"error": "이미지 파일이 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # RunPod API로 전송할 데이터와 파일 준비
            files = {'image_file': image_file.read()}
            data = {'prompt': prompt}

            # RunPod API 호출 (POST 요청)
            response = requests.post(VLM_API_URL, files=files, data=data)
            response.raise_for_status() # HTTP 에러 발생 시 예외 처리

            # RunPod에서 받은 결과 반환
            return Response(response.json(), status=status.HTTP_200_OK)

        except requests.exceptions.RequestException as e:
            return Response({"error": f"RunPod API 호출 실패: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
