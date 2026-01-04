# Oracle Cloud Free Tier + Cloudflare 도메인 배포 가이드

이 가이드는 Oracle Cloud Free Tier를 사용하여 Money Book 애플리케이션을 배포하는 방법을 설명합니다.

## 준비 사항

- ✅ Cloudflare에서 도메인 구매 완료
- Oracle Cloud Free Tier 계정 (신규 가입 필요)
- 기본적인 Linux 명령어 지식

## 1. Oracle Cloud Free Tier 계정 생성

### 1.1 계정 가입
1. https://www.oracle.com/cloud/free/ 접속
2. **"Start for free"** 클릭
3. 계정 정보 입력 및 신용카드 등록 (과금되지 않음)
4. 계정 승인 대기 (1-2일 소요, 이메일 확인)

### 1.2 로그인
1. https://cloud.oracle.com/ 접속
2. 계정 로그인

## 2. Oracle Cloud 인스턴스 생성

### 2.1 Compute Instance 생성

1. 메인 메뉴에서 **"Compute"** → **"Instances"** 클릭
2. **"Create Instance"** 클릭
3. 다음 설정 입력:

   **기본 정보:**
   - **Name**: `money-book-server` (원하는 이름)
   - **Create in compartment**: 기본값 사용
   
   **리전(Region) 선택** (상단 오른쪽):
   - 원하는 리전 선택 (예: Seoul, Tokyo, Osaka 등)
   - ⚠️ **"Out of capacity" 에러 발생 시**: 다른 리전 선택을 먼저 시도해보세요!
   
   **Placement:**
   - **Availability domain**: 기본값(AD-1) 사용
   - 다른 AD가 보이면 선택 가능
   - AD-1만 보이는 경우 다른 리전 선택 고려

   **Image and Shape:**
   - **Image**: **"Canonical Ubuntu"** → **Ubuntu 22.04** 선택
   - **Shape**: **"Change Shape"** 클릭
     - **옵션 1 (추천)**: **"VM.Standard.A1.Flex"** (ARM 기반, Always Free) 선택
       - **OCPU count**: **1** (무료 할당량)
       - **Memory (GB)**: **6** (무료 할당량)
       - **Networking bandwidth (Gbps)**: **1** (기본값)
     - **옵션 2**: **"VM.Standard.E2.1.Micro"** (x86 기반, Always Free) 선택
       - 고정 사양: 1 OCPU, 1GB RAM (변경 불가)
       - ⚠️ **주의**: 메모리가 1GB로 적어서 Docker 빌드 시 스왑 메모리 추가가 필요할 수 있습니다
       - 하지만 Always Free이므로 비용 부담 없음
     - **Apply** 클릭

   **Networking:**
   
   **중요**: VCN을 먼저 설정해야 Subnet을 생성할 수 있습니다!
   
   - **Virtual cloud network (Primary network)**: 
     - 처음 사용하는 경우: **"Create new virtual cloud network"** 라디오 버튼 선택
       - 새 VCN 이름과 설정이 자동으로 생성됩니다
     - 기존 VCN이 있는 경우: **"Select existing virtual cloud network"** 선택 후 드롭다운에서 VCN 선택
   
   - **Subnet**: 
     - VCN을 선택/생성한 후, **"Create new public subnet"** 라디오 버튼 선택 (중요! Public Subnet이어야 Public IP 할당 가능)
       - Subnet name: 기본값 사용 (예: `subnet-20260103-1449`) 또는 원하는 이름
       - Create in compartment: 기본값 사용
       - CIDR block: 기본값 사용 (예: `10.0.0.0/24`)
     - 기존 Public Subnet이 있는 경우: **"Select existing subnet"** 선택 후 Public Subnet 선택
     - ⚠️ **주의**: Private Subnet을 선택하면 Public IP를 할당할 수 없습니다!
   
   - **Public IPv4 address assignment** 섹션 (화면 아래쪽 스크롤 필요):
     - VCN과 Public Subnet을 모두 설정한 후에 활성화됩니다
     - **"Automatically assign public IPv4 address"** 토글을 **ON** (오른쪽으로) 설정 (중요!)
     - ⚠️ **토글이 활성화되지 않는 경우**:
       - Primary network에서 "Create new virtual cloud network"가 선택되어 있는지 확인
       - 페이지를 새로고침 (F5) 후 다시 시도
       - 화면을 아래로 스크롤하여 섹션 확인
       - 그래도 안 되면 인스턴스를 생성한 후, 인스턴스 상세 페이지에서 Public IP를 수동으로 할당할 수 있습니다 (2.3 절 참고)

   **SSH Keys:**
   - **"Generate a key pair for me"** 선택 (간단한 방법)
   - 또는 기존 SSH 키 사용
   - **Private key** 다운로드 (`.key` 파일) - 나중에 필요함!
   - **Public key**는 자동으로 추가됨

