"""
VM Setup - Creates VM disk and cloud-init configuration

Migrated from Tauri's setup.rs to Python for Gateway control.
"""

import os
import platform
import subprocess
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

from .ssh import get_ssh_key_manager

logger = logging.getLogger(__name__)


@dataclass
class SetupProgress:
    """Progress info for VM setup."""
    stage: str
    progress: float  # 0-100
    message: str


class VmSetup:
    """
    Handles VM disk and cloud-init creation.
    
    Operations:
    - Environment check (QEMU, mkisofs, etc.)
    - VM disk creation (qcow2 from base image)
    - Cloud-init ISO generation
    - UEFI firmware setup (ARM64)
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        from common.config import ServiceConfig
        
        # 统一使用 ServiceConfig.DATA_DIR
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(ServiceConfig.DATA_DIR)
        
        self.arch = platform.machine()  # 'arm64' or 'x86_64'
        self.is_arm = self.arch in ("arm64", "aarch64")
        self.is_macos = platform.system() == "Darwin"
    
    def get_vm_dir(self, agent_id: str) -> Path:
        """Get VM directory for an agent."""
        vm_dir = self.data_dir / "agents" / agent_id
        vm_dir.mkdir(parents=True, exist_ok=True)
        return vm_dir
    
    # ==================== Environment Check ====================
    
    def check_environment(self) -> Dict[str, Any]:
        """
        Check if all required dependencies are installed.
        
        Returns:
            Dict with ready status and dependency details.
        """
        deps = []
        
        # QEMU system
        qemu_path, qemu_version = self._find_qemu_system()
        deps.append({
            "name": "QEMU",
            "installed": qemu_path is not None,
            "version": qemu_version,
            "path": qemu_path,
            "install_command": "brew install qemu" if self.is_macos else "apt install qemu-system",
        })
        
        # qemu-img
        qemu_img_path, qemu_img_version = self._find_qemu_img()
        deps.append({
            "name": "qemu-img",
            "installed": qemu_img_path is not None,
            "version": qemu_img_version,
            "path": qemu_img_path,
        })
        
        # ISO tool (mkisofs/genisoimage/hdiutil)
        iso_path, iso_name = self._find_iso_tool()
        deps.append({
            "name": "ISO Creator",
            "installed": iso_path is not None,
            "version": iso_name,
            "path": iso_path,
            "install_command": "brew install cdrtools" if self.is_macos else "apt install genisoimage",
        })
        
        # UEFI firmware (ARM64 only)
        if self.is_arm:
            uefi_path = self._find_uefi_firmware()
            deps.append({
                "name": "UEFI Firmware",
                "installed": uefi_path is not None,
                "path": uefi_path,
            })
        
        ready = all(d["installed"] for d in deps)
        
        return {
            "ready": ready,
            "platform": platform.system(),
            "arch": self.arch,
            "dependencies": deps,
        }
    
    def _find_qemu_system(self) -> tuple[Optional[str], Optional[str]]:
        """Find QEMU system binary."""
        arch_suffix = "aarch64" if self.is_arm else "x86_64"
        binary_name = f"qemu-system-{arch_suffix}"
        
        # 1. Check bundled QEMU in resource directory (for packaged app)
        bundled_path = self._get_bundled_path("qemu", binary_name)
        if bundled_path:
            version = self._get_version(bundled_path, "--version")
            return bundled_path, version
        
        # 2. Fallback to system paths
        paths = [
            f"/opt/homebrew/bin/{binary_name}",
            f"/usr/local/bin/{binary_name}",
            f"/usr/bin/{binary_name}",
        ]
        
        for path in paths:
            if Path(path).exists():
                version = self._get_version(path, "--version")
                return path, version
        
        # Try PATH
        version = self._get_version(binary_name, "--version")
        if version:
            return binary_name, version
        
        return None, None
    
    def _find_qemu_img(self) -> tuple[Optional[str], Optional[str]]:
        """Find qemu-img binary."""
        # 1. Check bundled qemu-img in resource directory (for packaged app)
        bundled_path = self._get_bundled_path("qemu", "qemu-img")
        if bundled_path:
            version = self._get_version(bundled_path, "--version")
            return bundled_path, version
        
        # 2. Fallback to system paths
        paths = [
            "/opt/homebrew/bin/qemu-img",
            "/usr/local/bin/qemu-img",
            "/usr/bin/qemu-img",
        ]
        
        for path in paths:
            if Path(path).exists():
                version = self._get_version(path, "--version")
                return path, version
        
        version = self._get_version("qemu-img", "--version")
        if version:
            return "qemu-img", version
        
        return None, None
    
    def _find_iso_tool(self) -> tuple[Optional[str], Optional[str]]:
        """Find ISO creation tool."""
        # Try mkisofs first
        mkisofs_paths = [
            "/opt/homebrew/bin/mkisofs",
            "/usr/local/bin/mkisofs",
            "/usr/bin/mkisofs",
            "/opt/homebrew/bin/genisoimage",
            "/usr/local/bin/genisoimage",
            "/usr/bin/genisoimage",
        ]
        
        for path in mkisofs_paths:
            if Path(path).exists():
                return path, Path(path).name
        
        # hdiutil on macOS
        if self.is_macos and Path("/usr/bin/hdiutil").exists():
            return "/usr/bin/hdiutil", "hdiutil"
        
        return None, None
    
    def _find_uefi_firmware(self) -> Optional[str]:
        """Find UEFI firmware for ARM64."""
        # 1. Check bundled UEFI firmware in resource directory (for packaged app)
        # Firmware is in qemu/share/ subdirectory
        bundled_path = self._get_bundled_path("qemu/share", "edk2-aarch64-code.fd")
        if bundled_path:
            return bundled_path
        
        # 2. Fallback to system paths
        paths = [
            "/opt/homebrew/share/qemu/edk2-aarch64-code.fd",
            "/usr/local/share/qemu/edk2-aarch64-code.fd",
            "/usr/share/qemu/edk2-aarch64-code.fd",
        ]
        
        for path in paths:
            if Path(path).exists():
                return path
        
        return None
    
    def _get_bundled_path(self, subdir: str, filename: str) -> Optional[str]:
        """Get bundled file path from resource directory."""
        from common.config import ServiceConfig
        resource_dir = ServiceConfig.RESOURCE_DIR
        logger.info(f"[VmSetup] _get_bundled_path: RESOURCE_DIR='{resource_dir}'")
        if not resource_dir:
            logger.info(f"[VmSetup] _get_bundled_path: resource_dir is empty, returning None")
            return None
        
        bundled_path = Path(resource_dir) / subdir / filename
        logger.info(f"[VmSetup] _get_bundled_path: checking {bundled_path}, exists={bundled_path.exists()}")
        if bundled_path.exists():
            return str(bundled_path)
        
        return None
    
    def _get_version(self, cmd: str, arg: str) -> Optional[str]:
        """Get version string from command."""
        try:
            result = subprocess.run(
                [cmd, arg],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except Exception as e:
            logger.debug("[VmSetup] _get_version(%s) failed: %s", cmd, e)
        return None
    
    # ==================== VM Setup ====================
    
    def setup_vm(
        self,
        agent_id: str,
        source_image: str,
        disk_size: str = "40G",
        use_cn_mirrors: bool = False,
        on_progress: Optional[Callable[[SetupProgress], None]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Setup VM files (disk + cloud-init ISO + UEFI).

        Args:
            agent_id: Used as directory name under data_dir/agents/
            source_image: Path to source cloud image
            disk_size: Disk size (e.g., "40G")
            use_cn_mirrors: Use Chinese mirrors for apt/pip
            on_progress: Progress callback
            user_id: When provided, look up SSH key by user_id directly
                     (use for user-owned devices that have no agent row)

        Returns:
            Dict with paths to created files.
        """
        vm_dir = self.get_vm_dir(agent_id)

        # Resolve SSH public key
        mgr = get_ssh_key_manager()
        if user_id:
            ssh_pubkey = mgr.get_public_key(user_id)
        else:
            ssh_pubkey = mgr.get_public_key_for_agent(agent_id)
        
        result = {
            "vm_dir": str(vm_dir),
            "disk_path": None,
            "cloudinit_iso": None,
            "uefi_vars": None,
        }
        
        # Step 1: Create VM disk
        if on_progress:
            on_progress(SetupProgress("Creating VM disk", 10, "Converting cloud image..."))
        
        disk_path = vm_dir / "disk.qcow2"
        self._create_disk(source_image, disk_path, disk_size)
        result["disk_path"] = str(disk_path)
        logger.info(f"[VmSetup] Created disk: {disk_path}")
        
        # Step 2: Create cloud-init ISO
        if on_progress:
            on_progress(SetupProgress("Creating cloud-init", 50, "Generating cloud-init ISO..."))
        
        iso_path = vm_dir / "cloud-init.iso"
        self._create_cloud_init(vm_dir, iso_path, ssh_pubkey, use_cn_mirrors)
        result["cloudinit_iso"] = str(iso_path)
        logger.info(f"[VmSetup] Created cloud-init: {iso_path}")
        
        # Step 3: Setup UEFI (ARM64 only)
        if self.is_arm:
            if on_progress:
                on_progress(SetupProgress("Setting up UEFI", 80, "Copying UEFI firmware..."))
            
            vars_path = vm_dir / "QEMU_VARS.fd"
            self._setup_uefi(vm_dir, vars_path)
            result["uefi_vars"] = str(vars_path)
            logger.info(f"[VmSetup] UEFI vars: {vars_path}")
        
        if on_progress:
            on_progress(SetupProgress("Complete", 100, "VM setup complete"))
        
        return result
    
    def _create_disk(self, source_image: str, dest_path: Path, disk_size: str):
        """Create VM disk from source image."""
        qemu_img, _ = self._find_qemu_img()
        if not qemu_img:
            raise RuntimeError("qemu-img not found")
        
        # Convert to qcow2
        result = subprocess.run(
            [qemu_img, "convert", "-O", "qcow2", source_image, str(dest_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"qemu-img convert failed: {result.stderr}")
        
        # Resize
        result = subprocess.run(
            [qemu_img, "resize", str(dest_path), disk_size],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"qemu-img resize failed: {result.stderr}")
    
    def _create_cloud_init(
        self,
        vm_dir: Path,
        iso_path: Path,
        ssh_pubkey: str,
        use_cn_mirrors: bool,
    ):
        """Create cloud-init ISO."""
        config_dir = vm_dir / "cloud-init"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Mirrors configuration
        if use_cn_mirrors:
            # APT mirror (Ubuntu packages)
            apt_mirror = "mirrors.aliyun.com/ubuntu-ports" if self.is_arm else "mirrors.aliyun.com/ubuntu"
            # pip mirror (Python packages)
            pip_mirror = "mirrors.aliyun.com/pypi/simple/"
            pip_host = "mirrors.aliyun.com"
            # Node.js mirror
            nodejs_setup_url = "https://mirrors.aliyun.com/nodesource/setup_20.x"
            # npm mirror
            npm_registry = "https://registry.npmmirror.com"
            # Playwright mirror (Chromium download)
            playwright_mirror = "https://npmmirror.com/mirrors/playwright/"
        else:
            # APT mirror (Ubuntu packages)
            apt_mirror = "ports.ubuntu.com/ubuntu-ports" if self.is_arm else "archive.ubuntu.com/ubuntu"
            # pip mirror (Python packages)
            pip_mirror = "pypi.org/simple/"
            pip_host = "pypi.org"
            # Node.js mirror
            nodejs_setup_url = "https://deb.nodesource.com/setup_20.x"
            # npm mirror
            npm_registry = "https://registry.npmjs.org"
            # Playwright mirror (use default)
            playwright_mirror = ""
        
        ubuntu_codename = "noble"  # Ubuntu 24.04
        
        # Write meta-data
        meta_data = "instance-id: novaic-vm\nlocal-hostname: novaic-vm\n"
        (config_dir / "meta-data").write_text(meta_data)
        
        # Write user-data
        user_data = self._generate_user_data(
            ssh_pubkey=ssh_pubkey,
            apt_mirror=apt_mirror,
            ubuntu_codename=ubuntu_codename,
            pip_mirror=pip_mirror,
            pip_host=pip_host,
            nodejs_setup_url=nodejs_setup_url,
            npm_registry=npm_registry,
            playwright_mirror=playwright_mirror,
        )
        (config_dir / "user-data").write_text(user_data)
        
        # Create ISO
        iso_tool, tool_name = self._find_iso_tool()
        if not iso_tool:
            raise RuntimeError("No ISO creation tool found")
        
        if tool_name in ("mkisofs", "genisoimage"):
            result = subprocess.run(
                [
                    iso_tool,
                    "-output", str(iso_path),
                    "-volid", "cidata",
                    "-joliet",
                    "-rock",
                    str(config_dir / "user-data"),
                    str(config_dir / "meta-data"),
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(f"mkisofs failed: {result.stderr}")
        
        elif tool_name == "hdiutil":
            # macOS hdiutil
            temp_dir = config_dir / "iso-temp"
            temp_dir.mkdir(exist_ok=True)
            shutil.copy(config_dir / "user-data", temp_dir / "user-data")
            shutil.copy(config_dir / "meta-data", temp_dir / "meta-data")
            
            iso_base = iso_path.with_suffix("")
            result = subprocess.run(
                [
                    "/usr/bin/hdiutil", "makehybrid",
                    "-o", str(iso_base),
                    "-hfs", "-joliet", "-iso",
                    "-default-volume-name", "cidata",
                    str(temp_dir),
                ],
                capture_output=True,
                text=True,
            )
            
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"hdiutil failed: {result.stderr}")
            
            # hdiutil creates .iso
            created_iso = iso_base.with_suffix(".iso")
            if created_iso != iso_path and created_iso.exists():
                shutil.move(str(created_iso), str(iso_path))
    
    def _setup_uefi(self, vm_dir: Path, vars_path: Path):
        """Setup UEFI firmware for ARM64."""
        uefi_src = self._find_uefi_firmware()
        if not uefi_src:
            raise RuntimeError("UEFI firmware not found")
        
        # Copy firmware
        firmware_path = vm_dir / "QEMU_EFI.fd"
        if not firmware_path.exists():
            shutil.copy(uefi_src, firmware_path)
        
        # Create empty VARS file
        if not vars_path.exists():
            # Create 64MB empty file for UEFI vars
            with open(vars_path, "wb") as f:
                f.truncate(64 * 1024 * 1024)
    
    def _generate_user_data(
        self,
        ssh_pubkey: str,
        apt_mirror: str,
        ubuntu_codename: str,
        pip_mirror: str,
        pip_host: str,
        nodejs_setup_url: str,
        npm_registry: str,
        playwright_mirror: str,
    ) -> str:
        """Generate cloud-init user-data."""
        return f'''#cloud-config

# =====================================================
# NovAIC VM - Ubuntu Cloud-Init Configuration
# =====================================================

# bootcmd 在每次启动时最早执行，用于设置 TTY1 自动登录
# 这样用户可以在 cloud-init 运行期间看到日志
bootcmd:
  - mkdir -p /etc/systemd/system/getty@tty1.service.d
  - |
    cat > /etc/systemd/system/getty@tty1.service.d/override.conf << 'EOFGETTY'
    [Service]
    ExecStart=
    ExecStart=-/sbin/agetty --autologin ubuntu --noclear %I $TERM
    EOFGETTY
  - systemctl daemon-reload
  # 后台等待 ubuntu 用户创建后再重启 getty
  - |
    (while ! id ubuntu >/dev/null 2>&1; do sleep 1; done; sleep 2; systemctl restart getty@tty1.service) &

# User configuration
users:
  - name: ubuntu
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    lock_passwd: false
    groups: [adm, audio, cdrom, dialout, dip, floppy, lxd, netdev, plugdev, sudo, video]
    ssh_authorized_keys:
      - {ssh_pubkey}

# Set password
chpasswd:
  list: |
    ubuntu:ubuntu
  expire: false

# SSH configuration
ssh_pwauth: true

# APT source configuration
apt:
  primary:
    - arches: [default]
      uri: http://{apt_mirror}
  sources_list: |
    deb http://{apt_mirror} {ubuntu_codename} main restricted universe multiverse
    deb http://{apt_mirror} {ubuntu_codename}-updates main restricted universe multiverse
    deb http://{apt_mirror} {ubuntu_codename}-backports main restricted universe multiverse
    deb http://{apt_mirror} {ubuntu_codename}-security main restricted universe multiverse

# Package update
package_update: true
package_upgrade: false

# Install packages
packages:
  # X Server 核心（QEMU native VNC 必需）
  - xserver-xorg
  - xserver-xorg-core
  - xserver-xorg-input-all
  - xserver-xorg-video-dummy
  - x11-utils
  - x11-xserver-utils
  # 桌面环境
  - xfce4
  - xfce4-terminal
  - xfce4-goodies
  - lightdm
  - lightdm-gtk-greeter
  - dbus-x11
  # 浏览器和工具
  - chromium-browser
  - xdotool
  - wmctrl
  - scrot
  - imagemagick
  - xclip
  # Python 环境
  - python3
  - python3-pip
  - python3-venv
  # 系统工具
  - curl
  - wget
  - net-tools
  - openssh-server
  - git
  - vim
  - htop
  - qemu-guest-agent

# Write configuration files
write_files:
  # X Server 配置（使用 modesetting 驱动连接到 virtio-gpu）
  - path: /etc/X11/xorg.conf.d/10-novaic.conf
    content: |
      Section "Device"
        Identifier "VirtioGPU"
        Driver "modesetting"
        Option "AccelMethod" "glamor"
      EndSection
      Section "Screen"
        Identifier "DefaultScreen"
        Device "VirtioGPU"
        DefaultDepth 24
        SubSection "Display"
          Depth 24
          Modes "1280x720" "1024x768"
        EndSubSection
      EndSection
    permissions: '0644'
  
  # LightDM 自动登录配置
  - path: /etc/lightdm/lightdm.conf.d/50-autologin.conf
    content: |
      [Seat:*]
      autologin-user=ubuntu
      autologin-user-timeout=0
      autologin-session=xfce

  # 自动登录后显示 cloud-init 日志的脚本
  # 注意：不设置 owner，因为 write_files 在 users 创建之前执行
  # 所有权会在 runcmd 中设置
  - path: /home/ubuntu/.bash_profile
    content: |
      # NovAIC: 首次启动时自动显示 cloud-init 日志
      if [ -f /var/log/cloud-init-output.log ] && [ ! -f /var/log/novaic-init-done.log ]; then
        echo ""
        echo "=========================================="
        echo "  NovAIC VM 正在初始化..."
        echo "  Cloud-init 日志实时输出"
        echo "=========================================="
        echo ""
        tail -f /var/log/cloud-init-output.log &
        TAIL_PID=$!
        # 等待初始化完成
        while [ ! -f /var/log/novaic-init-done.log ]; do
          sleep 2
        done
        kill $TAIL_PID 2>/dev/null
        echo ""
        echo "=========================================="
        echo "  初始化完成！正在启动桌面环境..."
        echo "=========================================="
        sleep 2
      fi
    permissions: '0644'

  - path: /home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-power-manager.xml
    content: |
      <?xml version="1.0" encoding="UTF-8"?>
      <channel name="xfce4-power-manager" version="1.0">
        <property name="xfce4-power-manager" type="empty">
          <property name="dpms-enabled" type="bool" value="false"/>
          <property name="blank-on-ac" type="int" value="0"/>
          <property name="dpms-on-ac-sleep" type="uint" value="0"/>
          <property name="dpms-on-ac-off" type="uint" value="0"/>
        </property>
      </channel>

  - path: /etc/systemd/system/novaic-vmuse.service
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

  - path: /opt/novaic/scripts/playwright_helper.py
    content: |
      #!/usr/bin/env python3
      """
      Playwright 辅助脚本 - 由 Guest Agent 调用
      支持基本的浏览器操作
      
      使用方法:
          playwright_helper.py <command> [<args_json>]
      
      命令:
          navigate <args>  - 导航到 URL
          click <args>     - 点击元素
          type <args>      - 输入文本
          screenshot       - 截图
          content          - 获取页面内容
      
      示例:
          playwright_helper.py navigate '{{"url": "https://example.com"}}'
          playwright_helper.py click '{{"selector": "button#submit"}}'
          playwright_helper.py type '{{"selector": "input#username", "text": "admin"}}'
          playwright_helper.py screenshot
          playwright_helper.py content
      """
      
      import sys
      import json
      import os
      from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
      
      # 默认超时时间（毫秒）
      DEFAULT_TIMEOUT = 30000
      
      
      def main():
          if len(sys.argv) < 2:
              print(json.dumps({{"status": "error", "error": "Missing command"}}))
              sys.exit(1)
          
          command = sys.argv[1]
          args = {{}}
          
          if len(sys.argv) > 2:
              try:
                  args = json.loads(sys.argv[2])
              except json.JSONDecodeError as e:
                  print(json.dumps({{"status": "error", "error": f"Invalid JSON arguments: {{e}}"}}))
                  sys.exit(1)
          
          try:
              with sync_playwright() as p:
                  # 启动浏览器（非 headless 模式，以便用户可以看到）
                  browser = p.chromium.launch(
                      headless=False,
                      args=['--no-sandbox', '--disable-setuid-sandbox']
                  )
                  
                  # 创建新的浏览器上下文和页面
                  context = browser.new_context(
                      viewport={{'width': 1280, 'height': 720}},
                      user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                  )
                  page = context.new_page()
                  
                  # 设置默认超时
                  page.set_default_timeout(DEFAULT_TIMEOUT)
                  
                  result = {{}}
                  
                  if command == "navigate":
                      url = args.get("url")
                      if not url:
                          result = {{"status": "error", "error": "Missing 'url' parameter"}}
                      else:
                          try:
                              response = page.goto(url, wait_until="domcontentloaded")
                              result = {{
                                  "status": "success",
                                  "url": page.url,
                                  "title": page.title()
                              }}
                              if response:
                                  result["status_code"] = response.status
                          except PlaywrightTimeoutError:
                              result = {{"status": "error", "error": f"Timeout navigating to {{url}}"}}
                          except Exception as e:
                              result = {{"status": "error", "error": f"Navigation failed: {{str(e)}}"}}
                  
                  elif command == "click":
                      selector = args.get("selector")
                      if not selector:
                          result = {{"status": "error", "error": "Missing 'selector' parameter"}}
                      else:
                          try:
                              page.click(selector)
                              result = {{"status": "success"}}
                          except PlaywrightTimeoutError:
                              result = {{"status": "error", "error": f"Element not found or not clickable: {{selector}}"}}
                          except Exception as e:
                              result = {{"status": "error", "error": f"Click failed: {{str(e)}}"}}
                  
                  elif command == "type":
                      selector = args.get("selector")
                      text = args.get("text")
                      if not selector:
                          result = {{"status": "error", "error": "Missing 'selector' parameter"}}
                      elif text is None:
                          result = {{"status": "error", "error": "Missing 'text' parameter"}}
                      else:
                          try:
                              page.fill(selector, text)
                              result = {{"status": "success"}}
                          except PlaywrightTimeoutError:
                              result = {{"status": "error", "error": f"Element not found: {{selector}}"}}
                          except Exception as e:
                              result = {{"status": "error", "error": f"Type failed: {{str(e)}}"}}
                  
                  elif command == "screenshot":
                      try:
                          screenshot_bytes = page.screenshot(full_page=False)
                          # 转换为 hex 字符串以便 JSON 序列化
                          result = {{
                              "status": "success",
                              "data": screenshot_bytes.hex()
                          }}
                      except Exception as e:
                          result = {{"status": "error", "error": f"Screenshot failed: {{str(e)}}"}}
                  
                  elif command == "content":
                      try:
                          html = page.content()
                          result = {{
                              "status": "success",
                              "html": html,
                              "url": page.url,
                              "title": page.title()
                          }}
                      except Exception as e:
                          result = {{"status": "error", "error": f"Get content failed: {{str(e)}}"}}
                  
                  else:
                      result = {{"status": "error", "error": f"Unknown command: {{command}}"}}
                  
                  # 关闭浏览器
                  browser.close()
                  
                  # 输出结果
                  print(json.dumps(result))
          
          except Exception as e:
              print(json.dumps({{"status": "error", "error": f"Playwright error: {{str(e)}}"}}))
              sys.exit(1)
      
      
      if __name__ == "__main__":
          main()
    permissions: '0755'

# Startup commands
runcmd:
  # ========== Phase 1: Directory Setup ==========
  - echo "=== Phase 1 - Directory Setup ==="
  - mkdir -p /home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml
  - mkdir -p /opt/novaic/scripts
  - mkdir -p /opt/novaic/venv
  - mkdir -p /opt/novaic/novaic-mcp-vmuse/src/novaic_mcp_vmuse
  - mkdir -p /opt/novaic/.cache
  # 挂载 9p 共享目录（Host /tmp/novaic/share-<agent_id> → VM /mnt/novaic-share）
  - mkdir -p /mnt/novaic-share
  - modprobe 9pnet_virtio || true
  - mount -t 9p -o trans=virtio,version=9p2000.L novaic_share /mnt/novaic-share || echo "WARNING - 9p mount failed, continuing without share"
  - echo 'novaic_share /mnt/novaic-share 9p trans=virtio,version=9p2000.L,_netdev,nofail 0 0' >> /etc/fstab
  # 修复 write_files 创建的文件所有权（因为 write_files 在用户创建之前执行）
  - chown -R ubuntu:ubuntu /home/ubuntu
  
  # ========== Phase 2: Network & Environment ==========
  - echo "=== Phase 2 - Network & Environment ==="
  - until ping -c 1 -W 3 8.8.8.8 > /dev/null 2>&1; do sleep 2; done
  - echo "Network ready."
  - echo 'DISPLAY=:0' | sudo tee -a /etc/environment
  - echo 'export PATH="/opt/novaic/venv/bin:$PATH"' | sudo tee /etc/profile.d/novaic.sh
  
  # ========== Phase 3: Node.js Installation ==========
  - echo "=== Phase 3 - Installing Node.js 20 LTS ==="
  - curl -fsSL {nodejs_setup_url} | sudo -E bash -
  - apt-get install -y nodejs
  - node --version | tee /opt/novaic/.node_version
  - npm --version | tee /opt/novaic/.npm_version
  # Configure npm registry
  - npm config set registry {npm_registry}
  - echo "Node.js installed with registry {npm_registry}"
  
  # ========== Phase 4: Python Virtual Environment ==========
  - echo "=== Phase 4 - Python Virtual Environment ==="
  - python3 -m venv /opt/novaic/venv
  - /opt/novaic/venv/bin/pip install --upgrade pip --index-url https://{pip_mirror} --trusted-host {pip_host}
  
  # ========== Phase 5: VMUSE Python Dependencies ==========
  - echo "=== Phase 5 - VMUSE Python Dependencies ==="
  - /opt/novaic/venv/bin/pip install aiohttp pydantic pydantic-settings python-dotenv Pillow playwright --index-url https://{pip_mirror} --trusted-host {pip_host}
  - echo "VMUSE dependencies installed."
  
  # ========== Phase 6: Playwright + Chromium ==========
  - echo "=== Phase 6 - Playwright Chromium ==="
  # Install Playwright with mirror fallback
  - |
    install_playwright() {{
      if [ -n "{playwright_mirror}" ]; then
        echo "Trying Playwright mirror: {playwright_mirror}"
        export PLAYWRIGHT_DOWNLOAD_HOST="{playwright_mirror}"
        if /opt/novaic/venv/bin/playwright install --with-deps chromium 2>&1; then
          echo "Playwright installed from mirror"
          return 0
        else
          echo "Mirror failed, trying official source..."
          unset PLAYWRIGHT_DOWNLOAD_HOST
        fi
      fi
      # Fallback to official source
      echo "Installing Playwright from official source..."
      /opt/novaic/venv/bin/playwright install --with-deps chromium
    }}
    install_playwright
  - echo "Playwright Chromium installed."
  
  # ========== Phase 7: QEMU Guest Agent ==========
  - echo "=== Phase 7 - QEMU Guest Agent ==="
  - systemctl daemon-reload
  - systemctl enable qemu-guest-agent
  - systemctl start qemu-guest-agent
  
  # ========== Phase 8: Ownership ==========
  - echo "=== Phase 8 - Setting ownership ==="
  - chown -R ubuntu:ubuntu /home/ubuntu
  - chown -R ubuntu:ubuntu /opt/novaic
  
  # ========== Phase 9: Display Manager ==========
  - echo "=== Phase 9 - Display Manager ==="
  # 确保 /tmp/.X11-unix 目录存在并设置正确权限
  - mkdir -p /tmp/.X11-unix
  - chmod 1777 /tmp/.X11-unix
  - chown root:root /tmp/.X11-unix
  # 启用并启动 lightdm
  - systemctl enable lightdm
  - systemctl start lightdm
  - sleep 15
  # 验证 X server 是否运行
  - echo "Verifying X server..."
  - pgrep -x Xorg || (echo "ERROR - X server not running" && exit 1)
  # 验证 DISPLAY 是否可用
  - DISPLAY=:0 xdpyinfo > /dev/null 2>&1 || (echo "ERROR - DISPLAY not available" && exit 1)
  # 验证 lightdm 状态
  - systemctl is-active lightdm || (echo "ERROR - lightdm not active" && exit 1)
  # 验证桌面会话是否运行
  - echo "Verifying desktop session..."
  - pgrep -u ubuntu xfce4-session && echo "Desktop session is running" || echo "WARNING - Desktop session not detected yet, but lightdm will auto-start it on first login"
  
  # ========== Phase 10: Enable VMUSE Service ==========
  - echo "=== Phase 10 - VMUSE Service ==="
  - systemctl daemon-reload
  - systemctl enable novaic-vmuse
  - echo "VMUSE service enabled (will start after code deployment)."
  
  # ========== Phase 11: Completion ==========
  - touch /opt/novaic/.dependencies_installed
  - touch /opt/novaic/.cloud_init_complete
  - echo "NovAIC VM cloud-init completed at $(date)" | tee /var/log/novaic-init-done.log
  - echo "=== Cloud-Init Complete ==="

final_message: |
  =====================================================
  NovAIC VM configuration complete!
  =====================================================
  
  VM internal ports (mapped to dynamic host ports via QEMU):
  - SSH: 22
  
  Check NovAIC app for actual host port mappings.
'''
