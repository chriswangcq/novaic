#!/bin/bash

echo "=========================================="
echo "X Server 授权修复脚本"
echo "=========================================="
echo ""

# 检查是否以 ubuntu 用户运行
if [ "$USER" != "ubuntu" ]; then
    echo "警告: 此脚本应该以 ubuntu 用户身份运行"
    echo "当前用户: $USER"
    echo ""
fi

echo "=== 方法1：复制授权文件 ==="
echo ""

# 查找 lightdm 的授权文件
echo "查找 lightdm 授权文件..."
LIGHTDM_AUTH=$(sudo find /var/run/lightdm -name ":0" 2>/dev/null | head -1)

if [ -n "$LIGHTDM_AUTH" ]; then
    echo "找到授权文件: $LIGHTDM_AUTH"
    echo "复制到 ~/.Xauthority..."
    sudo cp "$LIGHTDM_AUTH" ~/.Xauthority
    sudo chown ubuntu:ubuntu ~/.Xauthority
    chmod 600 ~/.Xauthority
    echo "✓ 授权文件已复制"
else
    echo "✗ 未找到 lightdm 授权文件"
fi
echo ""

echo "=== 方法2：设置 XAUTHORITY 环境变量 ==="
echo ""

if [ -n "$LIGHTDM_AUTH" ]; then
    echo "export XAUTHORITY=$LIGHTDM_AUTH" >> ~/.bashrc
    echo "export DISPLAY=:0" >> ~/.bashrc
    echo "✓ 已添加到 ~/.bashrc"
    echo ""
    echo "请运行以下命令使其生效："
    echo "  source ~/.bashrc"
else
    echo "✗ 无法设置，未找到授权文件"
fi
echo ""

echo "=== 测试 X Server 访问 ==="
echo ""

if [ -f ~/.Xauthority ]; then
    echo "使用 ~/.Xauthority 测试："
    DISPLAY=:0 xdpyinfo | head -5 2>&1
    RESULT1=$?
    echo ""
fi

if [ -n "$LIGHTDM_AUTH" ]; then
    echo "使用 XAUTHORITY 环境变量测试："
    DISPLAY=:0 XAUTHORITY="$LIGHTDM_AUTH" xdpyinfo | head -5 2>&1
    RESULT2=$?
    echo ""
fi

echo "=== 方法3：通过 xhost 添加访问权限 ==="
echo ""
echo "尝试添加 localhost 访问权限..."
sudo DISPLAY=:0 xhost +local: 2>&1
echo ""

echo "测试 xhost 方法："
DISPLAY=:0 xdpyinfo | head -5 2>&1
echo ""

echo "=== 当前状态 ==="
echo ""
echo "DISPLAY: $DISPLAY"
echo "XAUTHORITY: $XAUTHORITY"
echo "~/.Xauthority: "
ls -la ~/.Xauthority 2>&1
echo ""

echo "=========================================="
echo "修复完成"
echo "=========================================="
echo ""
echo "下一步:"
echo "1. 如果修复成功，请测试: DISPLAY=:0 xclock"
echo "2. 如果仍然失败，请检查桌面会话是否真的启动了"
echo "3. 可能需要重启 lightdm: sudo systemctl restart lightdm"
