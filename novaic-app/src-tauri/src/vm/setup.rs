//! VM Setup Module
//! 
//! Handles VM creation including:
//! - Cloud image download
//! - VM disk creation (qcow2)
//! - Cloud-init ISO generation
//! - UEFI firmware setup (ARM64)

use std::path::PathBuf;
use std::process::Command;
use serde::{Deserialize, Serialize};
use tauri::Manager;
use tokio::io::AsyncWriteExt;

/// Download progress information
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DownloadProgress {
    pub downloaded: u64,
    pub total: u64,
    pub percent: f32,
    pub speed: String,  // e.g., "1.5 MB/s"
}

/// Image check result
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ImageCheckResult {
    pub exists: bool,
    pub path: Option<String>,
    pub size: Option<u64>,
}

/// VM setup result
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct VmSetupResult {
    pub disk_path: String,
    pub seed_iso_path: String,
    pub uefi_vars_path: Option<String>,
}

/// Setup progress information
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SetupProgress {
    pub stage: String,
    pub progress: u32,
    pub message: String,
}

/// Get cloud image download URL
/// Note: Always use official Ubuntu source as Chinese mirrors may have different structure or be unavailable
fn get_cloud_image_url(os_type: &str, os_version: &str, arch: &str, _use_cn_mirrors: bool) -> Result<String, String> {
    match os_type {
        "ubuntu" => {
            let codename = match os_version {
                "24.04" => "noble",
                "22.04" => "jammy",
                "20.04" => "focal",
                _ => return Err(format!("Unsupported Ubuntu version: {}", os_version)),
            };
            
            let arch_suffix = match arch {
                "arm64" | "aarch64" => "arm64",
                "amd64" | "x86_64" => "amd64",
                _ => return Err(format!("Unsupported architecture: {}", arch)),
            };
            
            // Use official Ubuntu cloud images (mirrors often have issues)
            Ok(format!(
                "https://cloud-images.ubuntu.com/{}/current/{}-server-cloudimg-{}.img",
                codename, codename, arch_suffix
            ))
        }
        "debian" => {
            let version_name = match os_version {
                "12" => "bookworm",
                "11" => "bullseye",
                _ => return Err(format!("Unsupported Debian version: {}", os_version)),
            };
            
            let arch_suffix = match arch {
                "arm64" | "aarch64" => "arm64",
                "amd64" | "x86_64" => "amd64",
                _ => return Err(format!("Unsupported architecture: {}", arch)),
            };
            
            Ok(format!(
                "https://cloud.debian.org/images/cloud/{}/latest/debian-{}-generic-{}.qcow2",
                version_name, version_name, arch_suffix
            ))
        }
        _ => Err(format!("Unsupported OS type: {}", os_type)),
    }
}

/// Get current architecture
fn get_current_arch() -> &'static str {
    #[cfg(target_arch = "aarch64")]
    {
        "arm64"
    }
    #[cfg(target_arch = "x86_64")]
    {
        "amd64"
    }
    #[cfg(not(any(target_arch = "aarch64", target_arch = "x86_64")))]
    {
        "unknown"
    }
}

/// Check if cloud image exists locally
#[tauri::command]
pub async fn check_cloud_image(
    app: tauri::AppHandle,
    os_type: String,
    os_version: String,
) -> Result<ImageCheckResult, String> {
    let data_dir = app.path().app_data_dir()
        .map_err(|e| format!("Failed to get app data dir: {}", e))?;
    
    let images_dir = data_dir.join("images");
    let arch = get_current_arch();
    let image_name = format!("{}-{}-{}.img", os_type, os_version, arch);
    let image_path = images_dir.join(&image_name);
    
    if image_path.exists() {
        let metadata = std::fs::metadata(&image_path)
            .map_err(|e| format!("Failed to get file metadata: {}", e))?;
        
        Ok(ImageCheckResult {
            exists: true,
            path: Some(image_path.to_string_lossy().to_string()),
            size: Some(metadata.len()),
        })
    } else {
        Ok(ImageCheckResult {
            exists: false,
            path: None,
            size: None,
        })
    }
}

