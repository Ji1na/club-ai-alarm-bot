# club-ai-alarm-bot

AI 학회 전용 Discord 알리미 봇

## 기능

| 명령어 | 설명 |
|--------|------|
| `!세션 제목\|날짜\|시간\|장소\|자료URL` | 세션 등록 + 채널 자동 공지 |
| `!출석 세션ID 도착시간` | 출석 체크 및 지각 자동 판정 |
| `!순위` | 이번 학기 지각 순위 조회 |
| `!퀴즈 세션ID` | 발표 자료 → AI 퀴즈 3개 자동 생성 |
| `!도움말` | 명령어 목록 |

- 지각 3회 이상 학회원은 세션 시작 30분 전에 별도 공지
- 매주 월요일 오전 9시 지각 순위 자동 공개

---

## 설치 방법

### 1. 레포 클론

```bash
git clone https://github.com/YOUR_USERNAME/club-ai-alarm-bot.git
cd club-ai-alarm-bot
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열고 아래 값을 채워넣기:

```
DISCORD_BOT_TOKEN=발급받은_봇_토큰
ANNOUNCE_CHANNEL_ID=공지_채널_ID
OPENAI_API_KEY=발급받은_OpenAI_키
```

---

## 환경변수 설정 방법

### Discord 봇 토큰 발급

1. https://discord.com/developers/applications 접속
2. **New Application** → 이름 입력 → Create
3. 왼쪽 **Bot** 탭 → **Reset Token** → 토큰 복사
4. **Privileged Gateway Intents** 에서 `Message Content Intent` 활성화
5. 왼쪽 **OAuth2** → **URL Generator** → `bot` 체크 → 권한 선택 → URL로 서버 초대

### 채널 ID 복사

디스코드 설정 → 고급 → **개발자 모드** 활성화  
→ 채널 우클릭 → **ID 복사**

### OpenAI API 키 발급

1. https://platform.openai.com/api-keys 접속
2. **Create new secret key** → 복사

---

## 실행 방법

```bash
python main.py
```

터미널에 `✅ 봇 실행 중: 봇이름#0000` 뜨면 성공

---

## 프로젝트 구조

```
club-ai-alarm-bot/
├── main.py            # 봇 진입점, 명령어 정의
├── db.py              # SQLite DB 초기화 및 쿼리
├── quiz_ai.py         # OpenAI 퀴즈 생성
├── material_reader.py # URL에서 발표 자료 읽기
├── late_manager.py    # 지각 판정 로직
├── scheduler.py       # 주기적 자동 공지
├── requirements.txt
├── .env.example       # 환경변수 템플릿
└── .gitignore
```
