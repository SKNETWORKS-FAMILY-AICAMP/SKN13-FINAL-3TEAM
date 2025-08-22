# Django 모델 객체를 JSON/XML과 같은 형태로 직렬화(Serialization)하고, 
# 외부 데이터를 모델 객체로 역직렬화(Deserialization)하는 역할
# 예: 사용자 정보, 아이템 정보 등을 React.js로 보내기 위해 모델 데이터를 JSON으로 변환

from django.db.models import Q
from rest_framework import serializers, exceptions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
<<<<<<< HEAD
from .models import Users, ChatSession, PromptLog, GeneratedResult, InsightTrends, UserReview, EngineeringSpec, DesignMaterial, SalesStat, AssetLibrary, LibraryComments


# --- Users
class UserDetailSerializer(serializers.Serializer):
    user_id   = serializers.UUIDField(source="id")
    user_name = serializers.CharField(source="username")
    e_mail    = serializers.EmailField(source="email")
    created_at = serializers.DateTimeField(source="date_joined", format=None)  # [UPDATED]
    last_login = serializers.DateTimeField(format=None, allow_null=True)       # [UPDATED]

class UserRegistrationSerializer(serializers.Serializer):
    user_name = serializers.CharField()
    e_mail = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"message": "비밀번호가 일치하지 않습니다."})
        if Users.objects.filter(Q(e_mail=attrs["e_mail"]) | Q(email=attrs["e_mail"])).exists():
            raise serializers.ValidationError({"message": "이미 존재하는 이메일입니다."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm", None)
        return Users.objects.create_user(
            username=validated_data["user_name"],
            email=validated_data["e_mail"],
            password=validated_data["password"],
        )

# --- Auth(Login)
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        email, password = attrs.get("email"), attrs.get("password")
        user = Users.objects.filter(Q(e_mail=email) | Q(email=email)).first()
        if not user or not user.check_password(password):
            raise exceptions.AuthenticationFailed("이메일 또는 비밀번호가 올바르지 않습니다.")
        refresh = self.get_token(user)
        return {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user": UserDetailSerializer(user).data,
        }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["uid"] = str(user.id)
        token["username"] = user.username
        return token

# --- Chat Session
class ChatSessionCreateSerializer(serializers.Serializer):
    started_at = serializers.DateTimeField()  # [UNCHANGED]

class ChatSessionOutSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(source="session_id")
    user_id    = serializers.UUIDField(source="user_id")
    started_at = serializers.DateTimeField(format=None)                           # [UPDATED]
    ended_at   = serializers.DateTimeField(format=None, allow_null=True)          # [UPDATED]

# --- Prompt Log
class PromptLogCreateSerializer(serializers.Serializer):
    session_id  = serializers.UUIDField()
    user_prompt = serializers.CharField()
    ai_response = serializers.CharField()

class PromptLogOutSerializer(serializers.Serializer):
    prompt_id   = serializers.UUIDField(source="prompt_id")
    session_id  = serializers.UUIDField()
    user_prompt = serializers.CharField()
    ai_response = serializers.CharField()
    created_at  = serializers.DateTimeField(format=None)                           # [UPDATED]

# --- Generated Result
class GeneratedResultOutSerializer(serializers.Serializer):
    result_id   = serializers.UUIDField(source="result_id")
    prompt_id   = serializers.UUIDField()
    result_type = serializers.CharField()
    result_path = serializers.CharField()
    result      = serializers.CharField()
    # created_at 등 확장 필요시 DateTimeField(format=None)로 추가

# -------------------------------------------- 중간 발표 구현 기능
=======
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *

# --- 1. 인증 및 사용자 ---
class UserDetailSerializer(serializers.ModelSerializer):
    e_mail = serializers.EmailField(source='email')
    user_name = serializers.CharField(source='first_name')
    class Meta:
        model = Users
        fields = ('user_id', 'user_name', 'e_mail', 'created_at', 'last_login')

# --- 회원가입 데이터 처리 ---
class UserRegistrationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(write_only=True, required=True)
    e_mail = serializers.EmailField(source='email', required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = Users
        fields = ('user_name', 'e_mail', 'password', 'password_confirm')
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, attrs):
        if Users.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"e_mail": "이미 사용 중인 이메일입니다."})
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "비밀번호가 일치하지 않습니다."})
        return attrs

    def create(self, validated_data):
        user = Users.objects.create_user(email=validated_data['email'], password=validated_data['password'])
        user.first_name = validated_data['user_name']
        user.save()
        return user

