//! VM Deploy Module
//!
//! Handles deploying novaic-vm-tools to the VM:
//! - Wait for SSH to be available
//! - Wait for cloud-init to complete
//! - Copy novaic-vm-tools code to VM
//! - Install dependencies and start service

use std::path::PathBuf;
use std::process::{Command, Stdio};
use serde::{Deserialize, Serialize};
use tauri::Manager;

/// Deploy progress information
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DeployProgress {
    pub stage: String,
    pub progress: u32,
    pub message: String,
}

/// SSH configuration
struct SshConfig {
    host: String,
    port: u16,
    user: String,
}

impl SshConfig {
    fn new(port: u16) -> Self {
        Self {
            host: "127.0.0.1".to_string(),
            port,
            user: "ubuntu".to_string(),
        }
    }

    /// Get SSH command arguments
    fn ssh_args(&self) -> Vec<String> {
        vec![
            "-o".to_string(), "StrictHostKeyChecking=no".to_string(),
            "-o".to_string(), "UserKnownHostsFile=/dev/null".to_string(),
            "-o".to_string(), "LogLevel=ERROR".to_string(),
            "-o".to_string(), "ConnectTimeout=10".to_string(),
            "-p".to_string(), self.port.to_string(),
            format!("{}@{}", self.user, self.host),
        ]
    }

