# Implementation Plan: image-classifier

## Overview

`classify.py` 단일 파일에 이미지 스캔 → 해싱 → complete-linkage 클러스터링 → 미리보기 →
파일 이동 → 복원 스크립트 생성의 전체 파이프라인을 구현한다.
각 단계는 독립 함수로 작성되어 테스트 가능하다.

## Architecture Decisions

- **단일 파일 (`classify.py`):** PyInstaller 단일 exe 배포 편의성, 소규모 도구
- **phash → normalized Hamming complete-linkage:** 이진 phash에는 해밍 거리를 사용하고, complete-linkage로 브리지 효과를 줄임
- **GIF:** `Image.seek(0)` 후 `.convert("RGB")`로 첫 프레임 통일 처리
- **skip 전략:** `except Exception`으로 광범위하게 잡고 `(path, reason)` 튜플 누적

## Dependency Graph

```
scan_images(dir)
    │
    └── compute_hashes(paths)          ← GIF 첫 프레임, 에러 스킵
            │
            └── cluster(vectors, eps, min_samples)
                    │
                    ├── print_preview(groups, ungrouped)
                    │
                    └── [Y 선택 시]
                            ├── move_files(groups, ungrouped, dir)
                            └── build_restore_script(moved, backup_dir)
                                        │
                                        └── main()  ← 전체 조립 + Y/N + 스킵 로그
```

---

## Task List

### Phase 1: 데이터 파이프라인 (스캔 → 해싱 → 클러스터링)

---

#### Task 1: 이미지 파일 스캔

**Description:** 대상 폴더 최상위에서 지원 확장자 파일만 수집한다.
`_classify_backup/`, `_ungrouped/`, `group_NNN/` 폴더 내 파일은 제외한다.

**Acceptance criteria:**
- [ ] 지원 확장자(`.jpg .jpeg .png .webp .bmp .gif`)만 반환
- [ ] 대소문자 확장자 모두 인식 (`.JPG`, `.Png` 등)
- [ ] `_classify_backup`, `_ungrouped`, `group_` 로 시작하는 하위 폴더 내 파일 제외
- [ ] 폴더가 없거나 이미지가 0개면 명확한 메시지 출력 후 종료

**Verification:**
- [ ] `pytest tests/ -k test_scan` 통과
- [ ] 임시 폴더에 혼합 파일 넣고 수동 확인

**Dependencies:** None

**Files likely touched:**
- `classify.py`
- `tests/test_classify.py`
- `tests/conftest.py`

**Estimated scope:** Small

---

#### Task 2: 이미지 해싱 (phash + GIF 처리 + 스킵)

**Description:** 각 이미지를 `imagehash.phash`로 해싱해 64차원 이진 벡터로 변환한다.
GIF는 첫 프레임만 사용. 실패 파일은 `skipped` 리스트에 기록하고 계속 진행한다.

**Acceptance criteria:**
- [ ] 각 이미지 → `np.ndarray` shape `(64,)` float 벡터 반환
- [ ] GIF: `img.seek(0)` + `.convert("RGB")` 로 첫 프레임 추출
- [ ] 손상 이미지: 예외 잡아 `skipped: list[tuple[Path, str]]` 에 추가, 스킵
- [ ] 콘솔에 `해싱 중... (N/전체)` 카운터 출력 (`\r` 덮어쓰기)

**Verification:**
- [ ] `pytest tests/ -k test_hash` 통과
- [ ] 정상 이미지 해시 값이 재실행 시 동일한지 확인
- [ ] 손상 파일 포함 시 skipped 리스트에 해당 파일 존재

**Dependencies:** Task 1

**Files likely touched:**
- `classify.py`
- `tests/test_classify.py`
- `tests/conftest.py`

**Estimated scope:** Small

---

#### Task 3: complete-linkage 클러스터링

**Description:** 해시 벡터 배열을 받아 complete-linkage로 클러스터링 후
`groups: dict[int, list[Path]]`와 `ungrouped: list[Path]`를 반환한다.

**Acceptance criteria:**
- [ ] `AgglomerativeClustering(distance_threshold=eps, metric='hamming', linkage='complete')` 적용
- [ ] 클러스터 ID → Path 리스트 딕셔너리 반환 (ID는 0-based 정수)
- [ ] `min_samples` 미만 클러스터는 `ungrouped` 리스트에 포함
- [ ] 이미지 1장 또는 0장 입력 시 예외 없이 처리

**Verification:**
- [ ] `pytest tests/ -k test_cluster` 통과
- [ ] 동일 이미지 복사본 2장 → 같은 그룹에 배정 확인

**Dependencies:** Task 2

**Files likely touched:**
- `classify.py`
- `tests/test_classify.py`

**Estimated scope:** Small

---

### Checkpoint: Phase 1

- [ ] `pytest tests/ -v` 통과 (Phase 1 관련 테스트)
- [ ] 데이터 파이프라인 함수 시그니처 확정

---

### Phase 2: I/O (미리보기 → 파일 이동 → 복원 스크립트)

---

#### Task 4: 미리보기 출력

**Description:** 클러스터링 결과를 콘솔에 출력한다.

**Acceptance criteria:**
- [ ] 총 그룹 수, 각 그룹 이미지 수, ungrouped 수 출력
- [ ] 예시 형식:
  ```
  분류 결과 미리보기
  ─────────────────────────────
  그룹 수     : 3
  group_001   : 12장
  group_002   : 5장
  group_003   : 8장
  미분류(_ungrouped): 4장
  ─────────────────────────────
  ```

