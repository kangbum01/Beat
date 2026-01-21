
```markdown
# 🎵 Beat Visual: High Speed Visualizer Infrastructure

Ansible을 활용하여 **고가용성(High Availability) 및 고성능 웹 서비스 환경**을 자동으로 구축하는 IaC 프로젝트입니다.
**'Beat Visual'** 애플리케이션의 안정적인 배포를 위해 **HAProxy 로드밸런싱**, **Iptables 기반의 NAT 구성**, 그리고 **무중단 배포 전략**이 적용되었습니다.

## 🏗️ 아키텍처 (Architecture)

```mermaid
graph TD
    User((User)) -->|HTTP/80| HA[HAProxy (LB)]
    HA -->|Round Robin| W1[Web Server 1]
    HA -->|Round Robin| W2[Web Server 2]
    HA -->|Round Robin| W3[Web Server 3]
    
    subgraph "LB Node (10.4.2.10)"
        HA
        FS[Nginx File Server :8080]
    end
    
    W1 -.->|Fetch JSON| FS
    W2 -.->|Fetch JSON| FS
    W3 -.->|Fetch JSON| FS

```

### 🖥️ 서버 구성 (Server Inventory)

| Role | Hostname | IP | Description |
| :--- | :---: | :---: | :--- |
| **Load Balancer** | `lb` | `10.4.2.10` | • **HAProxy (Port 80)**: 트래픽 분산 및 입구(Ingress)<br>• **Nginx (Port 8080)**: 분석 데이터(JSON) 제공 파일 서버<br>• **NAT Gateway**: 내부 웹 서버들의 인터넷 연결 공유 |
| **Web Server 1** | `web1` | `10.4.2.11` | **Nginx (Port 80)**: Beat Visual 프론트엔드 구동 |
| **Web Server 2** | `web2` | `10.4.2.12` | **Nginx (Port 80)**: Beat Visual 프론트엔드 구동 |
| **Web Server 3** | `web3` | `10.4.2.13` | **Nginx (Port 80)**: Beat Visual 프론트엔드 구동 |
---

## 🛠️ 기술 스택 (Tech Stack)

### Frontend (Visualizer)

Three.js: 3D 렌더링 엔진 (WebGL).

Post-processing: UnrealBloomPass를 이용한 네온 발광(Glow) 효과 구현.

Animation Logic: BPM 기반의 터널 주행 속도 제어 및 Camera Shake 효과.

Backend (Analysis)
Python & Librosa: 오디오 파형 분석 (Tempo, Spectral Centroid, RMS).

FFmpeg: 오디오 포맷 변환 및 전처리.

DevOps & Infrastructure
Ansible: 인프라 프로비저닝 및 설정 관리 자동화 (IaC).

HAProxy: L4/L7 로드밸런싱 및 SSL 종단.

Nginx: 고성능 웹 서버.

Linux (RHEL/CentOS): SELinux 보안 정책 관리 및 커널 파라미터 튜닝.

## ✨ 주요 기능 (Key Features)
### 1. 3D Hyper Loop Visualizer
    Infinite Tunnel: TorusGeometry를 활용한 끊임없는 웜홀 주행 효과.

    Dynamic Particles: 음악의 Intensity에 따라 가속하는 Starfield 입자 시스템.

    Audio Reactive: 킥 드럼(Kick)과 비트에 맞춰 터널의 크기와 카메라 앵글이 역동적으로 변화.

### 2. Intelligent Analysis
    음원의 물리적 특성을 분석하여 **25가지의 감정(Mood)**으로 분류 (e.g., Manic, Chill, Powerful).

    분석된 감정에 따라 웜홀의 Main/Accent 컬러 팔레트 자동 매핑.

### 3. Automated Infrastructure
    git push 시 Ansible을 통해 변경 사항이 웹 서버 클러스터에 즉시 배포.

    Self-Healing Network: 배포 중 네트워크 단절 시 자동 복구 로직 탑재.

## 🚀 트러블 슈팅 (Troubleshooting & Challenges)
프로젝트 진행 중 발생한 주요 기술적 난제와 해결 사례입니다.

### 1. 네트워크 데드락 (Network Deadlock in Ansible)
    
    문제: Ansible 배포 중 방화벽(iptables -F)을 초기화하는 순간 NAT 규칙이 삭제되어, 외부 패키지 설치가 불가능해지고 배포가 멈추는 현상 발생.

    해결: 패키지 설치 태스크의 순서를 조정하고, 방화벽 초기화 명령과 NAT 복구 명령을 **단일 쉘 트랜잭션(Atomic Operation)**으로 묶어 통신 단절 시간 '0' 구현.

### 2. 브라우저 캐시 및 경쟁 상태 (Race Condition)
    
    문제: 사용자가 새 파일을 업로드해도 브라우저가 캐시된 이전 분석 결과(theme.json)를 표시하거나, 서버에 잔존하는 구버전 파일을 읽는 문제.

    해결:

    Backend: 분석 시작 전 ssh 명령으로 기존 결과 파일 강제 삭제(Clean-up).

    Frontend: fetch 요청 시 ?t=${Date.now()} 쿼리 스트링을 추가하여 캐시 무효화(Cache Busting).

    UX: AI 분석 시간을 고려하여 30초 대기 후 폴링(Polling) 시작.

### 3. SELinux 보안 컨텍스트
    
    문제: 외부에서 복사된(SCP) 정적 파일을 Nginx가 읽지 못해 403 Forbidden 발생.

    해결: chcon 명령어를 통해 해당 디렉토리 및 파일에 httpd_sys_content_t 보안 라벨을 명시적으로 부여하여 해결.

## 📂 디렉토리 구조 (Directory Structure)

```bash
Web-LB-Server/
├── inventory.ini             # 서버 목록 및 접속 정보 정의
├── site.yml                  # 메인 플레이북 (네트워크 복구 -> 웹 -> LB 순서 실행)
├── roles/
│   ├── frontend/             # [Web 1~3] Beat Visual 프론트엔드 및 UI 인디케이터 배포
│   ├── backend_files/        # [LB Node] 파일 서버(8080) 및 캐시 설정 구성
│   └── loadbalancer/         # [LB Node] HAProxy(80) 및 NAT/Iptables 설정
└── README.md                 # 프로젝트 문서

