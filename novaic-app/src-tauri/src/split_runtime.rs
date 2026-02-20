/// Split runtime configuration helpers.
///
/// These helpers centralize environment-driven endpoint resolution so desktop
/// startup can run either in bundled monorepo mode or external split-service mode.

const DEFAULT_GATEWAY_BASE_URL: &str = "http://127.0.0.1:19999";

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
        .unwrap_or(false)
}

pub fn parse_gateway_port(base_url: &str) -> Option<u16> {
    let without_scheme = base_url.split("://").nth(1).unwrap_or(base_url);
    let host_port = without_scheme.split('/').next()?;
    let (_host, port) = host_port.rsplit_once(':')?;
    port.parse::<u16>().ok()
}
