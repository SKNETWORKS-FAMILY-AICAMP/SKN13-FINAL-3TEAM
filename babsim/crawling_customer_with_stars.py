import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get("https://www.hyundai.com/kr/ko/purchase-event/vehicles-review")
driver.maximize_window()
time.sleep(3)

car_reviews = []

for page in range(1, 51):
    print(f"\n📄 현재 페이지: {page}")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

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

            driver.execute_script("arguments[0].scrollIntoView(true);", review_item)
            time.sleep(0.3)

            # 자동차 이름 (span.best 제거)
            title_element = review_item.find_element(By.CSS_SELECTOR, ".title-wrap .title")
            try:
                span_best = title_element.find_element(By.TAG_NAME, "span")
                driver.execute_script("arguments[0].remove();", span_best)
            except:
                pass
            car_title = title_element.text.strip()

            # 별점 가져오기
            star_rating = 0
            try:
                review_star_element = review_item.find_element(By.CSS_SELECTOR, ".review-star")
                star_on_elements = review_star_element.find_elements(By.CSS_SELECTOR, ".star-on")
                star_half_elements = review_star_element.find_elements(By.CSS_SELECTOR, ".star-half")
                star_rating = len(star_on_elements) + 0.5 * len(star_half_elements)
            except Exception as e:
                # print(f"별점 가져오기 실패: {e}") # for debugging
                pass  # 별점 없을 수도 있음

            # 더보기 버튼 있는지 + 텍스트 확인
            has_more_btn = False
            try:
                toggle_btn = review_item.find_element(By.CLASS_NAME, "toggle-btn")
                toggle_text = toggle_btn.text.strip()
                if toggle_text == "더보기":
                    has_more_btn = True
                    driver.execute_script("arguments[0].click();", toggle_btn)
                    time.sleep(0.5)
            except:
                pass

            # 리뷰 내용 가져오기
            review_html = ""
            try:
                if has_more_btn:
                    review_elem = review_item.find_element(By.CSS_SELECTOR, ".desc .review-text .text.show-more")
                else:
                    review_elem = review_item.find_element(By.CSS_SELECTOR, ".desc .review-text .text")
                review_html = review_elem.get_attribute("innerHTML")
            except:
                review_html = ""

            review_text = review_html.replace("<br>", "\n").strip()

            # 태그 정보 가져오기 (딕셔너리로)
            tags_dict = {}
            try:
                category_items = review_item.find_elements(By.CSS_SELECTOR, ".category-list .list li")
                for cat in category_items:
                    tag_name = cat.find_element(By.CSS_SELECTOR, ".flag").text.strip()
                    tag_desc = cat.find_element(By.CSS_SELECTOR, ".txt").text.strip()
                    tags_dict[tag_name] = tag_desc
            except:
                pass  # 태그 없을 수도 있음

            # 데이터 저장
            car_reviews.append({
                "data_id": data_id,
                "car_name": car_title,
                "rating": star_rating,
                "review": review_text,
                "tags": tags_dict
            })

            print(f"✅ {idx + 1}: [{data_id}] {car_title} - {star_rating} stars - {review_text[:30]}... | tags: {list(tags_dict.keys())}")

        except Exception as e:
            continue

    if page < 50:
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "button.navi.next")
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(3)
        except Exception as e:
            print(f"❌ 페이지 {page + 1} 이동 실패: {e}")
            break

driver.quit()

# text_data/DB/hyundai_car_reviews.json 경로에 저장
with open("text_data/DB/hyundai_car_reviews.json", "w", encoding="utf-8") as f:
    json.dump(car_reviews, f, ensure_ascii=False, indent=2)

print("\n✅ 최종 저장 완료: text_data/DB/hyundai_car_reviews.json")