/// Download cloud image with progress reporting
#[tauri::command]
pub async fn download_cloud_image(
    app: tauri::AppHandle,
    os_type: String,
    os_version: String,
    use_cn_mirrors: bool,
    on_progress: tauri::ipc::Channel<DownloadProgress>,
) -> Result<String, String> {
    let data_dir = app.path().app_data_dir()
        .map_err(|e| format!("Failed to get app data dir: {}", e))?;
    
    let images_dir = data_dir.join("images");
    
    // Ensure images directory exists
    std::fs::create_dir_all(&images_dir)
        .map_err(|e| format!("Failed to create images directory: {}", e))?;
    
    let arch = get_current_arch();
    let image_name = format!("{}-{}-{}.img", os_type, os_version, arch);
    let image_path = images_dir.join(&image_name);
    let temp_path = images_dir.join(format!("{}.downloading", image_name));
    
    // Get download URL
    let url = get_cloud_image_url(&os_type, &os_version, arch, use_cn_mirrors)?;
    println!("[Setup] Downloading cloud image from: {}", url);
    
    // Create HTTP client with User-Agent (some servers reject requests without UA)
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(3600))  // 1 hour timeout for large files
        .user_agent("NovAIC/0.3.0 (https://github.com/chriswangcq/novaic)")
        .build()
        .map_err(|e| format!("Failed to create HTTP client: {}", e))?;
    
    // Start download
    let response = client.get(&url)
        .header("Accept", "*/*")
        .send().await
        .map_err(|e| format!("Failed to start download: {}", e))?;
    
    if !response.status().is_success() {
        return Err(format!("Download failed with status: {}", response.status()));
    }
    
    let total_size = response.content_length().unwrap_or(0);
    println!("[Setup] Total size: {} bytes", total_size);
    
    // Create temp file
    let mut file: tokio::fs::File = tokio::fs::File::create(&temp_path).await
        .map_err(|e| format!("Failed to create temp file: {}", e))?;
    
    // Download with progress
    let mut downloaded: u64 = 0;
    let mut last_progress_time = std::time::Instant::now();
    let mut last_downloaded: u64 = 0;
    let mut stream = response.bytes_stream();
    
    use futures_util::StreamExt;
    
    while let Some(chunk) = stream.next().await {
        let chunk = chunk.map_err(|e| format!("Download error: {}", e))?;
        file.write_all(&chunk).await
            .map_err(|e| format!("Failed to write chunk: {}", e))?;
        
        downloaded += chunk.len() as u64;
        
        // Report progress every 100ms
        let now = std::time::Instant::now();
        if now.duration_since(last_progress_time).as_millis() >= 100 {
            let elapsed = now.duration_since(last_progress_time).as_secs_f64();
            let bytes_per_sec = if elapsed > 0.0 {
                ((downloaded - last_downloaded) as f64 / elapsed) as u64
            } else {
                0
            };
            
            let speed = if bytes_per_sec >= 1_000_000 {
                format!("{:.1} MB/s", bytes_per_sec as f64 / 1_000_000.0)
            } else if bytes_per_sec >= 1_000 {
                format!("{:.1} KB/s", bytes_per_sec as f64 / 1_000.0)
            } else {
                format!("{} B/s", bytes_per_sec)
            };
            
            let percent = if total_size > 0 {
                (downloaded as f32 / total_size as f32) * 100.0
            } else {
                0.0
            };
            
            let _ = on_progress.send(DownloadProgress {
                downloaded,
                total: total_size,
                percent,
                speed,
            });
            
            last_progress_time = now;
            last_downloaded = downloaded;
        }
    }
    
    // Flush and close file
    file.flush().await
        .map_err(|e| format!("Failed to flush file: {}", e))?;
    drop(file);
    
    // Rename temp file to final name
    std::fs::rename(&temp_path, &image_path)
        .map_err(|e| format!("Failed to rename temp file: {}", e))?;
    
    println!("[Setup] Download complete: {}", image_path.display());
    
    // Send final progress
    let _ = on_progress.send(DownloadProgress {
        downloaded: total_size,
        total: total_size,
        percent: 100.0,
        speed: "Complete".to_string(),
    });
    
    Ok(image_path.to_string_lossy().to_string())
}

