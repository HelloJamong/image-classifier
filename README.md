# image-classifier

시각적 유사도 기반 이미지 자동 분류 도구.

수백~수천 장의 이미지(일러스트, 사진 등)가 혼재된 폴더를 분석하여 비슷한 이미지끼리 자동으로 그룹화합니다.

## 특징

- 파일명 무관 — 이미지 내용 기반 분류
- Python 설치 불필요 — 단일 `.exe` 실행
- 분류 전 미리보기 + 확인 프롬프트
- 복원 스크립트 자동 생성

## 사용법

1. `classify_images.exe`와 `main.bat`을 분류할 폴더에 복사
2. `main.bat` 실행

```
group_001/   ← 비슷한 이미지 그룹
group_002/
...
_ungrouped/  ← 유사 그룹 없는 이미지
_classify_backup/restore_YYYYMMDD_HHMMSS.bat  ← 복원 스크립트
```

## 옵션

```
classify_images.exe --dir <폴더> [--eps 0.35] [--min-samples 2]
```

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--dir` | 실행 위치 | 대상 폴더 경로 |
| `--eps` | 0.35 | 그룹화 민감도 (낮을수록 엄격) |
| `--min-samples` | 2 | 그룹 최소 이미지 수 |

## 빌드 (개발자)

```bat
pip install -r requirements.txt
build.bat
```

## 지원 형식

`.jpg` `.jpeg` `.png` `.webp` `.bmp` `.gif` (첫 프레임 기준)

## 라이선스

MIT License
