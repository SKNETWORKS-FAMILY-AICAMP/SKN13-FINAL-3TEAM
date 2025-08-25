# DRF의 ViewSet 또는 APIView를 활용하여 RESTful API 로직을 작성
# 클라이언트(React.js)로부터 요청을 받아 serializers.py를 통해 데이터를 처리하고,
# models.py를 통해 PostgreSQL과 상호작용하며, services.py의 비즈니스 로직을 호출

import logging
import os
import requests
import httpx
from datetime import datetime
from pathlib import Path
from asgiref.sync import async_to_sync
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
from langchain_openai import OpenAIEmbeddings
logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIM = 3072 

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다. RAG 기능이 비활성화됩니다.")


try:
    BASE_DIR = settings.BASE_DIR  # 보통 manage.py가 있는 경로
except Exception:
    # settings에 BASE_DIR이 없다면 views.py 기준으로 추정
    BASE_DIR = Path(__file__).resolve().parent.parent

ENV_PATH = Path(BASE_DIR) / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH, override=False)
else:
    logger.warning("RAG .env 파일을 찾지 못했습니다: %s", ENV_PATH)

# .env에서 OpenAI 키 로드
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY가 .env에서 로드되지 않았습니다. (RAG 임베딩은 건너뜁니다)")


class StandardResultSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ChatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    try:
        TOKENIZER = AutoTokenizer.from_pretrained(settings.EXAONE_MODEL_PATH, trust_remote_code=True)
        logger.info("ChatAPIView: 토크나이저 로딩 성공")
    except Exception as e:
        TOKENIZER = None
        logger.error("ChatAPIView: 토크나이저 로딩 실패: %s", e, exc_info=True)

    # 자동차 전용 System Prompt
    SYSTEM_PROMPT = (
        "당신은 자동차 디자인 트렌드와 역사에 정통한 '자동차 디자인 전문 AI'입니다. "
        "특히 현대자동차의 디자인 철학인 '센슈어스 스포티니스'와 '플루이딕 스컬프처'를 깊이 이해하고 있습니다. "
        "사용자의 질문에 대해, 전문 지식을 바탕으로 시각적이고 창의적인 관점에서 상세하게 설명해주세요."
    )
    # General fallback System Prompt
    GENERAL_PROMPT = (
        "당신은 현대자동차와 관련하여 지식이 풍부하고 친절한 AI 비서입니다. "
        "사용자의 현대자동차 관련 질문에 대해 자연스럽고 도움이 되는 답변을 해주세요."
        "답변은 항상 한국어로 진행하세요."
    )

    QDRANT_HOST = getattr(settings, "QDRANT_HOST", "qdrant")
    QDRANT_PORT = int(getattr(settings, "QDRANT_PORT_REST", 6333))
    QDRANT_COLLECTION = "babsim_rag_db"
    RAG_TOP_K = 5
    INFERENCE_URL = getattr(settings, "INFERENCE_SERVER_URL", "http://inference-server:8001")
    EMBEDDING_MODEL = "text-embedding-3-large"

    def post(self, request, *args, **kwargs):
        if not self.TOKENIZER:
            return Response({"error": "서버 내부 오류: 토크나이저가 로드되지 않았습니다."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        user_prompt = request.data.get("message")
        session_id = request.data.get("session_id")

        if not user_prompt or not session_id:
            return Response({"error": "세션 ID와 메시지를 모두 입력해주세요."},
                            status=status.HTTP_400_BAD_REQUEST)

        query_vec, context_str = None, ""
        if OPENAI_API_KEY:
            try:
                oai = OpenAIEmbeddings(api_key=OPENAI_API_KEY, model=self.EMBEDDING_MODEL)
                query_vec = oai.embed_query(user_prompt)

                qdrant = QdrantClient(host=self.QDRANT_HOST, port=self.QDRANT_PORT)
                search_res = qdrant.search(
                    collection_name=self.QDRANT_COLLECTION,
                    query_vector=query_vec, limit=self.RAG_TOP_K, with_payload=True
                )
                contexts = [(pt.payload or {}).get("text", "").strip()
                            for pt in search_res if (pt.payload or {}).get("text", "").strip()]
                if contexts:
                    context_str = "\n\n".join(contexts)
                    logger.info(f"RAG contexts found: {contexts}")
            except Exception as e:
                logger.warning("RAG 파이프라인 실패 → 일반 생성으로 전환: %s", e, exc_info=True)
        else:
            logger.warning("OPENAI_API_KEY 미설정 → RAG를 건너뜁니다.")

        # ----- 핵심 로직: contexts 여부에 따른 프롬프트 분기 -----
        messages = []
        if context_str:
            # RAG 모드 (자동차 전용 system prompt + context 포함)
            rag_prompt_content = (
                f"아래 컨텍스트를 참고해 질문에 답하세요.\n\n"
                f"### 컨텍스트:\n{context_str}\n\n### 질문:\n{user_prompt}"
            )
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": rag_prompt_content},
            ]
        else:
            # General fallback 모드
            messages = [
                {"role": "system", "content": self.GENERAL_PROMPT},
                {"role": "user", "content": user_prompt},
            ]

        chat_text = self.TOKENIZER.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=False
        )
        final_prompt = f"{chat_text.rstrip()}\n\n### Assistant:"

        # Inference Server 호출
        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(f"{self.INFERENCE_URL}/generate-text",
                                   json={"prompt": final_prompt})
                resp.raise_for_status()
                text_answer = resp.json().get("generated_text", "")

                # 시스템 프롬프트가 혹시라도 포함되면 제거
                if self.SYSTEM_PROMPT in text_answer:
                    text_answer = text_answer.replace(self.SYSTEM_PROMPT, "").strip()
                if self.GENERAL_PROMPT in text_answer:
                    text_answer = text_answer.replace(self.GENERAL_PROMPT, "").strip()
        except Exception as e:
            logger.exception("Inference 서버 통신 중 예외 발생")
            return Response({"error": f"AI 모델 서버와 통신 중 오류가 발생했습니다: {str(e)}"},
                            status=500)

        # 로그 저장 및 최종 응답
        try:
            session = ChatSession.objects.get(session_id=session_id, user=request.user)
            PromptLog.objects.create(session=session, user_prompt=user_prompt, ai_response=text_answer)
        except Exception as e:
            logger.exception("DB 저장 실패")

        return Response({"success": True, "response": text_answer, "generatedResults": []},
                        status=200)
    
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
    
