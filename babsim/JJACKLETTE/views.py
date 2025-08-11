import os, logging, uuid, logging
from django.utils import timezone
from datetime import datetime
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from concurrent.futures import ThreadPoolExecutor

from .models import Users, ChatSession, PromptLog, GeneratedResult
from .serializers import (
    UserDetailSerializer, UserRegistrationSerializer, MyTokenObtainPairSerializer,
    ChatSessionCreateSerializer, ChatSessionOutSerializer,
    PromptLogCreateSerializer, PromptLogOutSerializer,
    GeneratedResultOutSerializer
)

log = logging.getLogger("api")

# --- 공통 응답
def ok(data=None, code=200): return Response(data or {}, status=code)
def created(data=None): return Response(data or {}, status=201)

# [ADDED] GPU 1장 기준 안전치(병렬 늘리면 VRAM 주의)
EXECUTOR = ThreadPoolExecutor(max_workers=1)

# --- 공통 예외 핸들러 (settings.REST_FRAMEWORK.EXCEPTION_HANDLER에서 참조)
def custom_exception_handler(exc, context):
    from rest_framework.views import exception_handler as drf_handler
    resp = drf_handler(exc, context)
    if resp is not None:
        detail = resp.data
        if isinstance(detail, dict):
            if "message" in detail:
                pass
            elif "detail" in detail:
                resp.data = {"message": detail.get("detail")}
            else:
                first = next(iter(detail.values())) if detail else "요청이 올바르지 않습니다."
                if isinstance(first, (list, tuple)): first = first[0]
                resp.data = {"message": first}
        else:
            resp.data = {"message": str(detail)}
        return resp

    log.exception("Unhandled exception", exc_info=exc)
    return Response({"message": "서버 오류가 발생했습니다."}, status=500)

# --- AUTH
class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        ser = UserRegistrationSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return created({"message": "회원가입이 완료되었습니다.", "user": UserDetailSerializer(user).data})

class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        token_ser = MyTokenObtainPairSerializer(data={
            "email": request.data.get("e_mail"),   # [UPDATED] 명세 입력키 사용
            "password": request.data.get("password"),
        })
        token_ser.is_valid(raise_exception=True)
        payload = token_ser.validated_data

        user = Users.objects.filter(id=payload["user"]["user_id"]).first()
        if user:
            user.last_login = timezone.now()
            user.save(update_fields=["last_login"])
        # 날짜 포맷은 Serializer에서 처리되므로 여기서 별도 포맷팅 불필요
        payload["message"] = "로그인 성공"
        return ok(payload, 200)

class LogoutAPIView(APIView):
    def post(self, request):
        token = request.data.get("refresh_token")
        if not token:
            return ok({"message": "refresh_token이 필요합니다."}, 400)
        try:
            RefreshToken(token).blacklist()
        except Exception:
            pass
        return ok({"message": "로그아웃 성공"}, 200)

# --- USERS
class UserProfileAPIView(APIView):
    def get(self, request):
        return ok(UserDetailSerializer(request.user).data, 200)

# --- Pagination
class TenPaginator(PageNumberPagination):
    page_size = 10
    page_query_param = "page"
    page_size_query_param = "page_size"

class TwentyPaginator(PageNumberPagination):
    page_size = 20
    page_query_param = "page"
    page_size_query_param = "page_size"

# --- CHAT: Sessions
class ChatSessionListCreateAPIView(APIView):
    def get(self, request):
        qs = ChatSession.objects.filter(user=request.user).order_by("-started_at")
        paginator = TenPaginator()
        page = paginator.paginate_queryset(qs, request)
        results = [ChatSessionOutSerializer(o).data for o in page]
        return paginator.get_paginated_response({"results": results})  # DRF 표준 페이징 래핑

    def post(self, request):
        ser = ChatSessionCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        started_at = ser.validated_data.get("started_at")
        session = ChatSession.objects.create(user=request.user, started_at=started_at) \
                  if hasattr(ChatSession, "started_at") else ChatSession.objects.create(user=request.user)
        log.info("ChatSession created", extra={"session_id": str(getattr(session, "session_id", "")), "user_id": str(request.user.id)})
        return created(ChatSessionOutSerializer(session).data)

