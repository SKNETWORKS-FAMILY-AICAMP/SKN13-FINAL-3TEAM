import csv
import json
import os
import logging
from datetime import datetime
from collections import defaultdict, Counter
from statistics import mean
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from JJACKLETTE.models import InsightTrends, UserReview, EngineeringSpec, RecentArticle

# 로거 설정
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'CSV 및 JSON 파일들을 읽어 DB 데이터를 임포트합니다.'

    def get_category_map(self):
        """차량 이름과 카테고리 이름을 매핑하는 딕셔너리를 반환합니다."""
        categories = {
            '수소 / 전기차': ['더 뉴 아이오닉 6', '디 올 뉴 넥쏘', '아이오닉 5', '코나 Electric', '아이오닉 9', 'ST1', '포터 II Electric', '포터 II Electric 특장차', '2026 캐스퍼 일렉트릭'],
            'N': ['아반떼 N', '아이오닉 5 N'],
            '승용': ['그랜저', '그랜저 Hybrid', '아반떼', '아반떼 Hybrid', '쏘나타 디 엣지', '쏘나타 디 엣지 Hybrid'],
            'SUV': ['싼타페', '싼타페 Hybrid', '투싼', '투싼 Hybrid', '코나', '코나 Hybrid', '베뉴', '디 올 뉴 팰리세이드', '디 올 뉴 팰리세이드 Hybrid', '2026 캐스퍼'],
            'MPV': ['스타리아 라운지', '스타리아 라운지 Hybrid', '스타리아', '스타리아 Hybrid', '스타리아 킨더', '스타리아 라운지 캠퍼', '스타리아 라운지 캠퍼 Hybrid', '스타리아 라운지 리무진', '스타리아 라운지 리무진 Hybrid'],
            '소형트럭&택시': ['그랜저 택시', '쏘나타 택시', '스타리아 라운지 모빌리티', '스타리아 라운지 모빌리티 Hybrid', '포터 II', '포터 II 특장차'],
            '트럭': ['더 뉴 마이티', '더 뉴 파비스', '뉴파워트럭', '더 뉴 엑시언트', '엑시언트 수소전기트럭'],
            '버스': ['쏠라티', '카운티', '카운티 일렉트릭', '일렉시티 타운', '뉴 슈퍼에어로시티', '일렉시티', '일렉시티 수소전기버스', '일렉시티 이층버스', '유니버스', '유니버스 수소전기버스', '유니버스 모바일 오피스']
        }
        car_to_category = {}
        for category, cars in categories.items():
            for car in cars:
                car_to_category[car] = category
        return car_to_category

    def _clean_spec_value(self, value_str: str | None) -> int | None:
        if not value_str:
            return None
        try:
            cleaned_val = ''.join(filter(str.isdigit, value_str))
            return int(cleaned_val) if cleaned_val else None
        except (ValueError, TypeError):
            logger.warning(f"'{value_str}'를 숫자로 변환할 수 없어 None으로 처리합니다.")
            self.stdout.write(self.style.WARNING(f"경고: '{value_str}'를 숫자로 변환할 수 없습니다. None으로 처리합니다."))
            return None

    def get_base_car_name(self, car_name):
        """차량명에서 기본 차량명을 추출합니다."""
        # 특별한 매핑 규칙
        special_mappings = {
            '쏘나타 택시': '쏘나타 디 엣지',
            '그랜저 택시': '그랜저',
            '포터 II Electric 특장차': '포터 II Electric',
            '포터 II 특장차': '포터 II',
            '스타리아 라운지 모빌리티': '스타리아 라운지',
            '스타리아 라운지 모빌리티 Hybrid': '스타리아 라운지',
        }
        
        if car_name in special_mappings:
            return special_mappings[car_name]
        
        # 택시 제거
        if ' 택시' in car_name:
            return car_name.replace(' 택시', '')
        
        # Hybrid 제거
        if ' Hybrid' in car_name:
            return car_name.replace(' Hybrid', '')
        
        # 스타리아 라운지 관련 처리
        if '스타리아 라운지' in car_name:
            if '스타리아 라운지 캠퍼' in car_name:
                return '스타리아 라운지 캠퍼'
            elif '스타리아 라운지 모빌리티' in car_name:
                return '스타리아 라운지 모빌리티'
            elif '스타리아 라운지 리무진' in car_name:
                return '스타리아 라운지 리무진'
            else:
                return '스타리아 라운지'
        
        # 기본 차량명 반환
        return car_name

    # ---------------------- 이름 정규화/매핑 (GLB 기반) ----------------------
    @staticmethod
    def _normalize_name(name: str) -> str:
        if not name:
            return ''
        s = name.lower().strip()
        # 공백/특수문자 제거
        for ch in [' ', '\t', '\n', '-', '_']:
            s = s.replace(ch, '')
        # 접미 키워드 제거
        for kw in ['hybrid', ' hev', 'phev', 'taxi', ' 택시']:
            s = s.replace(kw, '')
        # 괄호 내용 제거
        import re
        s = re.sub(r"[()\[\]{}]+", '', s)
        return s

    def _get_canonical_car_name(self, json_car_name: str, db_car_names: list[str]) -> str | None:
        """GLB/CSV를 반영해 DB 내 존재하는 이름들(db_car_names) 중에서 json_car_name에 대한 최적 매칭을 반환.
        규칙: 공백/하이브리드/택시 등 제거 후 부분 포함(Longest match 우선)."""
        if not json_car_name:
            return None
        json_norm = self._normalize_name(json_car_name)
        if not json_norm:
            return None

        # 우선 특수 매핑 적용
        special = {
            '쏘나타': '쏘나타 디 엣지',
        }
        if json_car_name in special and special[json_car_name] in db_car_names:
            return special[json_car_name]

        best = None
        best_len = 0
        for db_name in db_car_names:
            dn = self._normalize_name(db_name)
            if not dn:
                continue
            if dn in json_norm or json_norm in dn:
                # 더 긴 이름을 우선
                l = max(len(dn), len(json_norm))
                if l > best_len:
                    best = db_name
                    best_len = l
        return best

    @staticmethod
    def _is_hybrid_source(name: str) -> bool:
        s = (name or '').lower()
        return ('hybrid' in s) or ('hev' in s) or ('하이브리드' in name)

    def handle_specs(self):
        """car_specs 폴더 내 CSV 파일들을 읽어 InsightTrends 및 EngineeringSpec 테이블에 저장합니다."""
        dir_path = os.path.join(settings.BASE_DIR, 'text_data', 'DB', 'car_specs')
        self.stdout.write(self.style.SUCCESS(f"1. '{dir_path}'에서 CSV 스펙 데이터 임포트를 시작합니다..."))

        if not os.path.isdir(dir_path):
            self.stdout.write(self.style.ERROR(f"오류: '{dir_path}' 폴더를 찾을 수 없습니다."))
            return

        car_category_map = self.get_category_map()
        # CSV 컬럼명이 파일마다 조금씩 다를 수 있어 유연 매핑을 사용합니다.
        # 각 내부 필드에 대해 가능한 헤더 후보를 정의합니다.
        spec_header_candidates = {
            'length': ['전장', '전장(mm)', '전장 (mm)'],
            'width': ['전폭', '전폭(mm)', '전폭 (mm)'],
            'height': ['전고', '전고(mm)', '전고 (mm)'],
            'wheelbase': ['축거', '축거(mm)', '축거 (mm)'],
            'seating_capacity': ['승차정원', '승차 정원'],
            'weight': ['공차중량', '공차중량(kg)', '공차중량 (kg)', '중량', '중량(kg)'],
        }

        def _lookup_spec_value(row_map: dict, header_candidates: list[str]) -> str | None:
            """주어진 CSV row 맵에서 후보 헤더들 중 하나를 찾아 값을 반환합니다.
            공백, 괄호, 단위를 유연하게 처리합니다."""
            if not row_map:
                return None
            # 1) 정확/근사 키 매칭을 위해 정규화한 키 맵 생성
            def _normalize_label(s: str) -> str:
                return (
                    s.replace(' ', '')
                     .replace('(', '')
                     .replace(')', '')
                     .replace('mm', '')
                     .replace('MM', '')
                     .replace('㎜', '')
                     .replace('kg', '')
                     .replace('KG', '')
                )

            normalized_map = { _normalize_label(k): v for k, v in row_map.items() }

            # 2) 후보 라벨 중 매칭되는 첫 값을 반환
            for cand in header_candidates:
                norm_cand = _normalize_label(cand)
                # 정확 일치
                if norm_cand in normalized_map:
                    return normalized_map[norm_cand]
                # 시작 일치 (예: 전장xxx)
                for key_norm, val in normalized_map.items():
                    if key_norm.startswith(norm_cand):
                        return val
            return None

        # CSV 파일에서 스펙 데이터를 미리 로드
        csv_specs = {}
        for filename in os.listdir(dir_path):
            if not filename.lower().endswith(".csv"):
                continue
            
            car_name = os.path.splitext(filename)[0].strip()
            file_path = os.path.join(dir_path, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    next(reader)
                    csv_data = {row[0].strip(): row[1].strip() for row in reader if len(row) >= 2}
                    csv_specs[car_name] = csv_data
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"오류: '{file_path}' 파일 읽기 중 문제 발생: {e}"))
                continue

        car_count, spec_count = 0, 0
        
        # 모든 차량에 대해 처리 (CSV에 있는 차량 + GLB에만 있는 차량)
        all_cars = set(csv_specs.keys())
        
        # GLB에만 있는 차량들도 추가 (React 빌드된 모델 파일들)
        glb_files = []
        try:
            # React 빌드된 모델 파일 경로 확인
            models_path = 'react/build/models'
            if os.path.exists(models_path):
                glb_files = [os.path.splitext(f)[0] for f in os.listdir(models_path) if f.endswith('.glb')]
                self.stdout.write(f"GLB 모델 파일 {len(glb_files)}개를 찾았습니다.")
            else:
                self.stdout.write(self.style.WARNING("GLB 모델 파일 경로를 찾을 수 없습니다. CSV 데이터만 처리합니다."))
        except FileNotFoundError:
            # GLB 파일이 없는 경우 무시하고 계속 진행
            self.stdout.write(self.style.WARNING("GLB 모델 파일 경로를 찾을 수 없습니다. CSV 데이터만 처리합니다."))
        
        all_cars.update(glb_files)
        
        for car_name in all_cars:
            car_type = car_category_map.get(car_name, 'Unknown')
            
            # InsightTrends에 차량 추가/업데이트
            car_model, created = InsightTrends.objects.update_or_create(
                car_name=car_name,
                defaults={'type': car_type, 'release_year': 2025}
            )
            if created:
                car_count += 1
                self.stdout.write(f"  > 새로운 차종 '{car_name}' (유형: {car_type})을(를) 추가했습니다.")

            # 스펙 데이터 처리
            spec_data = None
            
            # 직접 CSV가 있는 경우
            if car_name in csv_specs:
                spec_data = csv_specs[car_name]
                self.stdout.write(f"  > '{car_name}' 스펙을 직접 CSV에서 로드했습니다.")
            else:
                # 기본 차량의 스펙을 사용하는 경우
                base_car_name = self.get_base_car_name(car_name)
                if base_car_name in csv_specs:
                    spec_data = csv_specs[base_car_name]
                    self.stdout.write(f"  > '{car_name}' 스펙을 기본 차량 '{base_car_name}'에서 복사했습니다.")
                else:
                    self.stdout.write(self.style.WARNING(f"  > '{car_name}'의 기본 차량 '{base_car_name}' CSV를 찾을 수 없습니다."))
                    continue

            if spec_data:
                # 유연 헤더 매칭으로 값 조회 후 정수 정규화(가능하면), 아니면 원문 저장
                resolved = {
                    'length': _lookup_spec_value(spec_data, spec_header_candidates['length']),
                    'width': _lookup_spec_value(spec_data, spec_header_candidates['width']),
                    'height': _lookup_spec_value(spec_data, spec_header_candidates['height']),
                    'wheelbase': _lookup_spec_value(spec_data, spec_header_candidates['wheelbase']),
                    'seating_capacity': _lookup_spec_value(spec_data, spec_header_candidates['seating_capacity']),
                    'weight': _lookup_spec_value(spec_data, spec_header_candidates['weight']),
                }

                # DB 필드는 CharField이므로 문자열 보존. 숫자만 추출 가능한 경우 숫자 문자열로 저장
                def _normalize_str(v):
                    if v is None:
                        return None
                    s = str(v).strip()
                    # 숫자만 추출하되, 없으면 원문 보존
                    digits = ''.join(ch for ch in s if ch.isdigit())
                    return digits if digits else s

                spec_defaults = {k: _normalize_str(v) for k, v in resolved.items()}
                
                _, created = EngineeringSpec.objects.update_or_create(
                    car_model=car_model,
                    defaults=spec_defaults
                )
                if created:
                    spec_count += 1

        self.stdout.write(self.style.SUCCESS(f"\n총 {car_count}개의 새로운 차종이 추가되었습니다."))
        self.stdout.write(self.style.SUCCESS(f"총 {spec_count}개의 엔지니어링 스펙이 추가/업데이트되었습니다."))
        self.stdout.write(self.style.SUCCESS("CSV 스펙 임포트가 완료되었습니다.\n"))

    def handle_reviews(self):
        """hyundai_car_reviews.json 파일에서 UserReview 모델에 데이터를 임포트합니다."""
        file_path = os.path.join(settings.BASE_DIR, 'text_data', 'DB', 'hyundai_car_reviews.json')
        self.stdout.write(self.style.SUCCESS(f"2. '{file_path}'에서 리뷰 데이터 임포트를 시작합니다..."))
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"오류: '{file_path}' 파일을 찾을 수 없습니다."))
            return

        car_models_map = {car.car_name.strip(): car for car in InsightTrends.objects.all()}
        db_car_names = sorted([name.strip() for name in car_models_map.keys()], key=len, reverse=True)

        with open(file_path, 'r', encoding='utf-8') as f:
            reviews_data = json.load(f)

        count, updated_count, skipped_count = 0, 0, 0
        for item in reviews_data:
            json_car_name = item.get('car_name')
            if not json_car_name:
                continue

            matched_car_name = self._get_canonical_car_name(json_car_name, db_car_names)
            
            if matched_car_name:
                car_model_instance = car_models_map[matched_car_name]
                
                _, created = UserReview.objects.update_or_create(
                    data_id=item.get('data_id'),
                    car_model=car_model_instance,
                    defaults={
                        'car_name': item.get('car_name'),
                        'rating': item.get('rating'),
                        'review': item.get('review', ''),
                        'tags': item.get('tags', {})
                    }
                )
                if created:
                    count += 1
                else:
                    updated_count += 1
            else:
                self.stdout.write(self.style.WARNING(f"경고: JSON의 '{json_car_name}'에 해당하는 차종을 DB에서 찾을 수 없어 리뷰를 건너뜁니다."))
                skipped_count += 1
        
        self.stdout.write(self.style.SUCCESS(f"\n총 {count}개의 새로운 리뷰가 추가되었습니다."))
        self.stdout.write(self.style.SUCCESS(f"총 {updated_count}개의 리뷰가 업데이트되었습니다."))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f"총 {skipped_count}개의 리뷰를 건너뛰었습니다."))
        self.stdout.write(self.style.SUCCESS("리뷰 임포트가 완료되었습니다.\n"))

    def handle_history(self):
        """hyundai_car_history.json 파일에서 RecentArticle 모델에 데이터를 임포트합니다."""
        file_path = os.path.join(settings.BASE_DIR, 'text_data', 'DB', 'hyundai_car_history.json')
        self.stdout.write(self.style.SUCCESS(f"3. '{file_path}'에서 차량 역사 데이터 임포트를 시작합니다..."))
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"오류: '{file_path}' 파일을 찾을 수 없습니다."))
            return

        car_models_map = {car.car_name.strip(): car for car in InsightTrends.objects.all()}
        db_car_names = sorted([name.strip() for name in car_models_map.keys()], key=len, reverse=True)

        with open(file_path, 'r', encoding='utf-8') as f:
            history_data = json.load(f)

        count, updated_count, skipped_count = 0, 0, 0
        for item in history_data:
            json_car_name = item.get('car_name')
            if not json_car_name:
                continue

            matched_car_name = self._get_canonical_car_name(json_car_name, db_car_names)
            
            if matched_car_name:
                # 대상 타겟 계산 (일반/하이브리드 동시 분배 규칙)
                base = matched_car_name.replace(' Hybrid', '') if matched_car_name.endswith(' Hybrid') else matched_car_name
                hybrid = f"{base} Hybrid"
                src_name = item.get('car_name') or ''
                is_src_hybrid = self._is_hybrid_source(src_name)

                targets = []
                if is_src_hybrid:
                    # 소스가 하이브리드 성격이면 하이브리드 우선, 없으면 매칭된 대상만
                    if hybrid in car_models_map:
                        targets = [hybrid]
                    else:
                        targets = [matched_car_name]
                else:
                    # 일반 소스면 일반/하이브리드 둘 다 존재 시 둘 다
                    if base in car_models_map:
                        targets.append(base)
                    if hybrid in car_models_map:
                        targets.append(hybrid)
                    if not targets:
                        targets = [matched_car_name]

                # 공통 저장 루틴
                raw_year = item.get('year')
                year_str = ''
                if raw_year is not None:
                    import re
                    m = re.search(r"(19|20)\d{2}", str(raw_year))
                    if m:
                        year_str = m.group(0)
                year_str = year_str[:10]

                for tgt in targets:
                    car_model_instance = car_models_map[tgt]
                    _, created = RecentArticle.objects.update_or_create(
                        car_model=car_model_instance,
                        car_name=item.get('car_name'),
                        year=year_str,
                        defaults={'explain': item.get('explain', '')}
                    )
                    if created:
                        count += 1
                    else:
                        updated_count += 1
            else:
                self.stdout.write(self.style.WARNING(f"경고: JSON의 '{json_car_name}'에 해당하는 차종을 DB에서 찾을 수 없어 히스토리를 건너뜁니다."))
                skipped_count += 1
        
        self.stdout.write(self.style.SUCCESS(f"\n총 {count}개의 새로운 차량 역사가 추가되었습니다."))
        self.stdout.write(self.style.SUCCESS(f"총 {updated_count}개의 차량 역사가 업데이트되었습니다."))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f"총 {skipped_count}개의 차량 역사를 건너뛰었습니다."))
        self.stdout.write(self.style.SUCCESS("차량 역사 임포트가 완료되었습니다.\n"))

    def calculate_aggregates(self):
        """차량별 집계 통계를 계산하고 저장합니다"""
        self.stdout.write(self.style.SUCCESS("4. 차량별 집계 통계를 계산합니다..."))
        
        with transaction.atomic():
            for insight_trend in InsightTrends.objects.all():
                reviews = UserReview.objects.filter(car_model=insight_trend)
                
                if not reviews.exists():
                    continue
                
                # 1. 평균 평점 계산
                ratings = [r.rating for r in reviews if r.rating is not None]
                if ratings:
                    avg_rating = round(mean(ratings), 2)
                    insight_trend.average_rating = avg_rating
                    self.stdout.write(f"  {insight_trend.car_name}: 평균 평점 {avg_rating}")

                # 2. 리뷰 카테고리 통계 계산
                tag_stats = defaultdict(list)
                
                for review in reviews:
                    tags = review.tags or {}
                    if isinstance(tags, dict):
                        for tag_key, tag_value in tags.items():
                            if tag_value and isinstance(tag_value, str):
                                tag_stats[tag_key].append(tag_value)

                # 각 태그별로 가장 많이 나온 문장과 비율 계산
                review_categories = {}
                total_reviews = reviews.count()
                
                for tag_key, tag_values in tag_stats.items():
                    if not tag_values:
                        continue
                        
                    # 가장 많이 나온 문장 찾기
                    value_counts = Counter(tag_values)
                    most_common = value_counts.most_common(1)[0]
                    most_common_text = most_common[0]
                    most_common_count = most_common[1]
                    percentage = round((most_common_count / total_reviews) * 100, 1)
                    
                    review_categories[tag_key] = {
                        'most_common_text': most_common_text,
                        'count': most_common_count,
                        'percentage': percentage,
                        'total_mentions': len(tag_values)
                    }

                insight_trend.review_categories = review_categories
                insight_trend.save()

                # 로그 출력
                for tag_key, stats in review_categories.items():
                    self.stdout.write(
                        f"    {tag_key}: \"{stats['most_common_text']}\" "
                        f"({stats['count']}회, {stats['percentage']}%)"
                    )

        self.stdout.write(self.style.SUCCESS("집계 통계 계산이 완료되었습니다.\n"))

    def handle(self, *args, **kwargs):
        """메인 핸들러: 스펙, 리뷰, 히스토리 임포트를 순차적으로 실행합니다."""
        self.handle_specs()
        self.handle_reviews()
        self.handle_history()
        self.calculate_aggregates()
        self.stdout.write(self.style.SUCCESS("\n모든 데이터 임포트 작업이 완료되었습니다."))