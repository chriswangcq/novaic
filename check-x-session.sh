#!/bin/bash

echo "=========================================="
echo "X Server 授权和桌面会话诊断脚本"
echo "=========================================="
echo ""

echo "=== 1. 检查 X 授权文件 ==="
echo ""
echo "检查 ~/.Xauthority 文件："
ls -la ~/.Xauthority 2>&1
echo ""

echo "检查 /var/run/lightdm/root/:0 文件："
ls -la /var/run/lightdm/root/:0 2>&1
echo ""

echo "检查 /var/run/lightdm 目录结构："
sudo ls -la /var/run/lightdm/ 2>&1
echo ""

echo "使用 sudo 测试 DISPLAY=:0："
sudo DISPLAY=:0 xdpyinfo | head -20 2>&1
echo ""

echo "=== 2. 检查桌面会话进程 ==="
echo ""
echo "检查 xfce4-session："
ps aux | grep xfce4-session | grep -v grep
echo ""

echo "检查 ubuntu 用户的进程（前20个）："
ps aux | grep ubuntu | grep -v grep | head -20
echo ""

echo "检查 lightdm 进程："
ps aux | grep lightdm | grep -v grep
echo ""

echo "=== 3. 检查窗口管理器和桌面进程 ==="
echo ""
echo "检查 xfwm4（窗口管理器）："
ps aux | grep xfwm4 | grep -v grep
echo ""

echo "检查 xfdesktop（桌面环境）："
ps aux | grep xfdesktop | grep -v grep
echo ""

echo "检查 Xorg 进程："
ps aux | grep Xorg | grep -v grep
echo ""

echo "=== 4. 检查 lightdm 配置 ==="
echo ""
echo "检查自动登录配置："
if [ -f /etc/lightdm/lightdm.conf.d/50-autologin.conf ]; then
    cat /etc/lightdm/lightdm.conf.d/50-autologin.conf
else
    echo "配置文件不存在"
fi
echo ""

echo "检查主配置文件："
if [ -f /etc/lightdm/lightdm.conf ]; then
    cat /etc/lightdm/lightdm.conf | grep -v "^#" | grep -v "^$"
else
    echo "主配置文件不存在"
fi
echo ""

echo "=== 5. 检查 lightdm 日志 ==="
echo ""
echo "最近50条 lightdm 日志："
sudo journalctl -u lightdm -n 50 --no-pager 2>&1
echo ""

echo "=== 6. 环境变量测试 ==="
echo ""
echo "当前用户："
whoami
echo ""

echo "当前 DISPLAY 变量："
echo "DISPLAY=$DISPLAY"
echo ""

echo "尝试使用 XAUTHORITY 环境变量访问："
sudo -u ubuntu DISPLAY=:0 XAUTHORITY=/var/run/lightdm/root/:0 xdpyinfo | head -10 2>&1
echo ""

echo "=== 7. 检查 X Server 监听端口 ==="
echo ""
echo "检查 X11 socket："
ls -la /tmp/.X11-unix/ 2>&1
echo ""

echo "检查 X Server 网络连接："
sudo netstat -tlnp | grep :6000 2>&1
echo ""

echo "=== 8. 显示管理器状态 ==="
echo ""
echo "lightdm 服务状态："
sudo systemctl status lightdm --no-pager 2>&1
echo ""

echo "=========================================="
echo "诊断完成"
echo "=========================================="
