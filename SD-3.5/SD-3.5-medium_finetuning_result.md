# SD-3.5-medium 파인튜닝 결과 보고서

## 1. 실험 개요
- **모델**: `stabilityai/stable-diffusion-3.5-medium`
- **파인튜닝 방식**: LoRA 기반 미세조정(Fine-tuning)
- **데이터셋**: 이미지-캡션 쌍 100개 (학습/테스트 동일 데이터)
- **목표**: 베이스(Base) 모델과 파인튜닝(LoRA) 모델의 **이미지 생성 품질 비교**
- **평가 지표**
  - **CLIP Score**: 프롬프트와 생성 이미지 간의 의미적 유사도
  - **FID (Fréchet Inception Distance)**: 원본 이미지와 생성 이미지 간의 분포 차이

---

## 2. 실험 조건

### 1차 실험
```json
{
  "num_train_epochs": 2,
  "max_train_steps": 1000
}
```

#### CLIP Score (Prompt 10개)

| 프롬프트 | Base | LoRA | 변화 |
| --- | --- | --- | --- |
| 001 | 30.3353 | 30.7100 | ↑ |
| 002 | 22.6265 | 27.5713 | ↑ |
| 003 | 24.5506 | 29.9743 | ↑ |
| 004 | 25.0187 | 30.1118 | ↑ |
| 005 | 26.8785 | 25.9681 | ↓ |
| 006 | 29.0553 | 30.4901 | ↑ |
| 007 | 26.3300 | 29.9706 | ↑ |
| 008 | 24.0326 | 26.6362 | ↑ |
| 009 | 18.7915 | 25.1927 | ↑ |
| 010 | 26.4891 | 28.0963 | ↑ |

**평균 CLIP Score**

| 모델 | 평균 |
| --- | --- |
| Base | 25.4108 |
| LoRA | 28.4721 |

➡ **LoRA 모델이 평균 3.06점 상승**

---

### 2차 실험
```json
{
  "num_train_epochs": 5,
  "max_train_steps": 3000
}
```

#### CLIP Score (Prompt 10개)

| 프롬프트 | Base | LoRA | 변화 |
| --- | --- | --- | --- |
| 001 | 30.4717 | 31.4037 | ↑ |
| 002 | 25.7112 | 25.9213 | ↑ |
| 003 | 27.4651 | 29.6692 | ↑ |
| 004 | 30.7797 | 27.1946 | ↓ |
| 005 | 24.4910 | 28.6010 | ↑ |
| 006 | 27.3904 | 30.0472 | ↑ |
| 007 | 30.2498 | 28.7967 | ↓ |
| 008 | 27.2943 | 25.9734 | ↓ |
| 009 | 28.4575 | 29.2235 | ↑ |
| 010 | 27.6942 | 27.1093 | ↓ |

**평균 CLIP Score**

| 모델 | 평균 |
| --- | --- |
| Base | 28.0005 |
| LoRA | 28.3940 |

➡ **LoRA 모델이 평균 0.39점 상승**

---

## 3. FID Score 비교

| 실험 조건 | Base | LoRA | 변화 |
| --- | --- | --- | --- |
| 1차(2 epoch, 1000 steps) | 10.8827 | 6.3906 | ↓ **개선** |
| 2차(5 epoch, 3000 steps) | 7.9497 | 9.5222 | ↑ **악화** |

---

## 4. 분석

1. **1차 실험 결과**
   - CLIP 점수에서 LoRA 모델이 전반적으로 **유의미한 상승**(평균 +3.06).
   - FID 점수도 낮아져(10.88 → 6.39) **이미지 품질 향상**이 확인됨.
   - 적은 epoch에서도 효율적인 성능 개선 가능성을 확인.

2. **2차 실험 결과**
   - CLIP 점수는 소폭 향상(+0.39)으로 **개선폭 감소**.
   - FID 점수는 오히려 악화(7.94 → 9.52)되어, 장기 학습 시 **과적합(Overfitting)** 가능성 시사.
   - 일부 프롬프트에서 오히려 점수가 하락.

3. **종합 결론**
   - **LoRA 기반 파인튜닝은 적절한 학습 스텝에서 성능 향상에 효과적**.
   - 지나친 학습 스텝은 데이터 과적합으로 인해 **생성 다양성과 품질이 저하**될 수 있음.
   - 최적 학습 스텝은 1000~2000 사이에서 탐색 필요.

---

## 5. 향후 개선 방향
- 데이터 다양성 확보 및 augmentation 적용.
- 학습 스텝 별 중간 체크포인트 저장 후 비교.
- CLIP 외에도 **LPIPS**나 **Inception Score(IS)** 등 추가 지표 활용.
- 다양한 프롬프트 스타일(짧은 문장, 세부 묘사 포함)로 평가 확장.


## 6. 모델 출력 예시
```python
prompt = (
    "designed by Hyundai, front left 3/4 view, long sleek silhouette, "
    "aggressive LED headlamps, sculpted hood, parametric grille pattern, "
    "dynamic side character lines, floating roof, frameless windows, "
    "flush door handles, wide stance, concept lighting, premium metallic blue finish, high-tech minimalism"
    
)
negative_prompt = (
    "cartoon, illustration, sketch, anime, cgi, 3d render, "
    "side view, rear view, top view, back view, cropped, truncated, incomplete, out of frame, "
    "deformed, extra wheels, extra doors, text, watermark, logo, "
    "outdoor, street, landscape, colored background, "
    "cut, reflection, frame, border, blurry, low quality"
)
```

- Base Model<br>
<img width="1024" height="1024" alt="Image" src="https://github.com/user-attachments/assets/14317500-58ce-49eb-ad16-377ca6006333" />

- LoRA Model<br>
<img width="1024" height="1024" alt="Image" src="https://github.com/user-attachments/assets/46b1fac7-24a3-4c45-89ad-8c601d8c66da" />