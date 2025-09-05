import json

# 나중에 이 곳에 car_history를 크롤링하는 코드를 추가합니다.
# 예: driver.get("여기에 URL 입력")

# 현재는 빈 리스트를 포함한 JSON 파일을 생성합니다.
car_history = []

with open("text_data/DB/hyundai_car_history.json", "w", encoding="utf-8") as f:
    json.dump(car_history, f, ensure_ascii=False, indent=2)

print("\n✅ 최종 저장 완료: text_data/DB/hyundai_car_history.json")
