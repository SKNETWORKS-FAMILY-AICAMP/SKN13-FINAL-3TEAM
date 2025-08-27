# DRF의 ViewSet 또는 APIView를 활용하여 RESTful API 로직을 작성
# 클라이언트(React.js)로부터 요청을 받아 serializers.py를 통해 데이터를 처리하고,
# models.py를 통해 PostgreSQL과 상호작용하며, services.py의 비즈니스 로직을 호출

import logging
import os
import requests
import httpx
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from django.views import View 
from asgiref.sync import sync_to_async, async_to_sync
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings
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
from transformers import AutoTokenizer
from django.shortcuts import get_object_or_404
from django.utils import timezone
from dotenv import load_dotenv
from .models import *
from .serializers import *
from qdrant_client import QdrantClient
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from pipeline.services import babsim_pipeline_service

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024

class StandardResultSetPagination(PageNumberPagination):
    page_size = 10                          # 기본 페이지 사이즈
    page_size_query_param = 'page_size'     # 클라이언트가 ?page_size= 로 조절
    max_page_size = 100                     # 상한

class ChatAPIView(APIView):
    """
    사용자 채팅 요청을 처리하는 API 뷰 (동기 버전).
    1) 키워드 기반 라우팅 우선 처리
    2) 질문 의도 라우팅(일반 대화 vs RAG)
    3) 의도에 맞춰 프롬프트 구성
    4) 추론 서버 호출 후 결과 반환
    """
    permission_classes = [IsAuthenticated]

    # --- 상수/설정 ---
    QDRANT_HOST = getattr(settings, "QDRANT_HOST", "qdrant")
    QDRANT_PORT = int(getattr(settings, "QDRANT_PORT_REST", 6333))
    QDRANT_COLLECTION = getattr(settings, "QDRANT_COLLECTION", "babsim_rag_db")
    RAG_TOP_K = int(getattr(settings, "RAG_TOP_K", 5))
    INFERENCE_URL = getattr(settings, "INFERENCE_SERVER_URL", "http://inference-server:8001")
    EMBEDDING_MODEL_NAME = getattr(settings, "EMBEDDING_MODEL_NAME", "BAAI/bge-m3")
    TOKENIZER_PATH = getattr(settings, "EXAONE_MODEL_PATH", "/app/models/exaone_4.0_1.2b")

    # --- 프롬프트 템플릿 ---
    SYSTEM_PROMPT = (
        "당신은 자동차 디자인 트렌드와 역사에 정통한 '자동차 디자인 전문 AI'입니다. "
        "특히 현대자동차의 디자인 철학인 '센슈어스 스포티니스'와 '플루이딕 스컬프처'를 깊이 이해하고 있습니다. "
        "사용자의 질문에 대해, 전문 지식을 바탕으로 시각적이고 창의적인 관점에서 상세하게 설명해주세요."
    )
    GENERAL_PROMPT = (
        "당신은 친절한 AI 비서입니다. "
        "스몰톡/일반 질문에는 간결하고 자연스럽게 답하고, 현대자동차 디자인 관련 질문으로 이어질 수 있도록 돕습니다."
        "답변은 항상 한국어로 진행하세요."
    )
    ROUTING_PROMPT_TEMPLATE = (
        "당신은 사용자의 질문 의도를 분석하는 라우터 AI입니다. 주어진 질문의 종류를 \"[RAG]\" 또는 \"[GENERAL]\" 중 하나로만 분류하세요.\n\n"
        "## 지침:\n"
        "- 현대자동차의 디자인, 철학, 역사, 특정 모델 등 자동차 관련 전문 지식이 필요하면 \"[RAG]\"로 분류합니다.\n"
        "- 일상적인 대화, 인사, 날씨, 감정 표현 등 자동차와 관련 없는 일반적인 질문은 \"[GENERAL]\"로 분류합니다.\n\n"
        "--- 예시 ---\n"
        "질문: \"아이오닉 5의 파라메트릭 픽셀 디자인에 대해 알려줘.\"\n"
        "분류: \"[RAG]\"\n\n"
        "질문: \"플루이딕 스컬프처가 뭐야?\"\n"
        "분류: \"[RAG]\"\n\n"
        "질문: \"안녕?\"\n"
        "분류: \"[GENERAL]\"\n\n"
        "질문: \"오늘 날씨 어때?\"\n"
        "분류: \"[GENERAL]\"\n\n"
        "질문: \"사랑이란 무엇일까?\"\n"
        "분류: \"[GENERAL]\"\n"
        "--- 여기까지 예시 ---\n\n"
        "자, 이제 이 질문을 분류하세요.\n"
        "질문: \"{user_prompt}\"\n"
        "분류: "
    )

    TOKENIZER = None
    EMBEDDER = None
    try:
        TOKENIZER = AutoTokenizer.from_pretrained(TOKENIZER_PATH, trust_remote_code=True)
        logger.info("ChatAPIView: 토크나이저 로딩 성공 (%s)", TOKENIZER_PATH)
    except Exception as e:
        logger.error("ChatAPIView: 토크나이저 로딩 실패: %s", e, exc_info=True)

    try:
        EMBEDDER = HuggingFaceBgeEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        logger.info("ChatAPIView: 임베딩 모델 로딩 성공 (%s)", EMBEDDING_MODEL_NAME)
    except Exception as e:
        logger.error("ChatAPIView: 임베딩 모델 로딩 실패: %s", e, exc_info=True)

    def _call_inference_with_retry(
        self,
        prompt: str,
        *,
        max_new_tokens: Optional[int] = None,
        timeout: float = 60.0,
        retries: int = 3,
        backoff_seconds: float = 0.8,
    ) -> str:
        last_err: Optional[Exception] = None
        for attempt in range(1, retries + 1):
            if attempt > 1:
                delay = backoff_seconds * (2 ** (attempt - 2))
                logger.warning("Inference 재시도 %d/%d, %.1fs 대기...", attempt, retries, delay)
                time.sleep(delay)

            try:
                payload = {"prompt": prompt}

                if "라우터 AI" in prompt:
                    payload["do_sample"] = False
                # --------------------------------------------------------------------

                if max_new_tokens is not None:
                    payload["max_new_tokens"] = max_new_tokens

                with httpx.Client(timeout=timeout) as client:
                    resp = client.post(f"{self.INFERENCE_URL}/generate-text", json=payload)
                    resp.raise_for_status()
                    return resp.json().get("generated_text", "").strip()

            except httpx.RequestError as e:
                last_err = e
                logger.warning("Inference 호출 실패 (attempt %d/%d): %s", attempt, retries, e)
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                if 500 <= status_code < 600 and attempt < retries:
                    last_err = e
                    logger.warning("Inference 5xx 응답 (attempt %d/%d): %s", attempt, retries, e)
                    continue
                raise

        assert last_err is not None
        raise last_err

    def post(self, request, *args, **kwargs):
        user_prompt = request.data.get("message")
        session_id = request.data.get("session_id")

        if not user_prompt or not session_id:
            return Response(
                {"error": "세션 ID와 메시지를 모두 입력해주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # 사용자 이메일 가져오기
            user_email = request.user.email if request.user.is_authenticated else "anonymous@example.com"
            
            # Pipeline 서비스를 사용하여 메시지 처리
            logger.info("Pipeline을 사용하여 메시지 처리 시작: %s", user_prompt[:50])
            
            result = babsim_pipeline_service.process_user_message(user_email, user_prompt)
            
            if 'error' in result:
                logger.error("Pipeline 처리 실패: %s", result['error'])
                return Response(
                    {"error": result['error']},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            
            # 기존 세션과 연결하여 DB 저장
            try:
                session = ChatSession.objects.get(session_id=session_id, user=request.user)
                PromptLog.objects.create(
                    session=session, 
                    user_prompt=user_prompt, 
                    ai_response=result['response']
                )
                logger.info("DB 저장 성공: 세션 ID %s", session_id)
            except ChatSession.DoesNotExist:
                logger.error("DB 저장 실패: 세션 ID(%s)를 찾을 수 없습니다.", session_id)
            except Exception as e:
                logger.error("DB 저장 중 예외 발생: %s", e, exc_info=True)

            # 응답 데이터 구성
            response_data = {
                "success": True, 
                "response": result['response'],
                "intent": result.get('intent', ''),
                "is_form_complete": result.get('is_form_complete', False),
                "image_query": result.get('image_query', ''),
                "generatedResults": []
            }
            
            logger.info("Pipeline 처리 완료: 의도=%s, 폼완성=%s", 
                       result.get('intent', ''), result.get('is_form_complete', False))
            
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Pipeline 처리 중 예외 발생: %s", str(e))
            return Response(
                {"error": "요청 처리 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # except httpx.RequestError as e:
        #     logger.error(f"Inference 서버 연결 실패: {e}")
        #     return Response(
        #         {"error": f"inference 서버 연결 실패: {e}"},
        #         status=status.HTTP_502_BAD_GATEWAY,
        #     )
        # except httpx.HTTPStatusError as e:
        #     code = getattr(e.response, "status_code", "unknown")
        #     logger.error(f"Inference 서버 오류: {code}")
        #     return Response(
        #         {"error": f"inference 서버 오류: {code}"},
        #         status=status.HTTP_502_BAD_GATEWAY,
        #     )
        # except ChatSession.DoesNotExist:
        #     return Response(
        #         {"error": "유효하지 않은 세션 ID입니다."},
        #         status=status.HTTP_404_NOT_FOUND,
        #     )
        # except Exception as e:
        #     logger.exception("AI 모델 처리 중 오류 발생")
        #     return Response(
        #         {"error": f"AI 모델 처리 중 오류가 발생했습니다: {str(e)}"},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     )
# ---------------------------------------------------------------------
        
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

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
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
    
