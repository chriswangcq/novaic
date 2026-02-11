import { useState, useEffect, useCallback } from 'react';
import { Monitor, Smartphone, Plus, Play, Square, Trash2, X, ExternalLink } from 'lucide-react';
import { useAppStore } from '../../store';
import { vmService, VmStatus } from '../../services/vm';
import { androidService, AndroidDevice } from '../../services/android';
import { api } from '../../services/api';
import { VNCView } from '../Visual/VNCView';
import { ScrcpyView } from '../Visual/ScrcpyView';
import { AddLinuxVMModal } from '../VM/AddLinuxVMModal';
import { AddAndroidModal } from '../VM/AddAndroidModal';

interface DeviceSidebarProps {
  className?: string;
}

// 设备状态类型
type DeviceStatus = 'online' | 'offline' | 'connecting';

// 设备信息接口
interface DeviceInfo {
  id: string;
  type: 'linux' | 'android';
  name: string;
  status: DeviceStatus;
  serial?: string;  // Android 设备序列号
}

// 设备卡片组件
interface DeviceCardProps {
  device: DeviceInfo;
  isActive?: boolean;
  onClick?: () => void;
  onStart?: () => void;
  onStop?: () => void;
  onOpenDisplay?: () => void;
  onDelete?: () => void;
}

function DeviceCard({ 
  device, 
  isActive, 
  onClick,
  onStart,
  onStop,
  onOpenDisplay,
  onDelete,
}: DeviceCardProps) {
  const [showActions, setShowActions] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const Icon = device.type === 'linux' ? Monitor : Smartphone;
  const isRunning = device.status === 'online';
  
  const handleClick = () => {
    if (device.status === 'online' && onOpenDisplay) {
      onOpenDisplay();
    } else {
      onClick?.();
    }
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (showDeleteConfirm) {
      onDelete?.();
      setShowDeleteConfirm(false);
    } else {
      setShowDeleteConfirm(true);
      // 3秒后自动取消确认状态
      setTimeout(() => setShowDeleteConfirm(false), 3000);
    }
  };
  
  return (
    <div
      className="relative"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => {
        setShowActions(false);
        setShowDeleteConfirm(false);
      }}
    >
      <button
        onClick={handleClick}
        className={`
          w-full p-2 rounded-lg border transition-all
          ${isActive 
            ? 'bg-nb-accent/20 border-nb-accent/50' 
            : 'bg-nb-surface border-nb-border hover:bg-nb-surface-2 hover:border-nb-border-hover'
          }
        `}
        title={`${device.name}\n状态: ${device.status === 'online' ? '运行中' : device.status === 'connecting' ? '连接中' : '已停止'}`}
      >
        {/* 缩略图或图标 */}
        <div className="relative mx-auto mb-1.5">
          {isRunning ? (
            // 运行中：显示实时缩略图
            // Linux: 横屏 16:10，Android: 竖屏 9:20
            <div 
              className="w-full overflow-hidden rounded border border-nb-border bg-black relative"
              style={{ 
                aspectRatio: device.type === 'linux' ? '16/10' : '9/20'
              }}
            >
              {device.type === 'linux' ? (
                <VNCView isThumbnail />
              ) : (
                <ScrcpyView 
                  deviceSerial={device.serial} 
                  isThumbnail 
                  autoConnect={true}
                />
              )}
              {/* 状态指示点 */}
              <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-nb-surface bg-nb-success" />
            </div>
          ) : (
            // 未运行：显示图标，保持与运行时相同的宽高比
            <div 
              className={`
                w-full rounded-lg flex items-center justify-center relative
                ${device.type === 'linux' ? 'bg-blue-500/20' : 'bg-green-500/20'}
              `}
              style={{ 
                aspectRatio: device.type === 'linux' ? '16/10' : '9/20'
              }}
            >
              <Icon 
                size={24} 
                className={device.type === 'linux' ? 'text-blue-400' : 'text-green-400'} 
              />
              {/* 状态指示点 */}
              <span className={`
                absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-nb-surface
                ${device.status === 'connecting' ? 'bg-nb-warning animate-pulse' : 'bg-nb-text-secondary'}
              `} />
            </div>
          )}
        </div>
        
        {/* 名称 */}
        <div className="text-[10px] font-medium text-nb-text truncate text-center">
          {device.name}
        </div>
        
        {/* 状态文字 */}
        <div className="flex items-center justify-center gap-1 mt-1">
          <span className="text-[9px] text-nb-text-secondary">
            {device.status === 'online' ? '运行中' : 
             device.status === 'connecting' ? '连接中' : 
             '已停止'}
          </span>
        </div>
      </button>

      {/* 悬停操作按钮 */}
      {showActions && (
        <div className="absolute inset-0 bg-nb-surface/95 rounded-lg flex flex-col items-center justify-center gap-1.5 p-1.5">
          {device.status === 'online' ? (
            <>
              <button
                onClick={(e) => { e.stopPropagation(); onOpenDisplay?.(); }}
                className="w-full px-2 py-1 text-[9px] bg-nb-accent hover:bg-nb-accent/80 text-white rounded flex items-center justify-center gap-1"
                title="打开显示"
              >
                <ExternalLink size={10} />
                显示
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); onStop?.(); }}
                className="w-full px-2 py-1 text-[9px] bg-nb-error/80 hover:bg-nb-error text-white rounded flex items-center justify-center gap-1"
                title="停止"
              >
                <Square size={10} />
                停止
              </button>
            </>
          ) : device.status === 'connecting' ? (
            <span className="text-[9px] text-nb-text-secondary">连接中...</span>
          ) : (
            <button
              onClick={(e) => { e.stopPropagation(); onStart?.(); }}
              className="w-full px-2 py-1 text-[9px] bg-nb-success/80 hover:bg-nb-success text-white rounded flex items-center justify-center gap-1"
              title="启动"
            >
              <Play size={10} />
              启动
            </button>
          )}
          
          {/* 删除按钮 */}
          <button
            onClick={handleDelete}
            className={`w-full px-2 py-1 text-[9px] rounded flex items-center justify-center gap-1 ${
              showDeleteConfirm 
                ? 'bg-red-600 hover:bg-red-700 text-white' 
                : 'bg-nb-surface-2 hover:bg-nb-error/20 text-nb-text-secondary hover:text-nb-error'
            }`}
            title={showDeleteConfirm ? '确认删除' : '删除设备'}
          >
            <Trash2 size={10} />
            {showDeleteConfirm ? '确认?' : '删除'}
          </button>
        </div>
      )}
    </div>
  );
}

