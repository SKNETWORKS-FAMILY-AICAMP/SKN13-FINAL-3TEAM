from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    
    path('api/', include('JJACKLETTE.urls')),
    
    path('auth/', include('dj_rest_auth.urls')),
    
    path('auth/google/', include('allauth.socialaccount.providers.google.urls')),

    # --- Pipeline API 엔드포인트 ---
    path('api/pipeline/chat/', views.chatbot_api, name='pipeline-chat'),
    path('api/pipeline/history/', views.chat_history_api, name='pipeline-history'),
    path('api/pipeline/clear-session/', views.clear_session_api, name='pipeline-clear-session'),
]