4. **"Create"** 클릭

### 2.2 보안 그룹 설정 (방화벽)

1. **"Networking"** → **"Virtual Cloud Networks"** 클릭
2. 생성된 VCN 선택
3. **"Security Lists"** → **"Default Security List"** 클릭
4. **"Ingress Rules"** → **"Add Ingress Rules"** 클릭
5. 다음 규칙 추가:

   **SSH (포트 22):**
   - **Source Type**: CIDR
   - **Source CIDR**: `0.0.0.0/0`
   - **IP Protocol**: TCP
   - **Destination Port Range**: `22`
   - **Description**: `Allow SSH`
   - **"Add Ingress Rules"** 클릭

   **HTTP (포트 80):**
   - **Source Type**: CIDR
   - **Source CIDR**: `0.0.0.0/0`
   - **IP Protocol**: TCP
   - **Destination Port Range**: `80`
   - **Description**: `Allow HTTP`
   - **"Add Ingress Rules"** 클릭

   **HTTPS (포트 443):**
   - **Source Type**: CIDR
   - **Source CIDR**: `0.0.0.0/0`
   - **IP Protocol**: TCP
   - **Destination Port Range**: `443`
   - **Description**: `Allow HTTPS`
   - **"Add Ingress Rules"** 클릭

### 2.3 인스턴스 정보 확인 및 Public IP 할당

1. **"Compute"** → **"Instances"** 클릭
2. 생성된 인스턴스 클릭
3. **"Public IP address"** 확인
   - Public IP가 이미 할당되어 있다면 사용
   - Public IP가 없다면 아래 절차로 할당:

**Public IP가 없는 경우 할당 방법:**

1. 인스턴스 상세 페이지에서 **"Attached VNICs"** 섹션 찾기
2. VNIC 이름 (예: `money-report-hy`) 클릭
3. **"Edit"** 버튼 클릭
4. **"Public IPv4 address"** 섹션에서:
   - **"Assign a public IPv4 address"** 선택
   - **"Save"** 클릭
5. Public IP 주소 확인 (예: `123.45.67.89`)
6. 이 IP 주소를 메모해두세요 (나중에 Cloudflare DNS 설정에 필요)

## 3. 서버 초기 설정

### 3.1 SSH 접속

**Windows (Git Bash 또는 WSL):**

```bash
# SSH 키 파일 권한 설정 (필수!)
chmod 400 /path/to/your-private-key.key

# SSH 접속
ssh -i /path/to/your-private-key.key ubuntu@your-public-ip
```

**참고**: 
- `your-private-key.key`는 인스턴스 생성 시 다운로드한 파일 경로
- `your-public-ip`는 Oracle Cloud에서 확인한 Public IP 주소

처음 접속 시 "Are you sure you want to continue connecting (yes/no)?" 질문이 나오면 `yes` 입력

### 3.2 시스템 업데이트

```bash
sudo apt update && sudo apt upgrade -y
```

