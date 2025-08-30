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
from pipeline.llm_provider import generate_vllm_response

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
    TOKENIZER_PATH = getattr(settings, "KANANA_MODEL_PATH", "/app/models/kanana-1.5-8b-instruct-2505")

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

    # TOKENIZER = None
    # EMBEDDER = None
    # try:
    #     TOKENIZER = AutoTokenizer.from_pretrained(TOKENIZER_PATH, trust_remote_code=True)
    #     logger.info("ChatAPIView: 토크나이저 로딩 성공 (%s)", TOKENIZER_PATH)
    # except Exception as e:
    #     logger.error("ChatAPIView: 토크나이저 로딩 실패: %s", e, exc_info=True)

    # try:
    #     EMBEDDER = HuggingFaceBgeEmbeddings(
    #         model_name=EMBEDDING_MODEL_NAME,
    #         model_kwargs={'device': 'cpu'},
    #         encode_kwargs={'normalize_embeddings': True}
    #     )
    #     logger.info("ChatAPIView: 임베딩 모델 로딩 성공 (%s)", EMBEDDING_MODEL_NAME)
    # except Exception as e:
    #     logger.error("ChatAPIView: 임베딩 모델 로딩 실패: %s", e, exc_info=True)

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
        if not self.TOKENIZER or not self.EMBEDDER:
            return Response(
                {"error": "서버 내부 오류: 필수 모델이 로드되지 않았습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        user_prompt = request.data.get("message")
        session_id = request.data.get("session_id")

        if not user_prompt or not session_id:
            return Response(
                {"error": "세션 ID와 메시지를 모두 입력해주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            GENERAL_KEYWORDS = ["안녕", "누구야", "뭐해", "이름", "날씨", "고마워", "도와줘", "고맙", "땡큐"]
            intent = "[GENERAL]"  # 기본값을 GENERAL로 미리 설정

            # 정의된 키워드가 질문에 포함되어 있지 않은 경우에만 LLM 라우터를 호출
            if not any(keyword in user_prompt for keyword in GENERAL_KEYWORDS):
                logger.info("키워드를 찾지 못해 LLM 라우터를 호출합니다...")
                routing_prompt = self.ROUTING_PROMPT_TEMPLATE.format(user_prompt=user_prompt)
                intent_result = self._call_inference_with_retry(
                    routing_prompt, max_new_tokens=10, timeout=30.0
                )
                if "[RAG]" in intent_result:
                    intent = "[RAG]"
            # 키워드가 있으면, 기본값인 [GENERAL]을 그대로 사용
            # -------------------------------------------
            
            logger.info("최종 의도 '%s...': %s", user_prompt[:50], intent)

            if intent == "[RAG]":
                logger.info("RAG 검색을 수행합니다...")
                query_vec: List[float] = self.EMBEDDER.embed_query(user_prompt)
                qdrant = QdrantClient(host=self.QDRANT_HOST, port=self.QDRANT_PORT)
                search_res = qdrant.search(
                    collection_name=self.QDRANT_COLLECTION,
                    query_vector=query_vec,
                    limit=self.RAG_TOP_K,
                    with_payload=True,
                )
                contexts = [
                    (pt.payload or {}).get("page_content", "").strip()
                    for pt in search_res
                    if (pt.payload or {}).get("page_content", "").strip()
                ]
                context_str = "\n\n".join(contexts) if contexts else "관련 정보를 찾지 못했습니다."
                RAG_USER_PROMPT_TEMPLATE = """
                아래의 [컨텍스트]를 바탕으로 사용자의 [질문]에 대해 답변해 주세요.

                [지시사항]
                1. 답변은 반드시 한국어로만 작성하세요. 영어 단어는 절대 사용하지 마세요.
                2. [컨텍스트]의 핵심 내용을 세 가지 항목으로 요약하여 불렛 포인트(-)로 정리해 주세요.
                3. 각 항목은 간결하고 명확한 문장으로 설명해야 합니다. 
                4. 불필요한 서론이나 결론 없이 핵심 요약 내용만 바로 제시해 주세요.

                [컨텍스트]
                {context}

                [질문]
                {question}
                """
                messages = [
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": RAG_USER_PROMPT_TEMPLATE.format(
                            context=context_str,
                            question=user_prompt
                        )
                    },
                ]
            else: # intent == "[GENERAL]"
                logger.info("일반 응답을 생성합니다...")
                messages = [
                    {"role": "system", "content": self.GENERAL_PROMPT},
                    {"role": "user", "content": user_prompt},
                ]

            chat_text = self.TOKENIZER.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=False
            )
            final_prompt = f"{chat_text.rstrip()}\n\n### Assistant:"
            text_answer = self._call_inference_with_retry(
                final_prompt, timeout=120.0
            )

        except httpx.RequestError as e:
            logger.exception("Inference 서버 통신 중 예외 발생: %s", str(e))
            return Response(
                {"error": "AI 모델 서버와 통신 중 오류가 발생했습니다."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            logger.exception("전체 파이프라인 처리 중 예외 발생: %s", str(e))
            return Response(
                {"error": "요청 처리 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            session = ChatSession.objects.get(session_id=session_id, user=request.user)
            PromptLog.objects.create(
                session=session, user_prompt=user_prompt, ai_response=text_answer
            )
        except ChatSession.DoesNotExist:
            logger.error("DB 저장 실패: 세션 ID(%s)를 찾을 수 없습니다.", session_id)
        except Exception as e:
            logger.error("DB 저장 중 예외 발생: %s", e, exc_info=True)

        # 5) 최종 응답
        return Response(
            {"success": True, "response": text_answer, "generatedResults": []},
            status=status.HTTP_200_OK,
        )

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
    permission_classes = [IsAuthenticated]
    serializer_class = ChatSessionSerializer
    pagination_class = StandardResultSetPagination
    def get_queryset(self):
        return self.request.user.chat_sessions.all().order_by('-started_at')
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, session_title=self.request.data.get('session_title', 'New Chat'))
    
class ChatSessionEndView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatSessionSerializer
    lookup_field = 'session_id'
    def get_queryset(self): return self.request.user.chat_sessions.all()
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.ended_at = datetime.now()
        instance.save()
        return Response({"message": "세션이 종료되었습니다.", "session": self.get_serializer(instance).data})

class PromptLogListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PromptLogSerializer
    pagination_class = StandardResultSetPagination
    def get_queryset(self):
        session_id = self.kwargs.get('session_id')
        return PromptLog.objects.filter(session__user=self.request.user, session_id=session_id).order_by('created_at')

# --- 5 & 6. 라이브러리와 댓글 ---
class AssetLibraryListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AssetLibrarySerializer 
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [SearchFilter]
    search_fields = ['title', 'summary', 'category']
    pagination_class = StandardResultSetPagination
    def get_queryset(self): 
        return AssetLibrary.objects.all().order_by('-created_at')
    def perform_create(self, serializer): 
        serializer.save(user=self.request.user)

class LibraryCommentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LibraryCommentsSerializer
    def get_queryset(self): 
        return LibraryComments.objects.filter(asset_library_id=self.kwargs.get('lib_id')).order_by('-created_at')
    def perform_create(self, serializer):
        asset_library = get_object_or_404(AssetLibrary, lib_id=self.kwargs.get('lib_id'))
        serializer.save(user=self.request.user, asset_library=asset_library)

# --- 7-11. 인사이트 ---
class InsightTrendsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InsightTrendsSerializer
    queryset = InsightTrends.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['type', 'release_year']
    search_fields = ['car_name']
    pagination_class = StandardResultSetPagination

class InsightTrendsDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InsightTrendsDetailSerializer
    queryset = InsightTrends.objects.all().prefetch_related('engineering_specs', 'user_reviews', 'recent_articles')
    lookup_field = 'car_model_id'

class EngineeringSpecListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EngineeringSpecSerializer
    def get_queryset(self): return EngineeringSpec.objects.filter(car_model_id=self.kwargs['car_model_id'])

class UserReviewListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserReviewSerializer
    def get_queryset(self): 
        return UserReview.objects.filter(car_model_id=self.kwargs['car_model_id'])