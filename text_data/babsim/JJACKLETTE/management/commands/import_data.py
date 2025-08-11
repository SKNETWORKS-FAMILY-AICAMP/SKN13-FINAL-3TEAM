# babsim/JJACKLETTE/management/commands/import_data.py

import json
import csv
import os
from django.core.management.base import BaseCommand
from JJACKLETTE.models import InsightTrends, UserReview, EngineeringSpec
from django.conf import settings

class Command(BaseCommand):
    help = 'text_data/DB/ 폴더에서 자동차 관련 데이터를 가져와 DB에 저장합니다.'

    def handle_insight_trends(self):
        """
        리뷰와 스펙 데이터에 등장하는 모든 차종 정보를 먼저 InsightTrends 모델에 저장합니다.
        (다른 데이터들이 이 모델을 참조해야 하므로 가장 먼저 실행되어야 합니다.)
        """
        self.stdout.write("1. InsightTrends 데이터 생성 시작...")
        
        # 리뷰 파일에서 차종 정보 추출
        review_file_path = os.path.join(settings.BASE_DIR, 'text_data', 'DB', 'hyundai_car_reviews.json')
        with open(review_file_path, 'r', encoding='utf-8') as f:
            reviews_data = json.load(f)
        
        car_names = {item['car_name'] for item in reviews_data}

        # 스펙 파일에서 차종 정보 추출
        spec_dir_path = os.path.join(settings.BASE_DIR, 'text_data', 'DB', 'car_specs')
        for filename in os.listdir(spec_dir_path):
            if filename.endswith('.csv'):
                car_names.add(filename[:-4])

        count = 0
        for car_name in car_names:
            # 중복 방지: car_name이 이미 없으면 새로 생성
            _, created = InsightTrends.objects.get_or_create(
                car_name=car_name,
                defaults={
                    # 나머지 정보는 기본값 또는 임시값으로 설정
                    'type': 'Sedan', # 임시값
                    'release_year': 2024 # 임시값
                }
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f"총 {count}개의 새로운 차종(InsightTrends) 정보가 추가되었습니다."))


    def handle_reviews(self):
        """hyundai_car_reviews.json 파일에서 리뷰 데이터를 임포트합니다."""
        file_path = os.path.join(settings.BASE_DIR, 'text_data', 'DB', 'hyundai_car_reviews.json')
        self.stdout.write(f"2. '{file_path}'에서 리뷰 데이터 임포트 시작...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reviews_data = json.load(f)

        count = 0
        for item in reviews_data:
            # 리뷰를 저장하기 전에, 이 리뷰가 속한 차종(InsightTrends)이 DB에 있는지 확인
            try:
                car_model = InsightTrends.objects.get(car_name=item['car_name'])
                
                # 중복 방지
                _, created = UserReview.objects.get_or_create(
                    # review_id는 UUID로 자동 생성되므로, 다른 필드로 중복을 확인해야 합니다.
                    # 여기서는 car_model과 review 내용이 같으면 중복으로 간주합니다.
                    car_model_id=car_model,
                    mentioned_features=item['review'][:255], # 임시로 리뷰 내용 앞부분을 사용
                    defaults={
                        'sentiment_score': 0.8, # 임시값
                    }
                )
                if created:
                    count += 1
            except InsightTrends.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"경고: '{item['car_name']}' 차종을 찾을 수 없어 리뷰를 건너뜁니다."))
        
        self.stdout.write(self.style.SUCCESS(f"총 {count}개의 새로운 리뷰가 성공적으로 임포트되었습니다."))


    def handle_specs(self):
        """car_specs 폴더의 모든 CSV 파일에서 스펙 데이터를 임포트합니다."""
        dir_path = os.path.join(settings.BASE_DIR, 'text_data', 'DB', 'car_specs')
        self.stdout.write(f"3. '{dir_path}'에서 스펙 데이터 임포트 시작...")
        
        count = 0
        for filename in os.listdir(dir_path):
            if filename.endswith('.csv'):
                car_name_from_file = filename[:-4]
                
                try:
                    # 스펙을 저장하기 전에, 이 스펙이 속한 차종(InsightTrends)이 DB에 있는지 확인
                    car_model = InsightTrends.objects.get(car_name=car_name_from_file)
                    file_path = os.path.join(dir_path, filename)
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        next(reader) # 헤더 행 건너뛰기
                        
                        for row in reader:
                            spec_name = row[0]
                            # EngineeringSpec 모델 필드에 맞춰 데이터 할당
                            if spec_name == '공차중량':
                                # ' kg' 제거하고 숫자로 변환
                                weight_value = int(row[1].replace(',', '').replace(' kg', ''))
                                _, created = EngineeringSpec.objects.get_or_create(
                                    car_model_id=car_model,
                                    weight=weight_value,
                                    defaults={
                                        # 나머지 정보는 기본값 또는 임시값으로 설정
                                        'cd_value': 0.28,
                                        'material_al_ratio': 0.15,
                                        'wheel_base': 2900,
                                        'pedestrian_safety_score': 4.5,
                                        'sensor_ready': True
                                    }
                                )
                                if created:
                                    count += 1

                except InsightTrends.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"경고: '{car_name_from_file}' 차종을 찾을 수 없어 스펙을 건너뜁니다."))

        self.stdout.write(self.style.SUCCESS(f"총 {count}개의 새로운 엔지니어링 스펙이 성공적으로 임포트되었습니다."))

    def handle(self, *args, **kwargs):
        # 데이터 관계(ForeignKey) 때문에 반드시 이 순서대로 실행해야 합니다.
        self.handle_insight_trends()
        self.handle_reviews()
        self.handle_specs()