# --- 로그인 ---
# 얘가 로그인 기능
# 이 Serializer는 로그인 요청을 받아 JWT 토큰을 발급합니다.
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data.update({
            "message": "로그인 성공",
            "user": UserDetailSerializer(self.user).data,
            "access_token": data.pop('access'),
            "refresh_token": data.pop('refresh')
        })
        return data

# --- 로그아웃  ---
class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()
    def validate_refresh_token(self, value):
        try:
            self.token = RefreshToken(value)
        except Exception:
            raise serializers.ValidationError("유효하지 않은 리프레시 토큰입니다.")
        return value
    def save(self, **kwargs):
        self.token.blacklist()

class UserUpdateSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='first_name', required=False)
    e_mail = serializers.EmailField(source='email', required=False)
    class Meta:
        model = Users
        fields = ('user_name', 'e_mail')

# --- 2. 챗봇 세션 ---
class ChatSessionSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.user_id', read_only=True)
    class Meta:
        model = ChatSession
        fields = ('session_id', 'user_id', 'started_at', 'ended_at')

# --- 3. 프롬프트 로그 ---
class PromptLogSerializer(serializers.ModelSerializer):
    session_id = serializers.PrimaryKeyRelatedField(queryset=ChatSession.objects.all(), source='session')
    
    class Meta:
        model = PromptLog
        fields = ('prompt_id', 'session_id', 'user_prompt', 'ai_response', 'created_at')
        read_only_fields = ('prompt_id', 'created_at', 'ai_response')

# --- 4. 생성 결과 ---
class GeneratedResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedResult
        fields = ('result_id', 'prompt', 'result_type', 'result_path', 'result')
>>>>>>> 43f5a95cbd1ec8665d26ac5a1ee1136fee08aef5

# --- 5. 에셋 라이브러리 ---
class AssetLibrarySerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.user_id', read_only=True)
    documents = serializers.FileField(read_only=True)
    class Meta:
        model = AssetLibrary
        fields = ('lib_id', 'user_id', 'documents', 'img_path')

class AssetLibraryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetLibrary
        fields = ('documents', 'img_path')

# --- 6. 라이브러리 댓글 ---
class LibraryCommentsSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.user_id', read_only=True)
    class Meta:
        model = LibraryComments
        fields = ('comment_id', 'library_asset', 'user_id', 'comments', 'created_at')
        read_only_fields = ('comment_id', 'user_id', 'created_at')

# --- 7-11. 인사이트 ---
class DesignMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignMaterial
        fields = ('material_id', 'material_type', 'usage_area')

class EngineeringSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = EngineeringSpec
        fields = '__all__'
        # fields = ('spec_id', 'cd_value', 'weight', 'material_al_ratio', 'wheel_base', 'pedestrian_safety_score', 'sensor_ready')

class SalesStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesStat
        fields = ('year', 'month', 'units_sold')

class UserReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserReview
        fields = ('review_id', 'sentiment_score', 'mentioned_features')

class InsightTrendsSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsightTrends
        fields = ('car_model_id', 'car_name', 'type', 'release_year')

class InsightTrendsDetailSerializer(serializers.ModelSerializer):
    design_materials = DesignMaterialSerializer(many=True, read_only=True)
    engineeringspec = EngineeringSpecSerializer(read_only=True)
    sales_stats = SalesStatSerializer(many=True, read_only=True)
    user_reviews = UserReviewSerializer(many=True, read_only=True)
    class Meta:
        model = InsightTrends
        fields = ('car_model_id', 'car_name', 'type', 'release_year', 'design_materials', 'engineeringspec', 'sales_stats', 'user_reviews')






<<<<<<< HEAD
class LibraryCommentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibraryComments
        fields = '__all__'

# [ADDED] 생성 공용 요청 스키마
class GenerateRequestSerializer(serializers.Serializer):
    result_type = serializers.ChoiceField(choices=["text", "image", "3d", "4d"])
    session_id = serializers.UUIDField()
    prompt = serializers.CharField(max_length=4000)

class TextGenerateRequest(serializers.Serializer):  # [ADDED]
    session_id = serializers.UUIDField()
    prompt = serializers.CharField(max_length=4000)

class ImageGenerateRequest(serializers.Serializer):  # [ADDED]
    session_id = serializers.UUIDField()
    prompt = serializers.CharField(max_length=4000)






=======
>>>>>>> 43f5a95cbd1ec8665d26ac5a1ee1136fee08aef5
