# SKN13-FINAL-3TEAM

### 최종 프로젝트: JJACKLETTE - 현대자동차에 특화된 디자인 프로토타입 생성 플랫폼

**개발기간:** 2025.07.23 ~ 2025.09.15

## 🐥 팀 소개
### 팀명: 밥심 🍚

<table>
  <tr>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/50dc49bf-6b22-46f4-b98b-ca471b23e5e7" width="100"/><br/>기원준🥚
    </td>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/ff51f94a-0558-4baf-a81b-f833ae3b7a6e" width="100"/><br/>전진혁🐣
    </td>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/85c59737-8172-4319-ac86-f1a766d83dab" width="100"/><br/>강지윤🐥
    </td>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/7d5d501e-a319-4704-8f15-e593fcf2f90f" width="100"/><br/>최호연🐓
    </td>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/a7b70ca4-d2bc-4688-98fe-d45f8180a41b" width="100"/><br/>우민규🍗
    </td>
  </tr>
  <tr>
    <td align="center">
      <a href="https://github.com/ki-student"><img src="https://img.shields.io/badge/GitHub-ki--student-1F1F1F?logo=github" alt="기원준 GitHub"/></a>
    </td>
    <td align="center">
      <a href="https://github.com/Jinhyeok33"><img src="https://img.shields.io/badge/GitHub-Jinhyeok33-1F1F1F?logo=github" alt="전진혁 GitHub"/></a>
    </td>
    <td align="center">
      <a href="https://github.com/jiyun-kang12"><img src="https://img.shields.io/badge/GitHub-jiyun--kang12-1F1F1F?logo=github" alt="강지윤 GitHub"/></a>
    </td>
    <td align="center">
      <a href="https://github.com/oowixj819"><img src="https://img.shields.io/badge/GitHub-oowixj819-1F1F1F?logo=github" alt="최호연 GitHub"/></a>
    </td>
    <td align="center">
      <a href="https://github.com/mingyu-oo"><img src="https://img.shields.io/badge/GitHub-mingyu--oo-1F1F1F?logo=github" alt="우민규 GitHub"/></a>
    </td>
</table>

---

### 🐥 목차
1. 프로젝트 개요
2. 주요 기능
3. 기술 스택
4. R&R
5. 파이프라인, 시스템 아키텍처, ERD
6. 폴더 구조 / 주요 폴더 설명
7. 모델 학습 결과서
8. 프로토타입
9. 기대 효과
10. 한 줄 회고

---

## 🐥 1. 프로젝트 개요

### 1.1 개발 동기 및 목적

- **사용자 경험(UX) 중심의 디자인 혁신**  
  기존 자동차 디자인 프로세스는 복잡한 수정/피드백, 반복적인 3D 작업 등으로 시간과 비용이 많이 소요됨.  
  JJACKLETTE는 현대자동차의 데이터와 트렌드, 기업 고유의 디자인 아이덴티티를 반영해,  
  디자이너들이 빠르고 창의적으로 아이디어를 구체화할 수 있도록 지원하는 sLLM 기반 생성형 AI 플랫폼을 목표로 한다.

- **기업 특화 sLLM 챗봇의 필요성**  
  기업 내부 데이터를 안전하게 처리하면서, 실질적인 업무 효율을 높일 수 있는 맞춤형 챗봇 및 이미지 생성 시스템 개발.

- **비전**
  - 고객의 목소리와 트렌드를 반영하여 사용자 중심 설계 강화  
  - 브랜드 일관성(디자인 아이덴티티) 유지  
  - Agile·창의적인 디자인 프로토타이핑 환경 구축  

---

### 1.2 🛠️ 개발 목표

- 현대자동차 디자인 실무에 맞는, 통합형 **AI 프로토타입 생성 플랫폼** 개발
- 내부 규정/트렌드/피드백 등 기업 맥락을 반영한 텍스트·이미지 생성
- 프롬프트만으로 다양한 디자인 시안/시각화/3D·4D 모델 생성 지원
- 유연한 수정, 아카이빙, 프로젝트 관리 등 협업 효율화 기능 제공
- 모든 백엔드, 프론트엔드, 데이터베이스, 모델 서버를 Docker 기반 컨테이너로 운영
- docker-compose로 전체 서비스 통합 구동 및 재현 가능성 확보

