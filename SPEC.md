# Spec: image-classifier

## Objective

수백~수천 장의 이미지(일러스트, 사진, 애니메이션 GIF 포함)가 혼재된 폴더를
시각적 유사도 기반으로 자동 그룹화하는 CLI 도구.

**사용자:** 이미지 정리가 필요한 개인 사용자 (Python 비설치 환경 포함)  
**배포 형태:** 단일 `.exe` (PyInstaller), Windows 전용

**성공 기준:**
- 같은 폴더의 이미지를 실행 한 번으로 유사도 기반 그룹 폴더로 이동
- 실행 전 미리보기 + Y/N 확인 후 파일 이동
- 복원 `.bat` 스크립트 자동 생성으로 원상복구 가능
- 처리 불가 파일(손상, 읽기 오류 등)은 로그 기록 후 스킵, 전체 실행 중단 없음

---

## Tech Stack

| 항목 | 선택 |
|---|---|
| Language | Python 3.8+ |
| 해시 알고리즘 | `imagehash.phash` + `imagehash.whash` 앙상블 (각 64비트 → 128차원 벡터) |
| 클러스터링 | `sklearn.cluster.AgglomerativeClustering` (metric=`precomputed`, linkage=`complete`) |
| 이미지 로딩 | `Pillow` (GIF는 첫 프레임 `Image.seek(0)`) |
| 배포 | `PyInstaller --onefile` |
| 테스트 | `pytest` |

---

## Commands

```bat
# 개발 환경 설정
pip install -r requirements.txt

# 실행 (개발)
python classify.py [--dir DIR] [--eps 0.32] [--min-samples 2]

# 빌드
build.bat  →  dist\classify_images.exe

# 사용 (배포)
classify_images.exe   (또는 classify_images.exe --dir <폴더>)

# 테스트
pytest tests/ -v

# 린트
python -m flake8 classify.py --max-line-length 100
```

---

## Project Structure

```
image-classifier/
├── classify.py          ← 진입점 + 전체 로직 (단일 파일)
├── requirements.txt     ← 런타임 + 빌드 의존성
├── build.bat            ← PyInstaller 빌드 스크립트
├── main.bat             ← 로컬 실행 보조 스크립트 (릴리스 배포물 아님)
├── logo.png             ← exe 아이콘 원본 이미지
├── logo.ico             ← PyInstaller가 직접 임베드하는 Windows 아이콘
├── SPEC.md              ← 이 문서
├── tests/
│   ├── conftest.py      ← 테스트용 이미지 픽스처
│   └── test_classify.py ← 단위 테스트
└── dist/
    └── classify_images.exe  ← 빌드 결과물 (gitignore)
```

> `classify.py` 단일 파일 유지 — PyInstaller 단일 파일 배포 편의성 및 소규모 도구 특성상 모듈 분리 불필요.

---

## 알고리즘 흐름

```
1. 대상 폴더 스캔 (최상위만, 재귀 없음)
   → 지원 확장자: .jpg .jpeg .png .webp .bmp .gif
   → GIF: Image.seek(0)으로 첫 프레임 추출

2. 각 이미지 phash + whash 계산 (각 64비트 → 128차원 벡터)
   → 앞 64차원: phash (밝기/구도), 뒤 64차원: whash (웨이블릿, 고주파 패턴)
   → 진행 출력: "해싱 중... (N/전체)"
   → 실패 시: skip_log에 기록, 해당 파일 스킵

3. 앙상블 거리 행렬 계산 후 클러스터링
   → 거리 = (phash_hamming + whash_hamming) / 2 (pairwise, 정규화)
   → AgglomerativeClustering(distance_threshold=args.eps, metric='precomputed', linkage='complete') 실행

4. 미리보기 출력
   → "그룹 수: N개 / 각 그룹 이미지 수 / ungrouped: M개"
   → "실행하시겠습니까? (Y/N): " 프롬프트

5. 파일 이동
   → group_001/, group_002/, ... (3자리 zero-padding)
   → _ungrouped/  (클러스터 미배정 이미지)

6. 복원 스크립트 생성
   → _classify_backup/restore_YYYYMMDD_HHMMSS.bat
   → 각 이동 파일에 대한 `move "현재경로" "원래경로"` 명령 나열

7. 스킵 로그 출력
   → 처리 실패 파일 목록 콘솔 출력 (있을 경우만)
```

