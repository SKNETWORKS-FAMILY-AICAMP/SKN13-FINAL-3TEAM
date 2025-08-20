# Django 모델 객체를 JSON/XML과 같은 형태로 직렬화(Serialization)하고, 
# 외부 데이터를 모델 객체로 역직렬화(Deserialization)하는 역할
# 예: 사용자 정보, 아이템 정보 등을 React.js로 보내기 위해 모델 데이터를 JSON으로 변환

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
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