### 3.2.1 스왑 메모리 추가 (VM.Standard.E2.1.Micro 사용 시 강력 권장)

VM.Standard.E2.1.Micro (1GB RAM)을 사용하는 경우, Docker 빌드 시 메모리 부족을 방지하기 위해 스왑 메모리를 추가하는 것을 **강력히 권장**합니다:

```bash
# 스왑 메모리 추가 (2GB - E2.1.Micro는 메모리가 적으므로 2GB 권장)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 영구적으로 활성화
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 확인
free -h
```

스왑 메모리가 추가되었는지 확인 후 다음 단계로 진행하세요.

### 3.3 Docker 설치

```bash
# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker ubuntu

# Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker

# Docker Compose 설치
sudo apt install docker-compose -y

# 설치 확인 (로그아웃 후 재접속 필요)
docker --version
docker-compose --version
```

**중요**: Docker 그룹 적용을 위해 로그아웃 후 재접속하세요:
```bash
exit
# 다시 SSH 접속
ssh -i /path/to/your-private-key.key ubuntu@your-public-ip
```

### 3.4 Nginx 설치

```bash
sudo apt install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx
```

## 4. 애플리케이션 배포

### 4.1 프로젝트 업로드

로컬에서 Git 저장소에 업로드 (GitHub, GitLab 등) 후 서버에서 클론:

```bash
# 서버에서 실행
cd ~
sudo apt install git -y

# Git 저장소 클론 (GitHub/GitLab URL로 변경)
git clone https://github.com/your-username/money_book.git
cd money_book
```

```

### 4.2 데이터 파일 준비

로컬에서 `backend/data/ledger.json` 파일을 서버에 업로드:

```bash
# 로컬에서 실행
scp -i /path/to/your-private-key.key backend/data/ledger.json ubuntu@your-public-ip:~/money_book/backend/data/
```

또는 서버에서 직접 생성:

```bash
mkdir -p ~/money_book/backend/data
# ledger.json 파일 생성 또는 편집
nano ~/money_book/backend/data/ledger.json
```

### 4.3 프로덕션용 docker-compose.yml 생성

서버에서 `docker-compose.prod.yml` 파일 생성:

```bash
cd ~/money_book
nano docker-compose.prod.yml
```

다음 내용 입력 (`your-domain.com`을 실제 도메인으로 변경):

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "127.0.0.1:8000:8000"
    volumes:
      - ./backend/data:/app/data
    environment:
      - DATA_FILE_PATH=/app/data/ledger.json
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "127.0.0.1:3000:3000"
    depends_on:
      - backend
    environment:
      - REACT_APP_API_URL=https://your-domain.com/api
    restart: unless-stopped
```

**중요**: `your-domain.com`을 Cloudflare에서 구매한 실제 도메인으로 변경하세요!

### 4.4 애플리케이션 빌드 및 실행

```bash
cd ~/money_book

# Docker 이미지 빌드 및 실행
docker-compose -f docker-compose.prod.yml up -d --build

# 상태 확인
docker-compose -f docker-compose.prod.yml ps

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f
```

빌드에 시간이 걸릴 수 있습니다 (5-10분). 로그를 확인하여 오류가 없는지 확인하세요.

## 5. Nginx 리버스 프록시 설정

### 5.1 Nginx 설정 파일 생성

```bash
sudo nano /etc/nginx/sites-available/money-book
```

다음 내용 입력 (`your-domain.com`을 실제 도메인으로 변경):

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5.2 설정 활성화

```bash
# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/money-book /etc/nginx/sites-enabled/

# 기본 설정 제거
sudo rm /etc/nginx/sites-enabled/default

# 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl reload nginx
```

## 6. Cloudflare DNS 설정

### 6.1 Cloudflare 대시보드 접속

1. https://dash.cloudflare.com 접속
2. 구매한 도메인 선택

### 6.2 DNS 레코드 추가