/// Create VM disk from cloud image
#[tauri::command]
pub async fn setup_vm(
    app: tauri::AppHandle,
    agent_id: String,
    source_image: String,
    disk_size: String,
    ssh_pubkey: String,
    use_cn_mirrors: bool,
    on_progress: tauri::ipc::Channel<SetupProgress>,
) -> Result<VmSetupResult, String> {
    let data_dir = app.path().app_data_dir()
        .map_err(|e| format!("Failed to get app data dir: {}", e))?;
    
    let vm_dir = data_dir.join("vms").join(&agent_id);
    
    // Create VM directory
    std::fs::create_dir_all(&vm_dir)
        .map_err(|e| format!("Failed to create VM directory: {}", e))?;
    
    let _ = on_progress.send(SetupProgress {
        stage: "Creating VM disk".to_string(),
        progress: 10,
        message: "Converting cloud image...".to_string(),
    });
    
    // Create disk
    let disk_path = vm_dir.join("disk.qcow2");
    create_vm_disk(&source_image, &disk_path, &disk_size)?;
    
    let _ = on_progress.send(SetupProgress {
        stage: "Creating cloud-init".to_string(),
        progress: 40,
        message: "Generating cloud-init configuration...".to_string(),
    });
    
    // Create cloud-init ISO
    let seed_iso_path = vm_dir.join("cloud-init-seed.iso");
    create_cloud_init(&vm_dir, &seed_iso_path, &ssh_pubkey, use_cn_mirrors)?;
    
    // Setup UEFI firmware for ARM64
    let uefi_vars_path = if cfg!(target_arch = "aarch64") {
        let _ = on_progress.send(SetupProgress {
            stage: "Setting up UEFI".to_string(),
            progress: 70,
            message: "Configuring UEFI firmware...".to_string(),
        });
        
        let vars_path = vm_dir.join("QEMU_VARS.fd");
        setup_uefi_firmware(&vm_dir, &vars_path)?;
        Some(vars_path.to_string_lossy().to_string())
    } else {
        None
    };
    
    let _ = on_progress.send(SetupProgress {
        stage: "Complete".to_string(),
        progress: 100,
        message: "VM setup complete".to_string(),
    });
    
    Ok(VmSetupResult {
        disk_path: disk_path.to_string_lossy().to_string(),
        seed_iso_path: seed_iso_path.to_string_lossy().to_string(),
        uefi_vars_path,
    })
}

/// Create VM disk using qemu-img
fn create_vm_disk(source_image: &str, dest_path: &PathBuf, disk_size: &str) -> Result<(), String> {
    println!("[Setup] Creating VM disk from {} to {}", source_image, dest_path.display());
    
    // Convert image
    let output = Command::new("qemu-img")
        .args(["convert", "-f", "qcow2", "-O", "qcow2", source_image, dest_path.to_str().unwrap()])
        .output()
        .map_err(|e| format!("Failed to run qemu-img convert: {}", e))?;
    
    if !output.status.success() {
        return Err(format!(
            "qemu-img convert failed: {}",
            String::from_utf8_lossy(&output.stderr)
        ));
    }
    
    // Resize disk
    let output = Command::new("qemu-img")
        .args(["resize", dest_path.to_str().unwrap(), disk_size])
        .output()
        .map_err(|e| format!("Failed to run qemu-img resize: {}", e))?;
    
    if !output.status.success() {
        return Err(format!(
            "qemu-img resize failed: {}",
            String::from_utf8_lossy(&output.stderr)
        ));
    }
    
    println!("[Setup] VM disk created: {}", dest_path.display());
    Ok(())
}