    /// Get SCP command arguments for copying files
    fn scp_args(&self, src: &str, dest: &str) -> Vec<String> {
        vec![
            "-o".to_string(), "StrictHostKeyChecking=no".to_string(),
            "-o".to_string(), "UserKnownHostsFile=/dev/null".to_string(),
            "-o".to_string(), "LogLevel=ERROR".to_string(),
            "-r".to_string(),
            "-P".to_string(), self.port.to_string(),
            src.to_string(),
            format!("{}@{}:{}", self.user, self.host, dest),
        ]
    }
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

/// Wait for cloud-init to complete
async fn wait_for_cloud_init(ssh_config: &SshConfig) -> Result<(), String> {
    println!("[Deploy] Waiting for cloud-init to complete...");

    let max_wait_secs = 600; // 10 minutes
    let check_interval_secs = 5;
    let mut elapsed = 0;

    while elapsed < max_wait_secs {
        if check_cloud_init_done(ssh_config) {
            println!("[Deploy] cloud-init completed after {}s", elapsed);
            return Ok(());
        }

        tokio::time::sleep(tokio::time::Duration::from_secs(check_interval_secs)).await;
        elapsed += check_interval_secs;

        if elapsed % 30 == 0 {
            println!("[Deploy] Still waiting for cloud-init... {}s elapsed", elapsed);
        }
    }

    Err(format!("cloud-init did not complete within {}s", max_wait_secs))
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

    let args = vec![
        "-o".to_string(), "StrictHostKeyChecking=no".to_string(),
        "-o".to_string(), "UserKnownHostsFile=/dev/null".to_string(),
        "-o".to_string(), "LogLevel=ERROR".to_string(),
        "-P".to_string(), ssh_config.port.to_string(),
        src.to_str().unwrap().to_string(),
        format!("{}@{}:{}", ssh_config.user, ssh_config.host, dest),
    ];

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

/// Install dependencies and start service
fn install_and_start_service(ssh_config: &SshConfig, use_cn_mirrors: bool) -> Result<(), String> {
    // Configure pip source
    let (pip_index_url, pip_trusted_host) = if use_cn_mirrors {
        ("https://mirrors.aliyun.com/pypi/simple/", "mirrors.aliyun.com")
    } else {
        ("https://pypi.org/simple/", "pypi.org")
    };

    // Installation script
    let install_script = format!(r#"
set -e

# Wait for apt lock
echo "Waiting for apt..."
while pgrep -x "apt-get|apt|dpkg|unattended-upgr" > /dev/null 2>&1; do
    sleep 5
done

# Install python3-venv if needed
if ! dpkg -s python3-venv &> /dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3-venv
fi

# Create virtual environment
if [ ! -f /opt/novaic-venv/bin/activate ]; then
    sudo rm -rf /opt/novaic-venv
    sudo mkdir -p /opt/novaic-venv
    sudo chown $USER:$USER /opt/novaic-venv
    python3 -m venv /opt/novaic-venv
fi

source /opt/novaic-venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip -q -i "{pip_index_url}" --trusted-host "{pip_trusted_host}"
cd /opt/novaic-vm-tools
pip install -e . -q -i "{pip_index_url}" --trusted-host "{pip_trusted_host}"

# Install Playwright
echo "Installing Playwright..."
if ! playwright --version &> /dev/null 2>&1; then
    pip install playwright -q -i "{pip_index_url}" --trusted-host "{pip_trusted_host}"
    playwright install chromium
    sudo playwright install-deps chromium 2>/dev/null || true
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

/// Deploy novaic-vm-tools to VM
#[tauri::command]
pub async fn deploy_agent(
    app: tauri::AppHandle,
    ssh_port: u16,
    use_cn_mirrors: bool,
    on_progress: tauri::ipc::Channel<DeployProgress>,
) -> Result<(), String> {
    let ssh_config = SshConfig::new(ssh_port);

    // Step 1: Wait for SSH
    let _ = on_progress.send(DeployProgress {
        stage: "Connecting".to_string(),
        progress: 0,
        message: "Waiting for SSH connection...".to_string(),
    });

    wait_for_ssh(&ssh_config, 15, 20).await?;

    // Step 2: Wait for cloud-init
    let _ = on_progress.send(DeployProgress {
        stage: "Initializing".to_string(),
        progress: 15,
        message: "Waiting for cloud-init to complete...".to_string(),
    });

    wait_for_cloud_init(&ssh_config).await?;

    // Step 3: Get novaic-vm-tools resource path
    let _ = on_progress.send(DeployProgress {
        stage: "Preparing".to_string(),
        progress: 30,
        message: "Preparing to copy code...".to_string(),
    });

    // Try to get novaic-vm-tools from resources, fallback to development path
    let core_path: PathBuf = app.path().resource_dir()
        .ok()
        .map(|p: PathBuf| p.join("novaic-vm-tools"))
        .filter(|p: &PathBuf| p.exists())
        .unwrap_or_else(|| {
            // Development fallback: use executable-relative path
            // exe is at: novaic-app/src-tauri/target/release/novaic
            // core is at: novaic-vm-tools (4 levels up)
            std::env::current_exe()
                .ok()
                .and_then(|p| p.parent().map(|d| d.to_path_buf()))
                .map(|d| d.join("../../../..").join("novaic-vm-tools"))
                .and_then(|p| p.canonicalize().ok())
                .unwrap_or_else(|| PathBuf::from("novaic-vm-tools"))
        });

    if !core_path.exists() {
        return Err(format!("novaic-vm-tools not found at {}", core_path.display()));
    }

    println!("[Deploy] Using novaic-vm-tools from: {}", core_path.display());

    // Step 4: Create directories on VM
    let _ = on_progress.send(DeployProgress {
        stage: "Creating directories".to_string(),
        progress: 35,
        message: "Creating directories on VM...".to_string(),
    });

    ssh_run(&ssh_config, "sudo mkdir -p /opt/novaic-vm-tools && sudo chown ubuntu:ubuntu /opt/novaic-vm-tools")?;

    // Step 5: Stop existing service
    let _ = on_progress.send(DeployProgress {
        stage: "Stopping service".to_string(),
        progress: 40,
        message: "Stopping existing service...".to_string(),
    });

    let _ = ssh_run(&ssh_config, "sudo systemctl stop novaic 2>/dev/null || true");

    // Step 6: Clean old code
    ssh_run(&ssh_config, "rm -rf /opt/novaic-vm-tools/src /opt/novaic-vm-tools/skills /opt/novaic-vm-tools/pyproject.toml")?;

    // Step 7: Copy code
    let _ = on_progress.send(DeployProgress {
        stage: "Copying code".to_string(),
        progress: 50,
        message: "Copying novaic-vm-tools to VM...".to_string(),
    });

    // Copy src directory
    let src_path = core_path.join("src");
    if src_path.exists() {
        scp_directory(&ssh_config, &src_path, "/opt/novaic-vm-tools/")?;
    }

    // Copy skills directory (optional)
    let skills_path = core_path.join("skills");
    if skills_path.exists() {
        let _ = scp_directory(&ssh_config, &skills_path, "/opt/novaic-vm-tools/");
    }

    // Copy pyproject.toml
    let pyproject_path = core_path.join("pyproject.toml");
    if pyproject_path.exists() {
        scp_file(&ssh_config, &pyproject_path, "/opt/novaic-vm-tools/")?;
    }

    // Step 8: Install dependencies and start service
    let _ = on_progress.send(DeployProgress {
        stage: "Installing".to_string(),
        progress: 70,
        message: "Installing dependencies (this may take a few minutes)...".to_string(),
    });

    install_and_start_service(&ssh_config, use_cn_mirrors)?;

    // Step 9: Verify service is running
    let _ = on_progress.send(DeployProgress {
        stage: "Verifying".to_string(),
        progress: 95,
        message: "Verifying service status...".to_string(),
    });

    tokio::time::sleep(tokio::time::Duration::from_secs(3)).await;

    let status = ssh_run(&ssh_config, "systemctl is-active novaic.service 2>/dev/null || echo 'inactive'")
        .unwrap_or_else(|_| "unknown".to_string());

    if status.trim() == "active" {
        let _ = on_progress.send(DeployProgress {
            stage: "Complete".to_string(),
            progress: 100,
            message: "Deployment complete! Service is running.".to_string(),
        });
    } else {
        let _ = on_progress.send(DeployProgress {
            stage: "Complete".to_string(),
            progress: 100,
            message: format!("Deployment complete. Service status: {}", status.trim()),
        });
    }

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
    let ssh_config = SshConfig::new(ssh_port);

    // Check SSH connection
    let _ = on_progress.send(DeployProgress {
        stage: "Connecting".to_string(),
        progress: 0,
        message: "Connecting to VM...".to_string(),
    });

    if !check_ssh(&ssh_config) {
        return Err("Cannot connect to VM via SSH".to_string());
    }

    // Get novaic-vm-tools path
    let core_path: PathBuf = app.path().resource_dir()
        .ok()
        .map(|p: PathBuf| p.join("novaic-vm-tools"))
        .filter(|p: &PathBuf| p.exists())
        .unwrap_or_else(|| {
            // Development fallback: use executable-relative path
            std::env::current_exe()
                .ok()
                .and_then(|p| p.parent().map(|d| d.to_path_buf()))
                .map(|d| d.join("../../../..").join("novaic-vm-tools"))
                .and_then(|p| p.canonicalize().ok())
                .unwrap_or_else(|| PathBuf::from("novaic-vm-tools"))
        });

    if !core_path.exists() {
        return Err(format!("novaic-vm-tools not found at {}", core_path.display()));
    }

    // Stop service
    let _ = on_progress.send(DeployProgress {
        stage: "Stopping".to_string(),
        progress: 20,
        message: "Stopping service...".to_string(),
    });

    let _ = ssh_run(&ssh_config, "sudo systemctl stop novaic 2>/dev/null || true");

    // Copy code
    let _ = on_progress.send(DeployProgress {
        stage: "Copying".to_string(),
        progress: 40,
        message: "Copying code...".to_string(),
    });

    ssh_run(&ssh_config, "rm -rf /opt/novaic-vm-tools/src /opt/novaic-vm-tools/skills")?;

    let src_path = core_path.join("src");
    if src_path.exists() {
        scp_directory(&ssh_config, &src_path, "/opt/novaic-vm-tools/")?;
    }

    let skills_path = core_path.join("skills");
    if skills_path.exists() {
        let _ = scp_directory(&ssh_config, &skills_path, "/opt/novaic-vm-tools/");
    }

    // Restart service
    let _ = on_progress.send(DeployProgress {
        stage: "Restarting".to_string(),
        progress: 80,
        message: "Restarting service...".to_string(),
    });

    ssh_run(&ssh_config, "sudo systemctl restart novaic.service")?;

    let _ = on_progress.send(DeployProgress {
        stage: "Complete".to_string(),
        progress: 100,
        message: "Quick deploy complete!".to_string(),
    });

    Ok(())
}