```

## ⚡ 실행 방법 (How to Run)

**1. 전체 인프라 구축 및 배포**

```bash
ansible-playbook -i inventory.ini site.yml

```

**2. 문법 검사 (Syntax Check)**

```bash
ansible-playbook -i inventory.ini site.yml --syntax-check

```

```

---

### 💡 주요 변경 포인트 (수정 이유)

1.  **제목 변경:** `Music Project` ➔ **`Beat Visual`** (리브랜딩 반영)
2.  **기술 스택 수정:** `Firewalld` ➔ **`Iptables`** (가장 큰 변경점 반영)
3.  **핵심 기술 추가 (가장 중요):**
    * **네트워크 데드락 방지:** 아까 고생해서 해결한 순서 변경 로직을 기술적 성과로 포장했습니다.
    * **캐시 제어:** 브라우저 캐시 문제 해결(헤더 + 타임스탬프) 내용을 추가했습니다.
    * **NAT 아키텍처:** LB가 인터넷 공유기 역할을 한다는 점을 명시했습니다.
4.  **다이어그램 추가:** `mermaid` 코드를 넣어 구조를 한눈에 보이게 했습니다. (GitHub에서 예쁘게 렌더링 됩니다.)
5.  **UI 기능 명시:** "서버 인디케이터" 기능을 추가하여 프론트엔드 작업 내역도 포함했습니다.

```

### 🚨 CI/CD 통합 시 주의사항 및 병합 가이드
## 1. [Network] 데드락 방지 로직 (수정 금지 ❌)

우리의 LB 서버는 NAT Gateway 역할을 겸하고 있습니다. 

일반적인 Ansible 방화벽 모듈(firewalld, ufw)을 사용하여 순차적으로 규칙을 적용하면, **기존 규칙이 초기화되는 순간 인터넷이 끊겨 배포가 중단(Deadlock)**됩니다.

유의점: iptables 초기화와 NAT 설정은 반드시 하나의 shell 블록 안에서 원자적(Atomic)으로 실행되어야 합니다.

코드 위치: roles/loadbalancer/tasks/main.yml (또는 firewall 관련 태스크)

```YAML

# ⚠️ [경고] 이 태스크를 절대 분리하거나 일반 모듈로 대체하지 마십시오.
# 연결 끊김 방지를 위해 Flush와 Restore가 동시에 일어나야 합니다.
- name: Reset Firewall & Restore NAT immediately (Atomic)
  shell: |
    iptables -F
    iptables -t nat -F
    # 초기화 즉시 NAT 복구
    iptables -t nat -A POSTROUTING -o ens160 -s 10.4.0.0/16 -j MASQUERADE
    # ... (기타 정책)
  async: 0
  poll: 0

```

## 2. [LB Node] 포트 충돌 방지 (Nginx vs HAProxy)
LB 서버(10.4.2.10) 한 대에 두 개의 웹 서비스가 공존하는 특수한 구조입니다.

HAProxy: 외부 트래픽 수신 (Port 80)

Nginx: 정적 파일 및 JSON 데이터 제공 (Port 8080)

유의점: 통합 플레이북에서 "모든 Nginx 설정을 80번 포트로 통일"하는 실수를 범하면 안 됩니다. LB 노드의 Nginx 설정(nginx.conf.j2)은 반드시 8080 포트를 유지해야 합니다.