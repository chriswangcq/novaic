//! VM Setup Module
//! 
//! Handles VM creation including:
//! - Environment detection (QEMU, etc.)
//! - Cloud image download
//! - VM disk creation (qcow2)
//! - Cloud-init ISO generation
//! - UEFI firmware setup (ARM64)

use std::path::PathBuf;
use std::process::Command;
use serde::{Deserialize, Serialize};
use tauri::Manager;
use tokio::io::AsyncWriteExt;

/// Environment check result for a single dependency
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DependencyStatus {
    pub name: String,
    pub installed: bool,
    pub version: Option<String>,
    pub path: Option<String>,
    pub install_command: Option<String>,
    pub install_url: Option<String>,
}

/// Full environment check result
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct EnvironmentCheckResult {
    pub ready: bool,
    pub platform: String,
    pub arch: String,
    pub dependencies: Vec<DependencyStatus>,
    pub message: Option<String>,
}

/// Find QEMU system binary path
fn find_qemu_system() -> Option<(String, String)> {
    let arch_suffix = if cfg!(target_arch = "aarch64") {
        "aarch64"
    } else {
        "x86_64"
    };
    
    let binary_name = format!("qemu-system-{}", arch_suffix);
    
    let paths = [
        format!("/opt/homebrew/bin/{}", binary_name),  // Apple Silicon homebrew
        format!("/usr/local/bin/{}", binary_name),      // Intel homebrew
        format!("/usr/bin/{}", binary_name),            // System
    ];
    
    for path in paths {
        if std::path::Path::new(&path).exists() {
            // Try to get version
            if let Ok(output) = Command::new(&path).arg("--version").output() {
                if output.status.success() {
                    let version = String::from_utf8_lossy(&output.stdout)
                        .lines()
                        .next()
                        .unwrap_or("")
                        .to_string();
                    return Some((path, version));
                }
            }
            return Some((path, String::new()));
        }
    }
    
    // Try PATH
    if let Ok(output) = Command::new(&binary_name).arg("--version").output() {
        if output.status.success() {
            let version = String::from_utf8_lossy(&output.stdout)
                .lines()
                .next()
                .unwrap_or("")
                .to_string();
            return Some((binary_name, version));
        }
    }
    
    None
}

/// Find qemu-img binary and get version
fn find_qemu_img_with_version() -> Option<(String, String)> {
    let paths = [
        "/opt/homebrew/bin/qemu-img",
        "/usr/local/bin/qemu-img",
        "/usr/bin/qemu-img",
    ];
    
    for path in paths {
        if std::path::Path::new(path).exists() {
            if let Ok(output) = Command::new(path).arg("--version").output() {
                if output.status.success() {
                    let version = String::from_utf8_lossy(&output.stdout)
                        .lines()
                        .next()
                        .unwrap_or("")
                        .to_string();
                    return Some((path.to_string(), version));
                }
            }
            return Some((path.to_string(), String::new()));
        }
    }
    
    // Try PATH
    if let Ok(output) = Command::new("qemu-img").arg("--version").output() {
        if output.status.success() {
            let version = String::from_utf8_lossy(&output.stdout)
                .lines()
                .next()
                .unwrap_or("")
                .to_string();
            return Some(("qemu-img".to_string(), version));
        }
    }
    
    None
}

/// Check if UEFI firmware is available (ARM64 only)
fn check_uefi_firmware() -> Option<String> {
    if !cfg!(target_arch = "aarch64") {
        return Some("Not required (x86_64)".to_string());
    }
    
    let paths = [
        "/opt/homebrew/share/qemu/edk2-aarch64-code.fd",
        "/usr/local/share/qemu/edk2-aarch64-code.fd",
        "/usr/share/qemu/edk2-aarch64-code.fd",
    ];
    
    for path in paths {
        if std::path::Path::new(path).exists() {
            return Some(path.to_string());
        }
    }
    
    None
}