---

## Code Style

```python
# 함수는 단일 책임, snake_case
def compute_hashes(image_paths: list[Path]) -> tuple[list[np.ndarray], list[Path]]:
    """해시 계산 성공 목록과 스킵 목록을 함께 반환."""
    hashes, skipped = [], []
    for i, path in enumerate(image_paths, 1):
        print(f"해싱 중... ({i}/{len(image_paths)})", end="\r")
        try:
            img = Image.open(path)
            img.seek(0)  # GIF 첫 프레임
            h = imagehash.phash(img)
            hashes.append((path, np.array(h.hash).flatten().astype(float)))
        except Exception as e:
            skipped.append((path, str(e)))
    print()
    return hashes, skipped
```

- 타입 힌트 사용 (Python 3.9+ 내장 타입, 3.8 호환 시 `from __future__ import annotations`)
- 예외는 `except Exception as e`로 광범위하게 잡되 로그에 이유 기록
- f-string 사용, `%` 포맷 미사용
- 라인 최대 100자

---

## Testing Strategy

**프레임워크:** `pytest`  
**위치:** `tests/test_classify.py`  
**커버리지 목표:** 핵심 함수 80% 이상

| 테스트 레벨 | 대상 |
|---|---|
| 단위 | `scan_images`, `compute_hashes`, `cluster`, `build_restore_script` |
| 통합 | 임시 폴더 + 실제 이미지 픽스처로 전체 흐름 검증 |
| 제외 | PyInstaller `.exe` 빌드 자체 |

**픽스처 전략:** `conftest.py`에서 `Pillow`로 단색 테스트 이미지 생성 (외부 이미지 파일 불필요)

---

## Boundaries

**Always:**
- 파일 이동 전 반드시 Y/N 확인
- 복원 스크립트는 항상 생성 (이동된 파일이 1개 이상이면)
- 처리 실패 파일은 로그 기록 후 스킵 (전체 중단 없음)
- 지원 확장자 외 파일은 무시 (로그 없음)

**Ask first:**
- 재귀 폴더 스캔 지원 추가
- 해시 알고리즘 변경 (phash → dhash 등)
- 복수 폴더 동시 처리

**Never:**
- `--dir`이 없을 때 기본 대상 폴더 외 폴더를 수정
- `--dir`이 존재하지 않을 때 파일 이동을 시도
- 원본 파일 삭제 (이동만, 삭제 없음)
- `_classify_backup/` 폴더 내 파일 분류 대상에 포함

**Runtime path rule:**
- 배포 exe에서 `--dir` 미지정 시 exe가 있는 폴더를 대상으로 한다.
- 개발 실행에서 `--dir` 미지정 시 현재 작업 폴더를 대상으로 한다.
- PyInstaller onefile exe의 `__file__`은 임시 압축 해제 폴더를 가리킬 수 있으므로 배포 exe의 기본 대상 결정에 사용하지 않는다.

---

## Success Criteria

- [ ] `pytest tests/ -v` 전체 통과
- [ ] `python classify.py --dir <테스트폴더>` 실행 시 그룹 폴더 정상 생성
- [ ] 손상된 이미지 포함 폴더 실행 시 해당 파일 스킵 후 정상 완료
- [ ] 복원 스크립트 실행 시 파일 원위치 복원
- [ ] `build.bat` 실행 후 `dist/classify_images.exe` 생성 및 단독 실행 가능
- [ ] `N` 입력 시 파일 이동 없이 종료

## Open Questions

없음 — 모든 항목 확인 완료.
