from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    
    path('api/', include('JJACKLETTE.urls')),

    # 1. dj-rest-auth for auth endpoints (login, logout, password reset)
    path('auth/', include('dj_rest_auth.urls')),
    # 2. dj-rest-auth for registration endpoint
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    # 3. allauth for social account logic (providers views for social login)
    path('accounts/', include('allauth.urls')),
    # 4. 구글 OAuth 전용 라우트 추가 (중복 경로 제거)
    path('accounts/', include('allauth.socialaccount.providers.google.urls')),

    # --- Pipeline API 엔드포인트 ---
    path('api/pipeline/chat/', views.chatbot_api, name='pipeline-chat'),
    path('api/pipeline/history/', views.chat_history_api, name='pipeline-history'),
    path('api/pipeline/clear-session/', views.clear_session_api, name='pipeline-clear-session'),
]