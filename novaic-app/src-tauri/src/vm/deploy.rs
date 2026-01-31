//! VM Deploy Module
//!
//! Handles deploying novaic-mcp-vmuse to the VM:
//! - Wait for SSH to be available
//! - Wait for cloud-init to complete
//! - Copy novaic-mcp-vmuse code to VM
//! - Install dependencies and start service

use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::fs;
use std::os::unix::fs::PermissionsExt;
use serde::{Deserialize, Serialize};
use tauri::Manager;

use crate::gateway_client::GatewayClient;

/// Deploy progress information
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DeployProgress {
    pub stage: String,
    pub progress: u32,
    pub message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub log_line: Option<String>,  // Real-time log line from cloud-init
}

/// SSH configuration
struct SshConfig {
    host: String,
    port: u16,
    user: String,
    key_path: Option<PathBuf>,  // Path to private key file
}

impl SshConfig {
    fn with_key(port: u16, key_path: PathBuf) -> Self {
        Self {
            host: "127.0.0.1".to_string(),
            port,
            user: "ubuntu".to_string(),
            key_path: Some(key_path),
        }
    }

    /// Get SSH command arguments
    fn ssh_args(&self) -> Vec<String> {
        let mut args = Vec::new();
        
        // Add private key if available
        if let Some(key) = &self.key_path {
            args.push("-i".to_string());
            args.push(key.to_string_lossy().to_string());
        }
        
        args.extend([
            "-o".to_string(), "StrictHostKeyChecking=no".to_string(),
            "-o".to_string(), "UserKnownHostsFile=/dev/null".to_string(),
            "-o".to_string(), "LogLevel=ERROR".to_string(),
            "-o".to_string(), "ConnectTimeout=10".to_string(),
            "-p".to_string(), self.port.to_string(),
            format!("{}@{}", self.user, self.host),
        ]);
        
        args
    }

    /// Get SCP command arguments for copying files
    fn scp_args(&self, src: &str, dest: &str) -> Vec<String> {
        let mut args = Vec::new();
        
        // Add private key if available
        if let Some(key) = &self.key_path {
            args.push("-i".to_string());
            args.push(key.to_string_lossy().to_string());
        }
        
        args.extend([
            "-o".to_string(), "StrictHostKeyChecking=no".to_string(),
            "-o".to_string(), "UserKnownHostsFile=/dev/null".to_string(),
            "-o".to_string(), "LogLevel=ERROR".to_string(),
            "-r".to_string(),
            "-P".to_string(), self.port.to_string(),
            src.to_string(),
            format!("{}@{}:{}", self.user, self.host, dest),
        ]);
        
        args
    }
}

/// Get SSH private key from Gateway and save to file
/// Returns the path to the private key file
async fn get_ssh_key_from_gateway(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    // Get app data directory
    let data_dir = app.path().app_data_dir()
        .map_err(|e| format!("Failed to get app data dir: {}", e))?;
    
    // Create ssh directory
    let ssh_dir = data_dir.join("ssh");
    fs::create_dir_all(&ssh_dir)
        .map_err(|e| format!("Failed to create ssh dir: {}", e))?;
    
    let key_path = ssh_dir.join("id_novaic");
    
    // Fetch private key from Gateway
    let client = GatewayClient::new("http://127.0.0.1:19999".to_string());
    let response = client.get("/api/vm/ssh/private-key").await?;
    
    let private_key = response
        .get("private_key")
        .and_then(|v| v.as_str())
        .ok_or("Invalid response: missing private_key")?;
    
    // Write private key to file
    fs::write(&key_path, private_key)
        .map_err(|e| format!("Failed to write private key: {}", e))?;
    
    // Set correct permissions (600)
    #[cfg(unix)]
    {
        let mut perms = fs::metadata(&key_path)
            .map_err(|e| format!("Failed to get key metadata: {}", e))?
            .permissions();
        perms.set_mode(0o600);
        fs::set_permissions(&key_path, perms)
            .map_err(|e| format!("Failed to set key permissions: {}", e))?;
    }
    
    println!("[Deploy] SSH key saved to {:?}", key_path);
    Ok(key_path)
}