class ChatSessionEndAPIView(APIView):
    def put(self, request, session_id):
        session = get_object_or_404(ChatSession, session_id=session_id, user=request.user)
        ended_at = request.data.get("ended_at")
        if not ended_at:
            return ok({"message": "ended_at이 필요합니다."}, 400)
        if hasattr(session, "ended_at"):
            session.ended_at = ended_at
            session.save(update_fields=["ended_at"])
        return ok({"message": "세션이 종료되었습니다.", "session": ChatSessionOutSerializer(session).data}, 200)

# --- CHAT: Prompt Logs
class PromptLogListAPIView(APIView):
    def get(self, request, session_id):
        session = get_object_or_404(ChatSession, session_id=session_id, user=request.user)
        qs = PromptLog.objects.filter(session=session).order_by("-created_at")
        paginator = TwentyPaginator()
        page = paginator.paginate_queryset(qs, request)
        data = [PromptLogOutSerializer(o).data for o in page]
        return paginator.get_paginated_response({"results": data})

class PromptLogCreateAPIView(APIView):
    def post(self, request):
        ser = PromptLogCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        session = get_object_or_404(ChatSession, session_id=ser.validated_data["session_id"], user=request.user)

        if hasattr(PromptLog, "user_prompt") and hasattr(PromptLog, "ai_response"):
            plog = PromptLog.objects.create(
                session=session,
                user_prompt=ser.validated_data["user_prompt"],
                ai_response=ser.validated_data["ai_response"],
            )
        else:
            # 레거시 스키마 대응(필요 시)
            up = PromptLog.objects.create(session=session, role="user", content=ser.validated_data["user_prompt"])
            ap = PromptLog.objects.create(session=session, role="assistant", content=ser.validated_data["ai_response"])
            plog = ap
        return created(PromptLogOutSerializer(plog).data)

# --- CHAT: Generated Results
class GeneratedResultListAPIView(APIView):
    def get(self, request, prompt_id):
        qs = GeneratedResult.objects.filter(prompt_id=prompt_id, prompt__session__user=request.user).order_by("-created_at")
        data = [GeneratedResultOutSerializer(o).data for o in qs]
        return ok({"count": len(data), "results": data}, 200)
    
# -------------------------
# [ADDED] EXAONE 텍스트 생성기
# -------------------------
_exaone_lock = threading.Lock()
_exaone      = {"tok": None, "model": None}

def _load_exaone():
    if _exaone["model"] is None:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        with _exaone_lock:
            if _exaone["model"] is None:
                model_dir = settings.EXAONE_MODEL_PATH  # settings에서 경로 가져옴
                device = "cuda" if torch.cuda.is_available() else "cpu"
                log_ai.info(f"[EXAONE] loading from {model_dir} on {device}")
                tok = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
                mdl = AutoModelForCausalLM.from_pretrained(
                    model_dir,
                    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
                    low_cpu_mem_usage=True,
                    device_map="auto" if torch.cuda.is_available() else None,
                    trust_remote_code=True,
                )
                if device == "cuda":
                    mdl = mdl.to(device)
                _exaone["tok"], _exaone["model"] = tok, mdl
                log_ai.info("[EXAONE] loaded")
    return _exaone["tok"], _exaone["model"]

def exaone_generate(prompt: str, max_new_tokens: int = 256) -> str:
    tok, mdl = _load_exaone()
    with _exaone_lock, torch.no_grad():
        inputs = tok(prompt, return_tensors="pt").to(mdl.device)
        outs = mdl.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            top_p=0.9,
            temperature=0.7,
            pad_token_id=tok.eos_token_id,
        )
        text = tok.decode(outs[0], skip_special_tokens=True)
        if text.startswith(prompt):  # 입력 포함형 대비
            text = text[len(prompt):]
        return text.strip()

# -------------------------
# [ADDED] SD3.5 이미지 생성기
# -------------------------
_sd_lock = threading.Lock()
_sd      = {"pipe": None}

def _load_sd():
    if _sd["pipe"] is None:
        from diffusers import StableDiffusion3Pipeline
        with _sd_lock:
            if _sd["pipe"] is None:
                model_dir = settings.SD35_MODEL_ID  # settings에서 경로 가져옴
                device = "cuda" if torch.cuda.is_available() else "cpu"
                log_ai.info(f"[SD3.5] loading from {model_dir} on {device}")
                pipe = StableDiffusion3Pipeline.from_pretrained(
                    model_dir,
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32
                )
                if device == "cuda":
                    pipe = pipe.to(device)
                pipe.enable_attention_slicing()
                _sd["pipe"] = pipe
                log_ai.info("[SD3.5] loaded")
    return _sd["pipe"]

