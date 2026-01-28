import { invoke } from '@tauri-apps/api/core';

// VM 状态类型
export interface VmStatus {
  running: boolean;
  agent_healthy: boolean;
  mcp_healthy: boolean;          // NovAIC MCP Server 健康状态
  websockify_running: boolean;
  vnc_port: number;
  agent_port: number;
  mcp_port: number;              // MCP Server 端口
  websocket_port: number;
  vnc_url: string;
  agent_url: string;
  mcp_url: string;               // MCP Server URL
}

// VM 服务类
class VmService {
  /**
   * 启动虚拟机
   */
  async start(): Promise<string> {
    try {
      const result = await invoke<string>('start_vm');
      console.log('[VM Service] Start:', result);
      return result;
    } catch (error) {
      console.error('[VM Service] Start failed:', error);
      throw error;
    }
  }

  /**
   * 停止虚拟机
   */
  async stop(): Promise<string> {
    try {
      const result = await invoke<string>('stop_vm');
      console.log('[VM Service] Stop:', result);
      return result;
    } catch (error) {
      console.error('[VM Service] Stop failed:', error);
      throw error;
    }
  }

  /**
   * 重启虚拟机
   */
  async restart(): Promise<string> {
    try {
      const result = await invoke<string>('restart_vm');
      console.log('[VM Service] Restart:', result);
      return result;
    } catch (error) {
      console.error('[VM Service] Restart failed:', error);
      throw error;
    }
  }

  /**
   * 获取虚拟机状态
   */
  async getStatus(): Promise<VmStatus> {
    try {
      const status = await invoke<VmStatus>('get_vm_status');
      return status;
    } catch (error) {
      console.error('[VM Service] Get status failed:', error);
      throw error;
    }
  }

  /**
   * 获取 VNC WebSocket URL
   */
  async getVncUrl(): Promise<string> {
    try {
      const url = await invoke<string>('get_vnc_url');
      return url;
    } catch (error) {
      console.error('[VM Service] Get VNC URL failed:', error);
      // 返回默认 URL
      return 'ws://localhost:6080/websockify';
    }
  }

  /**
   * 获取 Agent API URL
   */
  async getAgentUrl(): Promise<string> {
    try {
      const url = await invoke<string>('get_agent_url');
      return url;
    } catch (error) {
      console.error('[VM Service] Get Agent URL failed:', error);
      // 返回默认 URL
      return 'http://localhost:9000';
    }
  }

  /**
   * 检查 VM 是否在运行
   */
  async isRunning(): Promise<boolean> {
    try {
      const status = await this.getStatus();
      return status.running;
    } catch {
      return false;
    }
  }

  /**
   * 等待 VM 就绪
   */
  async waitForReady(maxAttempts = 30, intervalMs = 2000): Promise<boolean> {
    for (let i = 0; i < maxAttempts; i++) {
      try {
        const status = await this.getStatus();
        if (status.running && status.agent_healthy) {
          return true;
        }
      } catch {
        // 继续等待
      }
      await new Promise(resolve => setTimeout(resolve, intervalMs));
    }
    return false;
  }
}

// 导出单例
export const vmService = new VmService();

