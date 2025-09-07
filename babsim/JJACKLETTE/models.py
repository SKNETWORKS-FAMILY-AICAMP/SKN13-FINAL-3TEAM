from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
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

# 1. Users (사용자 정보)
class Users(AbstractUser):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_name = models.CharField(max_length=50, verbose_name='사용자 이름')
    username = None
    email = models.EmailField(unique=True, verbose_name='이메일')
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name='전화번호')
    company = models.CharField(max_length=100, blank=True, null=True, verbose_name='회사명')
    department = models.CharField(max_length=100, blank=True, null=True, verbose_name='부서명')
    position = models.CharField(max_length=100, blank=True, null=True, verbose_name='직책')
    profile_image = models.TextField(blank=True, null=True, verbose_name='프로필 이미지 URL')
    background_image = models.TextField(blank=True, null=True, verbose_name='배경 이미지 URL')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='계정 생성일자')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    # REQUIRED_FIELDS = ['user_name']

    objects = UserManager()

    def __str__(self):
        return self.email

# 2. Chat_session (챗봇 세션)
class ChatSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_sessions")
    session_title = models.CharField(max_length=200, blank=True, null=True, verbose_name='세션 제목')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

# 3. Prompt_log & Generated_result (통합 테이블)
class PromptLog(models.Model):
    prompt_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey('ChatSession', on_delete=models.CASCADE, related_name="prompt_logs")
    user_prompt = models.TextField()
    ai_response = models.TextField(blank=True, null=True)
    result_type = models.CharField(max_length=50, choices=[('text', 'Text'), ('image', 'Image'), ('3d', '3D'), ('4d', '4D')], blank=True, null=True)
    result_path = models.CharField(max_length=255, blank=True, null=True)
    response_time = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

# 4. Asset_library (에셋 라이브러리)
class AssetLibrary(models.Model):
    lib_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="asset_libraries")
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    documents = models.FileField(upload_to='assets/', blank=True, null=True)  # 파일 업로드용
    cover_photo = models.ImageField(upload_to='assets_cover_image/', blank=True, null=True)  # 이미지 업로드용
    lib_name = models.CharField(max_length=255, blank=True, null=True)  # 원본 파일명 저장용
    pdf_path = models.CharField(max_length=255, blank=True, null=True)  # S3 URL 저장용
    img_path = models.CharField(max_length=255, blank=True, null=True)  # S3 URL 저장용
    upload_date = models.DateField(auto_now_add=True)
    likes = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# 5. Library_comments (라이브러리 댓글)
class LibraryComments(models.Model):
    comment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # ERD의 lib_id 외래키 필드명을 따라 asset_library로 정의
    asset_library = models.ForeignKey('AssetLibrary', on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="library_comments")
    # ERD의 username은 user의 user_name을 참조하므로 별도 필드 불필요
    comments = models.TextField()
    likes = models.IntegerField(default=0)
    # user_liked는 별도의 Like 모델(Asset_likes, Comment_likes)로 관리되므로 여기서는 제외
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# 6. Insight_trends (인사이트 트렌드)
class InsightTrends(models.Model):
    car_model_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    car_name = models.CharField(max_length=100)
    type = models.CharField(max_length=50)
    release_year = models.IntegerField()
    model_3d_path = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

# 7. Engineering_spec (공학적 스펙)
class EngineeringSpec(models.Model):
    spec_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    car_model = models.ForeignKey('InsightTrends', on_delete=models.CASCADE, related_name='engineering_specs')
    # ERD의 한글 필드명을 영어로 변환하여 정의합니다.
    length = models.CharField(max_length=20, blank=True, null=True, verbose_name='전장')
    width = models.CharField(max_length=20, blank=True, null=True, verbose_name='전폭')
    height = models.CharField(max_length=20, blank=True, null=True, verbose_name='전고')
    wheelbase = models.CharField(max_length=20, blank=True, null=True, verbose_name='축거')
    seating_capacity = models.CharField(max_length=10, blank=True, null=True, verbose_name='승차정원')
    weight = models.CharField(max_length=20, blank=True, null=True, verbose_name='공차중량')
    created_at = models.DateTimeField(auto_now_add=True)

# 8. User_review (사용자 리뷰)
class UserReview(models.Model):
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    car_model = models.ForeignKey('InsightTrends', on_delete=models.CASCADE, related_name='user_reviews')
    data_id = models.CharField(max_length=50, blank=True, null=True)
    car_name = models.CharField(max_length=100, blank=True, null=True)
    review = models.TextField()
    tags = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

# 9. Recent_article (최근 기사)
class RecentArticle(models.Model):
    article_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    car_model = models.ForeignKey('InsightTrends', on_delete=models.CASCADE, related_name='recent_articles')
    car_name = models.CharField(max_length=100, blank=True, null=True)
    year = models.CharField(max_length=10, blank=True, null=True)
    explain = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

# 10. Asset_likes (에셋 좋아요)
class AssetLikes(models.Model):
    like_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset_library = models.ForeignKey('AssetLibrary', on_delete=models.CASCADE, related_name='asset_likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_asset_likes')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('asset_library', 'user') # 한 사용자가 한 에셋에 한 번만 좋아요

# 11. Comment_likes (댓글 좋아요)
class CommentLikes(models.Model):
    like_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comment = models.ForeignKey('LibraryComments', on_delete=models.CASCADE, related_name='comment_likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_comment_likes')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('comment', 'user') # 한 사용자가 한 댓글에 한 번만 좋아요
