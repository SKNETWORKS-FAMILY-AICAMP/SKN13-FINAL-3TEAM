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
      <img src="https://github.com/user-attachments/assets/af8e3f73-c42f-451d-b3c9-1234aa6328cf" width="100"/><br/>우민규🍗
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
  - 기업 맞춤형 디자인 프롬프트 입력 → 이미지, 3D 모델, 주행 영상까지 생성 가능
- **2) 기업 내부 지식 반영**
  - 내부 규정·가이드라인·기술 문서 연동(RAG)
  - 과거 프로젝트·고객 피드백 반영
- **3) 실시간 협업 지원**
  - 생성된 시안 아카이빙, 버전 관리, 코멘트, 프로토타입 부분 수정 기능
- **4) 실사급 시각화/시뮬레이션**
  - Stable Diffusion 기반 렌더링, Trellis 기반 3D 변환, Stable-video-diffusion 기반 시뮬레이션 영상
- **5) 엔터프라이즈 수준 보안/확장성**
  - 데이터 암호화, 권한관리

---

## 🐥 3. 기술 스택

| **분야**                  | **기술 및 라이브러리**                                                                                                                                                                                                                    |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 🖥️ 프로그래밍 언어/환경      | <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=Python&logoColor=white" /> <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=JavaScript&logoColor=white" /> <img src="https://img.shields.io/badge/VS%20Code-007ACC?style=for-the-badge&logo=VisualStudioCode&logoColor=white" /> |
| 🐳 컨테이너/배포              | <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=Docker&logoColor=white" />                                                                                                                                                                   |
| 🖼️ 사용한 LLM/멀티모달 모델 | <img src="https://img.shields.io/badge/EXAONE--4.0%201.2B-008B8B?style=for-the-badge" /> <img src="https://img.shields.io/badge/InternVL3--8B-FF6F61?style=for-the-badge" /> <img src="https://img.shields.io/badge/stable--diffusion--v3.5-4F8A8B?style=for-the-badge&logo=StableDiffusion&logoColor=white" /> |
| 🗂️ 데이터 저장/검색          | <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=PostgreSQL&logoColor=white" /> <img src="https://img.shields.io/badge/Qdrant-E34F26?style=for-the-badge&logo=qdrant&logoColor=white" />                                              |
| 🖼️ 프론트엔드                | <img src="https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=React&logoColor=black" /> <img src="https://img.shields.io/badge/TailwindCSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white" />                                            |
| ⚙️ 백엔드                    | <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white" /> <img src="https://img.shields.io/badge/WSGI-000000?style=for-the-badge&logo=python&logoColor=white" />                                                     |
| ☁️ 인프라/클라우드            | <img src="https://img.shields.io/badge/Runpod-4285F4?style=for-the-badge" /> <img src="https://img.shields.io/badge/AWS%20EC2-FF9900?style=for-the-badge&logo=Amazon-EC2&logoColor=white" />                                                                         |
| 🛠️ 기타                      | <img src="https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=Selenium&logoColor=white" /> <img src="https://img.shields.io/badge/PyMuPDF-00599C?style=for-the-badge&logo=AdobeAcrobatReader&logoColor=white" /> <img src="https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" /> <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=GitHub&logoColor=white" />   |


---

## 🐥 4. R&R (Roles & Responsibilities)

| 이름     | 역할                                   | 주요 담당                                   |
|--------|--------------------------------------|------------------------------------------|
| **기원준** | PM / AI모델링(Exaone) / DevOps / DBA / 백엔드 | 파인튜닝, 배포, 백엔드              |
| **전진혁** | AI모델링(Trellis) / AI/ML 엔지니어링 / 디자인 / 프론트 | 3D 변환, 프론트 UI, 디자인                     |
| **강지윤** | AI모델링(InternVL3) / AI/ML 엔지니어링 / 디자인 / 파이프라인 | 이미지 특징추출, 전체 파이프라인, DB설계                    |
| **최호연** | AI모델링(stable-video-diffusion-img2vid) / AI/ML 엔지니어링 / 백엔드 | 영상 생성, 백엔드 API                          |
| **우민규** | AI모델링(Stable-Diffusion) / AI/ML 엔지니어링      | 이미지 생성, AI연동                           |

> ※ 상세:  
> - **DevOps**: 인프라, 배포, CI/CD  
> - **DBA**: DB 스키마, 운영  
> - **AI/ML**: 임베딩·RAG·모델 연동  
> - **디자인**: Figma UI/UX  
> - **백엔드**: Django  
> - **챗봇**: 모델 활용 Q&A 시스템

---

## 🐥 5. 파이프라인, 시스템 아키텍처, ERD

🔧**파이프라인**  
<img src="https://github.com/user-attachments/assets/ace36901-0056-4197-ad5b-1d7ccac15dba"" width="800" alt="Pipeline"> <br>

🔧**시스템 아키텍처**  
<img src="https://github.com/user-attachments/assets/e22b039c-0dc3-4e44-90c6-f902847507ae" width="800" alt="System Architecture"> <br>

🔧**ERD**  
<img src="https://github.com/user-attachments/assets/2283e29a-2568-46f0-b52f-6ef64ec4b643" width="800" alt="ERD"> <br>

---

## 🐥 6. 폴더 구조 / 주요 폴더 설명

> (구체적 폴더 구조와 각 디렉터리별 기능 및 예시 설명. 추후 작성)

---

## 🐥 7. 모델 학습 결과서

> (파인튜닝/모델 실험 결과, 주요 지표, 예시 Q&A 등. 추후 작성)

---

## 🐥 8. 프로토타입

> (프로토타입/서비스 구현 스크린샷, 핵심 기능별 예시 등. 추후 작성)

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

> (추후 작성)