---

## 🐥 2. 주요 기능

- **1) 텍스트·이미지·3D·비디오 프로토타입 생성**  
  - LLM 기반 자동차 디자인 관련 질의응답/아이디어 요약/트렌드 분석
  - 사용자와의 커뮤니케이션을 통한 체크리스트 완성
  - 기업 맞춤형 디자인 프롬프트 입력 → 이미지, 3D 모델, 주행 영상까지 생성 가능
- **2) 기업 내부 지식 반영**
  - 내부 규정·가이드라인·기술 문서 연동(RAG)
  - 과거 프로젝트·고객 피드백 반영
- **3) 실시간 협업 지원**
  - 생성된 시안 아카이빙, 버전 관리, 코멘트, 프로토타입 부분 수정 기능
- **4) 실사급 시각화/시뮬레이션**
  - FLUX.1 기반 렌더링, Hunyuan3D-2 기반 3D 변환, LTX-Video 기반 시뮬레이션 영상
- **5) 엔터프라이즈 수준 보안/확장성**
  - 데이터 암호화, 권한관리

---

## 🐥 3. 기술 스택

| **분야**                  | **기술 및 라이브러리**                                                                                                                                                                                                                     |
|---------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 🖥️ 프로그래밍 언어/환경      | <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=Python&logoColor=white" /> <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=JavaScript&logoColor=white" /> <img src="https://img.shields.io/badge/VS%20Code-007ACC?style=for-the-badge&logo=VisualStudioCode&logoColor=white" /> |
| 🐳 컨테이너/배포              | <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=Docker&logoColor=white" /> <img src="https://img.shields.io/badge/Airflow-017CEE?style=for-the-badge&logo=Apache-Airflow&logoColor=white" />                                                                                      |
| 🖼️ 사용한 LLM/멀티모달 모델 | <img src="https://img.shields.io/badge/kanana-008B8B?style=for-the-badge" /> <img src="https://img.shields.io/badge/InternVL3-FF6F61?style=for-the-badge" /> <img src="https://img.shields.io/badge/FLUX.1-4F8A8B?style=for-the-badge" /> <img src="https://img.shields.io/badge/Hunyuan3D--2-4F8A8B?style=for-the-badge" /> <img src="https://img.shields.io/badge/LTX--Video-4F8A8B?style=for-the-badge" /> |
| 🗂️ 데이터 저장/검색          | <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=PostgreSQL&logoColor=white" /> <img src="https://img.shields.io/badge/AWS%20S3-569A31?style=for-the-badge&logo=Amazon-S3&logoColor=white" /> <img src="https://img.shields.io/badge/Qdrant-E34F26?style=for-the-badge&logo=qdrant&logoColor=white" /> |
| 🖼️ 프론트엔드                | <img src="https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=React&logoColor=black" /> <img src="https://img.shields.io/badge/TailwindCSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white" />                                               |
| ⚙️ 백엔드                    | <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white" /> <img src="https://img.shields.io/badge/WSGI-000000?style=for-the-badge&logo=python&logoColor=white" /> <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=FastAPI&logoColor=white" /> |
| ☁️ 인프라/클라우드            | <img src="https://img.shields.io/badge/Runpod-4285F4?style=for-the-badge" /> <img src="https://img.shields.io/badge/AWS%20EC2-FF9900?style=for-the-badge&logo=Amazon-EC2&logoColor=white" /> <img src="https://img.shields.io/badge/AWS%20RDS-527FFF?style=for-the-badge&logo=Amazon-RDS&logoColor=white" /> |
| 🛠️ 기타                      | <img src="https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=Selenium&logoColor=white" /> <img src="https://img.shields.io/badge/PyMuPDF-00599C?style=for-the-badge&logo=AdobeAcrobatReader&logoColor=white" /> <img src="https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" /> <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=GitHub&logoColor=white" /> <img src="https://img.shields.io/badge/vLLM-00599C?style=for-the-badge" /> <img src="https://img.shields.io/badge/ComfyUI-007ACC?style=for-the-badge" /> |

---

