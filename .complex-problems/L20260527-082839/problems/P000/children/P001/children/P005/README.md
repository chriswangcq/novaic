# Inspect local Release Controller contract

## Problem

The deployment must use the controller correctly, so local docs/config/source must reveal the expected trigger API, namespaces, deploy scripts, health checks, and branch policy.

## Success Criteria

- Identify config file paths and important values for controller URL/port, branch, namespace, health URLs, and deploy script commands.
- Identify whether prod promotion is automatic or manual/promotion API only.
- Identify any required dry_run settings or guardrails that affect triggering.