1. **DNS** 탭 클릭
2. **A 레코드** 추가:
   - **Name**: `@` (루트 도메인)
   - **IPv4 address**: Oracle Cloud 인스턴스의 Public IP 주소
   - **Proxy status**: 🟠 **Proxied** (주황색 구름) - Cloudflare CDN 사용 (추천)
   - **TTL**: Auto
   - **"Save"** 클릭

3. **CNAME 레코드** 추가 (선택사항, www 서브도메인):
   - **Name**: `www`
   - **Target**: `your-domain.com`
   - **Proxy status**: 🟠 **Proxied**
   - **TTL**: Auto
   - **"Save"** 클릭

### 6.3 SSL/TLS 설정

1. **SSL/TLS** 탭 클릭
2. **Overview**에서 암호화 모드 선택:
   - **Flexible** 선택 (서버에 SSL 인증서가 없는 경우) - Cloudflare와 사용자 간만 HTTPS, Cloudflare와 서버 간은 HTTP
   - **Full** 또는 **Full (strict)** 선택 (서버에 SSL 인증서가 있는 경우) - Cloudflare와 서버 간도 HTTPS
   - ⚠️ **중요**: 서버에 SSL 인증서가 없으면 "Full" 모드에서 Error 521이 발생합니다!
3. **"Always Use HTTPS"** 켜기 (선택사항, 추천)
   - HTTP 요청을 HTTPS로 자동 리다이렉트

### 6.4 DNS 전파 대기

DNS 변경사항이 전 세계에 전파되는데 몇 분에서 몇 시간이 걸릴 수 있습니다. 보통 5-30분 정도 소요됩니다.

확인 방법:
```bash
# 로컬에서 실행
nslookup your-domain.com
# 또는
ping your-domain.com
```

## 7. 데이터 백업 설정

### 7.1 백업 스크립트 생성

```bash
nano ~/backup.sh
```

다음 내용 입력:

```bash
#!/bin/bash
BACKUP_DIR="$HOME/backups"
DATA_DIR="$HOME/money_book/backend/data"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp -r $DATA_DIR $BACKUP_DIR/ledger_${DATE}

# 오래된 백업 삭제 (30일 이상)
find $BACKUP_DIR -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: ledger_${DATE}"
```

```bash
chmod +x ~/backup.sh
```

### 7.2 자동 백업 설정 (Cron)

```bash
crontab -e
```

편집기에서 다음 줄 추가 (매일 새벽 3시 백업):

```
0 3 * * * /home/ubuntu/backup.sh >> /home/ubuntu/backup.log 2>&1
```

## 8. 애플리케이션 업데이트

새 버전을 배포할 때:

```bash
cd ~/money_book

# 코드 업데이트
git pull  # Git 사용하는 경우
# 또는 새로운 파일로 교체

# 데이터 백업
~/backup.sh

# 애플리케이션 재빌드 및 재시작
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f
```

## 9. 트러블슈팅

### 애플리케이션이 접속되지 않는 경우

```bash
# 컨테이너 상태 확인
docker-compose -f docker-compose.prod.yml ps

# 로그 확인
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend

# Nginx 상태 확인
sudo systemctl status nginx
sudo nginx -t

# 포트 확인 (ss 명령어 사용 - Ubuntu 22.04에 기본 설치됨)
sudo ss -tlnp | grep -E ':(80|443|3000|8000)'

# 또는 netstat을 사용하려면 net-tools 설치:
# sudo apt install net-tools -y
# sudo netstat -tlnp | grep -E ':(80|443|3000|8000)'
```

### Oracle Cloud 인스턴스가 자동 종료된 경우

Oracle Cloud Free Tier는 사용하지 않으면 자동으로 종료될 수 있습니다. 다시 시작:

1. Oracle Cloud 콘솔 접속
2. **"Compute"** → **"Instances"** 클릭
3. 인스턴스 선택
4. **"Start"** 버튼 클릭
5. Public IP 주소 확인 (변경되었을 수 있음)
6. Cloudflare DNS에서 IP 주소 업데이트 (필요한 경우)