def sd_generate_image(prompt: str, width=1024, height=1024):
    pipe = _load_sd()
    with _sd_lock:
        img = pipe(
            prompt=prompt,
            width=width,
            height=height,
            num_inference_steps=28,
            guidance_scale=5.0,
        ).images[0]
        return img
    
# -------------------------
# [ADDED] 이미지 저장 유틸 (/media/images/YYYYMMDD/uuid.png)
# -------------------------
def save_image_pil(img) -> str:
    day = datetime.utcnow().strftime("%Y%m%d")
    out_dir = Path(settings.MEDIA_ROOT) / "images" / day
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}.png"
    img.save(out_dir / name)
    return f"/media/images/{day}/{name}"  # 프런트에서 그대로 <img src=...>

# -------------------------
# [ADDED] 생성 API (텍스트)
# -------------------------
class GenerateTextAPIView(APIView):
    """
    POST /api/generate/text/
    { "session_id": "uuid", "prompt": "..." }
    -> 201 { "message": "ok", "result": "..." }
    """
    def post(self, request):
        ser = TextGenerateRequest(data=request.data)
        ser.is_valid(raise_exception=True)

        session = get_object_or_404(ChatSession, session_id=ser.validated_data["session_id"], user=request.user)
        prompt  = ser.validated_data["prompt"]

        def _run(): return exaone_generate(prompt)

        try:
            text = EXECUTOR.submit(_run).result(timeout=120)
        except Exception:
            log_ai.exception("EXAONE text generation failed")
            return ok({"message": "텍스트 생성 중 오류가 발생했습니다."}, 500)

        # 히스토리 저장(프런트엔드에는 노출 X, 필요 시 조회 API로 확인)
        plog = PromptLog.objects.create(session=session, user_prompt=prompt, ai_response=text)
        GeneratedResult.objects.create(prompt=plog, result_type="text", result=text, result_path="")

        return created({"message": "ok", "result": text})

# -------------------------
# [ADDED] 생성 API (이미지)
# -------------------------
class GenerateImageAPIView(APIView):
    """
    POST /api/generate/image/
    { "session_id": "uuid", "prompt": "..." }
    -> 201 { "message": "ok", "result_path": "/media/....png" }
    """
    def post(self, request):
        ser = ImageGenerateRequest(data=request.data)
        ser.is_valid(raise_exception=True)

        session = get_object_or_404(ChatSession, session_id=ser.validated_data["session_id"], user=request.user)
        prompt  = ser.validated_data["prompt"]

        def _run():
            img = sd_generate_image(prompt)
            return save_image_pil(img)

        try:
            rel_path = EXECUTOR.submit(_run).result(timeout=300)
        except Exception:
            log_ai.exception("SD image generation failed")
            return ok({"message": "이미지 생성 중 오류가 발생했습니다."}, 500)

        plog = PromptLog.objects.create(session=session, user_prompt=prompt, ai_response="IMAGE_OK")
        GeneratedResult.objects.create(prompt=plog, result_type="image", result="", result_path=rel_path)

        return created({"message": "ok", "result_path": rel_path})
# DRF의 ViewSet 또는 APIView를 활용하여 RESTful API 로직을 작성
# 클라이언트(React.js)로부터 요청을 받아 serializers.py를 통해 데이터를 처리하고,
# models.py를 통해 PostgreSQL과 상호작용하며, services.py의 비즈니스 로직을 호출

# JJACKLETTE/views.py

from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import *
from .models import *
# from .llm_interface import generate_response

# def chatbot_page(request):
#     return render(request, 'index.html')

# 챗봇 위치 필요


# 인증 API View
# 회원가입
class RegisterAPIView(APIView):
    permission_classes = [AllowAny] # 누구나 접근 가능

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            return Response({"message": "회원가입이 완료되었습니다.", "user": UserDetailSerializer(user).data}, status=status.HTTP_201_CREATED)

# 프로필 조회, 수정
class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated] # 로그인한 사용자만 접근 가능
    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # 사용자 프로필 정보를 수정합니다. (updateUserProfile 함수 대응)
    def put(self, request):
        serializer = UserDetailSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({"message": "사용자 정보가 성공적으로 업데이트되었습니다.", "user": serializer.data}, status=status.HTTP_200_OK)

