"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from JJACKLETTE import views
from rest_framework_simplejwt.views import TokenRefreshView
from JJACKLETTE.serializers import MyTokenObtainPairSerializer

from rest_framework_simplejwt.views import TokenObtainPairView
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', views.chatbot_page, name='chatbot_page'), # 전체 구조 비교해서 이거 다시보기

    # 1. 인증 API (authService.js)
    path('api/auth/register/', views.RegisterAPIView.as_view(), name='register'),
    path('api/auth/login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # React 코드의 refreshToken과 일치
    path('api/users/profile/', views.UserProfileAPIView.as_view(), name='user_profile'),
    path('api/auth/logout/', BlacklistTokenView.as_view(), name='token_blacklist'),
    path('api/auth/profile/update/', views.UserProfileAPIView.as_view(), name='user_profile_update'),

    # 2. 채팅 API (chatService.js)
    path('api/chat/sessions/', views.ChatSessionListCreateAPIView.as_view(), name='chat_sessions'),
    path('api/chat/sessions/<uuid:session_id>/end/', views.ChatSessionEndAPIView.as_view(), name='chat_session_end'),
    path('api/chat/sessions/<uuid:session_id>/prompts/', views.PromptLogListCreateAPIView.as_view(), name='prompt_logs_list'),
    path('api/chat/prompts/', views.PromptLogListCreateAPIView.as_view(), name='prompt_logs_create'), # createPromptLog 대응
    path('api/chat/prompts/<uuid:prompt_id>/results/', views.GeneratedResultListCreateAPIView.as_view(), name='generated_results_list'),
    path('api/chat/results/', views.GeneratedResultListCreateAPIView.as_view(), name='generated_results_create'),

    # 3. 인사이트 API (insightService.js)
    path('api/insights/models/', views.CarModelListAPIView.as_view(), name='car_model_list'),
    path('api/insights/models/<uuid:car_model_id>/', views.CarModelDetailAPIView.as_view(), name='car_model_detail'),

    # 4. 라이브러리 API (libraryService.js)
    path('api/library/assets/', views.AssetListCreateAPIView.as_view(), name='asset_library'),
    path('api/library/assets/<uuid:lib_id>/comments/', views.CommentListCreateAPIView.as_view(), name='asset_comments'),
    path('api/library/comments/', views.CommentListCreateAPIView.as_view(), name='create_comment'),

    # API 경로 ('/api/chat/')를 ChatbotAPIView와 직접 연결
    # path('api/chat/', views.ChatbotAPIView.as_view(), name='chatbot_api'),

]
