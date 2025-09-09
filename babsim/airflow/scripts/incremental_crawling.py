# incremental_crawling.py - 증분 크롤링 스크립트

import time, json, re, os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

def normalize_car_name(car_name):
    """크롤링된 차량명을 DB 표준명으로 변환"""
    if not car_name:
        return car_name
    
    # 특수 매핑 규칙
    mappings = {
        '더 뉴 아이오닉 6': '더 뉴 아이오닉 6',
        '아이오닉 6': '더 뉴 아이오닉 6',
        '아이오닉9': '아이오닉 9',
        '아이오닉 9': '아이오닉 9',
        '넥쏘': '디 올 뉴 넥쏘',
        '팰리세이드': '디 올 뉴 팰리세이드',
        '더 뉴 투싼': '투싼',
        '더 뉴 아이오닉 5': '아이오닉 5',
        '싼타페': '싼타페',  # CSV 기준으로 통일
        '산타페': '싼타페',
    }
    
    # 직접 매핑이 있으면 사용
    if car_name in mappings:
        return mappings[car_name]
    
    # Hybrid 제거 후 매핑 시도
    base_name = car_name.replace(' Hybrid', '').replace(' 하이브리드', '')
    if base_name in mappings:
        mapped = mappings[base_name]
        if 'Hybrid' in car_name:
            return f"{mapped} Hybrid"
        return mapped
    
    # 택시 제거 후 매핑 시도
    if ' 택시' in car_name:
        base_name = car_name.replace(' 택시', '')
        if base_name in mappings:
            return f"{mappings[base_name]} 택시"
    
    return car_name

def load_existing_reviews():
    """기존 리뷰 데이터 로드 (중복 체크용)"""
    file_path = "/app/text_data/DB/hyundai_car_reviews.json"
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_reviews(reviews, mode='append'):
    """리뷰 데이터 저장"""
    file_path = "/app/text_data/DB/hyundai_car_reviews.json"
    
    if mode == 'append':
        existing_reviews = load_existing_reviews()
        # data_id 기준으로 중복 제거
        existing_ids = {r.get('data_id') for r in existing_reviews if r.get('data_id')}
        new_reviews = [r for r in reviews if r.get('data_id') not in existing_ids]
        all_reviews = existing_reviews + new_reviews
    else:
        all_reviews = reviews
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(all_reviews, f, ensure_ascii=False, indent=2)
    
    return len(all_reviews)