// 添加设备按钮组件
interface AddDeviceButtonProps {
  type: 'linux' | 'android';
  onClick: () => void;
}

function AddDeviceButton({ type, onClick }: AddDeviceButtonProps) {
  const Icon = type === 'linux' ? Monitor : Smartphone;
  const label = type === 'linux' ? '+ Linux VM' : '+ Android';
  const bgColor = type === 'linux' ? 'bg-blue-500/10 hover:bg-blue-500/20' : 'bg-green-500/10 hover:bg-green-500/20';
  const textColor = type === 'linux' ? 'text-blue-400' : 'text-green-400';
  
  return (
    <button
      onClick={onClick}
      className={`
        w-full p-3 rounded-lg border border-dashed border-nb-border 
        hover:border-nb-border-hover transition-all
        ${bgColor}
        flex flex-col items-center justify-center gap-1.5
      `}
    >
      <Icon size={18} className={textColor} />
      <span className={`text-[10px] font-medium ${textColor}`}>
        {label}
      </span>
    </button>
  );
}

// 设备显示弹窗组件
interface DeviceDisplayModalProps {
  device: DeviceInfo | null;
  onClose: () => void;
}

function DeviceDisplayModal({ device, onClose }: DeviceDisplayModalProps) {
  if (!device) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-nb-surface border border-nb-border rounded-xl shadow-2xl w-[90vw] h-[85vh] max-w-5xl flex flex-col overflow-hidden">
        {/* 标题栏 */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-nb-border bg-nb-surface-2">
          <div className="flex items-center gap-2">
            {device.type === 'linux' ? (
              <Monitor size={18} className="text-blue-400" />
            ) : (
              <Smartphone size={18} className="text-green-400" />
            )}
            <span className="text-sm font-medium text-nb-text">{device.name}</span>
            <span className={`
              px-2 py-0.5 text-[10px] rounded-full
              ${device.status === 'online' ? 'bg-nb-success/20 text-nb-success' : 'bg-nb-text-secondary/20 text-nb-text-secondary'}
            `}>
              {device.status === 'online' ? '运行中' : '已停止'}
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-nb-surface transition-colors text-nb-text-secondary hover:text-nb-text"
          >
            <X size={18} />
          </button>
        </div>
        
        {/* 内容区域 */}
        <div className="flex-1 overflow-hidden">
          {device.type === 'linux' ? (
            <VNCView />
          ) : (
            <ScrcpyView 
              deviceSerial={device.serial} 
              autoConnect={true}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export function DeviceSidebar({ className = '' }: DeviceSidebarProps) {
  const { currentAgentId, agents, loadAgents } = useAppStore();
  const [activeDevice, setActiveDevice] = useState<string | null>(null);
  const [displayDevice, setDisplayDevice] = useState<DeviceInfo | null>(null);
  
  // 设备状态
  const [vmStatus, setVmStatus] = useState<VmStatus | null>(null);
  const [androidDevices, setAndroidDevices] = useState<AndroidDevice[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  // Modal 状态
  const [showAddVMModal, setShowAddVMModal] = useState(false);
  const [showAddAndroidModal, setShowAddAndroidModal] = useState(false);
  
  // 获取当前 Agent
  const currentAgent = currentAgentId 
    ? agents.find(a => a.id === currentAgentId) 
    : null;
  
  // 判断设备配置
  const hasLinuxConfig = Boolean(currentAgent?.vm);
  // 检查是否有 Android 配置（托管模式检查 avd_name，外部模式检查 device_serial）
  const hasAndroidConfig = Boolean(currentAgent?.android?.avd_name || currentAgent?.android?.device_serial);
  
  // 获取 VM 状态
  const fetchVmStatus = useCallback(async () => {
    if (!currentAgentId || !hasLinuxConfig) {
      setVmStatus(null);
      return;
    }
    
    try {
      const status = await vmService.getStatus(currentAgentId);
      setVmStatus(status);
    } catch (error) {
      console.error('[DeviceSidebar] Failed to fetch VM status:', error);
      setVmStatus(null);
    }
  }, [currentAgentId, hasLinuxConfig]);
  
  // 获取 Android 设备状态
  const fetchAndroidStatus = useCallback(async () => {
    if (!hasAndroidConfig) {
      setAndroidDevices([]);
      return;
    }
    
    const deviceSerial = currentAgent?.android?.device_serial;
    
    // 如果有 device_serial，尝试获取状态
    if (deviceSerial) {
      try {
        const status = await androidService.getStatus(deviceSerial);
        setAndroidDevices([status]);
        return;
      } catch (error) {
        console.error('[DeviceSidebar] Failed to fetch Android status:', error);
      }
    }
    
    // 尝试获取所有设备列表
    try {
      const devices = await androidService.listDevices();
      if (deviceSerial) {
        const targetDevice = devices.find(d => d.serial === deviceSerial);
        if (targetDevice) {
          setAndroidDevices([targetDevice]);
          return;
        }
      }
      // 如果是托管模式但还没有 serial，显示空列表（设备未启动）
      setAndroidDevices([]);
    } catch {
      setAndroidDevices([]);
    }
  }, [hasAndroidConfig, currentAgent?.android?.device_serial]);
  
  // 定期轮询状态
  useEffect(() => {
    fetchVmStatus();
    fetchAndroidStatus();
    
    const interval = setInterval(() => {
      fetchVmStatus();
      fetchAndroidStatus();
    }, 5000);
    
    return () => clearInterval(interval);
  }, [fetchVmStatus, fetchAndroidStatus]);
  
  // 构建设备列表
  const devices: DeviceInfo[] = [];
  
  // Linux VM
  if (hasLinuxConfig) {
    const status: DeviceStatus = vmStatus?.running 
      ? 'online' 
      : isLoading 
        ? 'connecting' 
        : 'offline';
    
    devices.push({
      id: 'linux-vm',
      type: 'linux',
      name: 'Linux VM',
      status,
    });
  }
  
  // Android 设备
  if (hasAndroidConfig && currentAgent?.android) {
    const deviceSerial = currentAgent.android.device_serial;
    const androidDevice = deviceSerial ? androidDevices.find(d => d.serial === deviceSerial) : null;
    const status: DeviceStatus = androidDevice?.status === 'online' || androidDevice?.status === 'connected'
      ? 'online'
      : androidDevice?.status === 'booting'
        ? 'connecting'
        : 'offline';
    
    devices.push({
      id: 'android-avd',
      type: 'android',
      name: currentAgent.android.avd_name || 'Android',
      status,
      serial: deviceSerial,
    });
  }
  
  // 操作处理函数
  const handleStartLinux = async () => {
    if (!currentAgentId) return;
    setIsLoading(true);
    try {
      await vmService.start(currentAgentId);
      await fetchVmStatus();
    } catch (error) {
      console.error('[DeviceSidebar] Failed to start VM:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleStopLinux = async () => {
    if (!currentAgentId) return;
    setIsLoading(true);
    try {
      await vmService.stop(currentAgentId);
      await fetchVmStatus();
    } catch (error) {
      console.error('[DeviceSidebar] Failed to stop VM:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleStartAndroid = async () => {
    if (!currentAgentId || !currentAgent?.android?.avd_name) return;
    setIsLoading(true);
    try {
      const result = await androidService.startEmulator(currentAgent.android.avd_name);
      // 更新 Agent 配置中的 device_serial
      if (result.serial) {
        await api.updateAgent(currentAgentId, {
          android: {
            device_serial: result.serial,
            managed: currentAgent.android.managed ?? true,
            avd_name: currentAgent.android.avd_name,
          },
        });
        // 重新加载 agents 以更新状态
        await loadAgents();
      }
      await fetchAndroidStatus();
    } catch (error) {
      console.error('[DeviceSidebar] Failed to start Android:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleStopAndroid = async () => {
    if (!currentAgent?.android?.device_serial) return;
    setIsLoading(true);
    try {
      await androidService.stopEmulator(currentAgent.android.device_serial);
      await fetchAndroidStatus();
    } catch (error) {
      console.error('[DeviceSidebar] Failed to stop Android:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleOpenDisplay = (device: DeviceInfo) => {
    setDisplayDevice(device);
  };
  
  const handleAddLinux = () => {
    setShowAddVMModal(true);
  };
  
  const handleAddAndroid = () => {
    setShowAddAndroidModal(true);
  };
  
  const handleDeleteDevice = (device: DeviceInfo) => {
    // TODO: 实现删除设备逻辑
    console.log('[DeviceSidebar] Delete device:', device.id);
  };
  
  return (
    <>
      <div className={`w-40 bg-nb-surface border-l border-nb-border flex flex-col ${className}`}>
        {/* 标题 */}
        <div className="h-10 px-2 flex items-center justify-center border-b border-nb-border">
          <span className="text-[10px] font-medium text-nb-text-muted">设备</span>
        </div>
        
        {/* 设备列表 */}
        <div className="flex-1 p-2 space-y-2 overflow-y-auto">
          {/* Linux VM 区域 */}
          {hasLinuxConfig ? (
            devices
              .filter(d => d.type === 'linux')
              .map(device => (
                <DeviceCard
                  key={device.id}
                  device={device}
                  isActive={activeDevice === device.id}
                  onClick={() => setActiveDevice(activeDevice === device.id ? null : device.id)}
                  onStart={handleStartLinux}
                  onStop={handleStopLinux}
                  onOpenDisplay={() => handleOpenDisplay(device)}
                  onDelete={() => handleDeleteDevice(device)}
                />
              ))
          ) : (
            <AddDeviceButton type="linux" onClick={handleAddLinux} />
          )}
          
          {/* 分隔线 */}
          <div className="border-t border-nb-border my-2" />
          
          {/* Android 区域 */}
          {hasAndroidConfig ? (
            devices
              .filter(d => d.type === 'android')
              .map(device => (
                <DeviceCard
                  key={device.id}
                  device={device}
                  isActive={activeDevice === device.id}
                  onClick={() => setActiveDevice(activeDevice === device.id ? null : device.id)}
                  onStart={handleStartAndroid}
                  onStop={handleStopAndroid}
                  onOpenDisplay={() => handleOpenDisplay(device)}
                  onDelete={() => handleDeleteDevice(device)}
                />
              ))
          ) : (
            <AddDeviceButton type="android" onClick={handleAddAndroid} />
          )}
        </div>
        
        {/* 底部添加按钮 */}
        <div className="p-2 border-t border-nb-border">
          <button
            className="w-full p-2 rounded-lg border border-dashed border-nb-border text-nb-text-secondary hover:text-nb-text hover:border-nb-border-hover hover:bg-nb-surface-2 transition-colors"
            title="添加设备"
            onClick={() => {
              // 根据当前缺少的设备类型决定添加哪种
              if (!hasLinuxConfig) {
                handleAddLinux();
              } else if (!hasAndroidConfig) {
                handleAddAndroid();
              }
            }}
          >
            <Plus size={14} className="mx-auto" />
          </button>
        </div>
      </div>
      
      {/* 设备显示弹窗 */}
      <DeviceDisplayModal 
        device={displayDevice} 
        onClose={() => setDisplayDevice(null)} 
      />
      
      {/* 添加 Linux VM 弹窗 */}
      <AddLinuxVMModal
        isOpen={showAddVMModal}
        onClose={() => setShowAddVMModal(false)}
        onCreated={() => {
          // 刷新 VM 状态
          fetchVmStatus();
        }}
      />
      
      {/* 添加 Android 弹窗 */}
      <AddAndroidModal
        isOpen={showAddAndroidModal}
        onClose={() => setShowAddAndroidModal(false)}
        onCreated={() => {
          // 刷新 Android 状态
          fetchAndroidStatus();
        }}
      />
    </>
  );
}