## 🐥 4. R&R (Roles & Responsibilities)

| 이름     | 역할                                   | 주요 담당                                   |
|--------|--------------------------------------|------------------------------------------|
| **기원준** | PM / AI모델링(Exaone) / DevOps / DBA / 백엔드 | 파인튜닝, 배포, 백엔드              |
| **전진혁** | AI/ML 엔지니어링 / 디자인 / 프론트 | 이미지 -> 3D 변환, 프론트 UI, 디자인                     |
| **강지윤** | AI모델링(InternVL3) / AI/ML 엔지니어링 / 디자인 / 파이프라인 | 이미지 특징추출, 전체 파이프라인, ERD설계                    |
| **최호연** | AI모델링(LTX-Video) / AI/ML 엔지니어링 / 백엔드 | 영상 생성, 백엔드                          |
| **우민규** | AI모델링(FLUX.1) / AI/ML 엔지니어링      | 이미지 생성, AI연동                           |

> ※ 상세:  
> - **DevOps**: 인프라, 배포, CI/CD  
> - **DBA**: DB 스키마, 운영  
> - **AI/ML**: 임베딩·RAG·모델 연동  
> - **디자인**: Figma UI/UX  
> - **백엔드**: Django  

---

## 🐥 5. 파이프라인, 시스템 아키텍처, ERD

🔧**파이프라인**  
<img width="4669" height="2146" alt="pipeline" src="https://github.com/user-attachments/assets/04dc5062-492c-43fa-a5ab-df1a3512c4d2" /> <br>

🔧**시스템 아키텍처**  
<img width="6220" height="4380" alt="Image" src="https://github.com/user-attachments/assets/040ee919-4aa7-4160-84e3-410a9fc4c3b7" />> <br>

🔧**ERD**  
<img src="https://github.com/user-attachments/assets/2283e29a-2568-46f0-b52f-6ef64ec4b643" width="800" alt="ERD"> <br>

---

## 🐥 6. 폴더 구조 / 주요 폴더 설명

