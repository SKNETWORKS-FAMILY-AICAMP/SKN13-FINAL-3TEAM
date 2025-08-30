import csv
import json
import os
import logging
from django.conf import settings
from django.core.management.base import BaseCommand
from JJACKLETTE.models import InsightTrends, UserReview, EngineeringSpec

# 로거 설정
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'CSV 및 JSON 파일들을 읽어 DB 데이터를 임포트합니다.'

    def _clean_spec_value(self, value_str: str | None) -> int | None:
        """
        문자열 형태의 스펙 값에서 숫자만 추출하여 정수형으로 변환합니다.
        값이 비어있거나 숫자 변환에 실패하면 None을 반환합니다.
        """
        if not value_str:
            return None
        try:
            # 문자열에서 숫자가 아닌 문자를 모두 제거
            cleaned_val = ''.join(filter(str.isdigit, value_str))
            return int(cleaned_val) if cleaned_val else None
        except (ValueError, TypeError):
            logger.warning(f"'{value_str}'를 숫자로 변환할 수 없어 None으로 처리합니다.")
            self.stdout.write(self.style.WARNING(f"경고: '{value_str}'를 숫자로 변환할 수 없습니다. None으로 처리합니다."))
            return None

    def handle_specs(self):
        """car_specs 폴더 내 CSV 파일들을 읽어 InsightTrends 및 EngineeringSpec 테이블에 저장합니다."""
        dir_path = os.path.join(settings.BASE_DIR, 'text_data', 'DB', 'car_specs')
        self.stdout.write(self.style.SUCCESS(f"1. '{dir_path}'에서 CSV 스펙 데이터 임포트를 시작합니다..."))

        if not os.path.isdir(dir_path):
            self.stdout.write(self.style.ERROR(f"오류: '{dir_path}' 폴더를 찾을 수 없습니다."))
            return

        spec_map = {
            'length': '전장 (mm)',
            'width': '전폭 (mm)',
            'height': '전고 (mm)',
            'wheelbase': '축거 (mm)',  # wheel_base -> wheelbase 로 모델 필드명에 맞게 수정
            # 'front_track': '윤거 (전) (mm)', # 모델에 없는 필드이므로 주석 처리
            # 'rear_track': '윤거 (후) (mm)', # 모델에 없는 필드이므로 주석 처리
            'seating_capacity': '승차정원',
            'weight': '공차중량 (kg)',
            # 'fuel_tank': '연료탱크 (ℓ)', # 모델에 없는 필드이므로 주석 처리
        }

        car_count, spec_count = 0, 0
        for filename in os.listdir(dir_path):
            if not filename.lower().endswith(".csv"):
                continue

            car_name = os.path.splitext(filename)[0]
            file_path = os.path.join(dir_path, filename)

            car_model, created = InsightTrends.objects.get_or_create(
                car_name=car_name,
                defaults={'type': 'Unknown', 'release_year': 2025}
            )
            if created:
                car_count += 1
                self.stdout.write(f"  > 새로운 차종 '{car_name}'을(를) 추가했습니다.")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader)  # 헤더 행 건너뛰기
                    csv_data = {row[0].strip(): row[1].strip() for row in reader if len(row) >= 2}
            except FileNotFoundError:
                self.stdout.write(self.style.ERROR(f"오류: 파일을 찾을 수 없습니다 - {file_path}"))
                continue
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"오류: '{file_path}' 파일 읽기 중 문제 발생: {e}"))
                continue

            spec_defaults = {
                field_name: self._clean_spec_value(csv_data.get(csv_key))
                for field_name, csv_key in spec_map.items()
            }
            
            _, created = EngineeringSpec.objects.get_or_create(
                car_model=car_model,
                defaults=spec_defaults
            )
            if created:
                spec_count += 1

        self.stdout.write(self.style.SUCCESS(f"\n총 {car_count}개의 새로운 차종이 추가되었습니다."))
        self.stdout.write(self.style.SUCCESS(f"총 {spec_count}개의 엔지니어링 스펙이 추가되었습니다."))
        self.stdout.write(self.style.SUCCESS("CSV 스펙 임포트가 완료되었습니다.\n"))

    def handle_reviews(self):
        """hyundai_car_reviews.json 파일에서 UserReview 모델에 데이터를 임포트합니다."""
        file_path = os.path.join(settings.BASE_DIR, 'text_data', 'DB', 'hyundai_car_reviews.json')
        self.stdout.write(self.style.SUCCESS(f"2. '{file_path}'에서 리뷰 데이터 임포트를 시작합니다..."))
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"오류: '{file_path}' 파일을 찾을 수 없습니다."))
            return

        car_models_map = {car.car_name: car for car in InsightTrends.objects.all()}

        db_car_names = list(car_models_map.keys())
        db_car_names.sort(key=len, reverse=True)

        with open(file_path, 'r', encoding='utf-8') as f:
            reviews_data = json.load(f)

        count = 0
        skipped_count = 0
        for item in reviews_data:
            json_car_name = item['car_name']
            # 띄어쓰기, 대소문자 등 노멀라이즈하여 매칭 시도
            normalized_json_name = json_car_name.lower().replace(" ", "")
            matched_car_name = None

            for db_name in db_car_names:
                normalized_db_name = db_name.lower().replace(" ", "")
                if normalized_db_name in normalized_json_name:
                    matched_car_name = db_name
                    break 
            
            if matched_car_name:
                car_model_instance = car_models_map[matched_car_name]
                
                _, created = UserReview.objects.get_or_create(
                    car_model=car_model_instance,
                    review=item['review']
                )
                if created:
                    count += 1
            else:
                self.stdout.write(self.style.WARNING(f"경고: JSON의 '{json_car_name}'에 해당하는 차종을 DB에서 찾을 수 없어 리뷰를 건너뜁니다."))
                skipped_count += 1
        
        self.stdout.write(self.style.SUCCESS(f"\n총 {count}개의 새로운 리뷰가 성공적으로 임포트되었습니다."))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f"총 {skipped_count}개의 리뷰를 건너뛰었습니다."))

    def handle(self, *args, **kwargs):
        """메인 핸들러: 스펙과 리뷰 임포트를 순차적으로 실행합니다."""
        self.handle_specs()
        self.handle_reviews()
        self.stdout.write(self.style.SUCCESS("\n모든 데이터 임포트 작업이 완료되었습니다."))