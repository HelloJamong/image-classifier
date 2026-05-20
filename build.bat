@echo off
setlocal

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: build.bat - PyInstaller로 단일 exe 빌드 (개발자용)
::
:: 사전 조건: Python 3.8+, pip install -r requirements.txt
:: 결과물:   dist\classify_images.exe
:: 아이콘:   logo.ico (logo.png에서 생성한 Windows 아이콘)
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

echo [build] classify_images.exe 빌드 시작...

if not exist "logo.png" (
    echo [ERROR] logo.png 를 찾을 수 없습니다. 프로젝트 루트에 logo.png 파일을 두세요.
    exit /b 1
)

python make_ico.py
if %errorlevel% neq 0 (
    echo [ERROR] ICO 생성 실패.
    exit /b 1
)

python -m PyInstaller --onefile --console --name classify_images --icon logo.ico classify.py

if %errorlevel% neq 0 (
    echo [ERROR] 빌드 실패. PyInstaller가 설치되어 있는지 확인하세요.
    echo         pip install -r requirements.txt
    exit /b 1
)

echo.
echo [build] 완료: dist\classify_images.exe
endlocal
