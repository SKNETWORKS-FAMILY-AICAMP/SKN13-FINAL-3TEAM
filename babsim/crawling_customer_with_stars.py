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

# ---- 공통 파서 (한 컨테이너에서 점수 읽기) ----
def parse_rating_from_container(root):
    def pick_num(text):
        if not text: return None
        m = re.search(r'([0-5](?:\.[05])?)', str(text))
        return float(m.group(1)) if m else None

    # 1) 별 컨테이너 고정
    star_root = None
    for sel in [".summary-wrap .review-star", ".review-star", "[class*='review-star']"]:
        try:
            star_root = root.find_element(By.CSS_SELECTOR, sel)
            break
        except:
            continue
    if not star_root:
        return None, "no_star_root"

    # 2) aria-label
    try:
        aria = star_root.get_attribute("aria-label") or ""
        val = pick_num(aria)
        if val is not None:
            return max(0.0, min(5.0, val)), "aria-label"
    except:
        pass

    # 3) 숨김텍스트
    try:
        hidden_nodes = []
        for sel in [".blind", ".sr-only", ".visually-hidden", ".ir", "[aria-hidden='false']"]:
            hidden_nodes += star_root.find_elements(By.CSS_SELECTOR, sel)
        for node in hidden_nodes:
            val = pick_num(node.text)
            if val is not None:
                return max(0.0, min(5.0, val)), "hidden-text"
    except:
        pass

    # 4) CSS 변수
    try:
        styles = driver.execute_script("return getComputedStyle(arguments[0]);", star_root)
        # Selenium에서 getPropertyValue를 직접 못 부르니 자바스크립트로 가져오자
        for var in ["--rating", "--score", "--value", "--rate"]:
            val = driver.execute_script("return getComputedStyle(arguments[0]).getPropertyValue(arguments[1]);", star_root, var)
            if val:
                num = pick_num(val.strip())
                if num is not None:
                    return max(0.0, min(5.0, num)), f"css-var({var})"
    except:
        pass

    # 5) 게이지 width
    try:
        bar = star_root.find_element(By.CSS_SELECTOR, ".bar")
        pct = None
        style_attr = bar.get_attribute("style") or ""
        m = re.search(r'width\s*:\s*([0-9.]+)\s*%', style_attr)
        if m:
            pct = float(m.group(1))
        else:
            # 계산된 width / 컨테이너 width로 비율
            bw = driver.execute_script("return parseFloat(getComputedStyle(arguments[0]).width);", bar)
            cw = driver.execute_script("return parseFloat(getComputedStyle(arguments[0]).width);", star_root)
            if bw and cw and cw > 0:
                pct = (bw / cw) * 100.0
        if pct is not None:
            val = round(min(5.0, max(0.0, pct / 20.0)) * 2) / 2.0
            return val, "bar-width"
    except:
        pass

    # 6) 클래스에 rating-xx
    try:
        cls = (star_root.get_attribute("class") or "") + " " + (root.get_attribute("class") or "")
        m = re.search(r'rating[-_]?([0-9]{2})', cls)
        if m:
            val = int(m.group(1)) / 10.0
            return max(0.0, min(5.0, val)), "class-rating"
    except:
        pass

    # 7) 아이콘 카운트(최후)
    try:
        full = len(star_root.find_elements(By.CSS_SELECTOR, ".star-on"))
        half = len(star_root.find_elements(By.CSS_SELECTOR, ".star-half"))
        # star-off는 점수에 직접 더하지 않음
        if full or half:
            return max(0.0, min(5.0, full + 0.5 * half)), "icon-count"
    except:
        pass

    return None, "no-match"

# ---- 모달에서 점수 읽기 ----
def get_rating_from_modal(data_id):
    try:
        # 모달 열기
        driver.execute_script("if (window.openReviewModal) { openReviewModal(arguments[0]); }", int(data_id))
        # 모달 대기(여러 후보 셀렉터)
        modal = None
        for sel in ["#reviewModal", ".layer-popup", ".modal", ".vehicle-review-modal", ".popup"]:
            try:
                modal = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, sel))
                )
                if modal:
                    break
            except:
                continue
        if not modal:
            return None, "modal-open-failed"

        # 모달 내부에서 직접 숫자 텍스트 시도
        for sel in [".avg .num", ".score .num", ".rating .num", ".point .num", ".review-score", "[aria-label]"]:
            elems = modal.find_elements(By.CSS_SELECTOR, sel)
            for e in elems:
                txt = e.get_attribute("aria-label") or e.text
                m = re.search(r'([0-5](?:\.[05])?)', txt)
                if m:
                    val = float(m.group(1))
                    close_modal_safely(modal)
                    return max(0.0, min(5.0, val)), f"modal-text({sel})"

        # 위에서 못 찾으면 별 컨테이너 파싱
        val, why = parse_rating_from_container(modal)
        close_modal_safely(modal)
        return val, f"modal-{why}"
    except Exception as e:
        try:
            close_modal_safely(None)
        except:
            pass
        return None, f"modal-exception:{e}"

def close_modal_safely(modal):
    # 닫기 버튼들 시도
    for sel in ["button.close", ".close", ".btn-close", ".btn_close", ".btn-layer-close", ".layer-popup .close"]:
        try:
            btn = (modal.find_element(By.CSS_SELECTOR, sel) if modal
                   else driver.find_element(By.CSS_SELECTOR, sel))
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.2)
            return
        except:
            continue
    # ESC 키나 바깥 클릭이 필요한 모달도 있음: 바깥 영역 클릭
    try:
        driver.execute_script("""
            var e = new KeyboardEvent('keydown', {key:'Escape', keyCode:27, which:27});
            document.dispatchEvent(e);
        """)
        time.sleep(0.2)
    except:
        pass

def get_rating(review_item, data_id, debug=False):
    # 1) 리스트 항목에서 먼저
    val, why = parse_rating_from_container(review_item)
    if debug:
        try:
            star_html = review_item.find_element(By.CSS_SELECTOR, ".summary-wrap .review-star").get_attribute("outerHTML")
        except:
            star_html = "(no star root)"
        print(f"[LIST] rating={val} why={why} | STAR HTML: {star_html[:200]}...")

    # 2) 실패하거나 5.0만 반복되면(비정상 패턴 의심) → 모달
    #    또는 .star-off/.star-half를 전혀 발견 못 했는데 텍스트 상으론 낮은 평이 보일 때도 모달 시도 권장
    if val is None or (val == 5.0 and "icon-count" in (why or "")):
        mval, mwhy = get_rating_from_modal(data_id)
        if debug:
            print(f"[MODAL] rating={mval} why={mwhy}")
        if mval is not None:
            return mval, mwhy
    return val or 0.0, why or "fallback-0"

# ---------------- 메인 루프 ----------------
for page in range(580, 588):
    print(f"\n📄 현재 페이지: {page}")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.0)

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

            # ★ 별점
            rating, why = get_rating(review_item, data_id, debug=(idx < 2))
            print(f"DEBUG: rating={rating} why={why}")

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

            # 리뷰 본문
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
                "rating": rating,
                "review": review_text,
                "tags": tags_dict
            })

            print(f"✅ {idx + 1}: [{data_id}] {car_title} - {rating}★ - {review_text[:30]}... | tags: {list(tags_dict.keys())}")

        except Exception as e:
            print(f"WARN: 항목 처리 실패: {e}")
            continue

    # 페이지 이동
    if page < 50:
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
