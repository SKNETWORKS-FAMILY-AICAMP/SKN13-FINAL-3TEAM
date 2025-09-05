import time, json, re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service(executable_path='/usr/bin/chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get("https://www.hyundai.com/kr/ko/purchase-event/vehicles-review")
driver.maximize_window()

WebDriverWait(driver, 15).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "#reviewList li"))
)
time.sleep(1)

car_reviews = []

def parse_rating(review_item, debug=False, debug_index=0):
    """
    평점 파서 (우선순위)
    1) 접근성/숨김텍스트(.blind, .sr-only, aria-label) → 숫자
    2) 게이지 막대 .bar[style*='width'] → 100% = 5.0
    3) 클래스 내 rating-(\d{2}) → 45 = 4.5
    4) .star-on / .star-half 카운트
    """
    rating = 0.0
    # 스코프를 요약영역으로 고정
    star_root = None
    try:
        star_root = review_item.find_element(By.CSS_SELECTOR, ".summary-wrap .review-star")
    except:
        # 폴백: 가장 가까운 .review-star (비권장)
        try:
            star_root = review_item.find_element(By.CSS_SELECTOR, ".review-star")
        except:
            return 0.0

    if debug:
        try:
            outer = star_root.get_attribute("outerHTML")
            print(f"[DEBUG HTML {debug_index}] {outer[:300]}...")
        except:
            pass

    # 1) 접근성/숨김 텍스트
    try:
        # aria-label 우선
        aria = star_root.get_attribute("aria-label") or ""
        m = re.search(r'([0-5](?:\.\d)?)', aria)
        if m:
            val = float(m.group(1))
            return max(0.0, min(5.0, val))
    except:
        pass
    try:
        # 숨김 텍스트들
        hidden_nodes = []
        hidden_nodes += star_root.find_elements(By.CSS_SELECTOR, ".blind, .sr-only, .visually-hidden, .ir")
        # 혹시 부모에 있는 경우
        try:
            summary = review_item.find_element(By.CSS_SELECTOR, ".summary-wrap")
            hidden_nodes += summary.find_elements(By.CSS_SELECTOR, ".blind, .sr-only, .visually-hidden, .ir")
        except:
            pass
        for node in hidden_nodes:
            t = (node.text or "").strip()
            m = re.search(r'([0-5](?:\.\d)?)', t)
            if m:
                val = float(m.group(1))
                return max(0.0, min(5.0, val))
    except:
        pass

    # 2) 게이지 막대 width
    try:
        bar = star_root.find_element(By.CSS_SELECTOR, ".bar")
        style = bar.get_attribute("style") or ""
        m = re.search(r'width\s*:\s*([0-9.]+)\s*%', style)
        if m:
            pct = float(m.group(1))
            return round(max(0.0, min(5.0, pct / 20.0)), 1)
    except:
        pass

    # 3) 클래스에 rating-xx 패턴
    try:
        cls = (star_root.get_attribute("class") or "") + " " + (review_item.get_attribute("class") or "")
        m = re.search(r'rating[-_]?([0-9]{2})', cls)
        if m:
            val = int(m.group(1)) / 10.0  # 45 -> 4.5
            return max(0.0, min(5.0, val))
    except:
        pass

    # 4) 마지막: 별 아이콘 카운트
    try:
        full = len(star_root.find_elements(By.CSS_SELECTOR, ".star-on"))
        half = len(star_root.find_elements(By.CSS_SELECTOR, ".star-half"))
        rating = max(0.0, min(5.0, full + 0.5 * half))
        return rating
    except:
        return 0.0

for page in range(1, 588):
    print(f"\n📄 현재 페이지: {page}")
    # 무한스크롤/지연 로딩 대비
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.2)

    review_list = driver.find_elements(By.CSS_SELECTOR, "#reviewList li")

    for idx, review_item in enumerate(review_list):
        try:
            data_id = review_item.get_attribute("data-id")
            li_class = review_item.get_attribute("class") or ""
            li_style = review_item.get_attribute("style") or ""

            if "clone" in li_class or "display:none" in li_style:
                continue
            if len(review_item.find_elements(By.CSS_SELECTOR, ".title-wrap .title")) == 0:
                continue

            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", review_item)
            time.sleep(0.15)

            # 제목
            title_element = review_item.find_element(By.CSS_SELECTOR, ".title-wrap .title")
            try:
                span_best = title_element.find_element(By.TAG_NAME, "span")
                driver.execute_script("arguments[0].remove();", span_best)
            except:
                pass
            car_title = title_element.text.strip()

            # 별점(디버그는 처음 몇 개만)
            debug_flag = (idx < 3)
            star_rating = parse_rating(review_item, debug=debug_flag, debug_index=idx)
            print(f"DEBUG: rating={star_rating}")

            # 더보기
            has_more_btn = False
            try:
                toggle_btn = review_item.find_element(By.CLASS_NAME, "toggle-btn")
                if toggle_btn.text.strip() == "더보기":
                    has_more_btn = True
                    driver.execute_script("arguments[0].click();", toggle_btn)
                    time.sleep(0.25)
            except:
                pass

            # 리뷰 내용
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

            # 태그
            tags_dict = {}
            try:
                for cat in review_item.find_elements(By.CSS_SELECTOR, ".category-list .list li"):
                    tag_name = cat.find_element(By.CSS_SELECTOR, ".flag").text.strip()
                    tag_desc = cat.find_element(By.CSS_SELECTOR, ".txt").text.strip()
                    tags_dict[tag_name] = tag_desc
            except:
                pass

            car_reviews.append({
                "data_id": data_id,
                "car_name": car_title,
                "rating": star_rating,
                "review": review_text,
                "tags": tags_dict
            })

            print(f"✅ {idx + 1}: [{data_id}] {car_title} - {star_rating}★ - {review_text[:30]}... | tags: {list(tags_dict.keys())}")

        except Exception as e:
            print(f"WARN: 항목 처리 실패: {e}")
            continue

    # 페이지 이동
    if page < 588:
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "button.navi.next")
            driver.execute_script("arguments[0].click();", next_button)
            WebDriverWait(driver, 10).until(EC.staleness_of(review_list[0]))
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#reviewList li")))
            time.sleep(0.4)
        except Exception as e:
            print(f"❌ 페이지 {page + 1} 이동 실패: {e}")
            break

driver.quit()

out_path = "/app/text_data/DB/hyundai_car_reviews.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(car_reviews, f, ensure_ascii=False, indent=2)
print(f"\n✅ 최종 저장 완료: {out_path}")