/// Create cloud-init ISO
fn create_cloud_init(vm_dir: &PathBuf, iso_path: &PathBuf, ssh_pubkey: &str, use_cn_mirrors: bool) -> Result<(), String> {
    let config_dir = vm_dir.join("cloud-init");
    std::fs::create_dir_all(&config_dir)
        .map_err(|e| format!("Failed to create cloud-init config dir: {}", e))?;
    
    // Determine APT mirror based on architecture
    let apt_mirror = if use_cn_mirrors {
        if cfg!(target_arch = "aarch64") {
            "mirrors.aliyun.com/ubuntu-ports"
        } else {
            "mirrors.aliyun.com/ubuntu"
        }
    } else {
        if cfg!(target_arch = "aarch64") {
            "ports.ubuntu.com/ubuntu-ports"
        } else {
            "archive.ubuntu.com/ubuntu"
        }
    };
    
    // Ubuntu codename (default to noble for 24.04)
    let ubuntu_codename = "noble";
    
    // Create meta-data
    let meta_data = "instance-id: novaic-vm\nlocal-hostname: novaic-vm\n";
    let meta_data_path = config_dir.join("meta-data");
    std::fs::write(&meta_data_path, meta_data)
        .map_err(|e| format!("Failed to write meta-data: {}", e))?;
    
    // Create user-data
    let user_data = format!(r#"#cloud-config

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
  # Desktop environment (XFCE - lightweight)
  - xfce4
  - xfce4-terminal
  - xfce4-goodies
  - lightdm
  - lightdm-gtk-greeter
  - dbus-x11
  
  # VNC service
  - x11vnc
  - xvfb
  - python3-websockify
  
  # Browser
  - chromium-browser
  
  # Desktop automation tools
  - xdotool
  - wmctrl
  - scrot
  - imagemagick
  
  # Python
  - python3
  - python3-pip
  - python3-venv
  
  # Network tools
  - curl
  - wget
  - net-tools
  - openssh-server
  
  # Other
  - git
  - vim
  - htop

# Write configuration files
write_files:
  # LightDM auto-login
  - path: /etc/lightdm/lightdm.conf.d/50-autologin.conf
    content: |
      [Seat:*]
      autologin-user=ubuntu
      autologin-user-timeout=0
      user-session=xfce

  # x11vnc service (no password mode)
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

  # websockify service (noVNC WebSocket proxy)
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

  # NovAIC service (MCP Server)
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
      Environment=PYTHONPATH=/opt/novaic-vm-tools/src
      Environment=NOVAIC_HOST=0.0.0.0
      Environment=NOVAIC_PORT=8080
      WorkingDirectory=/opt/novaic-vm-tools
      ExecStart=/opt/novaic-venv/bin/python -c "from novaic_vm_tools.main import mcp; mcp.run(transport='streamable-http', host='0.0.0.0', port=8080)"
      Restart=always
      RestartSec=3

      [Install]
      WantedBy=multi-user.target

  # Disable screen saver
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
  # Fix /home/ubuntu directory permissions (important!)
  - chown -R ubuntu:ubuntu /home/ubuntu
  
  # Create xfce4 config directory
  - mkdir -p /home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml
  - chown -R ubuntu:ubuntu /home/ubuntu/.config
  
  # Wait for network
  - echo "Waiting for network..."
  - until ping -c 1 -W 3 8.8.8.8 > /dev/null 2>&1; do sleep 2; done
  - echo "Network ready."
  
  # Create novaic directory
  - mkdir -p /opt/novaic-vm-tools /opt/novaic-venv
  - chown -R ubuntu:ubuntu /opt/novaic-vm-tools /opt/novaic-venv
  
  # Enable services
  - systemctl daemon-reload
  - systemctl enable lightdm
  - systemctl enable x11vnc
  - systemctl enable websockify
  - systemctl enable novaic
  - systemctl start lightdm
  
  # Wait for desktop to start, then start VNC and websockify
  - sleep 10
  - systemctl start x11vnc
  - sleep 2
  - systemctl start websockify
  
  # Completion marker
  - echo "NovAIC VM cloud-init completed at $(date)" > /var/log/novaic-init-done.log

final_message: |
  =====================================================
  NovAIC VM configuration complete!
  =====================================================
  
  VNC: vnc://localhost:5900 (no password)
  WebSocket: ws://localhost:6080
  SSH: ssh -p 2222 ubuntu@localhost (password: ubuntu)
  
  Please run deploy to install MCP Server
"#, 
        ssh_pubkey = ssh_pubkey,
        apt_mirror = apt_mirror,
        ubuntu_codename = ubuntu_codename,
    );
    
    let user_data_path = config_dir.join("user-data");
    std::fs::write(&user_data_path, user_data)
        .map_err(|e| format!("Failed to write user-data: {}", e))?;
    
    // Create ISO using mkisofs or hdiutil
    let iso_created = if cfg!(target_os = "macos") {
        // Try mkisofs first, then hdiutil
        let mkisofs_result = Command::new("mkisofs")
            .args([
                "-output", iso_path.to_str().unwrap(),
                "-volid", "cidata",
                "-joliet",
                "-rock",
                user_data_path.to_str().unwrap(),
                meta_data_path.to_str().unwrap(),
            ])
            .output();
        
        match mkisofs_result {
            Ok(output) if output.status.success() => true,
            _ => {
                // Fallback to hdiutil
                let temp_dir = config_dir.join("iso-temp");
                std::fs::create_dir_all(&temp_dir)
                    .map_err(|e| format!("Failed to create temp dir: {}", e))?;
                
                std::fs::copy(&user_data_path, temp_dir.join("user-data"))
                    .map_err(|e| format!("Failed to copy user-data: {}", e))?;
                std::fs::copy(&meta_data_path, temp_dir.join("meta-data"))
                    .map_err(|e| format!("Failed to copy meta-data: {}", e))?;
                
                let iso_base = iso_path.with_extension("");
                let output = Command::new("hdiutil")
                    .args([
                        "makehybrid",
                        "-o", iso_base.to_str().unwrap(),
                        "-hfs",
                        "-joliet",
                        "-iso",
                        "-default-volume-name", "cidata",
                        temp_dir.to_str().unwrap(),
                    ])
                    .output()
                    .map_err(|e| format!("Failed to run hdiutil: {}", e))?;
                
                let _ = std::fs::remove_dir_all(&temp_dir);
                
                if output.status.success() {
                    // hdiutil creates .iso file, rename if needed
                    let created_iso = iso_base.with_extension("iso");
                    if created_iso != *iso_path && created_iso.exists() {
                        std::fs::rename(&created_iso, iso_path)
                            .map_err(|e| format!("Failed to rename ISO: {}", e))?;
                    }
                    true
                } else {
                    false
                }
            }
        }
    } else {
        // Linux: use mkisofs or genisoimage
        let output = Command::new("mkisofs")
            .args([
                "-output", iso_path.to_str().unwrap(),
                "-volid", "cidata",
                "-joliet",
                "-rock",
                user_data_path.to_str().unwrap(),
                meta_data_path.to_str().unwrap(),
            ])
            .output();
        
        match output {
            Ok(o) if o.status.success() => true,
            _ => {
                // Try genisoimage
                let output = Command::new("genisoimage")
                    .args([
                        "-output", iso_path.to_str().unwrap(),
                        "-volid", "cidata",
                        "-joliet",
                        "-rock",
                        user_data_path.to_str().unwrap(),
                        meta_data_path.to_str().unwrap(),
                    ])
                    .output()
                    .map_err(|e| format!("Failed to run genisoimage: {}", e))?;
                
                output.status.success()
            }
        }
    };
    
    if !iso_created {
        return Err("Failed to create cloud-init ISO. Make sure mkisofs, genisoimage, or hdiutil is installed.".to_string());
    }
    
    println!("[Setup] Cloud-init ISO created: {}", iso_path.display());
    Ok(())
}

