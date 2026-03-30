# Desktop Pet Slime

바탕화면에 살아있는 슬라임 캐릭터가 시스템 상태를 모니터링하고, 사용자와 상호작용하는 Windows 데스크톱 유틸리티입니다.

> 2026 대한기계학회 춘계학술대회 Vibe Coding 경진대회 출품작

## 주요 기능

- **실시간 시스템 모니터링** - CPU, RAM, 디스크, 네트워크, 배터리 상태를 슬라임의 감정으로 표현
- **8가지 감정 상태** - 행복, 스트레스, 졸림, 배고픔, 아픔 등 시스템 상태에 따른 표정 변화
- **미니게임** - 슬라임 먹이주기 아케이드 게임 (콤보, 폭탄, 난이도 증가)
- **스마트 알림** - 휴식 알림, 배터리 경고, 예약 리마인더
- **풍부한 상호작용** - 클릭(쓰다듬기), 드래그(이동), 더블클릭(미니게임), 눈이 마우스 추적
- **설정** - 크기 조절, 알림 간격, 자동 시작 등

## 실행 방법

### exe 파일 (권장)
[Releases](../../releases)에서 `DesktopPetSlime.exe`를 다운로드하여 실행

### Python으로 실행
```bash
pip install PyQt6 psutil
cd desktop_pet
python main.py
```

## 프로젝트 보고서

📄 [report.html](report.html) - 상세 프로젝트 보고서 (단일 HTML 파일)

## 기술 스택

- Python 3.11 + PyQt6
- QPainter (100% 프로그래밍 드로잉)
- psutil (시스템 모니터링)
- ctypes/Win32 API (유휴 감지)
- Claude Code AI (바이브 코딩)
