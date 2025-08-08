# Django 모델 객체를 JSON/XML과 같은 형태로 직렬화(Serialization)하고, 
# 외부 데이터를 모델 객체로 역직렬화(Deserialization)하는 역할
# 예: 사용자 정보, 아이템 정보 등을 React.js로 보내기 위해 모델 데이터를 JSON으로 변환

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Users, ChatSession, PromptLog, InsightTrends, UserReview, EngineeringSpec, DesignMaterial, SalesStat, AssetLibrary, LibraryComments, GeneratedResult

# 보안을 위한 JWT Token 발급 조건으로 username 말고 email 사용하도록 지정.
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_name'] = user.user_name
        return token

    def validate(self, attrs):
        # React에서 e_mail로 보내므로, e_mail로 사용자를 찾아 username을 채워줍니다.
        user = Users.objects.filter(e_mail=attrs.get('e_mail')).first()
        if user and user.check_password(attrs.get('password')):
            attrs['username'] = user.username
        
        data = super().validate(attrs)
        
        serializer = UserDetailSerializer(self.user)
        data['user'] = serializer.data
        
        data['access_token'] = data.pop('access')
        data['refresh_token'] = data.pop('refresh')
        
        return data

# 1. Users 테이블 관련 API
# 1.1 회원가입
class UserRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()    
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = Users
        fields = ('username', 'email', 'password', 'password_confirm')
        extra_kwargs = {'password': {'write_only': True}} 
        # 응답에는 password 포함 X
    
    # 비밀번호 일치 검증
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "비밀번호가 일치하지 않습니다."})
        if Users.objects.filter(e_mail=data['e_mail']).exists():
            raise serializers.ValidationError({"e_mail": "이미 존재하는 이메일입니다."})
        return data
    
    # 이후 계정 생성
    def create(self, validated_data):
        # 비밀번호를 암호화하여 사용자 생성
        validated_data.app('password_confirm')
        validated_data['username'] = validated_data['user_name'] # username 필드 채우기
        user = Users.objects.create_user(**validated_data)
        return user

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ('user_id', 'username', 'e_mail', 'created_at', 'last_login')

# 채팅 관련 (Chatservice.js)
class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = '__all__'

class PromptLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptLog
        fields = '__all__'

class GeneratedResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedResult
        fields = '__all__'

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