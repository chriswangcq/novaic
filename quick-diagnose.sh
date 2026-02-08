#!/bin/bash

# 快速诊断脚本 - 一键运行所有检查

echo "=========================================="
echo "X Server 快速诊断"
echo "时间: $(date)"
echo "用户: $(whoami)"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_process() {
    local name=$1
    local process=$2
    if pgrep -x "$process" > /dev/null; then
        echo -e "${GREEN}✓${NC} $name 运行中 (PID: $(pgrep -x $process))"
        return 0
    else
        echo -e "${RED}✗${NC} $name 未运行"
        return 1
    fi
}

echo "=== 核心进程检查 ==="
echo ""

check_process "X Server" "Xorg"
XORG_RUNNING=$?

check_process "lightdm" "lightdm"
LIGHTDM_RUNNING=$?

check_process "XFCE4 会话" "xfce4-session"
SESSION_RUNNING=$?

check_process "窗口管理器" "xfwm4"
WM_RUNNING=$?

check_process "桌面环境" "xfdesktop"
DESKTOP_RUNNING=$?

echo ""

# 检查 greeter
if pgrep lightdm-greeter > /dev/null; then
    echo -e "${YELLOW}⚠${NC} lightdm-greeter 运行中 - 可能停留在登录界面"
    GREETER_RUNNING=1
else
    echo -e "${GREEN}✓${NC} lightdm-greeter 未运行 - 已登录"
    GREETER_RUNNING=0
fi

echo ""
echo "=== 诊断结论 ==="
echo ""

if [ $XORG_RUNNING -eq 0 ] && [ $SESSION_RUNNING -eq 0 ] && [ $WM_RUNNING -eq 0 ]; then
    echo -e "${GREEN}✓✓✓ 桌面会话完整运行${NC}"
    echo ""
    echo "问题诊断: 仅 X 授权问题"
    echo ""
    echo -e "${YELLOW}建议操作:${NC}"
    echo "  运行修复脚本: ./fix-x-authorization.sh"
    echo ""
    
elif [ $XORG_RUNNING -eq 0 ] && [ $SESSION_RUNNING -ne 0 ]; then
    echo -e "${YELLOW}⚠⚠⚠ X Server 运行但桌面会话未启动${NC}"
    echo ""
    echo "问题诊断: 桌面会话未启动"
    echo ""
    
    if [ $GREETER_RUNNING -eq 1 ]; then
        echo "原因: 停留在登录界面（greeter）"
        echo ""
        echo -e "${YELLOW}建议操作:${NC}"
        echo "  1. 检查自动登录配置"
        echo "  2. 运行: cat /etc/lightdm/lightdm.conf.d/50-autologin.conf"
        echo "  3. 如需配置自动登录，运行:"
        echo ""
        echo "     sudo tee /etc/lightdm/lightdm.conf.d/50-autologin.conf <<EOF"
        echo "     [Seat:*]"
        echo "     autologin-user=ubuntu"
        echo "     autologin-session=xfce"
        echo "     EOF"
        echo ""
        echo "  4. 重启 lightdm: sudo systemctl restart lightdm"
    else
        echo "原因: XFCE 会话未启动"
        echo ""
        echo -e "${YELLOW}建议操作:${NC}"
        echo "  1. 检查 lightdm 配置"
        echo "  2. 重启 lightdm: sudo systemctl restart lightdm"
        echo "  3. 查看日志: sudo journalctl -u lightdm -n 50"
    fi
    echo ""
    
elif [ $XORG_RUNNING -ne 0 ]; then
    echo -e "${RED}✗✗✗ X Server 未运行${NC}"
    echo ""
    echo "问题诊断: X Server 未启动"
    echo ""
    echo -e "${YELLOW}建议操作:${NC}"
    echo "  1. 启动 lightdm: sudo systemctl start lightdm"
    echo "  2. 检查状态: sudo systemctl status lightdm"
    echo "  3. 查看日志: sudo journalctl -u lightdm -n 50"
    echo ""
else
    echo -e "${YELLOW}⚠ 状态异常${NC}"
    echo ""
    echo "建议运行完整诊断: ./check-x-session.sh"
    echo ""
fi

echo "=== 快速测试命令 ==="
echo ""
echo "测试 X Server 连接:"
echo "  DISPLAY=:0 xdpyinfo | head -5"
echo ""
echo "测试图形应用:"
echo "  DISPLAY=:0 xclock &"
echo ""
echo "查看授权文件:"
echo "  ls -la ~/.Xauthority"
echo "  sudo find /var/run/lightdm -name ':*'"
echo ""

echo "=========================================="
echo "快速诊断完成"
echo ""
echo "如需详细信息，请运行:"
echo "  ./check-desktop-session.sh  # 详细会话检查"
echo "  ./check-x-session.sh        # 完整诊断"
echo "=========================================="