/// Check if ISO creation tool is available
fn check_iso_tool() -> Option<(String, String)> {
    // Check mkisofs
    if let Ok(output) = Command::new("mkisofs").arg("--version").output() {
        // mkisofs may exit with error but still show version
        let out = String::from_utf8_lossy(&output.stdout);
        let err = String::from_utf8_lossy(&output.stderr);
        let version = if !out.is_empty() { out } else { err };
        let version_line = version.lines().next().unwrap_or("").to_string();
        
        // Check if mkisofs is actually available
        for path in ["/opt/homebrew/bin/mkisofs", "/usr/local/bin/mkisofs", "/usr/bin/mkisofs"] {
            if std::path::Path::new(path).exists() {
                return Some((path.to_string(), version_line));
            }
        }
        return Some(("mkisofs".to_string(), version_line));
    }
    
    // Check genisoimage (Linux alternative)
    if let Ok(output) = Command::new("genisoimage").arg("--version").output() {
        let version = String::from_utf8_lossy(&output.stdout)
            .lines()
            .next()
            .unwrap_or("")
            .to_string();
        return Some(("genisoimage".to_string(), version));
    }
    
    // On macOS, hdiutil is always available as fallback
    if cfg!(target_os = "macos") {
        return Some(("hdiutil".to_string(), "Built-in macOS tool".to_string()));
    }
    
    None
}

/// Check all environment dependencies
#[tauri::command]
pub async fn check_environment() -> Result<EnvironmentCheckResult, String> {
    let mut dependencies = Vec::new();
    let mut all_ready = true;
    
    let platform = if cfg!(target_os = "macos") {
        "macOS"
    } else if cfg!(target_os = "linux") {
        "Linux"
    } else if cfg!(target_os = "windows") {
        "Windows"
    } else {
        "Unknown"
    };
    
    let arch = if cfg!(target_arch = "aarch64") {
        "arm64"
    } else {
        "x86_64"
    };
    
    // 1. Check QEMU system
    let qemu_status = match find_qemu_system() {
        Some((path, version)) => DependencyStatus {
            name: format!("QEMU (qemu-system-{})", arch),
            installed: true,
            version: if version.is_empty() { None } else { Some(version) },
            path: Some(path),
            install_command: None,
            install_url: None,
        },
        None => {
            all_ready = false;
            DependencyStatus {
                name: format!("QEMU (qemu-system-{})", arch),
                installed: false,
                version: None,
                path: None,
                install_command: Some(if cfg!(target_os = "macos") {
                    "brew install qemu".to_string()
                } else {
                    "sudo apt install qemu-system".to_string()
                }),
                install_url: Some("https://www.qemu.org/download/".to_string()),
            }
        }
    };
    dependencies.push(qemu_status);
    
    // 2. Check qemu-img
    let qemu_img_status = match find_qemu_img_with_version() {
        Some((path, version)) => DependencyStatus {
            name: "qemu-img".to_string(),
            installed: true,
            version: if version.is_empty() { None } else { Some(version) },
            path: Some(path),
            install_command: None,
            install_url: None,
        },
        None => {
            all_ready = false;
            DependencyStatus {
                name: "qemu-img".to_string(),
                installed: false,
                version: None,
                path: None,
                install_command: Some(if cfg!(target_os = "macos") {
                    "brew install qemu".to_string()
                } else {
                    "sudo apt install qemu-utils".to_string()
                }),
                install_url: Some("https://www.qemu.org/download/".to_string()),
            }
        }
    };
    dependencies.push(qemu_img_status);
    
    // 3. Check UEFI firmware (ARM64 only)
    if cfg!(target_arch = "aarch64") {
        let uefi_status = match check_uefi_firmware() {
            Some(path) => DependencyStatus {
                name: "UEFI Firmware (EDK2)".to_string(),
                installed: true,
                version: None,
                path: Some(path),
                install_command: None,
                install_url: None,
            },
            None => {
                all_ready = false;
                DependencyStatus {
                    name: "UEFI Firmware (EDK2)".to_string(),
                    installed: false,
                    version: None,
                    path: None,
                    install_command: Some(if cfg!(target_os = "macos") {
                        "brew install qemu".to_string()
                    } else {
                        "sudo apt install qemu-efi-aarch64".to_string()
                    }),
                    install_url: Some("https://github.com/tianocore/edk2".to_string()),
                }
            }
        };
        dependencies.push(uefi_status);
    }
    
    // 4. Check ISO creation tool
    let iso_status = match check_iso_tool() {
        Some((path, version)) => DependencyStatus {
            name: "ISO Creation Tool".to_string(),
            installed: true,
            version: if version.is_empty() { None } else { Some(version) },
            path: Some(path),
            install_command: None,
            install_url: None,
        },
        None => {
            all_ready = false;
            DependencyStatus {
                name: "ISO Creation Tool".to_string(),
                installed: false,
                version: None,
                path: None,
                install_command: Some(if cfg!(target_os = "macos") {
                    "brew install cdrtools".to_string()
                } else {
                    "sudo apt install genisoimage".to_string()
                }),
                install_url: None,
            }
        }
    };
    dependencies.push(iso_status);
    
    let message = if all_ready {
        None
    } else {
        Some("Some dependencies are missing. Please install them before creating an agent.".to_string())
    };
    
    Ok(EnvironmentCheckResult {
        ready: all_ready,
        platform: platform.to_string(),
        arch: arch.to_string(),
        dependencies,
        message,
    })
}

