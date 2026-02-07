#!/bin/bash
# Simple Browser Daemon Launcher
# 以 ubuntu 用户启动浏览器守护进程

export XAUTHORITY=/home/ubuntu/.Xauthority
export DISPLAY=:0
export PLAYWRIGHT_BROWSERS_PATH=/opt/novaic/.cache
export HOME=/home/ubuntu

# 启动守护进程
exec /opt/novaic/venv/bin/python3 /opt/novaic/scripts/browser_keep_alive.py >> /tmp/browser_daemon.log 2>&1
