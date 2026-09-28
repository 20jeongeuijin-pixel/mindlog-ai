# MindLog AI

MindLog AI는 일상 기록, 기분 점수, 스트레스 점수를 함께 수집하고 OpenAI API를 이용해 자기성찰용 피드백과 최근 기록의 정서 흐름을 보여주는 Streamlit 기반 디지털 정신건강 프로토타입입니다.

## 주요 기능

- 날짜별 기분 및 스트레스 점수 기록
- 자유 형식 일상 기록 작성
- AI 기반 감정 요약 및 주요 주제 추출
- 따뜻한 되돌아보기와 작은 행동 제안
- 최근 최대 7개 기록의 종합적인 정서 흐름 분석
- CSV 기반 로컬 저장
- 저장된 기록 표와 기분·스트레스 변화 그래프
- 전체 기록 CSV 다운로드
- 동일 기록 중복 저장 방지
- 삭제 전 자동 백업을 포함한 기록 삭제

## 기술 구성

- Python 3.12
- Streamlit
- pandas
- OpenAI Responses API
- Pydantic Structured Outputs

## 프로젝트 구조

```text
mindlog-ai-project/
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
├── .streamlit/
│   └── secrets.toml
└── data/
    ├── mindlog_records.csv
    └── backups/
```

`.streamlit/secrets.toml`과 `data` 폴더는 개인정보와 API 키 보호를 위해 GitHub에 업로드하지 않습니다.

## 설치 및 실행

### 1. 가상환경 생성

Windows PowerShell에서 다음 명령어를 실행합니다.

```powershell
python -m venv .venv
```

### 2. 패키지 설치

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. API 키 설정

프로젝트 안에 `.streamlit/secrets.toml` 파일을 만들고 다음 내용을 입력합니다.

```toml
OPENAI_API_KEY = "본인의_API_키"
```

API 키를 코드나 GitHub에 직접 올리지 않습니다.

### 4. 앱 실행

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

브라우저에서 `http://localhost:8501`을 열면 앱을 사용할 수 있습니다.

## 데이터 저장

- 기록은 사용자의 컴퓨터에 있는 `data/mindlog_records.csv`에 저장됩니다.
- 기록 삭제 전에는 `data/backups` 폴더에 백업 CSV가 자동 생성됩니다.
- AI 분석 버튼을 누를 때만 OpenAI API가 호출됩니다.
- AI 요청에는 `store=False`가 설정되어 있습니다.

## 주의사항

본 앱은 연구 아이디어와 자기모니터링 가능성을 탐색하기 위한 프로토타입입니다. 정신건강 문제를 진단하거나 치료를 제공하지 않습니다.

실제 연구 참여자를 대상으로 사용하려면 다음 사항을 별도로 검토해야 합니다.

- 기관생명윤리위원회(IRB) 승인
- 연구 참여 동의 절차
- 개인정보 비식별화 및 보안
- 위험 상황 대응 절차
- 모델 출력의 신뢰도와 타당도 검증
- 데이터 보관 및 폐기 기준

## 향후 확장 방향

- 기간별 기록 필터링
- 주간 및 월간 리포트 생성
- 사용자 인증과 암호화된 데이터베이스
- 표준화된 심리척도 연계
- 모델 출력 평가 및 임상적 타당도 검증

