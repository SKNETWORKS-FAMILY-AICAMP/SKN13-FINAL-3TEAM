# JJACKLETTE 앱 내의 API 엔드포인트들을 정의
# config/urls.py에서 이 앱의 urls.py를 include 하는 방식으로 구성
# 예: /api/items/, /api/search/ 등.

# JJACKLETTE/urls.py

from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from . import oauth_views

urlpatterns = [
    # --- 0. OAuth 콜백 처리 ---
    path('oauth/callback/', oauth_views.oauth_callback, name='oauth-callback'),
    path('oauth/google/callback/', oauth_views.google_oauth_callback, name='google-oauth-callback'),
    path('oauth/generate-token/', oauth_views.generate_jwt_token, name='generate-jwt-token'),
    path('auth/token-redirect/', oauth_views.oauth_callback_authenticated, name='oauth-token-redirect'),

    # --- 1. 인증 및 사용자 관리 (Auth & Users) ---
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/login/', views.MyTokenObtainPairView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/profile/', views.UserProfileView.as_view(), name='user-profile'),

    # --- 2. 챗봇 세션 (Chat Session) ---
    path('chat/sessions/', views.ChatSessionListCreateView.as_view(), name='chat-session-list-create'),
    path('chat/sessions/<uuid:session_id>/end/', views.ChatSessionEndView.as_view(), name='chat-session-end'),
    path('chat/sessions/<uuid:session_id>/prompts/', views.PromptLogListView.as_view(), name='prompt-log-list'),
    path('chat/sessions/<uuid:session_id>/message/', views.ChatAPIView.as_view(), name='chat-message'),
    # path('chat/prompts/<uuid:prompt_id>/results/', views.GeneratedResultListCreateView.as_view(), name='generated-result-list-create'),
    
    # --- 3. 에셋 라이브러리 ---
    path('library/assets/', views.AssetLibraryListCreateView.as_view(), name='asset-library-list-create'),
    path('library/assets/<uuid:lib_id>/comments/', views.LibraryCommentListCreateView.as_view(), name='library-comment-list-create'),

    # --- 4. 인사이트 ---
    path('insights/models/', views.InsightTrendsListView.as_view(), name='insight-trends-list'),
    path('insights/models/<uuid:car_model_id>/', views.InsightTrendsDetailView.as_view(), name='insight-trends-detail'),
    path('insights/models/<uuid:car_model_id>/specs/', views.EngineeringSpecListView.as_view(), name='engineering-spec-list'),
    path('insights/models/<uuid:car_model_id>/reviews/', views.UserReviewListView.as_view(), name='user-review-list'),
]