> (구체적 폴더 구조와 각 디렉터리별 기능 및 예시 설명. 추후 작성)
<br>
📦ProjectRoot<br>
┣ 📜README.md<br>
┣ 📂babsim<br>
┃ ┣ 📜.DS_Store<br>
┃ ┣ 📜.gitignore<br>
┃ ┣ 📜docker-compose.yml<br>
┃ ┣ 📜Dockerfile<br>
┃ ┣ 📜manage.py<br>
┃ ┣ 📜nginx.conf<br>
┃ ┣ 📜package-lock.json<br>
┃ ┣ 📜requirements.txt<br>
┃ ┣ 📜test_model.py<br>
┃ ┣ 📂.vscode<br>
┃ ┃ ┗ 📜settings.json<br>
┃ ┣ 📂config<br>
┃ ┃ ┣ 📜asgi.py<br>
┃ ┃ ┣ 📜settings.py<br>
┃ ┃ ┣ 📜urls.py<br>
┃ ┃ ┣ 📜views.py<br>
┃ ┃ ┣ 📜wsgi.py<br>
┃ ┃ ┣ 📜__init__.py<br>
┃ ┃ ┗ 📂__pycache__<br>
┃ ┃   ┣ 📜settings.cpython-310.pyc<br>
┃ ┃   ┣ ...<br>
┃ ┣ 📂data<br>
┃ ┃ ┗ 📜.DS_Store<br>
┃ ┣ 📂frontend<br>
┃ ┃ ┣ 📜.DS_Store<br>
┃ ┃ ┗ 📂build<br>
┃ ┃   ┣ 📜.DS_Store<br>
┃ ┃   ┣ 📜.gitignore<br>
┃ ┃   ┣ 📜index.html<br>
┃ ┃   ┣ 📜vite.svg<br>
┃ ┃   ┗ 📂assets<br>
┃ ┃     ┣ 📜index-BjJceZ3H.js<br>
┃ ┃     ┣ 📜index-tUhWM6ky.css<br>
┃ ┃     ┗ 📜ioniq5-1E-ln0eX.png<br>
┃ ┣ 📂JJACKLETTE<br>
┃ ┃ ┣ 📜admin.py<br>
┃ ┃ ┣ 📜apps.py<br>
┃ ┃ ┣ 📜llm.py<br>
┃ ┃ ┣ 📜llm_interface.py<br>
┃ ┃ ┣ 📜models.py<br>
┃ ┃ ┣ 📜serializers.py<br>
┃ ┃ ┣ 📜services.py<br>
┃ ┃ ┣ 📜tests.py<br>
┃ ┃ ┣ 📜urls.py<br>
┃ ┃ ┣ 📜views.py<br>
┃ ┃ ┣ 📜__init__.py<br>
┃ ┃ ┣ 📂management<br>
┃ ┃ ┃ ┗ 📂commands<br>
┃ ┃ ┃   ┣ 📜import_data.py<br>
┃ ┃ ┃   ┗ 📂__pycache__<br>
┃ ┃ ┣ 📂migrations<br>
┃ ┃ ┃ ┣ 📜0001_initial.py<br>
┃ ┃ ┃ ┣ 📜__init__.py<br>
┃ ┃ ┃ ┗ 📂__pycache__<br>
┃ ┃ ┣ 📂__pycache__<br>
┃ ┃ ┃ ┣ 📜admin.cpython-310.pyc<br>
┃ ┃ ┃ ┣ ...<br>
┃ ┣ 📂models<br>
┃ ┃ ┗ 📜.DS_Store<br>
┃ ┣ 📂node_modules<br>
┃ ┃ ┗ 📜.package-lock.json<br>
┃ ┣ 📂scripts<br>
┃ ┃ ┣ 📜embedding.py<br>
┃ ┃ ┗ 📜preprocess.py<br>
┃ ┣ 📂templates<br>
┃ ┃ ┗ 📜home.html<br>
┃ ┗ 📂text_data<br>
┃   ┣ 📜.DS_Store<br>
┃   ┗ 📂DB<br>
┃     ┣ 📜hyundai_car_reviews.json<br>
┃     ┗ 📂car_specs<br>
┃       ┣ 📜Electrified G80.csv<br>
┃       ┣ 📜Electrified GV70.csv<br>
┃       ┣ 📜G70.csv<br>
┃       ┣ ...<br>
┣ 📂document<br>
┃ ┣ 📜API_SPEC.md<br>
┃ ┣ 📜chat_pipeline_5.png<br>
┃ ┣ 📜jjacklette_ERD.png<br>
┃ ┗ 📜System Architecture.pdf<br>
┣ 📂evaluation<br>
┃ ┣ 📜baseline_performance_report.md<br>
┃ ┣ 📜base_model_evaluation_results.md<br>
┃ ┣ 📜finetuned_evaluation_results.md<br>
┃ ┗ 📜md.ipynb<br>
┣ 📂image_data<br>
┃ ┣ 📂hyundai_concept_car_nogb_cropped_1024<br>
┃ ┃ ┣ 📜Hyundai-45_EV_Concept-2019-thb.jpg<br>
┃ ┃ ┣ ...<br>
┃ ┗ 📂hyundai_images_nobg_cropped_1024<br>
┃   ┣ 📜Large-36014-2021Sonata.jpg<br>
┃   ┣ ...<br>
┣ 📂react<br>
┃ ┣ 📜.gitignore<br>
┃ ┣ 📜eslint.config.js<br>
┃ ┣ 📜index.html<br>
┃ ┣ 📜package-lock.json<br>
┃ ┣ 📜package.json<br>
┃ ┣ 📜postcss.config.js<br>
┃ ┣ 📜README.md<br>
┃ ┣ 📜tai



## 🐥 7. 모델 학습 결과서

### 📊 FLUX.1-Kontext-dev 파인튜닝 결과 요약

- **모델**: `black-forest-labs/FLUX.1-Kontext-dev`  
  - LoRA 방식, (`SimpleTuner` 사용), 시드값 42 고정  

#### 📂 데이터셋

- 이미지-캡션 쌍 총 1768개  
  - 학습 데이터: 1,604개  
  - 테스트 데이터: 164개  

#### 🎯 목표

- 베이스 모델 대비 파인튜닝 모델의 **이미지 생성 품질 향상**


