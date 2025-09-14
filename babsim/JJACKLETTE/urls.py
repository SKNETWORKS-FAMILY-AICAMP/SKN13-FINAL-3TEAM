# JJACKLETTE 앱 내의 API 엔드포인트들을 정의
# config/urls.py에서 이 앱의 urls.py를 include 하는 방식으로 구성
# 예: /api/items/, /api/search/ 등.

# JJACKLETTE/urls.py

from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from . import oauth_views
from config.views import chatbot_api

urlpatterns = [
    # --- 0. OAuth 콜백 처리 ---
    # OAuth 콜백 처리
    path('oauth/callback/', oauth_views.oauth_callback, name='oauth-callback'),
    # Google OAuth 콜백
    path('oauth/google/callback/', oauth_views.google_oauth_callback, name='google-oauth-callback'),
    # JWT 토큰 생성
    path('oauth/generate-token/', oauth_views.generate_jwt_token, name='generate-jwt-token'),
    # 인증된 OAuth 리다이렉트
    path('auth/token-redirect/', oauth_views.oauth_callback_authenticated, name='oauth-token-redirect'),

    # --- 1. 인증 및 사용자 관리 (Auth & Users) ---
    # 사용자 회원가입
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    # 사용자 로그인 (JWT 토큰 발급)
    path('auth/login/', views.MyTokenObtainPairView.as_view(), name='login'),
    # 사용자 로그아웃
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    # JWT 토큰 갱신
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # 사용자 프로필 조회/수정
    path('users/profile/', views.UserProfileView.as_view(), name='user-profile'),

    # --- 2. 챗봇 세션 (Chat Session) ---
    # 채팅 세션 목록 조회/생성
    path('chat/sessions/', views.ChatSessionListCreateView.as_view(), name='chat-session-list-create'),
    # 채팅 세션 삭제
    path('chat/sessions/<uuid:session_id>/delete/', views.ChatSessionDeleteView.as_view(), name='chat-session-delete'),
    # 프롬프트 로그 조회
    path('chat/sessions/<uuid:session_id>/prompts/', views.PromptLogListView.as_view(), name='prompt-log-list'),
    # 채팅 메시지 전송 (스트리밍)
    path('chat/sessions/<uuid:session_id>/message/', chatbot_api, name='chat-message'),
    # 채팅 기록 업데이트
    path('chat/sessions/<uuid:session_id>/update-history/', views.ChatHistoryUpdateView.as_view(), name='chat-history-update'),
    # 체크리스트 기반 이미지 생성
    path('chat/checklist/generate-image/', views.ChecklistImageGenerationView.as_view(), name='checklist-generate-image'),
    # path('chat/prompts/<uuid:prompt_id>/results/', views.GeneratedResultListCreateView.as_view(), name='generated-result-list-create'),
    
    # --- 3. 에셋 라이브러리 ---
    # 에셋 목록 조회/업로드
    path('library/assets/', views.AssetLibraryListCreateView.as_view(), name='asset-library-list-create'),
    # 댓글 목록 조회/생성
    path('library/assets/<uuid:lib_id>/comments/', views.LibraryCommentListCreateView.as_view(), name='library-comment-list-create'),
    # 댓글 상세/수정/삭제
    path('library/comments/<uuid:comment_id>/', views.LibraryCommentDetailView.as_view(), name='library-comment-detail'),
    # 에셋 좋아요 토글
    path('library/assets/<uuid:lib_id>/like/', views.AssetLikeToggleView.as_view(), name='asset-like-toggle'),
    # 댓글 좋아요 토글
    path('library/comments/<uuid:comment_id>/like/', views.CommentLikeToggleView.as_view(), name='comment-like-toggle'),

    # --- 4. 인사이트 ---
    # 인사이트 트렌드 목록 조회
    path('insights/models/', views.InsightTrendsListView.as_view(), name='insight-trends-list'),
    # 인사이트 트렌드 상세 조회
    path('insights/models/<uuid:car_model_id>/', views.InsightTrendsDetailView.as_view(), name='insight-trends-detail'),
    # 엔지니어링 스펙 조회
    path('insights/models/<uuid:car_model_id>/specs/', views.EngineeringSpecListView.as_view(), name='engineering-spec-list'),
    # 사용자 리뷰 조회
    path('insights/models/<uuid:car_model_id>/reviews/', views.UserReviewListView.as_view(), name='user-review-list'),
]