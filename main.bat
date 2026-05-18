@echo off
setlocal

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: main.bat - image-classifier 진입점
::
:: 사용법: main.bat을 분류할 폴더에 복사 후 실행
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

set "SCRIPT_DIR=%~dp0"
set "EXE=%SCRIPT_DIR%classify_images.exe"

if not exist "%EXE%" (
    echo [ERROR] classify_images.exe 를 찾을 수 없습니다.
    echo         build.bat 을 실행하여 먼저 빌드하세요.
    pause
    exit /b 1
)

"%EXE%" --dir "%~dp0" %*
if %errorlevel% neq 0 pause
endlocal
