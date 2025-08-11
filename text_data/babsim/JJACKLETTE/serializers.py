# Django 모델 객체를 JSON/XML과 같은 형태로 직렬화(Serialization)하고, 
# 외부 데이터를 모델 객체로 역직렬화(Deserialization)하는 역할
# 예: 사용자 정보, 아이템 정보 등을 React.js로 보내기 위해 모델 데이터를 JSON으로 변환

from django.db.models import Q
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from .serializers import UserDetailSerializer
from .models import Users, ChatSession, PromptLog, InsightTrends, UserReview, EngineeringSpec, DesignMaterial, SalesStat, AssetLibrary, LibraryComments

# --- UserDetailSerializer를 MyTokenObtainPairSerializer보다 먼저 정의 ---
class UserDetailSerializer(serializers.ModelSerializer):
    """성공 응답에 포함될 사용자 정보의 형식을 정의합니다."""
    class Meta:
        model = Users
        fields = ('user_id', 'user_name', 'e_mail', 'created_at', 'last_login')

# --- Users
class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = '__all__'

# --- Auth(Login)
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    e_mail = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        # e_mail로 사용자를 찾아 username을 채워주는 로직
        user = Users.objects.filter(e_mail=attrs.get('e_mail')).first()
        if user and user.check_password(attrs.get('password')):
            attrs['username'] = user.username
        else:
            raise serializers.ValidationError("이메일 또는 비밀번호가 올바르지 않습니다.")
        
        data = super().validate(attrs)
        data['user'] = UserDetailSerializer(self.user).data
        data['access_token'] = data.pop('access')
        data['refresh_token'] = data.pop('refresh')
        data['message'] = "로그인 성공"
        return data
    
class UserRegistrationSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = Users
        fields = ('user_name', 'e_mail', 'password', 'password_confirm')
        extra_kwargs = {'password': {'write_only': True}}

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


# --- Chat Session
class ChatSessionCreateSerializer(serializers.ModelSerializer):
    # started_at = serializers.DateTimeField()  # [UNCHANGED]
    class Meta:
        model = ChatSession
        fields = '__all__'


class ChatSessionOutSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(source="session_id")
    user_id    = serializers.UUIDField(source="user_id")
    started_at = serializers.DateTimeField(format=None)                           
    ended_at   = serializers.DateTimeField(format=None, allow_null=True)          

# --- Prompt Log
class PromptLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptLog
        fields = '__all__'                        

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
    # source 옵션 추가
    design_materials = DesignMaterialSerializer(many=True, read_only=True, source='designmaterial_set')
    engineering_specs = EngineeringSpecSerializer(many=True, read_only=True, source='engineeringspec_set')
    sales_stats = SalesStatSerializer(many=True, read_only=True, source='salesstat_set')
    user_reviews = UserReviewSerializer(many=True, read_only=True, source='userreview_set')

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

# class GenerateRequestSerializer(serializers.Serializer):
#     result_type = serializers.ChoiceField(choices=["text", "image", "3d", "4d"])
#     session_id = serializers.UUIDField()
#     prompt = serializers.CharField(max_length=4000)

# class TextGenerateRequest(serializers.Serializer):  # [ADDED]
#     session_id = serializers.UUIDField()
#     prompt = serializers.CharField(max_length=4000)

# class ImageGenerateRequest(serializers.Serializer):  # [ADDED]
#     session_id = serializers.UUIDField()
#     prompt = serializers.CharField(max_length=4000)






