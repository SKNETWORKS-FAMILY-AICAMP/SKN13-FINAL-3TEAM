from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from django.db import models
import uuid

# [추가] CustomUserManager 클래스를 Users 모델 위에 추가합니다.
# 이 클래스는 'username' 대신 'email'을 사용하여 사용자를 생성하는 방법을 Django에 알려줍니다.
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

# insight_trends
class InsightTrends(models.Model):
    car_model_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    car_name = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    release_year = models.IntegerField()

# design_material
class DesignMaterial(models.Model):
    material_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    car_model = models.ForeignKey(InsightTrends, on_delete=models.CASCADE, related_name='design_materials')
    material_type = models.CharField(max_length=100)
    usage_area = models.CharField(max_length=100)

# engineering_spec
class EngineeringSpec(models.Model):
    spec_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    car_model = models.ForeignKey(InsightTrends, on_delete=models.CASCADE, related_name='engineering_specs')
    cd_value = models.FloatField()
    weight = models.IntegerField()
    material_al_ratio = models.FloatField()
    wheel_base = models.IntegerField()
    pedestrian_safety_score = models.FloatField()
    sensor_ready = models.BooleanField()

# sales_stat
class SalesStat(models.Model):
    id = models.AutoField(primary_key=True)
    car_model = models.ForeignKey(InsightTrends, on_delete=models.CASCADE, related_name='sales_stats')
    year = models.IntegerField()
    month = models.IntegerField()
    units_sold = models.IntegerField()
    class Meta:
        unique_together = ('car_model', 'year', 'month')

# user_review
class UserReview(models.Model):
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    car_model = models.ForeignKey(InsightTrends, on_delete=models.CASCADE, related_name='user_reviews')
    sentiment_score = models.FloatField()
    mentioned_features = models.TextField(blank=True, null=True)

# ------------------------------------------------------------------------------------------------
# insight_trends 내의 기능 위에 먼저 정의

# users (Custom User Model)
class Users(AbstractUser):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # [수정] email 필드를 unique하게 설정합니다.
    email = models.EmailField(unique=True)
    # [수정] username 필드를 사용하지 않도록 None으로 설정합니다.
    username = None

    # [수정] Django 인증 시스템이 username 대신 email을 ID로 사용하도록 설정합니다.
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    # [추가] 위에서 만든 UserManager를 이 모델의 공식 관리자로 지정합니다.
    objects = UserManager()

    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    user_prompt = models.TextField(null=True, blank=True)
    ai_response = models.TextField(null=True, blank=True)

# chat_session
class ChatSession(models.Model):
    """챗봇 세션 모델"""
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_sessions")
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

# prompt_log
class PromptLog(models.Model):
    prompt_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="prompt_logs")
    user_prompt = models.TextField()
    ai_response = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

# generated_result
class GeneratedResult(models.Model):
    result_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prompt = models.ForeignKey(PromptLog, on_delete=models.CASCADE, related_name="generated_results")
    result_type = models.CharField(max_length=50, choices=[('text', 'Text'), ('image', 'Image'), ('3d', '3D'), ('4d', '4D')])
    result_path = models.CharField(max_length=255, blank=True)
    result = models.TextField(blank=True, null=True)

# asset_library
class AssetLibrary(models.Model):
    lib_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="asset_libraries")
    documents = models.FileField(upload_to='assets/documents/') # FileField로 변경하여 파일 직접 저장
    img_path = models.CharField(max_length=255, blank=True, null=True)

# library_comments
class LibraryComments(models.Model):
    comment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    library_asset = models.ForeignKey(AssetLibrary, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="library_comments")
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