/// Check if SSH is available
fn check_ssh(ssh_config: &SshConfig) -> bool {
    let mut args = ssh_config.ssh_args();
    args.push("echo connected".to_string());

    let output = Command::new("ssh")
        .args(&args)
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .output();

    match output {
        Ok(o) => o.status.success(),
        Err(_) => false,
    }
}

/// Wait for SSH to be available
async fn wait_for_ssh(ssh_config: &SshConfig, max_retries: u32, retry_interval_secs: u64) -> Result<(), String> {
    println!("[Deploy] Waiting for SSH connection...");

    for attempt in 1..=max_retries {
        if check_ssh(ssh_config) {
            println!("[Deploy] SSH connected after {} attempts", attempt);
            return Ok(());
        }

        if attempt < max_retries {
            println!("[Deploy] SSH not ready, retrying in {}s ({}/{})", retry_interval_secs, attempt, max_retries);
            tokio::time::sleep(tokio::time::Duration::from_secs(retry_interval_secs)).await;
        }
    }

    Err(format!("SSH connection failed after {} attempts", max_retries))
}

/// Check if cloud-init has completed
fn check_cloud_init_done(ssh_config: &SshConfig) -> bool {
    let mut args = ssh_config.ssh_args();
    args.push("test -f /var/log/novaic-init-done.log".to_string());

    let output = Command::new("ssh")
        .args(&args)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .output();

    match output {
        Ok(o) => o.status.success(),
        Err(_) => false,
    }
}

/// Wait for cloud-init to complete with real-time log streaming
async fn wait_for_cloud_init(
    ssh_config: &SshConfig,
    on_progress: &tauri::ipc::Channel<DeployProgress>,
) -> Result<(), String> {
    println!("[Deploy] Waiting for cloud-init to complete (this may take 10-30 minutes)...");

    let check_interval_secs = 5;
    let mut elapsed: u64 = 0;
    let mut last_line_count: usize = 0;

    loop {
        // Check if cloud-init is done
        if check_cloud_init_done(ssh_config) {
            println!("[Deploy] cloud-init completed after {}s", elapsed);
            let _ = on_progress.send(DeployProgress {
                stage: "Initializing".to_string(),
                progress: 20,
                message: format!("cloud-init completed after {}s", elapsed),
                log_line: None,
            });
            return Ok(());
        }

        // Try to get new log lines since last read
        if let Ok(new_lines) = get_cloud_init_new_lines(ssh_config, last_line_count) {
            let lines: Vec<&str> = new_lines.lines().collect();
            
            // Send new log lines to frontend
            for line in &lines {
                if !line.trim().is_empty() {
                    let _ = on_progress.send(DeployProgress {
                        stage: "Initializing".to_string(),
                        progress: 15,
                        message: format!("Installing packages... ({}min elapsed)", elapsed / 60),
                        log_line: Some(line.to_string()),
                    });
                }
            }
            
            // Update line count: get actual total from file
            if let Ok(total) = get_cloud_init_line_count(ssh_config) {
                last_line_count = total;
            }
        }

        tokio::time::sleep(tokio::time::Duration::from_secs(check_interval_secs)).await;
        elapsed += check_interval_secs;

        // Send progress update every minute
        if elapsed % 60 == 0 {
            println!("[Deploy] Still waiting for cloud-init... {}min elapsed", elapsed / 60);
            let _ = on_progress.send(DeployProgress {
                stage: "Initializing".to_string(),
                progress: 15,
                message: format!("Installing packages... ({}min elapsed)", elapsed / 60),
                log_line: None,
            });
        }
    }
}

/// Get total line count of cloud-init log
fn get_cloud_init_line_count(ssh_config: &SshConfig) -> Result<usize, String> {
    let mut args = ssh_config.ssh_args();
    args.push("wc -l < /var/log/cloud-init-output.log 2>/dev/null || echo 0".to_string());

    let output = Command::new("ssh")
        .args(&args)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("Failed to get line count: {}", e))?;

    let count_str = String::from_utf8_lossy(&output.stdout).trim().to_string();
    count_str.parse::<usize>().map_err(|_| "Invalid line count".to_string())
}

