@echo off
chcp 65001 >nul
:: ============================================================
::  Quest2ROS 连接助手 (Windows)
::  建立SSH隧道 + 配置防火墙
::  ============================================================
::  使用: 右键 -> 以管理员身份运行
:: ============================================================

set VM_IP=192.168.100.128
set VM_USER=dh
set TUNNEL_PORT=10000

echo.
echo ========================================
echo   Quest2ROS SSH 隧道连接助手
echo ========================================
echo.

:: ---------- 检查管理员权限 ----------
net session >nul 2>&1
if errorlevel 1 (
    echo [错误] 必须以管理员身份运行！
    echo   右键点击此文件 -> 以管理员身份运行
    echo.
    pause
    exit /b 1
)
echo [检查] 管理员权限: OK

:: ---------- 检查 ssh ----------
where ssh >nul 2>&1
if errorlevel 1 (
    echo [错误] 系统没有ssh命令，请安装OpenSSH客户端
    pause
    exit /b 1
)

:: ---------- 配置防火墙：允许10000端口入站 ----------
echo [1/4] 配置防火墙规则 (端口 %TUNNEL_PORT%)...
netsh advfirewall firewall add rule name="Quest2ROS Tunnel" dir=in action=allow protocol=tcp localport=%TUNNEL_PORT% >nul 2>&1
echo    -> 防火墙已放行

:: ---------- 从WiFi适配器获取IP ----------
echo [2/4] 获取本机WiFi IP...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4" ^| findstr /v "192.168.100\|172\.\|127\."') do (
    set WIFI_IP=%%a
    goto :found_ip
)
:found_ip
set WIFI_IP=%WIFI_IP: =%
if "%WIFI_IP%"=="" (
    echo    [警告] 未检测到WiFi IP，请手动输入
    set /p WIFI_IP="    WiFi IP: "
) else (
    echo    -> WiFi IP: %WIFI_IP%
)

:: ---------- 测试SSH ----------
echo [3/4] 测试SSH连接...
ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no %VM_USER%@%VM_IP% "echo OK" >nul 2>&1
if errorlevel 1 (
    echo    [失败] SSH连接失败
    pause
    exit /b 1
)
echo    -> SSH连接正常

:: ---------- 建立隧道 ----------
echo [4/4] 建立SSH隧道...
echo.
echo ========================================
echo   隧道已建立！
echo.
echo   Quest端设置:
echo     IP: %WIFI_IP%
echo     端口: %TUNNEL_PORT%
echo.
echo   按 Ctrl+C 断开
echo ========================================
echo.

ssh -N -L 0.0.0.0:%TUNNEL_PORT%:127.0.0.1:%TUNNEL_PORT% %VM_USER%@%VM_IP%

:: ---------- 清理 ----------
echo.
echo 隧道已断开。按任意键移除防火墙规则...
pause >nul
netsh advfirewall firewall delete rule name="Quest2ROS Tunnel" >nul 2>&1