### "Out of capacity" 에러 발생 시

Oracle Cloud Free Tier의 ARM 인스턴스는 인기가 많아서 가용성 도메인별로 용량이 부족할 수 있습니다.

**해결 방법:**

1. **다른 Availability Domain 선택** (가장 쉬운 방법):
   - 인스턴스 생성 페이지의 **"Placement"** 섹션에서
   - **"Availability domain"** 드롭다운 클릭
   - **AD-2** 또는 **AD-3** 선택 (만약 보이는 경우)
   - 다시 "Create" 버튼 클릭
   - ⚠️ **AD-1만 보이는 경우**: 이 리전에는 AD-1만 있거나 다른 AD에서 Free Tier ARM을 지원하지 않을 수 있습니다

2. **다른 리전(Region) 선택** (AD-1만 있을 때 추천):
   - 페이지 상단 오른쪽의 **리전 선택 메뉴** 클릭 (예: "AP-CHUNCHEON-1" 또는 현재 리전명)
   - 다른 리전 선택:
     - **Seoul (AP-SEOUL-1)** - 한국 서울
     - **Tokyo (AP-TOKYO-1)** - 일본 도쿄
     - **Osaka (AP-OSAKA-1)** - 일본 오사카
     - 기타 아시아 태평양 리전
   - 다른 리전 선택 후 인스턴스 생성 페이지로 돌아가서 다시 생성
   - ⚠️ **주의**: 리전을 변경하면 VCN과 Subnet도 새로 생성해야 할 수 있습니다

3. **나중에 다시 시도**:
   - 몇 시간 후 또는 다음 날 다시 시도
   - 용량이 해제되면 생성 가능

4. **x86 기반 인스턴스 사용**:
   - Shape를 VM.Standard.E2.1.Micro (Always Free) 또는 VM.Standard.E1.Flex로 변경
   - ⚠️ **중요**: VM.Standard.E1.Flex는 Always Free에 포함되지 않을 수 있습니다!
     - 비용이 발생할 수 있으니 Oracle Cloud 콘솔에서 사용량과 비용을 확인하세요
     - **"Billing and Cost Management"** → **"Cost Analysis"**에서 확인
   - 애플리케이션 실행에는 문제없지만, Free Tier 제한이 ARM보다 작을 수 있습니다
   - VM.Standard.E2.1.Micro는 Always Free이지만 1 OCPU, 1GB RAM으로 제한적

**권장**: AD-1만 보이는 경우, 다른 리전(Region)을 선택하는 것이 가장 좋은 방법입니다!

### SSH 접속이 안 되는 경우

1. Oracle Cloud 콘솔에서 인스턴스 상태 확인
2. 보안 그룹에서 포트 22가 열려있는지 확인
3. Public IP 주소 확인

### 메모리 부족 오류

VM.Standard.E2.1.Micro (1GB RAM) 또는 ARM 인스턴스 사용 시 Docker 빌드 중 메모리 부족이 발생할 수 있습니다:

**VM.Standard.E2.1.Micro 사용 시**: 스왑 메모리 추가를 **강력히 권장**합니다!

```bash
# 스왑 메모리 추가 (4GB)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 영구적으로 활성화
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Cloudflare Error 521 (Web server is down)

Cloudflare가 오리진 서버에 HTTPS 연결을 할 수 없을 때 발생합니다:

**원인:**
- Cloudflare SSL/TLS 모드가 "Full" 또는 "Full (strict)"로 설정되어 있는데, 서버에 SSL 인증서가 없는 경우

**해결 방법:**
1. Cloudflare 대시보드 → SSL/TLS 탭
2. 암호화 모드를 "Flexible"로 변경
3. 서버에 SSL 인증서를 설치한 경우에만 "Full" 또는 "Full (strict)" 사용

### Cloudflare Error 523 (Origin is unreachable)

Cloudflare가 오리진 서버에 연결할 수 없을 때 발생합니다. 다음을 순서대로 확인하세요:

**1. 서버 상태 확인:**
```bash
# SSH 접속이 되는지 확인
ssh -i /path/to/your-private-key.key ubuntu@your-public-ip
```

**2. 애플리케이션 실행 상태 확인:**
```bash
# Docker 컨테이너 상태 확인
docker-compose -f docker-compose.prod.yml ps

