# Django 모델 객체를 JSON/XML과 같은 형태로 직렬화(Serialization)하고, 
# 외부 데이터를 모델 객체로 역직렬화(Deserialization)하는 역할
# 예: 사용자 정보, 아이템 정보 등을 React.js로 보내기 위해 모델 데이터를 JSON으로 변환

from django.db.models import Q
from rest_framework import serializers, exceptions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
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

# 인사이트 관련 (InsightService.js)
class DesignMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignMaterial
        fields = '__all__'

class EngineeringSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = EngineeringSpec
        fields = '__all__'

class SalesStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesStat
        fields = '__all__'

class UserReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserReview
        fields = '__all__'

# 차량 모델 목록을 위한 serializer
class InsightTrendsSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsightTrends
        fields = ('car_model_id', 'car_name', 'type', 'release_year')

# 차량 모델 상세 정보 serializer. FK에 해당하는 serializer 중첩해서 꼬리물고 사용.
class InsightTrendsDetailSerializer(serializers.ModelSerializer):
    design_materials = DesignMaterialSerializer(many=True, read_only=True)
    engineering_specs = EngineeringSpecSerializer(many=True, read_only=True)
    sales_stats = SalesStatSerializer(many=True, read_only=True)
    user_reviews = UserReviewSerializer(many=True, read_only=True)

    class Meta:
        model = InsightTrends
        fields = ('car_model_id', 'car_name', 'type', 'release_year', 
                  'design_materials', 'engineering_specs', 'sales_stats', 'user_reviews')


# library 관련 (LibraryService.js)
class AssetLibrarySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetLibrary
        fields = '__all__'

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






