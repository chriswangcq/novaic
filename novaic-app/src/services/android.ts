/**
 * Android Service - 封装与后端 Android API 的交互
 *
 * 通过 vmcontrol 服务管理 Android 模拟器和 scrcpy 投屏
 */

import { WS_CONFIG, API_CONFIG } from '../config';

// ============ Types ============

/** Android 设备状态 */
export type AndroidDeviceStatus = 'offline' | 'booting' | 'online' | 'connected';

/** Android 设备信息 */
export interface AndroidDevice {
  serial: string;
  status: AndroidDeviceStatus;
  avdName?: string;
  managed?: boolean;
}

/** AVD 信息 */
export interface AvdInfo {
  name: string;
  device?: string;
  path?: string;
  target?: string;
  abi?: string;
}

/** 后端 API 响应类型 */
interface AvdListResponse {
  avds: AvdInfo[];
}

interface DeviceListResponse {
  devices: DeviceStatusResponse[];
}

interface DeviceStatusResponse {
  serial: string;
  avd_name?: string;
  managed: boolean;
  emulator_pid?: number;
  status: string;
}

interface StartEmulatorResponse {
  success: boolean;
  device: DeviceStatusResponse;
  message: string;
}

interface StopEmulatorResponse {
  success: boolean;
  message: string;
}

interface ScrcpyStatusResponse {
  available: boolean;
  version?: string;
}

/** 系统镜像检查结果 */
export interface SystemImageCheckResult {
  installed: boolean;
  path?: string;
}

interface SystemImageCheckResponse {
  available: boolean;
  message?: string;
  path?: string;
}

/** 设备定义信息 */
export interface DeviceDefinition {
  id: string;           // 设备 ID，如 "pixel_7"
  name: string;         // 显示名称，如 "Pixel 7"
  manufacturer: string; // 制造商，如 "Google"
  screenSize: string;   // 屏幕尺寸，如 "6.3"
  resolution: string;   // 分辨率，如 "1080x2400"
  density: number;      // 屏幕密度，如 420
}

interface DeviceDefinitionsResponse {
  devices: DeviceDefinition[];
}

// ============ Helpers ============

/** vmcontrol 服务基础 URL */
const getBaseUrl = (): string => {
  return `http://localhost:${WS_CONFIG.VMCONTROL_PORT}`;
};

/** 将后端 DeviceStatusResponse 转为前端 AndroidDevice */
const toAndroidDevice = (d: DeviceStatusResponse): AndroidDevice => ({
  serial: d.serial,
  status: d.status as AndroidDeviceStatus,
  avdName: d.avd_name,
  managed: d.managed,
});

/** 发起 GET 请求 */
async function fetchGet<T>(path: string): Promise<T> {
  const url = `${getBaseUrl()}${path}`;
  const response = await fetch(url, {
    signal: AbortSignal.timeout(API_CONFIG.ABORT_TIMEOUT),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Android API error ${response.status}: ${body || response.statusText}`);
  }

  return response.json();
}

/** 发起 POST 请求 */
async function fetchPost<T>(path: string, body: unknown): Promise<T> {
  const url = `${getBaseUrl()}${path}`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(API_CONFIG.ABORT_TIMEOUT),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Android API error ${response.status}: ${body || response.statusText}`);
  }

  return response.json();
}

// ============ Service ============

export const androidService = {
  /**
   * 列出可用的 AVD
   */
  async listAvds(): Promise<AvdInfo[]> {
    try {
      const res = await fetchGet<AvdListResponse>('/api/android/avds');
      return res.avds ?? [];
    } catch (error) {
      console.error('[Android Service] List AVDs failed:', error);
      throw error;
    }
  },

  /**
   * 列出已连接的设备
   */
  async listDevices(): Promise<AndroidDevice[]> {
    try {
      const res = await fetchGet<DeviceListResponse>('/api/android/devices');
      return (res.devices ?? []).map(toAndroidDevice);
    } catch (error) {
      console.error('[Android Service] List devices failed:', error);
      throw error;
    }
  },

  /**
   * 启动模拟器
   * @param avdName - AVD 名称
   * @param headless - 是否无头模式，默认 true
   */
  async startEmulator(avdName: string, headless = true): Promise<{ serial: string }> {
    try {
      const res = await fetchPost<StartEmulatorResponse>('/api/android/emulator/start', {
        avd: avdName,
        headless,
      });
      return { serial: res.device.serial };
    } catch (error) {
      console.error('[Android Service] Start emulator failed:', error);
      throw error;
    }
  },

  /**
   * 停止模拟器
   * @param serial - 设备序列号
   */
  async stopEmulator(serial: string): Promise<void> {
    try {
      await fetchPost<StopEmulatorResponse>('/api/android/emulator/stop', { serial });
    } catch (error) {
      console.error('[Android Service] Stop emulator failed:', error);
      throw error;
    }
  },

  /**
   * 获取设备状态
   * @param serial - 设备序列号
   */
  async getStatus(serial: string): Promise<AndroidDevice> {
    try {
      const res = await fetchGet<DeviceStatusResponse>(
        `/api/android/emulator/status?serial=${encodeURIComponent(serial)}`
      );
      return toAndroidDevice(res);
    } catch (error) {
      console.error('[Android Service] Get status failed:', error);
      throw error;
    }
  },

  /**
   * 获取 scrcpy WebSocket URL
   * @param serial - 设备序列号
   */
  getScrcpyUrl(serial: string): string {
    const base = `ws://localhost:${WS_CONFIG.VMCONTROL_PORT}`;
    return `${base}/api/android/scrcpy?device=${encodeURIComponent(serial)}`;
  },

  /**
   * 检查 scrcpy 是否可用
   */
  async checkScrcpyAvailable(): Promise<boolean> {
    try {
      const res = await fetchGet<ScrcpyStatusResponse>('/api/android/scrcpy/status');
      return res.available ?? false;
    } catch (error) {
      console.error('[Android Service] Check scrcpy available failed:', error);
      return false;
    }
  },

  /**
   * 检查 Android 34 系统镜像是否已安装
   */
  async checkSystemImage(): Promise<SystemImageCheckResult> {
    try {
      const res = await fetchGet<SystemImageCheckResponse>('/api/android/system-image/check');
      return {
        installed: res.available,
        path: res.path,
      };
    } catch (error) {
      console.error('[Android Service] Check system image failed:', error);
      throw error;
    }
  },

  /**
   * 列出可用的设备定义
   * 用于创建 AVD 时选择设备类型
   */
  async listDeviceDefinitions(): Promise<DeviceDefinition[]> {
    try {
      const res = await fetchGet<DeviceDefinitionsResponse>('/api/android/device-definitions');
      return res.devices ?? [];
    } catch (error) {
      console.error('[Android Service] List device definitions failed:', error);
      throw error;
    }
  },

  /**
   * 创建新的 AVD（使用固定的 Android 34 系统镜像）
   * @param name - AVD 名称
   * @param device - 设备定义 ID（可选，默认 pixel_7）
   * @param memory - 内存大小（可选，如 "4096"）
   * @param cores - CPU 核心数（可选）
   */
  async createAvd(
    name: string,
    device?: string,
    memory?: string,
    cores?: number
  ): Promise<{ success: boolean; avdName: string }> {
    try {
      const res = await fetchPost<{ success: boolean; avd_name: string }>('/api/android/avd/create', {
        name,
        ...(device && { device }),
        ...(memory && { memory }),
        ...(cores && { cores }),
      });
      return { success: res.success, avdName: res.avd_name };
    } catch (error) {
      console.error('[Android Service] Create AVD failed:', error);
      throw error;
    }
  },
};