# 모든 컨테이너가 "Up" 상태인지 확인
# 만약 문제가 있다면:
docker-compose -f docker-compose.prod.yml logs -f
```

**3. Nginx 실행 상태 확인:**
```bash
# Nginx 상태 확인
sudo systemctl status nginx

# Nginx가 실행 중이 아니면:
sudo systemctl start nginx
sudo systemctl enable nginx

# Nginx 설정 테스트
sudo nginx -t
```

**4. 포트 확인:**
```bash
# 포트 80, 443, 3000, 8000이 열려있는지 확인 (ss 명령어 사용 - Ubuntu 22.04에 기본 설치됨)
sudo ss -tlnp | grep -E ':(80|443|3000|8000)'

# 또는 netstat을 사용하려면 net-tools 설치:
# sudo apt install net-tools -y
# sudo netstat -tlnp | grep -E ':(80|443|3000|8000)'
```

**5. Oracle Cloud 보안 그룹 확인:**
- Oracle Cloud 콘솔 → "Networking" → "Virtual Cloud Networks"
- 생성된 VCN 선택 → "Security Lists" → "Default Security List"
- **Ingress Rules** 탭에서 포트 80, 443이 열려있는지 확인
  - 없으면 추가: Source CIDR `0.0.0.0/0`, Port `80`, `443`
- **Egress Rules** 탭도 확인 (나가는 트래픽)
  - 모든 트래픽이 허용되어 있는지 확인 (Destination CIDR `0.0.0.0/0`, All Protocols)
  - 없으면 추가: "Add Egress Rules" → Destination CIDR `0.0.0.0/0`, IP Protocol `All Protocols`

**5-1. Network Security Groups (NSG) 확인:**
- Oracle Cloud 콘솔 → "Compute" → "Instances"
- 인스턴스 선택 → "Attached VNICs" 섹션에서 VNIC 클릭
- "Network Security Groups" 탭 확인
- NSG가 연결되어 있으면, 해당 NSG에도 포트 80, 443 규칙이 있는지 확인

**5-2. Ubuntu 방화벽 (ufw) 확인:**
```bash
# ufw 상태 확인
sudo ufw status

# ufw가 활성화되어 있으면 포트 80, 443 허용
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload
```

**5-3. iptables 확인 및 포트 80, 443 허용 (중요!):**

Oracle Cloud Ubuntu 이미지는 기본적으로 iptables를 사용하여 SSH(포트 22)만 허용합니다. 포트 80, 443을 허용해야 합니다:

```bash
# 현재 iptables 규칙 확인
sudo iptables -L -n -v

# 포트 80, 443 허용 규칙 추가 (SSH 규칙 앞에 추가)
sudo iptables -I INPUT 4 -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 5 -p tcp --dport 443 -j ACCEPT

# 규칙 확인
sudo iptables -L -n -v | grep -E '(80|443)'

