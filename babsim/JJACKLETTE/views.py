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