/// Setup UEFI firmware for ARM64
fn setup_uefi_firmware(vm_dir: &PathBuf, vars_path: &PathBuf) -> Result<(), String> {
    // Check for UEFI firmware from Homebrew
    let homebrew_efi = PathBuf::from("/opt/homebrew/share/qemu/edk2-aarch64-code.fd");
    let firmware_path = vm_dir.join("QEMU_EFI.fd");
    
    if !firmware_path.exists() {
        if homebrew_efi.exists() {
            std::fs::copy(&homebrew_efi, &firmware_path)
                .map_err(|e| format!("Failed to copy UEFI firmware: {}", e))?;
            println!("[Setup] Copied UEFI firmware from Homebrew");
        } else {
            return Err("UEFI firmware not found. Please install QEMU via Homebrew.".to_string());
        }
    }
    
    // Create UEFI variables file (64MB)
    if !vars_path.exists() {
        let zeros = vec![0u8; 64 * 1024 * 1024];
        std::fs::write(vars_path, zeros)
            .map_err(|e| format!("Failed to create UEFI vars file: {}", e))?;
        println!("[Setup] Created UEFI vars file: {}", vars_path.display());
    }
    
    Ok(())
}

/// Get user's SSH public key
#[tauri::command]
pub async fn get_ssh_pubkey() -> Result<Option<String>, String> {
    let home = dirs::home_dir()
        .ok_or_else(|| "Failed to get home directory".to_string())?;
    
    let ssh_dir = home.join(".ssh");
    
    // Check for existing keys in order of preference
    for key_name in &["id_ed25519.pub", "id_rsa.pub", "id_ecdsa.pub"] {
        let key_path = ssh_dir.join(key_name);
        if key_path.exists() {
            let content = std::fs::read_to_string(&key_path)
                .map_err(|e| format!("Failed to read SSH key: {}", e))?;
            return Ok(Some(content.trim().to_string()));
        }
    }
    
    Ok(None)
}

