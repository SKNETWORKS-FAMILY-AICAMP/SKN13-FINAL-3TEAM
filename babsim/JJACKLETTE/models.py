from django.db import models

# PostgreSQL에 저장될 데이터 모델들을 정의
# 예를 들어, 아이템 정보, 사용자 정보 등
# 벡터 임베딩 값을 저장해야 한다면, VectorField (별도 라이브러리 필요) 또는
# ArrayField (PostgreSQL의 배열 필드)를 사용하여 임베딩 값을 저장할 수 있습니다.
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

# 6. users
class Users(models.Model):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    password = models.CharField(max_length=50)
    user_name = models.CharField(max_length=50)
    e_mail = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

# 7. chat_session
class ChatSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.ForeignKey('Users', on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

# 8. prompt_log
class PromptLog(models.Model):
    prompt_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.ForeignKey('ChatSession', on_delete=models.CASCADE)
    user_prompt = models.TextField()
    ai_response = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
# ai_response: max_length 255 -> textfield로 수정

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
    user = models.ForeignKey('Users', on_delete=models.CASCADE)
    documents = models.TextField(blank=True, null=True)
    img_path = models.CharField(max_length=255, blank=True, null=True)

# 11. library_comments
class LibraryComments(models.Model):
    comment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lib_id = models.ForeignKey('AssetLibrary', on_delete=models.CASCADE)
    user_id = models.ForeignKey('Users', on_delete=models.CASCADE)
    comments = models.TextField()from django.db import models
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

# 6. users
class Users(models.Model):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    password = models.CharField(max_length=50)
    user_name = models.CharField(max_length=50)
    e_mail = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

# 7. chat_session
class ChatSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.ForeignKey('Users', on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

# 8. prompt_log
class PromptLog(models.Model):
    prompt_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.ForeignKey('ChatSession', on_delete=models.CASCADE)
    user_prompt = models.TextField()
    ai_response = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
# ai_response: max_length 255 -> textfield로 수정

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
    user = models.ForeignKey('Users', on_delete=models.CASCADE)
    documents = models.TextField(blank=True, null=True)
    img_path = models.CharField(max_length=255, blank=True, null=True)

# 11. library_comments
class LibraryComments(models.Model):
    comment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lib_id = models.ForeignKey('AssetLibrary', on_delete=models.CASCADE)
    user_id = models.ForeignKey('Users', on_delete=models.CASCADE)
    comments = models.TextField()