### 평가 지표 1: CLIP Score, FID

| 지표         | Base 모델 | LoRA 모델 | 우수 모델 |
|--------------|------------|------------|------------|
| **CLIP Score** | 24.0207    | 22.0444    | Base       |
| **FID Score**  | 66.3546    | 52.4227    | LoRA       |

- **CLIP Score**: Base 모델이 LoRA보다 약간 높은 점수를 기록 → 프롬프트 일치도에서 우위  
- **FID Score**: LoRA 모델이 더 낮은 점수 → 실제 이미지 분포에 더 가까운 사실적인 이미지 생성


### 평가 지표 2: GPT 기반 정성적 평가 (5점 만점)

| 평가 항목       | Base 모델 평균 | LoRA 모델 평균 | 우수 모델 |
|----------------|----------------|----------------|------------|
| 프롬프트 충실도 | 3.28           | 3.82           | LoRA       |
| 디자인 품질     | 4.00           | 4.18           | LoRA       |
| 브랜드 정체성   | 4.18           | 4.27           | LoRA       |
| 이미지 품질     | 4.64           | 4.55           | Base       |

#### 🔍 주요 분석

- **프롬프트 충실도**: LoRA가 세부 사항 반영에 더 우수  
- **디자인 품질**: LoRA가 미학적 완성도에서 우위  
- **브랜드 정체성**: LoRA가 현대차 디자인 언어를 더 잘 표현  
- **이미지 품질**: Base 모델이 해상도 및 선명도에서 약간 우수  


### ⚙️ LoRA 스케일 조정 결과

- 테스트 스케일: `0.5`, `0.25`  
- **최적 스케일**: `0.5` → LoRA 가중치가 적절히 적용되어 성능 최적화


### 🧠 결론

- LoRA 파인튜닝은 **현대차 이미지 생성 모델의 사실성 및 프롬프트 반영 능력**을 효과적으로 향상시킴  
- 특히 **FID 점수 개선**과 **정성적 평가 항목에서 우수한 성능**을 보임  
- **CLIP Score 및 이미지 품질**은 Base 모델이 약간 우수하거나 유사  
- **LoRA 스케일 0.5**가 최적의 성능 제공  
- 향후 연구에서는 **이미지 품질 저하 없이 CLIP 점수 개선** 방안 모색 필요  
- **적절한 학습 스텝(1000~2000)**이 가장 효과적이며, 과도한 학습은 품질 저하 우려

---

### 📊 kanana-1.5-8b-instruct-2505 파인튜닝 결과 요약

- **모델**: `kakaocorp/kanana-1.5-8b-instruct-2505`  
  - LoRA 적용 (`peft` 사용), 시드값 42 고정  

#### 📂 데이터셋

- 자동차 디자인 QA 쌍  
  - 학습 데이터: 2324건  
  - 검증 데이터: 291건  
  - 테스트 데이터: 289건  

#### 🎯 목표
- 베이스 모델 대비 파인튜닝 모델의 **응답 품질 향상**


### 평가 지표 1: BERTScore (Precision, Recall, F1)

| 실험 | 학습 조건 | BERTScore-F1 변화 | 분석 |
|------|-----------|-------------------|------|
| 1차  | 5 epoch, batch size 4, LoRA 적용 | 0.6977 → **0.7058** (+0.0081 ↑) | 응답 품질 소폭 향상, 할루시네이션 및 일관성 발견 |
| 2차  | 3 epoch, batch size 2, LoRA 적용 | 0.7344 → **0.8884** (+0.1540 ↑) | 응답 품질 대폭 향상, 할루시네이션 및 일관성 여전히 발견 |
| 3차  | 5 epoch, batch size 2, LoRA 적용 | 0.8011 → **0.9161** (+0.1150 ↑) | 응답 품질 대폭 향상, 할루시네이션 및 일관성 제거 |


### 평가 지표 2: Cosine Similarity

| 지표         | Base 모델 | Finetuned 모델 | 변화 |
|--------------|------------|----------------|------|
| CosineSim    | 0.9004     | **0.9526**     | +0.0523 ↑ |

- 파인튜닝 모델이 문맥 유사도 측면에서도 베이스 모델보다 높은 일치도를 보임  
- 응답의 의미적 일관성과 정보 정합성이 개선됨을 시사

