### 구성
```
music_project/
└── infra/
    ├── inventory/
    │   ├── hosts.ini            # 기존 hosts.ini 활용
    │   └── group_vars/
    │       ├── all.yml          # [중요] 모든 공통 변수
    │       ├── ai_server.yml    # AI 서버 관련 변수
    │       └── jenkins.yml      # 젠킨스 관련 변수
    ├── roles/
    │   ├── common/              # distribute_key.yaml, sync_time.yaml 로직
    │   ├── ai_server/           # setup_git_client.yaml 로직
    │   ├── jenkins_setup/       # install_Jenkins.yaml, Dockerfile, jenkins.yaml.j2
    │   └── web_deploy/          # deploy.yaml 로직
    └── playbooks/
        └── site.yml             # 모든 Role을 실행하는 마스터 코드
```
# 📘 1차 프로젝트 README

## 1️⃣ 프로젝트 소개
본 프로젝트는 **온프레미스 환경에서 CI/CD 기반 웹 서비스 자동 배포 시스템**을 구축하는 것을 목표로 한다.  
단순한 웹 서버 구성에 그치지 않고, **소스 코드 변경 → 자동 빌드 → 자동 배포 → 로드밸런싱 적용**까지 이어지는 전체 흐름을 직접 설계하고 구현하였다.

특히 내부 네트워크 환경에서의 실습을 고려하여  
외부 Git 서비스 대신 **내부 Bare Git 저장소**를 구축하고,  
**Jenkins + Ansible**을 활용한 자동화 파이프라인을 구성하였다.

이를 통해 CI/CD의 실제 동작 원리와 서버 간 **권한·네트워크·배포 자동화**에서 발생하는 문제들을 실습 기반으로 학습하였다.

---

## 2️⃣ 사용한 기술 · 도구

### 🔧 CI / CD & 자동화
- **Jenkins**: Git Push 이벤트 기반 CI 트리거 및 파이프라인 실행
- **Ansible**: 서버 설정 및 웹 배포 자동화
- **Docker**: Jenkins 실행 환경 컨테이너화
- **Git (Bare Repository)**: 내부 중앙 저장소 및 CI 트리거용 저장소

### 🌐 서버 · 네트워크
- **Nginx**: 웹 서버 및 Reverse Proxy
- **HAProxy**: L4 로드 밸런싱
- **NFS**: 웹 리소스 공유 스토리지
- **CentOS Stream 9**

### 📦 기타
- Shell Script
- ACL 기반 권한 제어
- SSH Key 기반 인증

---

## 3️⃣ 서버 구성 및 역할 소개

| 서버 | 역할 | 주요 기능 |
|---|---|---|
| CI 서버 | Jenkins | Git Push 감지, 빌드 및 배포 자동화 |
| Git 서버 | Bare Git | 내부 중앙 저장소, CI 트리거 |
| LB 서버 | HAProxy | 웹 트래픽 로드 밸런싱 |
| WEB 서버 | Nginx | 실제 웹 서비스 제공 |
| NFS 서버 | NFS | 웹 리소스 공유 스토리지 |

---

# 📕 CI / CD 전용 README

## 1️⃣ CI/CD 작업 소개
본 CI/CD 구성은 **Git Push 이벤트**를 시작점으로 하여 다음과 같은 자동화 흐름을 가진다.

Git Push  
→ Jenkins Pipeline 실행  
→ Ansible Playbook 수행  
→ 웹 서버 자동 배포  
→ LB 서버를 통한 서비스 제공

Jenkins는 **빌드·배포의 제어 역할**을 수행하고,  
Ansible은 **실제 서버 작업을 수행하는 자동화 도구**로 사용하였다.

---

## 2️⃣ 아키텍처 소개

### 📌 아키텍처 핵심 포인트
- 외부 GitHub 대신 **내부 Bare Git 저장소 사용**
- **Jenkins 컨테이너 기반** CI 환경 구성
- **Ansible 기반 자동 배포**로 반복 작업 최소화
- **HAProxy(L4) 트래픽 분산**으로 서비스 제공 안정성 확보
- **NFS 공유 스토리지**로 웹 리소스 일관성 유지

> 아키텍처 다이어그램: (여기에 이미지/그림 삽입)

---

## 3️⃣ 주요 트러블 슈팅

### 🔴 문제 1. 단일 SSH Key 사용 시 세밀한 권한 제어 불가능
- **문제 상황**
  - Jenkins와 Ansible이 동일 SSH Key 사용
  - 보안상 필요한 권한 분리 불가
  - Jenkins UID와 실제 서버 계정 간 충돌 발생
- **해결 방법**
  - Jenkins 전용 배포 키와 관리용 SSH 키 분리
  - ACL을 활용하여 특정 디렉토리 접근 권한만 허용
  - 서비스별 최소 권한 원칙 적용
- **결과**
  - 보안 강화
  - 배포 자동화 안정성 향상

---

### 🔴 문제 2. Git Dubious Ownership 보안 오류
- **문제 상황**
  - Jenkins 컨테이너 내부에서 Bare Git 저장소 접근 시
  - Git 보안 정책으로 인해 dubious ownership 오류 발생
- **해결 방법**
  - 안전 디렉토리 등록
  ```bash
  git config --system --add safe.directory /path/to/bare-repo
