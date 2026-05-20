# Changelog

모든 주요 변경 사항을 이 파일에 기록합니다.  
버전 형식: `연도.메이저.마이너` (예: `26.1.0`)

---

## [26.1.3] - 2026-05-21

### Fixed
- PyInstaller exe 아이콘이 기본 아이콘으로 표시되던 문제를 수정했습니다. 단일 해상도 ICO 대신 16/32/48/64/128/256px 6개 해상도를 포함한 ICO를 빌드 시 자동 생성하도록 변경했습니다.

### Added
- `make_ico.py` 스크립트를 추가했습니다. `logo.png`에서 Windows 표준 다중 해상도 ICO를 생성하며, 빌드(`build.bat`)와 GitHub Actions 릴리스 워크플로우에서 PyInstaller 실행 전에 자동으로 호출됩니다.

### Changed
- 이미지 분류 정확도를 개선했습니다. 해시 알고리즘을 `phash` 단독에서 `phash + whash` 앙상블로 변경했습니다. 두 해시의 normalized Hamming distance 평균을 거리 기준으로 사용하여 구도만 비슷한 이미지의 오그룹 및 색상·텍스처가 유사한 이미지의 미분류를 모두 줄였습니다.
- `build.bat`의 아이콘 사전 검증 방식을 `logo.ico` 존재 확인에서 `logo.png` 존재 확인 후 ICO 자동 생성으로 변경했습니다.
- GitHub Actions 릴리스 워크플로우의 "Verify icon asset" 스텝을 "Generate icon asset"으로 교체했습니다.

---

## [26.1.2] - 2026-05-20

### Fixed
- PyInstaller exe 아이콘이 기본 로고로 보일 수 있던 문제를 줄이기 위해 `logo.png` 자동 변환 대신 Windows용 `logo.ico`를 직접 임베드하도록 변경했습니다.
- 다양한 이미지가 하나의 거대 그룹으로 합쳐질 수 있던 문제를 줄이기 위해 클러스터링 기준을 `cosine DBSCAN`에서 normalized Hamming distance 기반 complete-linkage로 변경했습니다.

### Added
- `logo.png`에서 생성한 다중 해상도 Windows 아이콘 파일 `logo.ico`를 추가했습니다.
- GitHub Actions 릴리스 빌드에서 `logo.ico` 존재 여부를 사전 검증하도록 변경했습니다.
- 서로 다른 phash가 기본 threshold에서 묶이지 않는지와 브리지 효과가 전체 그룹 병합으로 이어지지 않는지 검증하는 회귀 테스트를 추가했습니다.

### Changed
- `--eps` 기본값을 `0.35`에서 `0.32`로 낮춰 phash 64비트 기준 약 20비트 이내 차이만 기본 그룹 후보로 보도록 조정했습니다.
- 로컬 검증용 `sample/` 폴더가 git에 포함되지 않도록 `.gitignore`에 추가했습니다.

---

## [26.1.1] - 2026-05-20

### Fixed
- PyInstaller onefile 배포 exe를 이미지 폴더에서 직접 실행할 때 임시 압축 해제 폴더를 스캔해 “이미지를 찾을 수 없습니다.”로 종료되던 문제를 수정했습니다.
- 배포 exe에서 `--dir` 미지정 시 exe가 위치한 폴더를 기본 대상 폴더로 사용하도록 변경했습니다.

### Changed
- README 사용법을 `classify_images.exe` 단일 파일 배포 기준으로 정리하고, `main.bat`이 필요하지 않음을 명시했습니다.
- `main.bat`은 릴리스 배포물이 아닌 로컬 실행 보조 스크립트로 문서화했습니다.

### Added
- `logo.png`를 PyInstaller exe 아이콘으로 사용하도록 로컬 빌드와 GitHub Actions 릴리스 빌드에 반영했습니다.
- GitHub Actions 릴리스 빌드에서 `logo.png` 존재 여부를 사전 검증하도록 추가했습니다.
- 배포 exe의 기본 대상 폴더 결정 로직에 대한 테스트를 추가했습니다.

---

## [26.1.0] - 2026-05-18

### Added
- 시각적 유사도 기반 이미지 자동 분류 (perceptual hash + DBSCAN 클러스터링)
- 지원 형식: `.jpg` `.jpeg` `.png` `.webp` `.bmp` `.gif` (애니메이션 GIF 첫 프레임 기준)
- 대소문자 확장자 무관 인식 (`.JPG`, `.Png` 등)
- 분류 전 미리보기 출력 + Y/N 확인 프롬프트
- 손상·읽기 불가 파일 자동 스킵 및 실행 후 경고 로그 출력
- 복원 스크립트 자동 생성 (`_classify_backup/restore_YYYYMMDD_HHMMSS.bat`)
- CLI 옵션:
  - `--dir` : 대상 폴더 경로 (기본값: 실행 위치)
  - `--eps` : 그룹화 민감도, 낮을수록 엄격 (기본값: `0.35`)
  - `--min-samples` : 그룹 최소 이미지 수 (기본값: `2`)
- 단일 `.exe` 배포 (Python 설치 불필요)
