# """
# URL configuration for config project.

# The `urlpatterns` list routes URLs to views. For more information please see:
#     https://docs.djangoproject.com/en/5.2/topics/http/urls/
# Examples:
# Function views
#     1. Add an import:  from my_app import views
#     2. Add a URL to urlpatterns:  path('', views.home, name='home')
# Class-based views
#     1. Add an import:  from other_app.views import Home
#     2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
# Including another URLconf
#     1. Import the include() function: from django.urls import include, path
#     2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
# """
# from django.contrib import admin
# from django.urls import path
# from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView, TokenObtainPairView
# from JJACKLETTE.serializers import MyTokenObtainPairSerializer
# from JJACKLETTE import views # 챗/계정 뷰 JJACKLETTE에서 직접 사용
# from django.conf import settings
# from django.conf.urls.static import static
# from django.conf import settings

# class MyTokenObtainPairView(TokenObtainPairView):
#     serializer_class = MyTokenObtainPairSerializer # <- AUTH



# urlpatterns = [
#     path("admin/", admin.site.urls),

#     # ── AUTH
#     path("api/auth/register/", views.RegisterAPIView.as_view()),
#     path("api/auth/login/", views.LogoutAPIView.as_view()),
#     path("api/auth/logout/", views.LogoutAPIView.as_view(), name='logout'),  # ← 로그아웃(블랙리스트)
#     path("auth/refresh/", TokenRefreshView.as_view()),

#     # ── USER
#     path("users/profile/", views.UserProfileAPIView.as_view()),

#     # ── CHAT
#     path("api/chat/sessions/", views.ChatSessionListCreateAPIView.as_view()),
#     path("api/chat/sessions/<uuid:session_id>/end/", views.ChatSessionEndAPIView.as_view()),
#     path("api/chat/prompts/<uuid:session_id>/prompts/", views.PromptLogListCreateAPIView.as_view()),
#     path("api/chat/respond/", views.ChatRespondAPIView.as_view()),
#     path("api/chat/results/<uuid:prompt_id>/results/", views.GeneratedResultListCreateAPIView.as_view()),
#     path("api/generate/", views.GenerateUniversalAPIView.as_view()),
#     path("api/generate/text/", views.GenerateTextAPIView.as_view()),   
#     path("api/generate/image/", views.GenerateImageAPIView.as_view()), 
    
# ]
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


#     # 다른 페이지에서 사용할 기능 작성 요.

from django.contrib import admin
from django.urls import path
from JJACKLETTE import views
from rest_framework_simplejwt.views import TokenRefreshView
from JJACKLETTE.serializers import MyTokenObtainPairSerializer

from rest_framework_simplejwt.views import TokenObtainPairView

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # AUTH
    path('auth/register/', views.RegisterAPIView.as_view(), name='register'),
    path('auth/login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/logout/', views.LogoutAPIView.as_view(), name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/profile/', views.UserProfileAPIView.as_view(), name='user_profile'),
    

    # USER
    path("api/users/profile/", views.UserProfileAPIView.as_view(), name="user-profile"),
    path('api/auth/profile/update/', views.UserProfileAPIView.as_view(), name='user_profile_update'), 
    
    # 2. 채팅 API
    path('chat/sessions/', views.ChatSessionListCreateAPIView.as_view(), name='chat_sessions'),
    path('chat/sessions/<uuid:session_id>/end/', views.ChatSessionEndAPIView.as_view(), name='chat_session_end'),
    path('chat/sessions/<uuid:session_id>/prompts/', views.PromptLogListCreateAPIView.as_view(), name='prompt_logs_list'),
    path('chat/prompts/', views.PromptLogListCreateAPIView.as_view(), name='prompt_logs_create'),
    path('chat/prompts/<uuid:prompt_id>/results/', views.GeneratedResultListCreateAPIView.as_view(), name='generated_results_list'),
    path('chat/results/', views.GeneratedResultListCreateAPIView.as_view(), name='generated_results_create'),
    
#     # GENERATE (단일/분리 엔드포인트)
#     path("api/generate/", views.GeneratedResultListAPIView.as_view(), name="generate-universal"),
#     path("api/generate/text/", views.GenerateTextAPIView.as_view(), name="generate-text"),
#     path("api/generate/image/", views.GenerateImageAPIView.as_view(), name="generate-image"),

]
