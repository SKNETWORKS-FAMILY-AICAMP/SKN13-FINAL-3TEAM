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
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView, TokenObtainPairView
from JJACKLETTE.serializers import MyTokenObtainPairSerializer
from JJACKLETTE import views # 챗/계정 뷰 JJACKLETTE에서 직접 사용
from django.conf import settings
from django.conf.urls.static import static

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer # <- AUTH



urlpatterns = [
    path("admin/", admin.site.urls),

    # ── AUTH
    path("api/auth/register/", views.RegisterAPIView.as_view()),
    path("api/auth/login/", views.LogoutAPIView.as_view()),
    path("api/auth/logout/", views.LogoutAPIView.as_view(), name='logout'),  # ← 로그아웃(블랙리스트)
    path("auth/refresh/", TokenRefreshView.as_view()),

    # ── USER
    path("users/profile/", views.UserProfileAPIView.as_view()),

    # ── CHAT
    path("api/chat/sessions/", views.ChatSessionListCreateAPIView.as_view()),
    path("api/chat/sessions/<uuid:session_id>/end/", views.ChatSessionEndAPIView.as_view()),
    path("api/chat/prompts/<uuid:session_id>/prompts/", views.PromptLogListCreateAPIView.as_view()),
    path("api/chat/respond/", views.ChatRespondAPIView.as_view()),
    path("api/chat/results/<uuid:prompt_id>/results/", views.GeneratedResultListCreateAPIView.as_view()),
    path("api/generate/", views.GenerateUniversalAPIView.as_view()),
    path("api/generate/text/", views.GenerateTextAPIView.as_view()),   
    path("api/generate/image/", views.GenerateImageAPIView.as_view()), 
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


    # 다른 페이지에서 사용할 기능 작성 요.
