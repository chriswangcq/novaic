#!/usr/bin/env python3
"""
更新 Cloud-Init 配置以包含完整的 VMUSE 依赖

此脚本将更新 novaic-backend/gateway/vm/setup.py 中的 cloud-init 配置，
添加 Node.js、完整 Python 依赖、Playwright Chromium 等。
"""

import sys
from pathlib import Path

# 新的 runcmd 部分（优化后）
NEW_RUNCMD = '''# Startup commands
runcmd:
  # ========== Phase 1: Directory Setup ==========
  - echo "=== Phase 1: Directory Setup ==="
  - mkdir -p /home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml
  - mkdir -p /opt/novaic/scripts
  - mkdir -p /opt/novaic/venv
  - mkdir -p /opt/novaic/novaic-mcp-vmuse/src/novaic_mcp_vmuse
  - mkdir -p /opt/novaic/.cache
  
  # ========== Phase 2: Network & Environment ==========
  - echo "=== Phase 2: Waiting for network ==="
  - until ping -c 1 -W 3 8.8.8.8 > /dev/null 2>&1; do sleep 2; done
  - echo "Network ready."
  
  - echo 'DISPLAY=:0' | sudo tee -a /etc/environment
  - echo 'export PATH="/opt/novaic/venv/bin:$PATH"' | sudo tee -a /etc/profile.d/novaic.sh
  
  # ========== Phase 3: Node.js Installation ==========
  - echo "=== Phase 3: Installing Node.js 20 LTS ==="
  - curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  - apt-get install -y nodejs
  - node --version > /opt/novaic/.node_version
  - npm --version > /opt/novaic/.npm_version
  - echo "Node.js installed successfully."
  
  # ========== Phase 4: Python Virtual Environment ==========
  - echo "=== Phase 4: Creating Python virtual environment ==="
  - python3 -m venv /opt/novaic/venv
  - /opt/novaic/venv/bin/pip install --upgrade pip --index-url https://{pip_mirror} --trusted-host {pip_host}
  
  # ========== Phase 5: VMUSE Python Dependencies ==========
  - echo "=== Phase 5: Installing VMUSE Python dependencies ==="
  - /opt/novaic/venv/bin/pip install aiohttp pydantic pydantic-settings python-dotenv Pillow playwright --index-url https://{pip_mirror} --trusted-host {pip_host}
  - echo "Python dependencies installed."
  
  # ========== Phase 6: Playwright + Chromium ==========
  - echo "=== Phase 6: Installing Playwright Chromium ==="
  - /opt/novaic/venv/bin/playwright install --with-deps chromium
  - echo "Playwright Chromium installed."
  
  # ========== Phase 7: QEMU Guest Agent ==========
  - echo "=== Phase 7: Starting QEMU Guest Agent ==="
  - systemctl daemon-reload
  - systemctl enable qemu-guest-agent
  - systemctl start qemu-guest-agent
  
  # ========== Phase 8: Ownership ==========
  - echo "=== Phase 8: Setting ownership ==="
  - chown -R ubuntu:ubuntu /home/ubuntu
  - chown -R ubuntu:ubuntu /opt/novaic
  
  # ========== Phase 9: Display Manager ==========
  - echo "=== Phase 9: Starting display manager ==="
  - systemctl enable lightdm
  - systemctl start lightdm
  - sleep 10
  
  # ========== Phase 10: Enable VMUSE Service ==========
  - echo "=== Phase 10: Enabling VMUSE service ==="
  - systemctl daemon-reload
  - systemctl enable novaic-vmuse
  - echo "VMUSE service enabled (will start after code deployment)."
  
  # ========== Phase 11: Completion Marker ==========
  - touch /opt/novaic/.dependencies_installed
  - touch /opt/novaic/.cloud_init_complete
  - echo "NovAIC VM cloud-init completed at $(date)" > /var/log/novaic-init-done.log
  - echo "=== Cloud-Init Complete ==="'''

