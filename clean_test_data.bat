@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "TARGET_DIR=.\src\data\test"
set "KEEP_FILES=projects.json model_configs.json workspace_configs.json"

echo ============================================
echo Clean Dev Data Directory
echo Target: %TARGET_DIR%
echo Keep: %KEEP_FILES%
echo ============================================
echo.

if not exist "%TARGET_DIR%" (
    echo Error: Target directory not found - %TARGET_DIR%
    pause
    exit /b 1
)

cd /d "%TARGET_DIR%"

echo Deleting files...
for %%f in (*.json) do (
    set "delete=1"
    for %%k in (%KEEP_FILES%) do (
        if "%%f"=="%%k" (
            set "delete=0"
        )
    )
    if !delete! equ 1 (
        echo Delete: %%f
        del "%%f"
    ) else (
        echo Keep: %%f
    )
)

echo.
echo ============================================
echo Clean completed!
echo ============================================
pause