def crawl_single_page(driver, page_num):
    """단일 페이지 크롤링"""
    print(f"\n📄 현재 페이지: {page_num}")
    
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)
    except WebDriverException as e:
        print(f"❌ 브라우저 오류: {type(e).__name__} - {str(e)}")
        return []

    review_list = driver.find_elements(By.CSS_SELECTOR, "#reviewList li")
    if not review_list:
        print("❌ 리뷰 항목 없음. 재시도 중...")
        time.sleep(3)
        review_list = driver.find_elements(By.CSS_SELECTOR, "#reviewList li")
        if not review_list:
            print("❌ 리뷰 항목 여전히 없음.")
            return []

    page_reviews = []
    seen_ids = set()

    def parse_rating(review_item):
        try:
            star_root = review_item.find_element(By.CSS_SELECTOR, ".summary-wrap .review-star")
        except:
            try:
                star_root = review_item.find_element(By.CSS_SELECTOR, ".review-star")
            except:
                return 0.0

        try:
            aria = star_root.get_attribute("aria-label") or ""
            m = re.search(r'([0-5](?:\.\d)?)', aria)
            if m:
                return float(m.group(1))
        except:
            pass

        try:
            hidden_nodes = star_root.find_elements(By.CSS_SELECTOR, ".blind, .sr-only, .visually-hidden, .ir")
            for node in hidden_nodes:
                t = (node.text or "").strip()
                m = re.search(r'([0-5](?:\.\d)?)', t)
                if m:
                    return float(m.group(1))
        except:
            pass

        try:
            bar = star_root.find_element(By.CSS_SELECTOR, ".bar")
            style = bar.get_attribute("style") or ""
            m = re.search(r'width\s*:\s*([0-9.]+)\s*%', style)
            if m:
                return round(float(m.group(1)) / 20.0, 1)
        except:
            pass

        try:
            cls = star_root.get_attribute("class") or ""
            m = re.search(r'rating[-_]?([0-9]{2})', cls)
            if m:
                return int(m.group(1)) / 10.0
        except:
            pass

        try:
            full = len(star_root.find_elements(By.CSS_SELECTOR, ".star-on"))
            half = len(star_root.find_elements(By.CSS_SELECTOR, ".star-half"))
            return full + 0.5 * half
        except:
            return 0.0

    for idx, review_item in enumerate(review_list):
        try:
            data_id = review_item.get_attribute("data-id")
            if not data_id or data_id in seen_ids:
                continue
            seen_ids.add(data_id)

            li_class = review_item.get_attribute("class") or ""
            li_style = review_item.get_attribute("style") or ""
            if "clone" in li_class or "display:none" in li_style:
                continue

            if len(review_item.find_elements(By.CSS_SELECTOR, ".title-wrap .title")) == 0:
                continue

            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", review_item)
            time.sleep(0.2)

            title_element = review_item.find_element(By.CSS_SELECTOR, ".title-wrap .title")
            try:
                span_best = title_element.find_element(By.TAG_NAME, "span")
                driver.execute_script("arguments[0].remove();", span_best)
            except:
                pass
            car_title = title_element.text.strip()
            
            # 차량명 정규화
            normalized_car_name = normalize_car_name(car_title)
            if not normalized_car_name:
                continue

            star_rating = parse_rating(review_item)

            has_more_btn = False
            try:
                toggle_btn = review_item.find_element(By.CLASS_NAME, "toggle-btn")
                if toggle_btn.text.strip() == "더보기":
                    has_more_btn = True
                    driver.execute_script("arguments[0].click();", toggle_btn)
                    time.sleep(0.3)
            except:
                pass

            review_html = ""
            try:
                if has_more_btn:
                    review_elem = review_item.find_element(By.CSS_SELECTOR, ".desc .review-text .text.show-more")
                else:
                    review_elem = review_item.find_element(By.CSS_SELECTOR, ".desc .review-text .text")
                review_html = review_elem.get_attribute("innerHTML") or ""
            except:
                review_html = ""
            review_text = review_html.replace("<br>", "\n").strip()

            tags_dict = {}
            try:
                for cat in review_item.find_elements(By.CSS_SELECTOR, ".category-list .list li"):
                    tag_name = cat.find_element(By.CSS_SELECTOR, ".flag").text.strip()
                    tag_desc = cat.find_element(By.CSS_SELECTOR, ".txt").text.strip()
                    tags_dict[tag_name] = tag_desc
            except:
                pass

            page_reviews.append({
                "data_id": data_id,
                "car_name": normalized_car_name,  # 정규화된 차량명 사용
                "rating": star_rating,
                "review": review_text,
                "tags": tags_dict,
                "crawled_at": datetime.now().isoformat()  # 크롤링 시간 추가
            })

            review_preview = review_text.replace("\n", " ").strip()[:40] + "..."
            tag_keys = list(tags_dict.keys())
            print(f"✅ {idx + 1}: [{data_id}] {normalized_car_name} - {star_rating}★ - \"{review_preview}\" | tags: {tag_keys}")

        except Exception as e:
            print(f"WARN: 항목 처리 실패: {type(e).__name__} - {str(e)}")
            continue

    return page_reviews

def main():
    # 명령행 인수 처리
    import sys
    page_num = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    print(f"🚀 증분 크롤링 시작: 페이지 {page_num}부터 {page_num + max_pages - 1}까지")
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--disable-background-networking")

    service = Service(executable_path='/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get("https://www.hyundai.com/kr/ko/purchase-event/vehicles-review")
        
        # 초기 페이지 로딩 대기
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#reviewList li"))
        )
        time.sleep(1.5)

        all_reviews = []
        
        # 지정된 페이지부터 크롤링
        for current_page in range(page_num, page_num + max_pages):
            # 페이지 이동
            if current_page > 1:
                next_btns = driver.find_elements(By.CSS_SELECTOR, "button.navi.next")
                if not next_btns or not next_btns[0].is_enabled():
                    print(f"❌ 페이지 {current_page}로 이동할 수 없습니다. 마지막 페이지에 도달했을 수 있습니다.")
                    break
                
                try:
                    driver.execute_script("arguments[0].click();", next_btns[0])
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#reviewList li"))
                    )
                    time.sleep(1.5)
                except TimeoutException:
                    print(f"❌ 페이지 {current_page} 로딩 타임아웃")
                    break
            
            # 페이지 크롤링
            page_reviews = crawl_single_page(driver, current_page)
            all_reviews.extend(page_reviews)
            
            print(f"📊 페이지 {current_page} 완료: {len(page_reviews)}개 리뷰 수집")

        # 결과 저장
        if all_reviews:
            total_count = save_reviews(all_reviews, mode='append')
            print(f"\n✅ 크롤링 완료!")
            print(f"📈 새로 수집된 리뷰: {len(all_reviews)}개")
            print(f"📊 전체 리뷰 수: {total_count}개")
            print(f"💾 저장 위치: /app/text_data/DB/hyundai_car_reviews.json")
        else:
            print("❌ 수집된 리뷰가 없습니다.")

    except Exception as e:
        print(f"❌ 크롤링 중 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
