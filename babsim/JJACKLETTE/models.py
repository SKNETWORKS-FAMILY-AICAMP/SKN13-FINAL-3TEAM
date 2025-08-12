from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

# 1. design_material
class DesignMaterial(models.Model):
    
    material_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    car_model_id = models.ForeignKey('InsightTrends', on_delete=models.CASCADE)
    material_type = models.CharField(max_length=100)
    usage_area = models.CharField(max_length=100)

    # 2. engineering_spec
class EngineeringSpec(models.Model):
    
    spec_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    car_model_id = models.ForeignKey('InsightTrends', on_delete=models.CASCADE)
    cd_value = models.FloatField()
    weight = models.IntegerField()
    material_al_ratio = models.FloatField()
    wheel_base = models.IntegerField()
    pedestrian_safety_score = models.FloatField()
    sensor_ready = models.BooleanField()

# 3. sales_stat
class SalesStat(models.Model):
    car_model_id = models.ForeignKey('InsightTrends', on_delete=models.CASCADE)
    year = models.IntegerField()
    month = models.IntegerField()
    units_sold = models.IntegerField()

    class Meta: # 같은 차종, 같은 연월에 두 번 이상 판매 데이터가 들어갈 수 없다는 비즈니스 로직을 보장하기 위한 것
            unique_together = (('car_model_id', 'year', 'month'),)

    # 4. user_review
class UserReview(models.Model):
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    car_model_id = models.ForeignKey('InsightTrends', on_delete=models.CASCADE)
    sentiment_score = models.FloatField()
    mentioned_features = models.TextField(blank=True, null=True)

# 5. insight_trends
class InsightTrends(models.Model):
    car_model_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    car_name = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    release_year = models.IntegerField()

# 6. users (Custom User Model)
class Users(AbstractUser):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # AbstractUser가 기본적으로 제공하는 필드 (username, email, password)는 제거
    # user_name -> username, e_mail -> email 로 매핑됨
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    user_prompt = models.TextField()
    ai_response = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

# 7. chat_session
class ChatSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(  # ← 변경: 필드명 user로 정리 + AUTH_USER_MODEL 사용
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_sessions"
    )
    title = models.CharField(max_length=200, blank=True)  # ← 변경: 세션 제목(선택)
    # user_id = models.ForeignKey('Users', on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True) # 변경: 세션 상태 플래그

# 8. prompt_log
class PromptLog(models.Model):
    prompt_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.ForeignKey('ChatSession', on_delete=models.CASCADE)
    user_prompt = models.TextField()
    ai_response = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

# 9. generated_result
class GeneratedResult(models.Model):
    result_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prompt_id = models.ForeignKey('PromptLog', on_delete=models.CASCADE)
    result_type = models.CharField(max_length=50)
    result_path = models.CharField(max_length=255)
    result = models.TextField(blank=True, null=True)

# 10. asset_library
class AssetLibrary(models.Model): 
    lib_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # user = models.ForeignKey('Users', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # ← 수정
    documents = models.TextField(blank=True, null=True)
    img_path = models.CharField(max_length=255, blank=True, null=True)

# 11. library_comments
class LibraryComments(models.Model):
    comment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lib_id = models.ForeignKey('AssetLibrary', on_delete=models.CASCADE)
    # user_id = models.ForeignKey('Users', on_delete=models.CASCADE)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # ← 수정
    comments = models.TextField()