**Verification:**
- [ ] `pytest tests/ -k test_preview` 통과 (출력 문자열 캡처 검증)

**Dependencies:** Task 3

**Files likely touched:**
- `classify.py`
- `tests/test_classify.py`

**Estimated scope:** XS

---

#### Task 5: 파일 이동

**Description:** 확인 후 이미지를 그룹 폴더로 이동한다.

**Acceptance criteria:**
- [ ] `group_001/`, `group_002/`, ... (3자리 zero-padding) 폴더 생성 후 이동
- [ ] `_ungrouped/` 폴더에 미분류 이미지 이동
- [ ] 이동된 파일 목록 `list[tuple[Path, Path]]` (원본경로, 이동후경로) 반환
- [ ] 이동 중 오류 발생 시 해당 파일 스킵, 로그 기록

**Verification:**
- [ ] `pytest tests/ -k test_move` 통과 (임시 폴더 사용)
- [ ] 이동 후 원본 위치에 파일 없음, 대상 위치에 파일 있음

**Dependencies:** Task 3

**Files likely touched:**
- `classify.py`
- `tests/test_classify.py`

**Estimated scope:** Small

---

#### Task 6: 복원 스크립트 생성

**Description:** 이동된 파일을 원래 위치로 되돌리는 Windows `.bat` 파일을 생성한다.

**Acceptance criteria:**
- [ ] `_classify_backup/restore_YYYYMMDD_HHMMSS.bat` 경로에 생성
- [ ] 각 이동 파일마다 `move "현재경로" "원래경로"` 라인 포함
- [ ] 스크립트 헤더: `@echo off` + 주석으로 생성 일시 기재
- [ ] 이동된 파일 0개이면 스크립트 생성 안 함

**Verification:**
- [ ] `pytest tests/ -k test_restore` 통과
- [ ] 생성된 `.bat` 파일 내용 수동 검토

**Dependencies:** Task 5

**Files likely touched:**
- `classify.py`
- `tests/test_classify.py`

**Estimated scope:** Small

---

### Checkpoint: Phase 2

- [ ] `pytest tests/ -v` 전체 통과
- [ ] 임시 폴더로 수동 end-to-end 흐름 확인

---

### Phase 3: 조립 및 통합 테스트

---

#### Task 7: `main()` 조립 + Y/N 프롬프트 + 스킵 로그

**Description:** 모든 함수를 연결하는 `main()` 완성. Y/N 프롬프트 + 최종 스킵 로그 출력.

**Acceptance criteria:**
- [ ] `N` 입력 → 파일 이동 없이 종료
- [ ] `Y` 입력 → 이동 + 복원 스크립트 생성 + 완료 메시지
- [ ] 스킵 파일 있을 경우 마지막에 목록 출력:
  ```
  [경고] 처리 실패한 파일 2개:
    - bad_image.jpg: cannot identify image file
    - anim.gif: seek out of range
  ```
- [ ] `--dir` 미지정 시 스크립트 실행 위치 사용
- [ ] `--dir` 경로가 존재하지 않으면 에러 메시지 출력 후 종료 (code 1)

**Verification:**
- [ ] `python classify.py --dir tests/fixtures/sample` 수동 실행
- [ ] `pytest tests/ -k test_main` 통과

**Dependencies:** Tasks 4, 5, 6

**Files likely touched:**
- `classify.py`
- `tests/test_classify.py`

**Estimated scope:** Small

---

#### Task 8: 통합 테스트

**Description:** 실제 이미지 픽스처로 전체 파이프라인을 검증하는 통합 테스트 작성.

**Acceptance criteria:**
- [ ] `conftest.py`에서 Pillow로 단색 PNG, 유사 이미지 쌍, 손상 파일 픽스처 생성
- [ ] 통합 테스트: 유사 이미지 2장 → 같은 그룹 배정 확인
- [ ] 통합 테스트: 손상 파일 포함 → 스킵 후 나머지 정상 처리 확인
- [ ] 통합 테스트: `N` 응답 시 폴더 변경 없음 확인

**Verification:**
- [ ] `pytest tests/ -v` 전체 통과
- [ ] 커버리지: `pytest --cov=classify tests/` 핵심 함수 80% 이상

**Dependencies:** Task 7

**Files likely touched:**
- `tests/conftest.py`
- `tests/test_classify.py`

**Estimated scope:** Medium

---

### Checkpoint: Complete

- [ ] `pytest tests/ -v` 전체 통과
- [ ] `python -m flake8 classify.py --max-line-length 100` 통과
- [ ] 수동 end-to-end: 실제 이미지 폴더로 분류 → 복원 스크립트 실행 → 원상복구 확인
- [ ] SPEC.md 성공 기준 전 항목 체크

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| 느슨한 threshold나 density chaining이 거대 그룹을 만들 수 있음 | Medium | normalized Hamming distance와 complete-linkage 회귀 테스트로 검증 |
| GIF seek(0)이 일부 GIF에서 실패 | Low | except Exception으로 스킵 처리 |
| PyInstaller 빌드 환경 (Windows) | Low | 빌드는 로컬 Windows에서 진행, CI 제외 |
| 대용량 폴더(수천 장) 성능 | Low | 현 스코프 외, 필요 시 별도 이슈 |

## Open Questions

없음