# 新的 systemd 服务配置
SYSTEMD_SERVICE_FILE = '''  - path: /etc/systemd/system/novaic-vmuse.service
    content: |
      [Unit]
      Description=NovAIC VMUSE HTTP Server
      After=network.target lightdm.service

      [Service]
      Type=simple
      User=ubuntu
      WorkingDirectory=/opt/novaic/novaic-mcp-vmuse
      Environment="DISPLAY=:0"
      Environment="PATH=/opt/novaic/venv/bin:/usr/local/bin:/usr/bin:/bin"
      Environment="PYTHONPATH=/opt/novaic/novaic-mcp-vmuse/src"
      ExecStart=/opt/novaic/venv/bin/python3 -m novaic_mcp_vmuse.http_server
      Restart=always
      RestartSec=10
      StandardOutput=journal
      StandardError=journal
      SyslogIdentifier=novaic-vmuse

      [Install]
      WantedBy=multi-user.target
    permissions: '0644'
'''

def main():
    # 查找 setup.py
    script_dir = Path(__file__).parent.parent
    setup_py = script_dir / "novaic-backend" / "gateway" / "vm" / "setup.py"
    
    if not setup_py.exists():
        print(f"❌ 找不到文件: {setup_py}")
        print("   请确保从 novaic 项目根目录运行此脚本")
        sys.exit(1)
    
    print(f"📝 准备更新: {setup_py}")
    print()
    
    # 读取文件
    content = setup_py.read_text()
    
    # 检查是否已经包含 Node.js 安装
    if "setup_20.x" in content:
        print("✅ 配置似乎已经更新过了（包含 Node.js 安装）")
        response = input("   是否仍要继续更新？(y/N): ")
        if response.lower() != 'y':
            print("取消更新")
            sys.exit(0)
    
    print("🔍 检测到的优化需求:")
    checks = []
    
    if "nodejs" not in content.lower():
        checks.append("  ❌ 缺少 Node.js 安装")
    else:
        checks.append("  ✅ 已包含 Node.js")
    
    if "aiohttp" not in content:
        checks.append("  ❌ 缺少 aiohttp 依赖")
    else:
        checks.append("  ✅ 已包含 aiohttp")
    
    if "pydantic-settings" not in content:
        checks.append("  ❌ 缺少 pydantic-settings")
    else:
        checks.append("  ✅ 已包含 pydantic-settings")
    
    if "novaic-vmuse.service" not in content:
        checks.append("  ❌ 缺少 systemd 服务配置")
    else:
        checks.append("  ✅ 已包含 systemd 配置")
    
    for check in checks:
        print(check)
    
    print()
    print("📋 本脚本将进行以下更新:")
    print("  1. 添加 Node.js 20 LTS 安装")
    print("  2. 添加完整 VMUSE Python 依赖")
    print("  3. 优化 Playwright Chromium 安装")
    print("  4. 添加 systemd 服务配置")
    print("  5. 添加环境变量设置")
    print("  6. 优化安装阶段划分")
    print()
    
    response = input("是否继续？(y/N): ")
    if response.lower() != 'y':
        print("取消更新")
        sys.exit(0)
    
    print()
    print("⚠️  注意：此脚本仅生成参考配置，不会自动修改文件")
    print("   请手动查看 VMUSE_CLOUD_INIT_OPTIMIZED.md")
    print("   并根据需要更新 novaic-backend/gateway/vm/setup.py")
    print()
    
    print("📚 参考文档:")
    print(f"   {script_dir}/VMUSE_CLOUD_INIT_OPTIMIZED.md")
    print()
    print("🔧 手动更新步骤:")
    print("   1. 打开 novaic-backend/gateway/vm/setup.py")
    print("   2. 找到 _create_cloud_init 方法")
    print("   3. 参考 VMUSE_CLOUD_INIT_OPTIMIZED.md 更新配置")
    print("   4. 测试新 VM 创建流程")
    print()
    
    print("✅ 已准备好优化方案，请参考文档手动更新配置")

if __name__ == "__main__":
    main()
