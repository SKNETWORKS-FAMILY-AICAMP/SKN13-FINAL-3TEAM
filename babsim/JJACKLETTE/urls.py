# JJACKLETTE 앱 내의 API 엔드포인트들을 정의
# config/urls.py에서 이 앱의 urls.py를 include 하는 방식으로 구성
# 예: /api/items/, /api/search/ 등.

# JJACKLETTE/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # 챗봇 UI 페이지를 보여주는 URL
    # 예: http://localhost:8000/chatbot/
    path('', views.chatbot_page, name='chatbot_page'),

    # 챗봇 API와 통신하는 URL
    # 예: http://localhost:8000/chatbot/api/
    # 클래스 기반 뷰(APIView)를 사용했으므로, .as_view()를 꼭 붙여줘야 합니다.
    path('api/', views.ChatbotAPIView.as_view(), name='chatbot_api'),
]
