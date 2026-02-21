use std::path::PathBuf;

/// Split runtime configuration helpers.
///
/// These helpers centralize environment-driven endpoint resolution so desktop
/// startup can run either in bundled monorepo mode or external split-service mode.
///
/// Split-mode activation:
///   NOVAIC_TOOLS_SERVER_SPLIT_REPO=<path>  — desktop spawns main_tools.py from split repo;
///                                            monorepo fallback is disabled.

const DEFAULT_GATEWAY_BASE_URL: &str = "http://127.0.0.1:19999";
#[allow(dead_code)]
const DEFAULT_AGENT_BASE_URL: &str = "http://127.0.0.1:20000";
const DEFAULT_TOOLS_SERVER_BASE_URL: &str = "http://127.0.0.1:19998";

pub fn gateway_base_url() -> String {
    std::env::var("NOVAIC_GATEWAY_URL")
        .ok()
        .map(|v| v.trim().to_string())
        .filter(|v| !v.is_empty())
        .unwrap_or_else(|| DEFAULT_GATEWAY_BASE_URL.to_string())
}

pub fn external_services_mode() -> bool {
    std::env::var("NOVAIC_EXTERNAL_SERVICES_MODE")
        .ok()
        .map(|v| {
            let lowered = v.trim().to_ascii_lowercase();
            matches!(lowered.as_str(), "1" | "true" | "yes" | "on")
        })
        .unwrap_or(!cfg!(debug_assertions))
}

#[allow(dead_code)]
pub fn agent_base_url() -> String {
    std::env::var("NOVAIC_AGENT_BASE_URL")
        .ok()
        .map(|v| v.trim().to_string())
        .filter(|v| !v.is_empty())
        .unwrap_or_else(|| DEFAULT_AGENT_BASE_URL.to_string())
}

/// Returns the tools-server base URL, respecting NOVAIC_TOOLS_SERVER_URL override.
#[allow(dead_code)]
pub fn tools_server_base_url() -> String {
    std::env::var("NOVAIC_TOOLS_SERVER_URL")
        .ok()
        .map(|v| v.trim().to_string())
        .filter(|v| !v.is_empty())
        .unwrap_or_else(|| DEFAULT_TOOLS_SERVER_BASE_URL.to_string())
}

/// Returns the split repo path for tools-server, or None if split mode is not active.
#[allow(dead_code)]
pub fn tools_server_split_repo() -> Option<String> {
    std::env::var("NOVAIC_TOOLS_SERVER_SPLIT_REPO")
        .ok()
        .map(|v| v.trim().to_string())
        .filter(|v| !v.is_empty())
}

pub fn parse_gateway_port(base_url: &str) -> Option<u16> {
    let without_scheme = base_url.split("://").nth(1).unwrap_or(base_url);
    let host_port = without_scheme.split('/').next()?;
    let (_host, port) = host_port.rsplit_once(':')?;
    port.parse::<u16>().ok()
}

pub fn tools_server_repo_dir() -> Option<PathBuf> {
    if let Ok(from_env) = std::env::var("NOVAIC_TOOLS_SERVER_DIR") {
        let trimmed = from_env.trim();
        if !trimmed.is_empty() {
            return Some(PathBuf::from(trimmed));
        }
    }

    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            let candidate = exe_dir.join("../../../..").join("novaic-tools-server");
            return Some(candidate);
        }
    }

    None
}
