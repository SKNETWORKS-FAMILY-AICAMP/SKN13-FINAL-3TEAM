# DRF의 ViewSet 또는 APIView를 활용하여 RESTful API 로직을 작성
# 클라이언트(React.js)로부터 요청을 받아 serializers.py를 통해 데이터를 처리하고,
# models.py를 통해 PostgreSQL과 상호작용하며, services.py의 비즈니스 로직을 호출

import logging
import os
import requests
import httpx
import time
import boto3
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
from pipeline.services import babsim_pipeline_service
from .services import get_chatbot_response # Added for vLLM integration

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024

class StandardResultSetPagination(PageNumberPagination):
    page_size = 10                          # 기본 페이지 사이즈
    page_size_query_param = 'page_size'     # 클라이언트가 ?page_size= 로 조절
    max_page_size = 100                     # 상한

# class ChatAPIView(APIView):
    """
    사용자 채팅 요청을 처리하는 API 뷰 (동기 버전).
    1) 키워드 기반 라우팅 우선 처리
    2) 질문 의도 라우팅(일반 대화 vs RAG)
    3) 의도에 맞춰 프롬프트 구성
    4) 추론 서버 호출 후 결과 반환
    """
    permission_classes = [AllowAny] # Temporarily set to AllowAny for testing vLLM integration

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
        "- 현대자동차의 디자인, 철학, 역사, 특정 모델 등 자동차 관련 전문 지식이 필요하면 \"[RAG]\"로 분류합니다.\\n"
        "- 일상적인 대화, 인사, 날씨, 감정 표현 등 자동차와 관련 없는 일반적인 질문은 \"[GENERAL]\"로 분류합니다.\\n\n"
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


    # def _call_inference_with_retry(
    #     self,
    #     prompt: str,
    #     *,
    #     max_new_tokens: Optional[int] = None,
    #     timeout: float = 60.0,
    #     retries: int = 3,
    #     backoff_seconds: float = 0.8,
    # ) -> str:
    #     last_err: Optional[Exception] = None
    #     for attempt in range(1, retries + 1):
    #         if attempt > 1:
    #             delay = backoff_seconds * (2 ** (attempt - 2))
    #             logger.warning("Inference 재시도 %d/%d, %.1fs 대기...", attempt, retries, delay)
    #             time.sleep(delay)

    #         try:
    #             payload = {"prompt": prompt}

    #             if "라우터 AI" in prompt:
    #                 payload["do_sample"] = False
    #             # --------------------------------------------------------------------

    #             if max_new_tokens is not None:
    #                 payload["max_new_tokens"] = max_new_tokens

    #             with httpx.Client(timeout=timeout) as client:
    #                 resp = client.post(f"{self.INFERENCE_URL}/generate-text", json=payload)
    #                 resp.raise_for_status()
    #                 return resp.json().get("generated_text", "").strip()

    #         except httpx.RequestError as e:
    #             last_err = e
    #             logger.warning("Inference 호출 실패 (attempt %d/%d): %s", attempt, retries, e)
    #         except httpx.HTTPStatusError as e:
    #             status_code = e.response.status_code
    #             if 500 <= status_code < 600 and attempt < retries:
    #                 last_err = e
    #                 logger.warning("Inference 5xx 응답 (attempt %d/%d): %s", attempt, retries, e)
    #                 continue
    #             raise

    #     assert last_err is not None
    #     raise last_err

    def post(self, request, *args, **kwargs):
        user_prompt = request.data.get("message")
        session_id = kwargs.get("session_id")  # URL 파라미터에서 가져오기
        checklist_data = request.data.get("checklistData", {})
        completion_status = request.data.get("completionStatus", {})

        if not session_id:
            return Response(
                {"error": "세션 ID를 입력해주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # 파이프라인 서비스를 사용하여 완전한 AI 응답 생성
            # logger.info(f"파이프라인 처리 시작: {user_prompt}")
            # logger.info(f"체크리스트 데이터: {checklist_data}")
            # logger.info(f"완성도 상태: {completion_status}")
            
            # 파이프라인 서비스 호출 (체크리스트 데이터 포함)
            pipeline_result = babsim_pipeline_service.process_query(
                user_prompt, 
                user_id=session_id,  # session_id를 user_id로 사용
                checklist_data=checklist_data,
                completion_status=completion_status
            )
            
            # 파이프라인 결과에서 응답 추출
            if pipeline_result and 'response' in pipeline_result:
                text_answer = pipeline_result['response']
                generated_results = pipeline_result.get('generated_results', [])
                pipeline_completion_status = pipeline_result.get('completion_status', {})
            else:
                # 파이프라인 실패 시 폴백
                logger.warning("파이프라인 처리 실패, 폴백 응답 사용")
                text_answer = get_chatbot_response(user_prompt)
                generated_results = []
                pipeline_completion_status = {}

            # Log the prompt and response (인증된 사용자만)
            if request.user.is_authenticated:
                try:
                    session = ChatSession.objects.get(session_id=session_id, user=request.user)
                    PromptLog.objects.create(
                        session=session, user_prompt=user_prompt, ai_response=text_answer
                    )
                except ChatSession.DoesNotExist:
                    logger.error("DB 저장 실패: 세션 ID(%s)를 찾을 수 없습니다.", session_id)
                except Exception as e:
                    logger.error("DB 저장 중 예외 발생: %s", e, exc_info=True)
            else:
                logger.info("인증되지 않은 사용자 - DB 저장 건너뜀")

            # Final response with completion status and checklist data
            response_data = {
                "success": True, 
                "ai_response": text_answer, 
                "generated_results": generated_results,
                "completion_status": pipeline_completion_status,
                "auto_retry": pipeline_completion_status.get('auto_retry', False) if pipeline_completion_status else False
            }
            
            # 체크리스트 데이터가 있으면 응답에 포함
            if pipeline_completion_status and 'checklist_data' in pipeline_completion_status:
                response_data["completion_status"]["checklist_data"] = pipeline_completion_status['checklist_data']
            
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"ChatAPIView 처리 중 오류 발생: {e}")
            return Response(
                {"error": f"요청 처리 중 오류가 발생했습니다: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
    
class ChatSessionDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatSessionSerializer
    lookup_field = 'session_id'
    
    def get_queryset(self):
        return self.request.user.chat_sessions.all()
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        session_id = instance.session_id
        instance.delete()
        return Response({"message": "세션이 삭제되었습니다.", "session_id": str(session_id)}, status=status.HTTP_200_OK)

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
    def upload_to_s3(self, file, folder, filename):
        """S3에 파일 업로드"""
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            
            # S3 키 생성
            s3_key = f"{folder}/{filename}"
            
            # 파일 업로드
            s3_client.upload_fileobj(
                file,
                settings.AWS_STORAGE_BUCKET_NAME,
                s3_key,
                ExtraArgs={'ContentType': file.content_type}
            )
            
            # S3 URL 생성
            s3_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"
            
            return s3_url
        except Exception as e:
            logging.error(f"S3 업로드 실패: {str(e)}")
            raise e

    def perform_create(self, serializer): 
        # 파일 저장 로직
        instance = serializer.save(user=self.request.user)
        
        # PDF 파일을 S3에 저장
        if 'documents' in self.request.FILES:
            documents_file = self.request.FILES['documents']
            
            try:
                # 파일 검증
                self._validate_document_file(documents_file)
                
                # 파일명을 안전하게 처리
                safe_filename = f"{instance.title}_{documents_file.name}"
                
                # S3에 업로드
                s3_url = self.upload_to_s3(documents_file, 'assets', safe_filename)
                
                # 모델에 정보 저장 (S3 URL과 원본 파일명만 저장)
                instance.pdf_path = s3_url
                instance.lib_name = documents_file.name
                instance.save()
                
            except ValueError as e:
                # 검증 실패 시 인스턴스 삭제하고 오류 반환
                instance.delete()
                from rest_framework.response import Response
                from rest_framework import status
                raise serializers.ValidationError({"documents": str(e)})
        
        # 커버 이미지를 S3에 저장
        if 'cover_photo' in self.request.FILES:
            cover_photo = self.request.FILES['cover_photo']
            
            try:
                # 파일 검증
                self._validate_image_file(cover_photo)
                
                # 파일명을 안전하게 처리
                safe_filename = f"{instance.lib_id}_{cover_photo.name}"
                
                # S3에 업로드
                s3_url = self.upload_to_s3(cover_photo, 'assets_cover_image', safe_filename)
                
                # 모델에 정보 저장 (S3 URL만 저장)
                instance.img_path = s3_url
                instance.save()
                
            except ValueError as e:
                # 검증 실패 시 인스턴스 삭제하고 오류 반환
                instance.delete()
                from rest_framework.response import Response
                from rest_framework import status
                raise serializers.ValidationError({"cover_photo": str(e)})
    
    def _validate_document_file(self, file):
        """문서 파일 검증"""
        # 파일 크기 검증 (100MB 제한)
        if file.size > 100 * 1024 * 1024:
            raise ValueError("파일 크기는 100MB를 초과할 수 없습니다.")
        
        # 파일 형식 검증
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt']
        file_extension = os.path.splitext(file.name)[1].lower()
        if file_extension not in allowed_extensions:
            raise ValueError(f"지원하지 않는 파일 형식입니다. 허용된 형식: {', '.join(allowed_extensions)}")
    
    def _validate_image_file(self, file):
        """이미지 파일 검증"""
        # 파일 크기 검증 (10MB 제한)
        if file.size > 10 * 1024 * 1024:
            raise ValueError("이미지 파일 크기는 10MB를 초과할 수 없습니다.")
        
        # 이미지 형식 검증
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        file_extension = os.path.splitext(file.name)[1].lower()
        if file_extension not in allowed_extensions:
            raise ValueError(f"지원하지 않는 이미지 형식입니다. 허용된 형식: {', '.join(allowed_extensions)}")

# 댓글 목록 조회/생성 API
class LibraryCommentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LibraryCommentsSerializer
    def get_queryset(self): 
        return LibraryComments.objects.filter(asset_library_id=self.kwargs.get('lib_id')).order_by('-created_at')
    def perform_create(self, serializer):
        asset_library = get_object_or_404(AssetLibrary, lib_id=self.kwargs.get('lib_id'))
        comment = serializer.save(user=self.request.user, asset_library=asset_library)
        # 댓글 수 증가
        asset_library.comment_count += 1
        asset_library.save()

# 댓글 상세/수정/삭제 API
class LibraryCommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LibraryCommentsSerializer
    lookup_field = 'comment_id'
    
    def get_queryset(self):
        return LibraryComments.objects.all()
    
    def perform_destroy(self, instance):
        # 댓글 삭제 시 comment_count 감소
        asset_library = instance.asset_library
        asset_library.comment_count = max(0, asset_library.comment_count - 1)
        asset_library.save()
        instance.delete()

# --- 7-11. 인사이트 ---
class InsightTrendsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InsightTrendsSerializer
    queryset = InsightTrends.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['type', 'release_year']
    search_fields = ['car_name']
    pagination_class = None

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

# --- 좋아요 관련 API ---
# 에셋 좋아요 토글 API
class AssetLikeToggleView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, lib_id):
        """에셋 좋아요 토글 - 좋아요 추가/제거"""
        try:
            asset = get_object_or_404(AssetLibrary, lib_id=lib_id)
            user = request.user
            
            # 기존 좋아요 확인
            like, created = AssetLikes.objects.get_or_create(
                asset_library=asset,
                user=user
            )
            
            if created:
                # 좋아요 추가
                asset.likes += 1
                asset.save()
                user_liked = True
            else:
                # 좋아요 제거
                like.delete()
                asset.likes = max(0, asset.likes - 1)
                asset.save()
                user_liked = False
            
            return Response({
                'likes': asset.likes,
                'user_liked': user_liked
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Asset like toggle error: {e}")
            return Response(
                {'error': '좋아요 처리 중 오류가 발생했습니다.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# 댓글 좋아요 토글 API
class CommentLikeToggleView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, comment_id):
        """댓글 좋아요 토글 - 좋아요 추가/제거"""
        try:
            comment = get_object_or_404(LibraryComments, comment_id=comment_id)
            user = request.user
            
            # 기존 좋아요 확인
            like, created = CommentLikes.objects.get_or_create(
                comment=comment,
                user=user
            )
            
            if created:
                # 좋아요 추가
                comment.likes += 1
                comment.save()
                user_liked = True
            else:
                # 좋아요 제거
                like.delete()
                comment.likes = max(0, comment.likes - 1)
                comment.save()
                user_liked = False
            
            return Response({
                'likes': comment.likes,
                'user_liked': user_liked
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Comment like toggle error: {e}")
            return Response(
                {'error': '좋아요 처리 중 오류가 발생했습니다.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChatHistoryUpdateView(APIView):
    """채팅 기록 업데이트 API"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, session_id):
        try:
            data = request.data
            user_id = data.get('user_id')
            user_message = data.get('user_message')
            assistant_response = data.get('assistant_response')
            
            print(f"🔍 ChatHistoryUpdateView 요청 데이터:")
            print(f"  - session_id: {session_id}")
            print(f"  - user_id: {user_id}")
            print(f"  - user_message 길이: {len(user_message) if user_message else 0}")
            print(f"  - assistant_response 길이: {len(assistant_response) if assistant_response else 0}")
            
            if not all([user_id, user_message, assistant_response]):
                print(f"❌ 필수 필드 누락: user_id={user_id}, user_message={user_message}, assistant_response={assistant_response}")
                return Response(
                    {'error': '필수 필드가 누락되었습니다.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 세션 확인
            try:
                print(f"🔍 세션 조회 시도: session_id={session_id}, user_id={user_id}")
                session = ChatSession.objects.get(session_id=session_id, user_id=user_id)
                print(f"✅ 세션 조회 성공: {session}")
            except ChatSession.DoesNotExist:
                print(f"❌ 세션을 찾을 수 없음: session_id={session_id}, user_id={user_id}")
                return Response(
                    {'error': '세션을 찾을 수 없습니다.'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 프롬프트 로그 생성
            try:
                print(f"🔍 프롬프트 로그 생성 시도: session={session}, user_message='{user_message[:50]}...', assistant_response='{assistant_response[:50]}...'")
                prompt_log = PromptLog.objects.create(
                    session=session,
                    user_prompt=user_message,
                    ai_response=assistant_response,
                    response_time=0  # 스트리밍이므로 0으로 설정
                )
                print(f"✅ 프롬프트 로그 생성 성공: prompt_id={prompt_log.prompt_id}")
            except Exception as e:
                print(f"❌ 프롬프트 로그 생성 실패: {e}")
                raise e
            
            print(f"🔍 응답 반환 준비")
            return Response({
                'success': True,
                'prompt_id': prompt_log.prompt_id,
                'message': '채팅 기록이 업데이트되었습니다.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"❌ ChatHistoryUpdateView 예외 발생: {e}")
            print(f"❌ 예외 타입: {type(e)}")
            import traceback
            print(f"❌ 스택 트레이스: {traceback.format_exc()}")
            logger.error(f"Chat history update error: {e}")
            return Response(
                {'error': f'채팅 기록 업데이트 중 오류가 발생했습니다: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChecklistImageGenerationView(APIView):
    """체크리스트 기반 이미지 생성 API"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            print(f"🔍 [라우팅] 체크리스트 이미지 생성 요청 받음")
            
            # 요청 데이터 추출
            checklist_data = request.data.get('checklist_data', {})
            session_id = request.data.get('session_id')
            user_id = request.data.get('user_id', 'anonymous_user')
            
            print(f"🔍 체크리스트 데이터: {checklist_data}")
            print(f"🔍 세션 ID: {session_id}")
            print(f"🔍 사용자 ID: {user_id}")
            
            # 필수 필드 검증
            required_fields = ['viewpoint', 'body_type', 'color_finish']
            missing_fields = [field for field in required_fields if not checklist_data.get(field)]
            
            if missing_fields:
                return Response(
                    {'error': f'필수 필드가 누락되었습니다: {", ".join(missing_fields)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 파이프라인 서비스를 통한 이미지 생성
            from pipeline.services import BabsimPipelineService
            pipeline_service = BabsimPipelineService()
            
            # 체크리스트 데이터를 이미지 쿼리로 변환
            image_query = pipeline_service.generate_image_query_from_checklist(checklist_data)
            print(f"🔍 생성된 이미지 쿼리: {image_query}")
            
            # 이미지 생성 실행
            result = pipeline_service.generate_image_from_checklist(
                checklist_data=checklist_data,
                image_query=image_query,
                session_id=session_id,
                user_id=user_id
            )
            
            print(f"✅ 체크리스트 이미지 생성 완료: {result}")
            
            return Response({
                'success': True,
                'generated_results': result.get('generated_results', []),
                'image_query': image_query,
                'message': '이미지가 성공적으로 생성되었습니다.'
            })
            
        except Exception as e:
            print(f"❌ ChecklistImageGenerationView 예외 발생: {e}")
            import traceback
            print(f"❌ 스택 트레이스: {traceback.format_exc()}")
            logger.error(f"Checklist image generation error: {e}")
            return Response(
                {'error': f'이미지 생성 중 오류가 발생했습니다: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )