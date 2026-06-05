@echo off
chcp 65001 >nul
echo ====================================
echo JS 文件打包工具 (使用 esbuild)
echo ====================================
echo.
cd /d "%~dp0"
npm run build
echo.
echo 打包完成！按任意键退出...
pause >nul