/// Generate SSH key pair if not exists
#[tauri::command]
pub async fn generate_ssh_key() -> Result<String, String> {
    let home = dirs::home_dir()
        .ok_or_else(|| "Failed to get home directory".to_string())?;
    
    let ssh_dir = home.join(".ssh");
    std::fs::create_dir_all(&ssh_dir)
        .map_err(|e| format!("Failed to create .ssh directory: {}", e))?;
    
    let key_path = ssh_dir.join("id_ed25519_novaic");
    let pub_key_path = ssh_dir.join("id_ed25519_novaic.pub");
    
    if !key_path.exists() {
        // Generate new key
        let output = Command::new("ssh-keygen")
            .args([
                "-t", "ed25519",
                "-f", key_path.to_str().unwrap(),
                "-N", "",  // No passphrase
                "-C", &format!("novaic-vm-{}", chrono::Utc::now().format("%Y%m%d")),
            ])
            .output()
            .map_err(|e| format!("Failed to run ssh-keygen: {}", e))?;
        
        if !output.status.success() {
            return Err(format!(
                "ssh-keygen failed: {}",
                String::from_utf8_lossy(&output.stderr)
            ));
        }
    }
    
    // Read and return public key
    let pubkey = std::fs::read_to_string(&pub_key_path)
        .map_err(|e| format!("Failed to read public key: {}", e))?;
    
    Ok(pubkey.trim().to_string())
}
