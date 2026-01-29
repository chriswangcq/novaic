/**
 * VM Setup Service
 * 
 * Handles communication with Tauri backend for VM setup operations:
 * - Check/download cloud images
 * - Setup VM (disk creation, cloud-init)
 * - Deploy code to VM
 */

import { invoke, Channel } from '@tauri-apps/api/core';

// Types for setup operations

export interface ImageCheckResult {
  exists: boolean;
  path: string | null;
  size: number | null;
}

export interface DownloadProgress {
  downloaded: number;
  total: number;
  percent: number;
  speed: string;
}

export interface SetupProgress {
  stage: string;
  progress: number;
  message: string;
}

export interface DeployProgress {
  stage: string;
  progress: number;
  message: string;
}

export interface VmSetupResult {
  disk_path: string;
  seed_iso_path: string;
  uefi_vars_path: string | null;
}

export interface VmSetupConfig {
  agentId: string;
  sourceImage: string;
  diskSize: string;
  sshPubkey: string;
  useCnMirrors: boolean;
}

/**
 * Check if cloud image exists locally
 */
export async function checkCloudImage(
  osType: string,
  osVersion: string
): Promise<ImageCheckResult> {
  return await invoke('check_cloud_image', {
    osType,
    osVersion,
  });
}

/**
 * Download cloud image with progress reporting
 */
export async function downloadCloudImage(
  osType: string,
  osVersion: string,
  useCnMirrors: boolean,
  onProgress: (progress: DownloadProgress) => void
): Promise<string> {
  const channel = new Channel<DownloadProgress>();
  channel.onmessage = onProgress;

  return await invoke('download_cloud_image', {
    osType,
    osVersion,
    useCnMirrors,
    onProgress: channel,
  });
}

/**
 * Setup VM (create disk, cloud-init ISO, UEFI firmware)
 */
export async function setupVm(
  config: VmSetupConfig,
  onProgress: (progress: SetupProgress) => void
): Promise<VmSetupResult> {
  const channel = new Channel<SetupProgress>();
  channel.onmessage = onProgress;

  return await invoke('setup_vm', {
    agentId: config.agentId,
    sourceImage: config.sourceImage,
    diskSize: config.diskSize,
    sshPubkey: config.sshPubkey,
    useCnMirrors: config.useCnMirrors,
    onProgress: channel,
  });
}

/**
 * Deploy novaic-vm-tools to VM
 */
export async function deployAgent(
  sshPort: number,
  useCnMirrors: boolean,
  onProgress: (progress: DeployProgress) => void
): Promise<void> {
  const channel = new Channel<DeployProgress>();
  channel.onmessage = onProgress;

  return await invoke('deploy_agent', {
    sshPort,
    useCnMirrors,
    onProgress: channel,
  });
}

/**
 * Quick deploy (only copy code and restart service)
 */
export async function quickDeployAgent(
  sshPort: number,
  onProgress: (progress: DeployProgress) => void
): Promise<void> {
  const channel = new Channel<DeployProgress>();
  channel.onmessage = onProgress;

  return await invoke('quick_deploy_agent', {
    sshPort,
    onProgress: channel,
  });
}

/**
 * Get user's SSH public key
 */
export async function getSshPubkey(): Promise<string | null> {
  return await invoke('get_ssh_pubkey');
}

/**
 * Generate new SSH key pair
 */
export async function generateSshKey(): Promise<string> {
  return await invoke('generate_ssh_key');
}
