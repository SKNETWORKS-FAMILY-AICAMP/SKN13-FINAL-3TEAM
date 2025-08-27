# Django 모델 객체를 JSON/XML과 같은 형태로 직렬화(Serialization)하고, 
# 외부 데이터를 모델 객체로 역직렬화(Deserialization)하는 역할
# 예: 사용자 정보, 아이템 정보 등을 React.js로 보내기 위해 모델 데이터를 JSON으로 변환

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *

# 사용자 상세 정보 (ERD의 모든 필드 포함)
class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = (
            'user_id', 'user_name', 'email', 'phone_number', 
            'company', 'department', 'position', 'profile_image', 
            'background_image', 'created_at', 'last_login'
        )

# 회원가입 데이터 처리
class UserRegistrationSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = Users
        fields = ('user_name', 'email', 'password', 'password_confirm')
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, attrs):
        if Users.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "이미 사용 중인 이메일입니다."})
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "비밀번호가 일치하지 않습니다."})
        return attrs

    def create(self, validated_data):
        # create_user 호출 시 user_name을 함께 전달
        user = Users.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            user_name=validated_data['user_name']
        )
        return user

# 로그인
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user_data = UserDetailSerializer(self.user).data
        user_data['e_mail'] = user_data.pop('email')

        data.update({
            "message": "로그인 성공",
            "user": user_data,
            "access_token": data.pop('access'),
            "refresh_token": data.pop('refresh')
        })
        return data

# 로그아웃
class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()
    def validate(self, attrs):
        try:
            self.token = RefreshToken(attrs['refresh_token'])
        except Exception:
            raise serializers.ValidationError("유효하지 않거나 만료된 리프레시 토큰입니다.")
        return attrs
    def save(self, **kwargs):
        self.token.blacklist()

# 사용자 정보 수정
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ('user_name', 'phone_number', 'company', 'department', 'position', 'profile_image', 'background_image')
        extra_kwargs = {field: {'required': False} for field in fields}

# --- 2. 챗봇 세션 ---
class ChatSessionSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.user_id', read_only=True)
    class Meta:
        model = ChatSession
        fields = ('session_id', 'user_id', 'session_title', 'started_at', 'ended_at')

# --- 3. 프롬프트 로그 (통합 모델) ---
class PromptLogSerializer(serializers.ModelSerializer):
    session_id = serializers.PrimaryKeyRelatedField(queryset=ChatSession.objects.all(), source='session')
    
    class Meta:
        model = PromptLog
        fields = (
            'prompt_id', 'session_id', 'user_prompt', 'ai_response', 
            'result_type', 'result_path', 'response_time', 'created_at'
        )
        read_only_fields = ('prompt_id', 'created_at', 'ai_response')

# --- 4. 에셋 라이브러리 ---
class AssetLibrarySerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.user_id', read_only=True)
    user_name = serializers.CharField(source='user.user_name', read_only=True) # 작성자 이름 추가

    class Meta:
        model = AssetLibrary
        fields = (
            'lib_id', 'user_id', 'user_name', 'title', 'summary', 'category', 
            'documents', 'pdf_path', 'img_path', 'upload_date', 
            'likes', 'comment_count', 'created_at', 'updated_at'
        )

class AssetLibraryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetLibrary
        fields = ('documents', 'img_path')

# --- 5. 라이브러리 댓글 ---
class LibraryCommentsSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.user_id', read_only=True)
    user_name = serializers.CharField(source='user.user_name', read_only=True) # 작성자 이름 추가

    class Meta:
        model = LibraryComments
        fields = ('comment_id', 'asset_library', 'user_id', 'user_name', 'comments', 'likes', 'created_at', 'updated_at')
        read_only_fields = ('comment_id', 'user_id', 'created_at', 'updated_at')

# --- 6. 인사이트 ---
class EngineeringSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = EngineeringSpec
        fields = '__all__'

class UserReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserReview
        fields = '__all__'

class RecentArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecentArticle
        fields = '__all__'

class InsightTrendsDetailSerializer(serializers.ModelSerializer):
    engineering_specs = EngineeringSpecSerializer(many=True, read_only=True)
    user_reviews = UserReviewSerializer(many=True, read_only=True)
    recent_articles = RecentArticleSerializer(many=True, read_only=True)
    
    class Meta:
        model = InsightTrends
        fields = (
            'car_model_id', 'car_name', 'type', 'release_year', 'model_3d_path',
            'engineering_specs', 'user_reviews', 'recent_articles'
        )

class InsightTrendsSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsightTrends
        fields = ('car_model_id', 'car_name', 'type', 'release_year', 'model_3d_path')

# --- 7. 좋아요 ---
class AssetLikesSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetLikes
        fields = '__all__'

class CommentLikesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentLikes
        fields = '__all__'





