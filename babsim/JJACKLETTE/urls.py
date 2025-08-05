# JJACKLETTE 앱 내의 API 엔드포인트들을 정의
# config/urls.py에서 이 앱의 urls.py를 include 하는 방식으로 구성
# 예: /api/items/, /api/search/ 등.

# JJACKLETTE/urls.py

from django.urls import path
from .views import VLMGenerateCaptionView, ExaoneGenerateTextView

urlpatterns = [
    # ... (기존의 다른 URL 패턴들)
    path('vlm-caption/', VLMGenerateCaptionView.as_view(), name='vlm-caption'),
    path('generate-text/', ExaoneGenerateTextView.as_view(), name='generate-text'),
]