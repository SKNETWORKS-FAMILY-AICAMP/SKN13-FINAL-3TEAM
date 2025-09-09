import time, json, re, os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

def main():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--disable-background-networking")

    service = Service(executable_path='/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get("https://www.hyundai.com/kr/ko/purchase-event/vehicles-review")

    # 초기 페이지 로딩 대기 시간을 20초로 유지
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#reviewList li"))
    )
    time.sleep(1.5)

    car_reviews = []
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

    page = 1
    # 580페이지부터 587페이지까지 테스트를 원할 경우 아래 줄의 주석을 해제하세요.
    # page = 580
    while page <= 587:
        print(f"\n📄 현재 페이지: {page}")
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)
        except WebDriverException as e:
            print(f"❌ 브라우저 오류: {type(e).__name__} - {str(e)}")
            break

        review_list = driver.find_elements(By.CSS_SELECTOR, "#reviewList li")
        if not review_list:
            print("❌ 리뷰 항목 없음. 재시도 중...")
            time.sleep(3)
            review_list = driver.find_elements(By.CSS_SELECTOR, "#reviewList li")
            if not review_list:
                print("❌ 리뷰 항목 여전히 없음. 종료.")
                break

        if page >= 1: # 1페이지부터 수집하도록 조건 변경
            for idx, review_item in enumerate(review_list):
                try:
                    data_id = review_item.get_attribute("data-id")
                    if data_id in seen_ids:
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

                    car_reviews.append({
                        "data_id": data_id,
                        "car_name": car_title,
                        "rating": star_rating,
                        "review": review_text,
                        "tags": tags_dict
                    })

                    review_preview = review_text.replace("\n", " ").strip()[:40] + "..."
                    tag_keys = list(tags_dict.keys())
                    print(f"✅ {idx + 1}: [{data_id}] {car_title} - {star_rating}★ - \"{review_preview}\" | tags: {tag_keys}")

                except Exception as e:
                    print(f"WARN: 항목 처리 실패: {type(e).__name__} - {str(e)}")
                    continue

        next_btns = driver.find_elements(By.CSS_SELECTOR, "button.navi.next")
        if not next_btns or not next_btns[0].is_enabled():
            print("✅ 마지막 페이지 도달. 종료.")
            break

        # 페이지 이동 실패 시 재시도 로직 추가
        try:
            current_ids = set([r.get_attribute("data-id") for r in review_list])
            
            for attempt in range(3): # 최대 3번 재시도
                try:
                    driver.execute_script("arguments[0].click();", next_btns[0])
                    WebDriverWait(driver, 30).until( # 타임아웃 30초로 증가
                        lambda d: any(
                            r.get_attribute("data-id") not in current_ids
                            for r in d.find_elements(By.CSS_SELECTOR, "#reviewList li")
                        )
                    )
                    time.sleep(1.5)
                    page += 1
                    break # 성공 시 재시도 루프 종료
                except (TimeoutException, WebDriverException) as e:
                    print(f"❌ 페이지 이동 재시도 ({attempt+1}/3): {type(e).__name__} - {str(e)}")
                    time.sleep(5) # 재시도 전 5초 대기
            else:
                print("❌ 반복된 페이지 이동 실패. 스크래퍼 종료.")
                break # 모든 재시도 실패 시 전체 루프 종료

        except Exception as e:
            print(f"❌ 페이지 이동 실패: {type(e).__name__} - {str(e)}")
            time.sleep(2)
            continue

    driver.quit()

    out_path = "/app/text_data/DB/hyundai_car_reviews.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(car_reviews, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 최종 저장 완료: {out_path}")

if __name__ == "__main__":
    main()