# 채팅 API View        
# 채팅 세션 목록 조회 및 새 세션 생성 API (/api/chat/sessions/)
class ChatSessionListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        sessions = ChatSession.objects.filter(user_id=request.user).order_by('-started_at')
        serializer = ChatSessionSerializer(sessions, many=True)
        return Response({"count": len(serializer.data), "results": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        session = ChatSession.objects.create(user_id=request.user)
        serializer = ChatSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# 특정 세션의 프롬프트(대화) 내역 조회 API (/api/chat/sessions/<uuid:session_id>/prompts/)
class PromptLogListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, session_id):
        if not ChatSession.objects.filter(session_id=session_id, user_id=request.user).exists():
            return Response({"error": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        prompts = PromptLog.objects.filter(session_id=session_id).order_by('created_at')
        serializer = PromptLogSerializer(prompts, many=True)
        return Response({"count": len(serializer.data), "results": serializer.data}, status=status.HTTP_200_OK)

# 텍스트, 이미지 생성 결과 조회 및 저장 API
class GeneratedResultListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, prompt_id):
        results = GeneratedResult.objects.filter(prompt_id=prompt_id)
        serializer = GeneratedResultSerializer(results, many=True)
        return Response({"count": len(serializer.data), "results": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = GeneratedResultSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            # TODO: prompt_id가 현재 로그인한 유저의 것인지 검증하는 로직 추가하면 더 안전
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

# 트렌즈인사이트 API 뷰

# 차량 모델 리스트
class CarModelListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        # TODO: 명세서에 있는 type, release_year 등 쿼리 파라미터를 사용한 필터링 기능 구현
        car_models = InsightTrends.objects.all()
        serializer = InsightTrendsSerializer(car_models, many=True)
        return Response({"count": car_models.count(), "results": serializer.data}, status=status.HTTP_200_OK)

# 차량 모델 상세 리스트. 띄우기만 하면 되는데 상세가 필요한가? 
class CarModelDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, car_model_id):
        try:
            car_model = InsightTrends.objects.get(pk=car_model_id)
            serializer = InsightTrendsDetailSerializer(car_model)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except InsightTrends.DoesNotExist:
            return Response({"error": "차량 모델을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

# 라이브러리 API 뷰

# 라이브러리 댓글 조회
class AssetListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    def get(self, request):
        # TODO: 명세서에 있는 search 쿼리 파라미터를 사용한 검색 기능 구현
        assets = AssetLibrary.objects.filter(user=request.user)
        serializer = AssetLibrarySerializer(assets, many=True)
        return Response({"count": assets.count(), "results": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AssetLibrarySerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

# 댓글 작성
class CommentListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, lib_id):
        comments = LibraryComments.objects.filter(lib_id=lib_id)
        serializer = LibraryCommentsSerializer(comments, many=True)
        return Response({"count": comments.count(), "results": serializer.data}, status=status.HTTP_200_OK)
    
    def post(self, request): # React 코드에서는 lib_id를 body에 담아 /library/comments/로 보냄
        serializer = LibraryCommentsSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            # user_id는 토큰에서 자동으로 가져와 설정
            serializer.save(user_id=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


























# 이거 좀더 손볼 필요
class ChatAPIView(APIView):
    """챗봇 메시지 전송 및 응답 API (sendChatMessage 함수 대응) (/api/chat/)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        session_id = request.data.get('session_id')
        user_prompt = request.data.get('message')

        if not all([session_id, user_prompt]):
            return Response({"error": "세션 ID와 메시지를 모두 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            session = ChatSession.objects.get(session_id=session_id, user_id=request.user)
            
            # TODO: 실제 LLM, Stable Diffusion 연동 로직
            mock_ai_response = f"'{user_prompt}'에 대한 AI 답변입니다."
            
            # 대화 기록 저장
            prompt_log = PromptLog.objects.create(
                session_id=session,
                user_prompt=user_prompt,
                ai_response=mock_ai_response
            )
            
            return Response({
                "success": True,
                "response": mock_ai_response,
                "promptLog": PromptLogSerializer(prompt_log).data
            }, status=status.HTTP_200_OK)
        except ChatSession.DoesNotExist:
            return Response({"error": "세션을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)