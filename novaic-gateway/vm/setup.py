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
        self.data_dir = Path(data_dir or os.environ.get("NOVAIC_DATA_DIR", "/tmp/novaic"))
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
        paths = [
            "/opt/homebrew/share/qemu/edk2-aarch64-code.fd",
            "/usr/local/share/qemu/edk2-aarch64-code.fd",
            "/usr/share/qemu/edk2-aarch64-code.fd",
        ]
        
        for path in paths:
            if Path(path).exists():
                return path
        
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
        except Exception:
            pass
        return None
    
    # ==================== VM Setup ====================
    
    async def setup_vm(
        self,
        agent_id: str,
        source_image: str,
        disk_size: str = "40G",
        use_cn_mirrors: bool = False,
        on_progress: Optional[Callable[[SetupProgress], None]] = None,
    ) -> Dict[str, Any]:
        """
        Setup VM for an agent.
        
        Args:
            agent_id: Agent ID
            source_image: Path to source cloud image
            disk_size: Disk size (e.g., "40G")
            use_cn_mirrors: Use Chinese mirrors for apt/pip
            on_progress: Progress callback
        
        Returns:
            Dict with paths to created files.
        """
        vm_dir = self.get_vm_dir(agent_id)
        
        # Get SSH public key
        ssh_manager = get_ssh_key_manager()
        ssh_pubkey = await ssh_manager.get_public_key()
        
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
        
        # APT mirror
        if use_cn_mirrors:
            apt_mirror = "mirrors.aliyun.com/ubuntu-ports" if self.is_arm else "mirrors.aliyun.com/ubuntu"
            pip_mirror = "mirrors.aliyun.com/pypi/simple/"
            pip_host = "mirrors.aliyun.com"
        else:
            apt_mirror = "ports.ubuntu.com/ubuntu-ports" if self.is_arm else "archive.ubuntu.com/ubuntu"
            pip_mirror = "pypi.org/simple/"
            pip_host = "pypi.org"
        
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
    ) -> str:
        """Generate cloud-init user-data."""
        return f'''#cloud-config

# =====================================================
# NovAIC VM - Ubuntu Cloud-Init Configuration
# =====================================================

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
  - xfce4
  - xfce4-terminal
  - xfce4-goodies
  - lightdm
  - lightdm-gtk-greeter
  - dbus-x11
  - x11vnc
  - xvfb
  - python3-websockify
  - chromium-browser
  - xdotool
  - wmctrl
  - scrot
  - imagemagick
  - python3
  - python3-pip
  - python3-venv
  - curl
  - wget
  - net-tools
  - openssh-server
  - git
  - vim
  - htop

# Write configuration files
write_files:
  - path: /etc/lightdm/lightdm.conf.d/50-autologin.conf
    content: |
      [Seat:*]
      autologin-user=ubuntu
      autologin-user-timeout=0
      user-session=xfce

  - path: /etc/systemd/system/x11vnc.service
    content: |
      [Unit]
      Description=x11vnc VNC Server
      After=display-manager.service
      Requires=display-manager.service

      [Service]
      Type=simple
      User=ubuntu
      Environment=DISPLAY=:0
      ExecStartPre=/bin/sleep 5
      ExecStart=/usr/bin/x11vnc -display :0 -auth guess -forever -loop -noxdamage -repeat -rfbport 5900 -shared -nopw
      Restart=always
      RestartSec=3

      [Install]
      WantedBy=multi-user.target

  - path: /etc/systemd/system/websockify.service
    content: |
      [Unit]
      Description=Websockify VNC WebSocket Proxy
      After=x11vnc.service
      Requires=x11vnc.service

      [Service]
      Type=simple
      User=ubuntu
      ExecStart=/usr/bin/websockify 6080 localhost:5900
      Restart=always
      RestartSec=3

      [Install]
      WantedBy=multi-user.target

  - path: /etc/systemd/system/novaic.service
    content: |
      [Unit]
      Description=NovAIC Core - MCP Server (FastMCP)
      After=network.target display-manager.service x11vnc.service
      Wants=display-manager.service

      [Service]
      Type=simple
      User=ubuntu
      Environment=DISPLAY=:0
      Environment=XAUTHORITY=/home/ubuntu/.Xauthority
      Environment=HOME=/home/ubuntu
      Environment=PATH=/opt/novaic-venv/bin:/usr/local/bin:/usr/bin:/bin
      Environment=PYTHONPATH=/opt/novaic-mcp-vmuse/src
      Environment=NOVAIC_HOST=0.0.0.0
      Environment=NOVAIC_PORT=8080
      WorkingDirectory=/opt/novaic-mcp-vmuse
      ExecStart=/opt/novaic-venv/bin/python -c "from novaic_mcp_vmuse.main import mcp; mcp.run(transport='streamable-http', host='0.0.0.0', port=8080)"
      Restart=always
      RestartSec=3

      [Install]
      WantedBy=multi-user.target

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

# Startup commands
runcmd:
  - chown -R ubuntu:ubuntu /home/ubuntu
  - mkdir -p /home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml
  - chown -R ubuntu:ubuntu /home/ubuntu/.config
  - echo "Waiting for network..."
  - until ping -c 1 -W 3 8.8.8.8 > /dev/null 2>&1; do sleep 2; done
  - echo "Network ready."
  - mkdir -p /opt/novaic-mcp-vmuse /opt/novaic-venv
  - chown -R ubuntu:ubuntu /opt/novaic-mcp-vmuse /opt/novaic-venv
  - echo "Creating Python virtual environment..."
  - sudo -u ubuntu python3 -m venv /opt/novaic-venv
  - echo "Installing Python dependencies..."
  - sudo -u ubuntu /opt/novaic-venv/bin/pip install --upgrade pip -q -i "http://{pip_mirror}" --trusted-host "{pip_host}"
  - sudo -u ubuntu /opt/novaic-venv/bin/pip install -q -i "http://{pip_mirror}" --trusted-host "{pip_host}" fastmcp fastapi "uvicorn[standard]" pydantic pydantic-settings playwright httpx python-dotenv Pillow
  - echo "Installing Playwright Chromium..."
  - sudo -u ubuntu /opt/novaic-venv/bin/playwright install chromium
  - /opt/novaic-venv/bin/playwright install-deps chromium || true
  - systemctl daemon-reload
  - systemctl enable lightdm
  - systemctl enable x11vnc
  - systemctl enable websockify
  - systemctl enable novaic
  - systemctl start lightdm
  - sleep 10
  - systemctl start x11vnc
  - sleep 2
  - systemctl start websockify
  - echo "NovAIC VM cloud-init completed at $(date)" > /var/log/novaic-init-done.log

final_message: |
  =====================================================
  NovAIC VM configuration complete!
  =====================================================
  
  VM internal ports (mapped to dynamic host ports via QEMU):
  - VNC: 5900 (no password)
  - WebSocket: 6080
  - MCP: 8080
  - SSH: 22
  
  Check NovAIC app for actual host port mappings.
  Please run deploy to install MCP Server.
'''
