# DRF의 ViewSet 또는 APIView를 활용하여 RESTful API 로직을 작성
# 클라이언트(React.js)로부터 요청을 받아 serializers.py를 통해 데이터를 처리하고,
# models.py를 통해 PostgreSQL과 상호작용하며, services.py의 비즈니스 로직을 호출

import requests
from datetime import datetime
from rest_framework.pagination import PageNumberPagination
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone

from .models import *
from .serializers import *

class StandardResultSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

INFERENCE_SERVER_URL = "http://inference-server:8001"

class ChatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_prompt = request.data.get('message')
        session_id = request.data.get('session_id')

        if not user_prompt or not session_id:
            return Response({"error": "세션 ID와 메시지를 모두 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. 실제 LLM 호출
            text_answer = ai_services.generate_text(user_prompt)

            # 2. 실제 Stable Diffusion 호출
            generated_image = ai_services.generate_image(text_answer)   

            # 3. 이미지 저장 및 URL 받기
            image_url = ai_services.save_image_and_get_url(generated_image)

            # 4. 대화 기록 저장
            session = ChatSession.objects.get(session_id=session_id, user_id=request.user)
            prompt_log = PromptLog.objects.create(
                session_id=session, user_prompt=user_prompt, ai_response=text_answer
            )
            GeneratedResult.objects.create(
                prompt_id=prompt_log, result_type='image', result_path=image_url, result=text_answer
            )

            # 5. 최종 응답 반환
            return Response({
                "text_answer": text_answer,
                "image_url": image_url
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"AI 모델 처리 중 오류 발생: {e}")
            return Response({"error": "AI 모델 처리 중 오류가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# -----------------------------------------------------------------------
        
# --- 공통 응답 (변경 없음) ---
def ok(data=None, code=200): return Response(data or {}, status=code)
def created(data=None): return Response(data or {}, status=201)

# 회원가입
class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"message": "회원가입이 완료되었습니다.", "user": UserDetailSerializer(user).data}, status=status.HTTP_201_CREATED)
    
# 로그인
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

# 로그아웃 (토큰 블랙리스트 방식)
class LogoutView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "로그아웃 성공"}, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    def get_object(self): return self.request.user
    def get_serializer_class(self):
        return UserUpdateSerializer if self.request.method in ['PUT', 'PATCH'] else UserDetailSerializer
    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response({"message": "유저 정보가 업데이트되었습니다.", "user": UserDetailSerializer(self.get_object()).data})


# --- 채팅 API 뷰 ---
class ChatSessionListCreateView(generics.ListCreateAPIView):
    """2.1 유저별 세션 조회 (GET) 및 2.2 세션 생성 (POST)"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChatSessionSerializer
    pagination_class = StandardResultSetPagination
    def get_queryset(self):
        return self.request.user.chat_sessions.all().order_by('-started_at')
    def perform_create(self, serializer): serializer.save(user=self.request.user)
    
class ChatSessionEndView(generics.UpdateAPIView):
    """2.3 챗봇 세션 종료"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChatSessionSerializer # 응답용
    lookup_field = 'session_id'
    def get_queryset(self): return self.request.user.chat_sessions.all()
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.ended_at = datetime.now()
        instance.save()
        return Response({"message": "세션이 종료되었습니다.", "session": self.get_serializer(instance).data})

# 특정 세션의 프롬프트(대화) 내역 조회 API (/api/chat/sessions/<uuid:session_id>/prompts/)
# --- 3 & 4. 프롬프트와 결과 (가장 중요한 수정 부분) ---
class PromptLogListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PromptLogSerializer
    pagination_class = StandardResultSetPagination

    def get_queryset(self):
        session_id = self.kwargs.get('session_id')
        if not session_id: return PromptLog.objects.none()
        return PromptLog.objects.filter(session__user=self.request.user, session_id=session_id).order_by('created_at')

    # create 메서드를 AI 서버와 통신하도록 완전히 수정합니다.
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 1. 사용자 프롬프트를 DB에 먼저 저장합니다.
        prompt_log = serializer.save()
        
        # 2. (RAG) 향후 이 부분에 Qdrant, DB, 웹 검색으로 컨텍스트를 보강하는 로직이 들어갑니다.
        # context_data = retrieve_context(prompt_log.user_prompt)

        try:
            # --- 텍스트 생성 요청 ---
            sllm_prompt = f"..."
            response = requests.post(...)
            response.raise_for_status()
            ai_query = response.json().get("generated_text", "")
            
            # [수정] 텍스트 결과는 PromptLog 테이블에 저장
            prompt_log.ai_response = ai_query
            prompt_log.save()

            # --- 이미지 생성 요청 ---
            img_response = requests.post(
                f"{INFERENCE_SERVER_URL}/generate-image",
                json={"prompt": ai_query},
                timeout=300.0
            )
            img_response.raise_for_status()
            # AI 서버는 이제 상대 경로를 반환합니다. (예: 'generated_images/2025/08/18/uuid.png')
            relative_image_path = img_response.json().get("image_path", "")

            # [수정] 이미지 결과는 GeneratedResult 테이블에 'URL'로 저장
            generated_result = GeneratedResult.objects.create(
                prompt=prompt_log,
                result_type="image",
                # settings.MEDIA_URL을 사용하여 완전한 URL 경로를 만들어 저장합니다.
                # 예: '/media/generated_images/2025/08/18/uuid.png'
                result_path=f"{settings.MEDIA_URL}{relative_image_path}",
                # 텍스트 결과는 이제 PromptLog에 있으므로 여기서는 비워둡니다.
                result="" 
            )
            
        except requests.exceptions.RequestException as e:
            # AI 서버와 통신 자체를 실패했을 때의 에러 처리
            return Response({"error": f"AI 서버와 통신할 수 없습니다: {e}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            # 그 외 모든 예외 상황에 대한 에러 처리
            return Response({"error": f"AI 모델 처리 중 알 수 없는 오류가 발생했습니다: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 7. 모든 작업이 성공하면, 최종 결과를 React에 반환합니다.
        final_response_data = {
            "prompt_log": PromptLogSerializer(prompt_log).data,
            "generated_result": GeneratedResultSerializer(generated_result).data
        }
        return Response(final_response_data, status=status.HTTP_201_CREATED)

# 텍스트, 이미지 생성 결과 조회 및 저장 API
class GeneratedResultListCreateView(generics.ListCreateAPIView):
    """4.1 프롬프트별 결과 조회 (GET) 및 4.2 결과 저장 (POST)"""
    permission_classes = [IsAuthenticated]
    serializer_class = GeneratedResultSerializer
    def get_queryset(self):
        prompt_id = self.kwargs.get('prompt_id')
        if not prompt_id: return GeneratedResult.objects.none()
        return GeneratedResult.objects.filter(prompt__session__user=self.request.user, prompt_id=prompt_id)

# --- 5 & 6. 라이브러리와 댓글 ---
class AssetLibraryListCreateView(generics.ListCreateAPIView):
    """5.1 자료 목록 조회 (GET) 및 5.2 자료 업로드 (POST)"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [SearchFilter]
    search_fields = ['documents']
    pagination_class = StandardResultSetPagination
    def get_serializer_class(self):
        return AssetLibraryCreateSerializer if self.request.method == 'POST' else AssetLibrarySerializer
    def get_queryset(self): return AssetLibrary.objects.all().order_by('-lib_id')
    def perform_create(self, serializer): serializer.save(user=self.request.user)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(user=self.request.user)
        return Response(AssetLibrarySerializer(instance).data, status=status.HTTP_201_CREATED)

class LibraryCommentListCreateView(generics.ListCreateAPIView):
    """6.1 댓글 조회 (GET) 및 6.2 댓글 작성 (POST)"""
    permission_classes = [IsAuthenticated]
    serializer_class = LibraryCommentsSerializer
    def get_queryset(self): return LibraryComments.objects.filter(library_asset_id=self.kwargs.get('lib_id')).order_by('-created_at')
    def perform_create(self, serializer): serializer.save(user=self.request.user)

# --- 7-11. 인사이트 ---
class InsightTrendsListView(generics.ListAPIView):
    """7.1 차량 모델 목록 조회"""
    permission_classes = [IsAuthenticated]
    serializer_class = InsightTrendsSerializer
    queryset = InsightTrends.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type', 'release_year']
    pagination_class = StandardResultSetPagination

class InsightTrendsDetailView(generics.RetrieveAPIView):
    """7.2 특정 차량 모델 상세 정보"""
    permission_classes = [IsAuthenticated]
    serializer_class = InsightTrendsDetailSerializer
    queryset = InsightTrends.objects.all().prefetch_related('design_materials', 'engineering_specs', 'sales_stats', 'user_reviews')
    lookup_field = 'car_model_id'

class DesignMaterialListView(generics.ListAPIView):
    """8.1 차량별 디자인 재질 정보 조회"""
    permission_classes = [IsAuthenticated]; serializer_class = DesignMaterialSerializer; filter_backends = [DjangoFilterBackend]; filterset_fields = ['material_type', 'usage_area']
    def get_queryset(self): return DesignMaterial.objects.filter(car_model_id=self.kwargs['car_model_id'])

class EngineeringSpecListView(generics.ListAPIView):
    """9.1 차량별 공학적 스펙 조회"""
    permission_classes = [IsAuthenticated]; serializer_class = EngineeringSpecSerializer
    def get_queryset(self): return EngineeringSpec.objects.filter(car_model_id=self.kwargs['car_model_id'])

class SalesStatListView(generics.ListAPIView):
    """10.1 차량별 판매 통계 조회"""
    permission_classes = [IsAuthenticated]; serializer_class = SalesStatSerializer; filter_backends = [DjangoFilterBackend]; filterset_fields = ['year', 'month']
    def get_queryset(self): return SalesStat.objects.filter(car_model_id=self.kwargs['car_model_id']).order_by('-year', '-month')

class UserReviewListView(generics.ListAPIView):
    """11.1 차량별 사용자 리뷰 조회"""
    permission_classes = [IsAuthenticated]; serializer_class = UserReviewSerializer
    def get_queryset(self):
        queryset = UserReview.objects.filter(car_model_id=self.kwargs['car_model_id'])
        min_s = self.request.query_params.get('sentiment_score_min'); max_s = self.request.query_params.get('sentiment_score_max')
        if min_s: queryset = queryset.filter(sentiment_score__gte=min_s)
        if max_s: queryset = queryset.filter(sentiment_score__lte=max_s)
        return queryset
    
