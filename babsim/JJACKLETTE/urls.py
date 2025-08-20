# JJACKLETTE 앱 내의 API 엔드포인트들을 정의
# config/urls.py에서 이 앱의 urls.py를 include 하는 방식으로 구성
# 예: /api/items/, /api/search/ 등.

# JJACKLETTE/urls.py

from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # --- 1. 인증 및 사용자 관리 (Auth & Users) ---
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/login/', views.MyTokenObtainPairView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/profile/', views.UserProfileView.as_view(), name='user-profile'),

    # --- 2. 챗봇 세션 (Chat Session) ---
    path('chat/sessions/', views.ChatSessionListCreateView.as_view(), name='chat-session-list-create'),
    path('chat/sessions/<uuid:session_id>/end/', views.ChatSessionEndView.as_view(), name='chat-session-end'),
    
    # --- 3. 프롬프트 로그 (Prompt Log) ---
    path('chat/sessions/<uuid:session_id>/prompts/', views.PromptLogListCreateView.as_view(), name='prompt-log-list-create'),
    
    # --- 4. 생성 결과 (Generated Result) ---
    path('chat/prompts/<uuid:prompt_id>/results/', views.GeneratedResultListCreateView.as_view(), name='generated-result-list-create'),

    # --- 5. 디자인 자료 라이브러리 (Asset Library) ---
    path('library/assets/', views.AssetLibraryListCreateView.as_view(), name='asset-library-list-create'),

    # --- 6. 라이브러리 댓글 (Library Comments) ---
    path('library/assets/<uuid:lib_id>/comments/', views.LibraryCommentListCreateView.as_view(), name='library-comment-list-create'),

    # --- 7. 인사이트 - 차량 모델 (Insight Trends) ---
    path('insights/models/', views.InsightTrendsListView.as_view(), name='insight-trends-list'),
    path('insights/models/<uuid:car_model_id>/', views.InsightTrendsDetailView.as_view(), name='insight-trends-detail'),
    
    # --- 8, 9, 10, 11. 차량 상세 정보 ---
    path('insights/models/<uuid:car_model_id>/materials/', views.DesignMaterialListView.as_view(), name='design-material-list'),
    path('insights/models/<uuid:car_model_id>/specs/', views.EngineeringSpecListView.as_view(), name='engineering-spec-list'),
    path('insights/models/<uuid:car_model_id>/sales/', views.SalesStatListView.as_view(), name='sales-stat-list'),
    path('insights/models/<uuid:car_model_id>/reviews/', views.UserReviewListView.as_view(), name='user-review-list'),
    
]