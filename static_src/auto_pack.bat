@echo off
chcp 65001 >nul
echo ====================================
echo JS 文件自动打包监控 (使用 esbuild)
echo ====================================
echo.
echo 监控文件变化，自动重新打包...
echo 按 Ctrl+C 停止监控
echo.
cd /d "%~dp0"
npm run build:dev