/// Get new lines from cloud-init log since last read
fn get_cloud_init_new_lines(ssh_config: &SshConfig, from_line: usize) -> Result<String, String> {
    let mut args = ssh_config.ssh_args();
    // Use sed to get lines from `from_line + 1` to end
    let cmd = if from_line > 0 {
        format!("sed -n '{},$p' /var/log/cloud-init-output.log 2>/dev/null", from_line + 1)
    } else {
        // First read: get last 30 lines to show some initial context
        "tail -n 30 /var/log/cloud-init-output.log 2>/dev/null".to_string()
    };
    args.push(cmd);

    let output = Command::new("ssh")
        .args(&args)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("Failed to get cloud-init logs: {}", e))?;

    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}

/// Run SSH command on VM
fn ssh_run(ssh_config: &SshConfig, command: &str) -> Result<String, String> {
    let mut args = ssh_config.ssh_args();
    args.push(command.to_string());

    let output = Command::new("ssh")
        .args(&args)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("Failed to run SSH command: {}", e))?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(format!(
            "SSH command failed: {}",
            String::from_utf8_lossy(&output.stderr)
        ))
    }
}

/// Copy directory to VM using SCP
fn scp_directory(ssh_config: &SshConfig, src: &PathBuf, dest: &str) -> Result<(), String> {
    println!("[Deploy] Copying {} to VM:{}", src.display(), dest);

    let args = ssh_config.scp_args(src.to_str().unwrap(), dest);

    let output = Command::new("scp")
        .args(&args)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("Failed to run SCP: {}", e))?;

    if output.status.success() {
        Ok(())
    } else {
        Err(format!(
            "SCP failed: {}",
            String::from_utf8_lossy(&output.stderr)
        ))
    }
}

/// Copy file to VM using SCP
fn scp_file(ssh_config: &SshConfig, src: &PathBuf, dest: &str) -> Result<(), String> {
    println!("[Deploy] Copying file {} to VM:{}", src.display(), dest);

    let mut args = Vec::new();
    
    // Add private key if available
    if let Some(key) = &ssh_config.key_path {
        args.push("-i".to_string());
        args.push(key.to_string_lossy().to_string());
    }
    
    args.extend([
        "-o".to_string(), "StrictHostKeyChecking=no".to_string(),
        "-o".to_string(), "UserKnownHostsFile=/dev/null".to_string(),
        "-o".to_string(), "LogLevel=ERROR".to_string(),
        "-P".to_string(), ssh_config.port.to_string(),
        src.to_str().unwrap().to_string(),
        format!("{}@{}:{}", ssh_config.user, ssh_config.host, dest),
    ]);

    let output = Command::new("scp")
        .args(&args)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("Failed to run SCP: {}", e))?;

    if output.status.success() {
        Ok(())
    } else {
        Err(format!(
            "SCP failed: {}",
            String::from_utf8_lossy(&output.stderr)
        ))
    }
}

