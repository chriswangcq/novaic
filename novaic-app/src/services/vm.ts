/**
 * VM Service - Gateway API based VM management
 * 
 * All VM operations are now handled by Gateway, not Tauri.
 * This provides better state management and crash recovery.
 */

import { invoke } from '@tauri-apps/api/core';
import type { PortConfig } from './api';

// VM 状态类型 - matches Gateway VmStatus
export interface VmStatus {
  agent_id: string;              // Agent ID
  running: boolean;
  agent_healthy: boolean;
  mcp_healthy: boolean;          // NovAIC MCP Server 健康状态
  websockify_running: boolean;
  ports: PortConfig | Record<string, number>;  // 端口配置
  vnc_url: string;
  mcp_url: string;               // MCP Server URL
  pid?: number;                  // QEMU PID
  started_at?: string;           // Start time
  error_message?: string;        // Error if any
}

// VM 服务类 - 通过 Gateway API 管理 VM
class VmService {
  /**
   * 启动虚拟机
   * @param agentId - Agent ID
   * @param agentIndex - Agent 索引（用于端口分配）
   */
  async start(agentId: string, agentIndex: number): Promise<string> {
    try {
      const result = await invoke<{ success: boolean; status?: string; pid?: number }>('gateway_post', {
        path: '/api/vm/start',
        body: {
          agent_id: agentId,
          agent_index: agentIndex,
          memory: '4096',
          cpus: 4,
        }
      });
      console.log('[VM Service] Start:', result, 'agentId:', agentId, 'agentIndex:', agentIndex);
      return result.status || 'started';
    } catch (error) {
      console.error('[VM Service] Start failed:', error);
      throw error;
    }
  }

  /**
   * 停止特定 agent 的虚拟机
   * @param agentId - Agent ID
   */
  async stop(agentId: string): Promise<string> {
    try {
      const result = await invoke<{ success: boolean; status: string }>('gateway_post', {
        path: '/api/vm/stop',
        body: {
          agent_id: agentId,
          graceful: true,
        }
      });
      console.log('[VM Service] Stop:', result, 'agentId:', agentId);
      return result.status;
    } catch (error) {
      console.error('[VM Service] Stop failed:', error);
      throw error;
    }
  }

  /**
   * 停止所有虚拟机
   */
  async stopAll(): Promise<string> {
    try {
      const result = await invoke<{ success: boolean }>('gateway_post', {
        path: '/api/vm/stop-all',
        body: {}
      });
      console.log('[VM Service] Stop all:', result);
      return result.success ? 'stopped' : 'failed';
    } catch (error) {
      console.error('[VM Service] Stop all failed:', error);
      throw error;
    }
  }

  /**
   * 重启虚拟机
   * @param agentId - Agent ID
   * @param agentIndex - Agent 索引（用于端口分配）
   */
  async restart(agentId: string, agentIndex: number): Promise<string> {
    try {
      // Stop then start
      await this.stop(agentId);
      await new Promise(resolve => setTimeout(resolve, 2000));
      return await this.start(agentId, agentIndex);
    } catch (error) {
      console.error('[VM Service] Restart failed:', error);
      throw error;
    }
  }

  /**
   * 获取特定 agent 的虚拟机状态
   * @param agentId - Agent ID
   */
  async getStatus(agentId: string): Promise<VmStatus | null> {
    try {
      const status = await invoke<VmStatus>('gateway_get', {
        path: `/api/vm/status/${agentId}`
      });
      return status;
    } catch (error) {
      // 404 means VM not found, which is normal
      if (String(error).includes('404')) {
        return null;
      }
      console.error('[VM Service] Get status failed:', error);
      return null;
    }
  }

  /**
   * 获取所有 VM 的状态
   */
  async getAllStatus(): Promise<Record<string, VmStatus>> {
    try {
      const status = await invoke<Record<string, VmStatus>>('gateway_get', {
        path: '/api/vm/status'
      });
      return status || {};
    } catch (error) {
      console.error('[VM Service] Get all status failed:', error);
      return {};
    }
  }

  /**
   * 获取所有运行中的 agent ID
   */
  async getRunningAgents(): Promise<string[]> {
    try {
      const result = await invoke<{ agents: string[] }>('gateway_get', {
        path: '/api/vm/running'
      });
      return result.agents || [];
    } catch (error) {
      console.error('[VM Service] Get running agents failed:', error);
      return [];
    }
  }

  /**
   * 获取 VNC WebSocket URL
   * @param agentId - Agent ID
   */
  async getVncUrl(agentId: string): Promise<string> {
    try {
      const status = await this.getStatus(agentId);
      if (status?.vnc_url) {
        return status.vnc_url;
      }
      // 返回默认 URL (Agent 0 websocket port: 20007)
      return 'ws://localhost:20007/websockify';
    } catch (error) {
      console.error('[VM Service] Get VNC URL failed:', error);
      return 'ws://localhost:20007/websockify';
    }
  }

  /**
   * 获取 Agent API URL (Gateway URL，固定端口)
   */
  async getAgentUrl(): Promise<string> {
    // Gateway is always at fixed port
    return 'http://localhost:19999';
  }

  /**
   * 检查特定 agent 的 VM 是否在运行
   * @param agentId - Agent ID
   */
  async isRunning(agentId: string): Promise<boolean> {
    try {
      const result = await invoke<{ running: boolean }>('gateway_get', {
        path: `/api/vm/is-running/${agentId}`
      });
      return result.running;
    } catch {
      return false;
    }
  }

  /**
   * 等待特定 agent 的 VM 就绪
   * @param agentId - Agent ID
   */
  async waitForReady(agentId: string, maxAttempts = 30, intervalMs = 2000): Promise<boolean> {
    for (let i = 0; i < maxAttempts; i++) {
      try {
        const status = await this.getStatus(agentId);
        if (status && status.running && status.agent_healthy) {
          return true;
        }
      } catch {
        // 继续等待
      }
      await new Promise(resolve => setTimeout(resolve, intervalMs));
    }
    return false;
  }

  /**
   * 检查环境依赖
   */
  async checkEnvironment(): Promise<{
    ready: boolean;
    platform: string;
    arch: string;
    dependencies: Array<{
      name: string;
      installed: boolean;
      version?: string;
      path?: string;
      install_command?: string;
    }>;
  }> {
    try {
      return await invoke('gateway_get', { path: '/api/vm/environment' });
    } catch (error) {
      console.error('[VM Service] Check environment failed:', error);
      throw error;
    }
  }

  /**
   * 设置 VM（创建磁盘和 cloud-init）
   */
  async setupVm(params: {
    agentId: string;
    sourceImage: string;
    diskSize?: string;
    useCnMirrors?: boolean;
  }): Promise<{
    success: boolean;
    vm_dir: string;
    disk_path: string;
    cloudinit_iso: string;
    uefi_vars?: string;
  }> {
    try {
      return await invoke('gateway_post', {
        path: '/api/vm/setup',
        body: {
          agent_id: params.agentId,
          source_image: params.sourceImage,
          disk_size: params.diskSize || '40G',
          use_cn_mirrors: params.useCnMirrors || false,
        }
      });
    } catch (error) {
      console.error('[VM Service] Setup VM failed:', error);
      throw error;
    }
  }
}

// 导出单例
export const vmService = new VmService();