### 🧠 결론
- 적절한 에폭 수(3~5)와 LoRA 설정으로 큰 품질 향상 가능  
- 과도한 학습은 성능 정체 또는 미세한 저하 등의 과적합 유발  
- 주어진 문맥에서 핵심 정보 파악 가능  
- 베이스 모델 대비 파인튜닝 모델은 전문성, 응답 일관성, 문맥 이해에서 우수함 
- Cosine 유사도 향상은 의미적 응답 품질 개선을 뒷받침함 

---

## 📦 모델 저장 및 활용

- **저장 형식**: LoRA 어댑터 허깅페이스에 업로드 (sLLM: `ki-student/kanana-finetuned-model-v1`, Flux: `mingyu-oo/FLUX_LoRA_adapter`), PyTorch 기반  
- **추론 속도**: sLLM - 평균 0.3초/건, FLUX.1 - 평균 1분 30초/건 (GPU 기준)  
- **활용 방안**:  
  - 자동차 디자인 챗봇  
  - 브랜드 철학 설명 AI  
  - 디자인 문서 요약 및 질의응답

---

## 🐥 8. 프로토타입

  
><br>**Home**<br>
<img width="1617" height="1447" alt="Image" src="https://github.com/user-attachments/assets/7234b089-538c-4928-ad77-e54fd853bd6a" />  
<br>
<br>**Asset Library**<br>
<img width="1617" height="1453" alt="Image" src="https://github.com/user-attachments/assets/46c11afd-71da-4326-9f60-fd7dfce95d38" />  
&emsp;📄**세부 사항**  
&emsp;&emsp;자료 내부<br>
&emsp;&emsp;<img width="1192" height="1206" alt="Image" src="https://github.com/user-attachments/assets/687319be-b494-470f-b188-4f6ae19fb2c1" />  
<br>
<br>**Insight & Trends**<br>
<img width="797" height="1022" alt="Image" src="https://github.com/user-attachments/assets/10632320-88c8-4542-a0fe-4795aa7d7d66" />
<br>  
&emsp;📄**세부 사항**  
&emsp;&emsp;제원<br>
&emsp;&emsp;<img width="1009" height="877" alt="Image" src="https://github.com/user-attachments/assets/46ce8ab5-72b8-4425-994c-fbad7a1d6529" />  
&emsp;&emsp;리뷰 분석<br>
&emsp;&emsp;<img width="1016" height="977" alt="Image" src="https://github.com/user-attachments/assets/a7cdb6cb-83a5-4a8d-b21e-2192c3bd4090" />  
&emsp;&emsp;트렌드<br>
&emsp;&emsp;<img width="1007" height="479" alt="Image" src="https://github.com/user-attachments/assets/8448ea96-c815-4e74-91c0-e9236dcaa794" />  
<br>
<br>**Prototype Lab**<br>
<img width="1632" height="1426" alt="Image" src="https://github.com/user-attachments/assets/440d2dd3-6de2-4531-89ee-44df5cd6b096" />

---

## 🐥 9. 기대 효과

- 자동차 산업, 디자인 실무에 실제로 투입 가능한 수준의 AI 도구 제공
- **디자인 프로세스 가속화**: 반복적 렌더링/수정 작업을 단축, 실시간 시각화로 업무 효율 증대  
- **아이디어 다양화 및 창의성 촉진**: 생성형 AI를 통한 새로운 디자인 시안/트렌드 발굴  
- **통합 정보 제공**: 내부 규정·기술 문서·고객 피드백 등의 정보를 LLM 기반으로 통합/즉시 제공
- **비용 절감**: 물리적 시제품 제작, 고비용 3D/시뮬레이션 공정 감소
- **기업 데이터 보안**: 권한 관리, NDA 기반 데이터 거버넌스 체계 강화

---

## 🐥 10. 한 줄 회고

 - 🥚기원준: AWS EC2 "Legend Server"
 - 🐣전진혁: React master
 - 🐥강지윤: "image to text" InternVL3 master 
 - 🐓최호연: ComfyUI master
 - 🍗우민규: Image Generate master

