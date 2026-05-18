@echo off
setlocal

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: build.bat - PyInstaller로 단일 exe 빌드 (개발자용)
::
:: 사전 조건: Python 3.8+, pip install -r requirements.txt
:: 결과물:   dist\classify_images.exe
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

echo [build] classify_images.exe 빌드 시작...

python -m PyInstaller --onefile --console --name classify_images classify.py

if %errorlevel% neq 0 (
    echo [ERROR] 빌드 실패. PyInstaller가 설치되어 있는지 확인하세요.
    echo         pip install -r requirements.txt
    exit /b 1
)

echo.
echo [build] 완료: dist\classify_images.exe
endlocal