/// Install dependencies and start service (check-style: skip if already installed)
fn install_and_start_service(ssh_config: &SshConfig, use_cn_mirrors: bool) -> Result<(), String> {
    // Configure pip source
    let (pip_index_url, pip_trusted_host) = if use_cn_mirrors {
        ("https://mirrors.aliyun.com/pypi/simple/", "mirrors.aliyun.com")
    } else {
        ("https://pypi.org/simple/", "pypi.org")
    };

    // Installation script with check-style install (cloud-init should have installed deps)
    let install_script = format!(r#"
set -e

# Check if venv exists (should be created by cloud-init)
if [ ! -f /opt/novaic-venv/bin/activate ]; then
    echo "Creating venv (cloud-init may have failed)..."
    
    # Wait for apt lock
    while pgrep -x "apt-get|apt|dpkg|unattended-upgr" > /dev/null 2>&1; do
        sleep 5
    done
    
    # Install python3-venv if needed
    if ! dpkg -s python3-venv &> /dev/null; then
        sudo apt-get update -qq
        sudo apt-get install -y -qq python3-venv
    fi
    
    sudo rm -rf /opt/novaic-venv
    sudo mkdir -p /opt/novaic-venv
    sudo chown $USER:$USER /opt/novaic-venv
    python3 -m venv /opt/novaic-venv
fi

source /opt/novaic-venv/bin/activate

# Check if fastmcp is installed (indicator that deps are installed)
if ! python -c "import fastmcp" &> /dev/null 2>&1; then
    echo "Installing dependencies (cloud-init may have failed)..."
    pip install --upgrade pip -q -i "{pip_index_url}" --trusted-host "{pip_trusted_host}"
    cd /opt/novaic-mcp-vmuse
    pip install -e . -q -i "{pip_index_url}" --trusted-host "{pip_trusted_host}"
else
    echo "Dependencies already installed, skipping..."
    # Still install in editable mode to link the code
    cd /opt/novaic-mcp-vmuse
    pip install -e . -q --no-deps 2>/dev/null || true
fi

# Check if Playwright chromium is installed
if [ ! -d ~/.cache/ms-playwright/chromium-* ]; then
    echo "Installing Playwright chromium (cloud-init may have failed)..."
    pip install playwright -q -i "{pip_index_url}" --trusted-host "{pip_trusted_host}" 2>/dev/null || true
    playwright install chromium
    sudo playwright install-deps chromium 2>/dev/null || true
else
    echo "Playwright chromium already installed, skipping..."
fi

# Reload and start service
sudo systemctl daemon-reload
sudo systemctl enable novaic.service
sudo systemctl restart novaic.service

echo "Done!"
"#, pip_index_url = pip_index_url, pip_trusted_host = pip_trusted_host);

    ssh_run(ssh_config, &install_script)?;
    Ok(())
}

/// Deploy novaic-mcp-vmuse to VM
#[tauri::command]
pub async fn deploy_agent(
    app: tauri::AppHandle,
    ssh_port: u16,
    use_cn_mirrors: bool,
    on_progress: tauri::ipc::Channel<DeployProgress>,
) -> Result<(), String> {
    // Step 0: Get SSH private key from Gateway
    let _ = on_progress.send(DeployProgress {
        stage: "Preparing".to_string(),
        progress: 0,
        message: "Getting SSH key from Gateway...".to_string(),
        log_line: None,
    });

    let key_path = get_ssh_key_from_gateway(&app).await?;
    let ssh_config = SshConfig::with_key(ssh_port, key_path);

    // Step 1: Wait for SSH
    let _ = on_progress.send(DeployProgress {
        stage: "Connecting".to_string(),
        progress: 5,
        message: "Waiting for SSH connection...".to_string(),
        log_line: None,
    });

    wait_for_ssh(&ssh_config, 15, 20).await?;

    // Step 2: Check if cloud-init already completed (skip waiting if done)
    if check_cloud_init_done(&ssh_config) {
        println!("[Deploy] cloud-init already completed, skipping wait");
        let _ = on_progress.send(DeployProgress {
            stage: "Initializing".to_string(),
            progress: 20,
            message: "cloud-init already completed".to_string(),
            log_line: None,
        });
    } else {
        let _ = on_progress.send(DeployProgress {
            stage: "Initializing".to_string(),
            progress: 15,
            message: "First boot: waiting for cloud-init (10-30 min)...".to_string(),
            log_line: None,
        });
        wait_for_cloud_init(&ssh_config, &on_progress).await?;
    }

    // Step 3: Get novaic-mcp-vmuse resource path
    let _ = on_progress.send(DeployProgress {
        stage: "Preparing".to_string(),
        progress: 30,
        message: "Preparing to copy code...".to_string(),
        log_line: None,
    });

    // Try to get novaic-mcp-vmuse from resources, fallback to development path
    let core_path: PathBuf = app.path().resource_dir()
        .ok()
        .map(|p: PathBuf| p.join("novaic-mcp-vmuse"))
        .filter(|p: &PathBuf| p.exists())
        .unwrap_or_else(|| {
            // Development fallback: use executable-relative path
            // exe is at: novaic-app/src-tauri/target/release/novaic
            // core is at: novaic-mcp-vmuse (4 levels up)
            std::env::current_exe()
                .ok()
                .and_then(|p| p.parent().map(|d| d.to_path_buf()))
                .map(|d| d.join("../../../..").join("novaic-mcp-vmuse"))
                .and_then(|p| p.canonicalize().ok())
                .unwrap_or_else(|| PathBuf::from("novaic-mcp-vmuse"))
        });

    if !core_path.exists() {
        return Err(format!("novaic-mcp-vmuse not found at {}", core_path.display()));
    }

    println!("[Deploy] Using novaic-mcp-vmuse from: {}", core_path.display());

    // Step 4: Create directories on VM
    let _ = on_progress.send(DeployProgress {
        stage: "Creating directories".to_string(),
        progress: 35,
        message: "Creating directories on VM...".to_string(),
        log_line: None,
    });

    ssh_run(&ssh_config, "sudo mkdir -p /opt/novaic-mcp-vmuse && sudo chown ubuntu:ubuntu /opt/novaic-mcp-vmuse")?;

    // Step 5: Stop existing service
    let _ = on_progress.send(DeployProgress {
        stage: "Stopping service".to_string(),
        progress: 40,
        message: "Stopping existing service...".to_string(),
        log_line: None,
    });

    let _ = ssh_run(&ssh_config, "sudo systemctl stop novaic 2>/dev/null || true");

    // Step 6: Clean old code
    ssh_run(&ssh_config, "rm -rf /opt/novaic-mcp-vmuse/src /opt/novaic-mcp-vmuse/skills /opt/novaic-mcp-vmuse/pyproject.toml")?;

    // Step 7: Copy code
    let _ = on_progress.send(DeployProgress {
        stage: "Copying code".to_string(),
        progress: 50,
        message: "Copying novaic-mcp-vmuse to VM...".to_string(),
        log_line: None,
    });

    // Copy src directory
    let src_path = core_path.join("src");
    if src_path.exists() {
        scp_directory(&ssh_config, &src_path, "/opt/novaic-mcp-vmuse/")?;
    }

    // Copy skills directory (optional)
    let skills_path = core_path.join("skills");
    if skills_path.exists() {
        let _ = scp_directory(&ssh_config, &skills_path, "/opt/novaic-mcp-vmuse/");
    }

    // Copy pyproject.toml
    let pyproject_path = core_path.join("pyproject.toml");
    if pyproject_path.exists() {
        scp_file(&ssh_config, &pyproject_path, "/opt/novaic-mcp-vmuse/")?;
    }

    // Step 8: Install dependencies and start service
    let _ = on_progress.send(DeployProgress {
        stage: "Installing".to_string(),
        progress: 70,
        message: "Installing dependencies (this may take a few minutes)...".to_string(),
        log_line: None,
    });

    install_and_start_service(&ssh_config, use_cn_mirrors)?;

    // Step 9: Wait for service to be ready
    let _ = on_progress.send(DeployProgress {
        stage: "Verifying".to_string(),
        progress: 90,
        message: "Waiting for service to start...".to_string(),
        log_line: None,
    });

    // Wait for service to become active (with retries)
    let max_service_wait = 60; // 60 seconds
    let check_interval = 5;
    let mut service_ready = false;
    let mut elapsed = 0;

    while elapsed < max_service_wait {
        tokio::time::sleep(tokio::time::Duration::from_secs(check_interval)).await;
        elapsed += check_interval;

        let status = ssh_run(&ssh_config, "systemctl is-active novaic.service 2>/dev/null || echo 'inactive'")
            .unwrap_or_else(|_| "unknown".to_string());

        let _ = on_progress.send(DeployProgress {
            stage: "Verifying".to_string(),
            progress: 90 + (elapsed as u32 * 8 / max_service_wait as u32).min(8),
            message: format!("Checking service status... ({}s)", elapsed),
            log_line: None,
        });

        if status.trim() == "active" {
            println!("[Deploy] Service is active after {}s", elapsed);
            service_ready = true;
            break;
        }

        println!("[Deploy] Service status: {}, waiting... ({}s)", status.trim(), elapsed);
    }

    if !service_ready {
        // Get service logs for debugging
        let logs = ssh_run(&ssh_config, "journalctl -u novaic.service -n 20 --no-pager 2>/dev/null || echo 'no logs'")
            .unwrap_or_else(|_| "Failed to get logs".to_string());
        println!("[Deploy] Service failed to start. Logs:\n{}", logs);
        
        return Err(format!("Service failed to start within {}s. Check service logs.", max_service_wait));
    }

    // Step 10: Verify MCP server is responding
    let _ = on_progress.send(DeployProgress {
        stage: "Verifying".to_string(),
        progress: 98,
        message: "Verifying MCP server...".to_string(),
        log_line: None,
    });

    // Wait for MCP HTTP server to be ready (port 8080 in VM)
    let max_mcp_wait = 30;
    let mut mcp_ready = false;
    elapsed = 0;

    while elapsed < max_mcp_wait {
        let check = ssh_run(&ssh_config, "curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/mcp/ 2>/dev/null || echo '000'")
            .unwrap_or_else(|_| "000".to_string());
        
        let http_code = check.trim();
        if http_code == "200" || http_code == "404" || http_code == "405" {
            // 200 = ok, 404/405 = server running but different endpoint - both mean server is up
            println!("[Deploy] MCP server responding (HTTP {})", http_code);
            mcp_ready = true;
            break;
        }

        tokio::time::sleep(tokio::time::Duration::from_secs(3)).await;
        elapsed += 3;
        println!("[Deploy] MCP server not ready (HTTP {}), waiting... ({}s)", http_code, elapsed);
    }

    if !mcp_ready {
        println!("[Deploy] Warning: MCP server not responding, but service is active. Continuing...");
    }

    let _ = on_progress.send(DeployProgress {
        stage: "Complete".to_string(),
        progress: 100,
        message: "Deployment complete! Service is running.".to_string(),
        log_line: None,
    });

    println!("[Deploy] Deployment complete");
    Ok(())
}

/// Quick deploy: only copy code and restart service (skip waiting)
#[tauri::command]
pub async fn quick_deploy_agent(
    app: tauri::AppHandle,
    ssh_port: u16,
    on_progress: tauri::ipc::Channel<DeployProgress>,
) -> Result<(), String> {
    // Get SSH private key from Gateway
    let key_path = get_ssh_key_from_gateway(&app).await?;
    let ssh_config = SshConfig::with_key(ssh_port, key_path);

    // Check SSH connection
    let _ = on_progress.send(DeployProgress {
        stage: "Connecting".to_string(),
        progress: 0,
        message: "Connecting to VM...".to_string(),
        log_line: None,
    });

    if !check_ssh(&ssh_config) {
        return Err("Cannot connect to VM via SSH".to_string());
    }

    // Get novaic-mcp-vmuse path
    let core_path: PathBuf = app.path().resource_dir()
        .ok()
        .map(|p: PathBuf| p.join("novaic-mcp-vmuse"))
        .filter(|p: &PathBuf| p.exists())
        .unwrap_or_else(|| {
            // Development fallback: use executable-relative path
            std::env::current_exe()
                .ok()
                .and_then(|p| p.parent().map(|d| d.to_path_buf()))
                .map(|d| d.join("../../../..").join("novaic-mcp-vmuse"))
                .and_then(|p| p.canonicalize().ok())
                .unwrap_or_else(|| PathBuf::from("novaic-mcp-vmuse"))
        });

    if !core_path.exists() {
        return Err(format!("novaic-mcp-vmuse not found at {}", core_path.display()));
    }

    // Stop service
    let _ = on_progress.send(DeployProgress {
        stage: "Stopping".to_string(),
        progress: 20,
        message: "Stopping service...".to_string(),
        log_line: None,
    });

    let _ = ssh_run(&ssh_config, "sudo systemctl stop novaic 2>/dev/null || true");

    // Copy code
    let _ = on_progress.send(DeployProgress {
        stage: "Copying".to_string(),
        progress: 40,
        message: "Copying code...".to_string(),
        log_line: None,
    });

    ssh_run(&ssh_config, "rm -rf /opt/novaic-mcp-vmuse/src /opt/novaic-mcp-vmuse/skills")?;

    let src_path = core_path.join("src");
    if src_path.exists() {
        scp_directory(&ssh_config, &src_path, "/opt/novaic-mcp-vmuse/")?;
    }

    let skills_path = core_path.join("skills");
    if skills_path.exists() {
        let _ = scp_directory(&ssh_config, &skills_path, "/opt/novaic-mcp-vmuse/");
    }

    // Restart service
    let _ = on_progress.send(DeployProgress {
        stage: "Restarting".to_string(),
        progress: 80,
        message: "Restarting service...".to_string(),
        log_line: None,
    });

    ssh_run(&ssh_config, "sudo systemctl restart novaic.service")?;

    let _ = on_progress.send(DeployProgress {
        stage: "Complete".to_string(),
        progress: 100,
        message: "Quick deploy complete!".to_string(),
        log_line: None,
    });

    Ok(())
}