# 규칙을 영구적으로 저장 (재부팅 후에도 유지)
sudo apt install iptables-persistent -y
sudo netfilter-persistent save
```

⚠️ **중요**: 재부팅 후에도 규칙이 유지되도록 `iptables-persistent` 패키지를 설치하고 저장해야 합니다!

**6. Cloudflare DNS 설정 확인:**
- Cloudflare 대시보드 → DNS 탭
- A 레코드가 올바른 Public IP로 설정되어 있는지 확인
- Public IP는 Oracle Cloud 콘솔 → "Compute" → "Instances" → 인스턴스 선택 → "Public IP address"에서 확인

**7. Cloudflare SSL/TLS 설정:**
- Cloudflare 대시보드 → SSL/TLS 탭
- 암호화 모드 확인:
  - 서버에 SSL 인증서가 **없는 경우**: "Flexible" 선택 (Cloudflare↔사용자: HTTPS, Cloudflare↔서버: HTTP)
  - 서버에 SSL 인증서가 **있는 경우**: "Full" 또는 "Full (strict)" 선택 (모두 HTTPS)
  - ⚠️ 서버에 SSL이 없는데 "Full" 모드면 Error 521 발생!

**8. Public IP 직접 접속 테스트:**
```bash
# 로컬에서 실행 (Public IP로 직접 접속)
curl http://your-public-ip

# 또는 브라우저에서 http://your-public-ip 접속
# 이것이 작동하면 Cloudflare DNS 설정 문제일 가능성 높음
```

**9. Internet Gateway 및 Route Table 확인:**

Public Subnet이 인터넷에 연결되려면 Internet Gateway와 Route Table이 필요합니다:

1. Oracle Cloud 콘솔 → "Networking" → "Virtual Cloud Networks"
2. VCN 선택 → "Internet Gateways" 탭 확인
   - Internet Gateway가 생성되어 있고 "Available" 상태인지 확인
   - 없으면 생성: "Create Internet Gateway" → 이름 입력 → "Create Internet Gateway"
3. "Route Tables" 탭 클릭
4. 서브넷에 연결된 Route Table 확인 (보통 "Default Route Table for vcn-xxx")
5. Route Table 클릭 → "Route Rules" 탭 확인
   - `0.0.0.0/0` → Internet Gateway로의 라우팅 규칙이 있는지 확인
   - 없으면 추가: "Add Route Rules"
     - Target Type: `Internet Gateway`
     - Destination CIDR Block: `0.0.0.0/0`
     - Target: Internet Gateway 선택
     - "Add Route Rules" 클릭
6. "Subnets" 탭에서 서브넷 클릭
7. "Route Table" 섹션에서 올바른 Route Table이 연결되어 있는지 확인

**10. Nginx 로그 확인:**
```bash
# Nginx 액세스 로그
sudo tail -f /var/log/nginx/access.log

# Nginx 에러 로그
sudo tail -f /var/log/nginx/error.log
```

### API 연결 오류

- 프론트엔드의 `REACT_APP_API_URL` 환경변수가 올바른지 확인
- 브라우저 개발자 도구의 Network 탭에서 API 요청 확인
- CORS 에러가 발생하면 백엔드에서 CORS 설정 확인

## 10. 보안 권장사항

1. **SSH 키 기반 인증 사용** (비밀번호 인증 비활성화)
2. **정기적인 시스템 업데이트**: `sudo apt update && sudo apt upgrade`
3. **방화벽 설정**: Oracle Cloud Security Lists 사용
4. **Cloudflare DDoS 보호 활성화**: 자동으로 활성화됨
5. **정기적인 데이터 백업**: 위의 백업 스크립트 사용
6. **SSH 키 파일 보관**: 로컬에서 안전하게 보관

## 11. 비용 요약

- **도메인**: Cloudflare (연간 약 $10-15, 도메인에 따라 다름)
- **서버**: Oracle Cloud Free Tier (무료!)
- **총 비용**: 약 $10-15/년 (도메인만)

**연간 약 84,000원 정도만 지출하면 됩니다!** (도메인 비용만)

## 12. 다음 단계

1. ✅ Oracle Cloud Free Tier 계정 생성
2. ✅ 인스턴스 생성
3. ✅ 서버 설정
4. ✅ 애플리케이션 배포
5. ✅ Cloudflare DNS 설정
6. ✅ 완료!

질문이나 문제가 있으면 알려주세요!