/// Find qemu-img binary path
/// GUI apps on macOS don't inherit shell PATH, so we check common locations
fn find_qemu_img() -> String {
    let paths = [
        "/opt/homebrew/bin/qemu-img",  // Apple Silicon homebrew
        "/usr/local/bin/qemu-img",      // Intel homebrew
        "/usr/bin/qemu-img",            // System
    ];
    
    for path in paths {
        if std::path::Path::new(path).exists() {
            return path.to_string();
        }
    }
    
    // Fallback to PATH (may work in dev mode)
    "qemu-img".to_string()
}

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
    let data_dir = get_data_directory(&app)?;
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

/// Get or create a reliable data directory with multiple fallbacks
fn get_data_directory(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    // Try 1: Tauri's app_data_dir
    if let Ok(data_dir) = app.path().app_data_dir() {
        println!("[Setup] Trying Tauri app_data_dir: {}", data_dir.display());
        if let Ok(()) = std::fs::create_dir_all(&data_dir) {
            if data_dir.exists() {
                println!("[Setup] Using Tauri app_data_dir: {}", data_dir.display());
                return Ok(data_dir);
            }
        }
        println!("[Setup] Warning: Tauri app_data_dir not usable, trying fallback...");
    }
    
    // Try 2: Manual ~/Library/Application Support/com.novaic.app (macOS)
    // or ~/.local/share/com.novaic.app (Linux)
    if let Some(home) = dirs::home_dir() {
        let manual_path = if cfg!(target_os = "macos") {
            home.join("Library/Application Support/com.novaic.app")
        } else {
            home.join(".local/share/com.novaic.app")
        };
        
        println!("[Setup] Trying manual path: {}", manual_path.display());
        if let Ok(()) = std::fs::create_dir_all(&manual_path) {
            if manual_path.exists() {
                println!("[Setup] Using manual path: {}", manual_path.display());
                return Ok(manual_path);
            }
        }
        println!("[Setup] Warning: Manual path not usable, trying fallback...");
    }
    
    // Try 3: Fallback to home directory directly
    if let Some(home) = dirs::home_dir() {
        let fallback_path = home.join(".novaic");
        println!("[Setup] Trying home fallback: {}", fallback_path.display());
        if let Ok(()) = std::fs::create_dir_all(&fallback_path) {
            if fallback_path.exists() {
                println!("[Setup] Using home fallback: {}", fallback_path.display());
                return Ok(fallback_path);
            }
        }
    }
    
    // Try 4: Last resort - temp directory
    let temp_path = std::env::temp_dir().join("novaic-data");
    println!("[Setup] Trying temp fallback: {}", temp_path.display());
    std::fs::create_dir_all(&temp_path)
        .map_err(|e| format!("All directory options failed. Last error: {}", e))?;
    
    if temp_path.exists() {
        println!("[Setup] WARNING: Using temp directory (data may be lost on reboot): {}", temp_path.display());
        return Ok(temp_path);
    }
    
    Err("Failed to create any data directory. Check disk permissions.".to_string())
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
    // Get a reliable data directory with fallbacks
    let data_dir = get_data_directory(&app)?;
    let images_dir = data_dir.join("images");
    
    println!("[Setup] Data dir: {}", data_dir.display());
    println!("[Setup] Images dir: {}", images_dir.display());
    
    // Create images directory
    std::fs::create_dir_all(&images_dir)
        .map_err(|e| format!("Failed to create images directory {}: {} (check disk space and permissions)", images_dir.display(), e))?;
    
    // Double-check it exists
    if !images_dir.exists() {
        return Err(format!(
            "Images directory does not exist after creation attempt: {}. \
            This might be a permission issue or disk is full.",
            images_dir.display()
        ));
    }
    
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
    
    // Small delay to ensure file is fully written (especially on network drives or slow storage)
    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
    
    // Verify temp file exists and has content
    if !temp_path.exists() {
        return Err(format!("Temp file not found after download: {}", temp_path.display()));
    }
    
    let temp_size = std::fs::metadata(&temp_path)
        .map(|m| m.len())
        .unwrap_or(0);
    println!("[Setup] Temp file size: {} bytes", temp_size);
    
    if temp_size == 0 {
        return Err("Downloaded file is empty".to_string());
    }
    
    // Ensure target directory still exists (in case it was deleted during download)
    if let Some(parent) = image_path.parent() {
        if !parent.exists() {
            println!("[Setup] Re-creating target directory: {}", parent.display());
            std::fs::create_dir_all(parent)
                .map_err(|e| format!("Failed to create target directory {}: {}", parent.display(), e))?;
        }
    }
    
    // Rename temp file to final name
    println!("[Setup] Renaming {} -> {}", temp_path.display(), image_path.display());
    std::fs::rename(&temp_path, &image_path)
        .map_err(|e| format!("Failed to rename temp file: {} (from: {}, to: {})", e, temp_path.display(), image_path.display()))?;
    
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
    let data_dir = get_data_directory(&app)?;
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
    
    let qemu_img = find_qemu_img();
    println!("[Setup] Using qemu-img: {}", qemu_img);
    
    // Convert image
    let output = Command::new(&qemu_img)
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
    let output = Command::new(&qemu_img)
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
    
    // Determine pip mirror
    let (apt_mirror_pip, apt_mirror_pip_host) = if use_cn_mirrors {
        ("mirrors.aliyun.com/pypi/simple/", "mirrors.aliyun.com")
    } else {
        ("pypi.org/simple/", "pypi.org")
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
      Environment=PYTHONPATH=/opt/novaic-mcp-vmuse/src
      Environment=NOVAIC_HOST=0.0.0.0
      Environment=NOVAIC_PORT=8080
      WorkingDirectory=/opt/novaic-mcp-vmuse
      ExecStart=/opt/novaic-venv/bin/python -c "from novaic_mcp_vmuse.main import mcp; mcp.run(transport='streamable-http', host='0.0.0.0', port=8080)"
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
  - mkdir -p /opt/novaic-mcp-vmuse /opt/novaic-venv
  - chown -R ubuntu:ubuntu /opt/novaic-mcp-vmuse /opt/novaic-venv
  
  # =====================================================
  # Install Python dependencies (so deploy only copies code)
  # =====================================================
  - echo "Creating Python virtual environment..."
  - sudo -u ubuntu python3 -m venv /opt/novaic-venv
  
  - echo "Installing Python dependencies..."
  - sudo -u ubuntu /opt/novaic-venv/bin/pip install --upgrade pip -q -i "http://{apt_mirror_pip}" --trusted-host "{apt_mirror_pip_host}"
  - sudo -u ubuntu /opt/novaic-venv/bin/pip install -q -i "http://{apt_mirror_pip}" --trusted-host "{apt_mirror_pip_host}" fastmcp fastapi "uvicorn[standard]" pydantic pydantic-settings playwright httpx python-dotenv Pillow
  
  - echo "Installing Playwright Chromium..."
  - sudo -u ubuntu /opt/novaic-venv/bin/playwright install chromium
  - /opt/novaic-venv/bin/playwright install-deps chromium || true
  
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
  
  VM internal ports (mapped to dynamic host ports via QEMU):
  - VNC: 5900 (no password)
  - WebSocket: 6080
  - MCP: 8080
  - SSH: 22
  
  Check NovAIC app for actual host port mappings.
  Please run deploy to install MCP Server.
"#, 
        ssh_pubkey = ssh_pubkey,
        apt_mirror = apt_mirror,
        ubuntu_codename = ubuntu_codename,
        apt_mirror_pip = apt_mirror_pip,
        apt_mirror_pip_host = apt_mirror_pip_host,
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
