# Docker 설치 가이드 (macOS)

## 🐳 Docker Desktop 설치

### 1. Docker Desktop 다운로드

1. **Docker 공식 웹사이트 방문**: https://www.docker.com/products/docker-desktop/
2. **"Download for Mac"** 클릭
3. **Apple Silicon Mac** 또는 **Intel Mac**에 맞는 버전 선택

### 2. Docker Desktop 설치

1. 다운로드된 `.dmg` 파일 실행
2. Docker 아이콘을 Applications 폴더로 드래그
3. Applications 폴더에서 Docker 앱 실행
4. 설치 완료 후 Docker Desktop 실행

### 3. Docker 설치 확인

```bash
# Docker 버전 확인
docker --version

# Docker Compose 버전 확인
docker compose version

# Docker 실행 상태 확인
docker info
```

## 🚀 Docker Desktop 설정

### 1. 리소스 할당 (권장)

Docker Desktop > Settings > Resources에서:

- **Memory**: 4GB 이상 (8GB 권장)
- **CPU**: 2코어 이상 (4코어 권장)
- **Disk**: 20GB 이상

### 2. 포트 설정

Docker Desktop > Settings > Resources > Advanced에서:

- **Port forwarding**: 활성화
- **Port 8000, 8001, 6333, 6334**: 사용 가능한지 확인

## 🔧 Docker 설치 후 확인

### 1. Docker 서비스 상태 확인

```bash
# Docker가 실행 중인지 확인
docker ps

# Docker Compose 사용 가능한지 확인
docker compose version
```

### 2. 테스트 컨테이너 실행

```bash
# 간단한 테스트
docker run hello-world
```

## 🚨 문제 해결

### Docker Desktop이 실행되지 않는 경우

1. **시스템 요구사항 확인**:
   - macOS 10.15 (Catalina) 이상
   - 최소 4GB RAM
   - 가상화 지원 (Intel VT-x 또는 AMD-V)

2. **권한 문제 해결**:
   ```bash
   # Docker 그룹에 사용자 추가 (필요시)
   sudo usermod -aG docker $USER
   ```

3. **Docker Desktop 재시작**:
   - Docker Desktop 완전 종료
   - Applications에서 다시 실행

### Docker 명령어가 인식되지 않는 경우

1. **터미널 재시작**:
   ```bash
   # 새 터미널 창 열기
   # 또는 현재 터미널에서
   source ~/.zshrc
   ```

2. **PATH 확인**:
   ```bash
   echo $PATH
   # /usr/local/bin이 포함되어 있는지 확인
   ```

## 📋 설치 완료 후 다음 단계

Docker가 성공적으로 설치되면:

1. **Docker Desktop 실행**
2. **Docker 상태 확인**: `docker ps`
3. **BABSIM Pipeline 테스트 실행**:
   ```bash
   cd babsim
   docker compose up -d postgres qdrant inference-server
   python test_pipeline_complete.py
   ```

## 🔗 참고 링크

- **Docker Desktop 공식 문서**: https://docs.docker.com/desktop/install/mac/
- **Docker Compose 문서**: https://docs.docker.com/compose/
- **Docker 문제 해결**: https://docs.docker.com/desktop/troubleshoot/

## 💡 팁

- Docker Desktop은 처음 실행 시 시간이 걸릴 수 있습니다
- 시스템 리소스가 부족하면 Docker Desktop 설정에서 메모리/CPU 할당을 조정하세요
- Docker Desktop이 실행 중이어야 `docker` 명령어를 사용할 수 있습니다
