/**
 * Setup Progress Component
 * 
 * Displays the progress of VM setup and deployment:
 * - Download progress with speed
 * - Stage indicators
 * - Progress messages
 * - Real-time cloud-init logs during deployment
 */

import { useState, useEffect, useRef } from 'react';
import { Download, HardDrive, Upload, CheckCircle, Loader2, Terminal } from 'lucide-react';
import type { DownloadProgress, SetupProgress as SetupProgressType, DeployProgress } from '../../services/setup';

interface SetupProgressProps {
  step: 'checking' | 'downloading' | 'creating' | 'deploying';
  downloadProgress: DownloadProgress | null;
  setupProgress: SetupProgressType | null;
  deployProgress: DeployProgress | null;
}

// Step definitions
const STEPS = [
  { id: 'download', label: 'Download Image', icon: Download },
  { id: 'create', label: 'Create VM', icon: HardDrive },
  { id: 'deploy', label: 'Deploy Code', icon: Upload },
];

export function SetupProgress({ step, downloadProgress, setupProgress, deployProgress }: SetupProgressProps) {
  // Log lines for real-time display
  const [logLines, setLogLines] = useState<string[]>([]);
  const logContainerRef = useRef<HTMLDivElement>(null);

  // Collect log lines from deployProgress
  useEffect(() => {
    if (deployProgress?.log_line) {
      setLogLines(prev => {
        const newLines = [...prev, deployProgress.log_line!];
        // Keep last 100 lines
        return newLines.slice(-100);
      });
    }
  }, [deployProgress?.log_line]);

  // Reset logs when step changes away from deploying
  useEffect(() => {
    if (step !== 'deploying') {
      setLogLines([]);
    }
  }, [step]);

  // Auto-scroll log container
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logLines]);

  // Determine current step index
  const currentStepIndex = 
    step === 'checking' || step === 'downloading' ? 0 :
    step === 'creating' ? 1 :
    step === 'deploying' ? 2 : -1;

  // Format file size
  const formatSize = (bytes: number): string => {
    if (bytes >= 1_000_000_000) {
      return `${(bytes / 1_000_000_000).toFixed(2)} GB`;
    } else if (bytes >= 1_000_000) {
      return `${(bytes / 1_000_000).toFixed(1)} MB`;
    } else if (bytes >= 1_000) {
      return `${(bytes / 1_000).toFixed(1)} KB`;
    }
    return `${bytes} B`;
  };

  // Get current message
  const getCurrentMessage = () => {
    if (step === 'checking') {
      return 'Checking for existing image...';
    }
    if (step === 'downloading' && downloadProgress) {
      return `Downloading: ${formatSize(downloadProgress.downloaded)} / ${formatSize(downloadProgress.total)}`;
    }
    if (step === 'creating' && setupProgress) {
      return setupProgress.message;
    }
    if (step === 'deploying' && deployProgress) {
      return deployProgress.message;
    }
    return 'Preparing...';
  };

  // Get current progress percentage
  const getCurrentProgress = () => {
    if (step === 'checking') return 0;
    if (step === 'downloading' && downloadProgress) return downloadProgress.percent;
    if (step === 'creating' && setupProgress) return setupProgress.progress;
    if (step === 'deploying' && deployProgress) return deployProgress.progress;
    return 0;
  };

  return (
    <div className="max-w-lg mx-auto w-full">
      <h2 className="text-xl font-semibold text-nb-text text-center mb-8">
        Setting up your AI Computer
      </h2>

      {/* Step indicators */}
      <div className="flex items-center justify-between mb-8">
        {STEPS.map((s, index) => {
          const Icon = s.icon;
          const isActive = index === currentStepIndex;
          const isComplete = index < currentStepIndex;

          return (
            <div key={s.id} className="flex flex-col items-center flex-1">
              <div className="flex items-center w-full">
                {/* Line before */}
                {index > 0 && (
                  <div className={`flex-1 h-0.5 ${isComplete || isActive ? 'bg-blue-500' : 'bg-nb-border'}`} />
                )}
                
                {/* Icon */}
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    isComplete ? 'bg-blue-500' :
                    isActive ? 'bg-blue-500/20 border-2 border-blue-500' :
                    'bg-nb-surface border-2 border-nb-border'
                  }`}
                >
                  {isComplete ? (
                    <CheckCircle size={20} className="text-white" />
                  ) : isActive ? (
                    <Loader2 size={20} className="text-blue-500 animate-spin" />
                  ) : (
                    <Icon size={20} className="text-nb-text-secondary" />
                  )}
                </div>

                {/* Line after */}
                {index < STEPS.length - 1 && (
                  <div className={`flex-1 h-0.5 ${isComplete ? 'bg-blue-500' : 'bg-nb-border'}`} />
                )}
              </div>
              
              {/* Label */}
              <span className={`mt-2 text-xs ${
                isActive ? 'text-blue-500 font-medium' :
                isComplete ? 'text-nb-text' :
                'text-nb-text-secondary'
              }`}>
                {s.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="h-2 bg-nb-surface rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${getCurrentProgress()}%` }}
          />
        </div>
      </div>

      {/* Current status */}
      <div className="text-center">
        <p className="text-nb-text-secondary text-sm">
          {getCurrentMessage()}
        </p>
        
        {/* Download speed */}
        {step === 'downloading' && downloadProgress && (
          <p className="text-blue-500 text-sm mt-1">
            {downloadProgress.speed}
          </p>
        )}

        {/* Stage info */}
        {step === 'creating' && setupProgress && (
          <p className="text-blue-500 text-sm mt-1">
            {setupProgress.stage}
          </p>
        )}
        {step === 'deploying' && deployProgress && (
          <p className="text-blue-500 text-sm mt-1">
            {deployProgress.stage}
          </p>
        )}
      </div>

      {/* Real-time logs during deployment */}
      {step === 'deploying' && logLines.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center gap-2 mb-2">
            <Terminal size={14} className="text-nb-text-secondary" />
            <span className="text-xs text-nb-text-secondary">Installation Log</span>
          </div>
          <div 
            ref={logContainerRef}
            className="bg-black/50 rounded-lg p-3 h-40 overflow-y-auto font-mono text-xs"
          >
            {logLines.map((line, i) => (
              <div key={i} className="text-green-400/80 leading-relaxed">
                {line}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tips */}
      <div className="mt-8 p-4 bg-nb-surface rounded-lg">
        <p className="text-xs text-nb-text-secondary text-center">
          {step === 'downloading' ? (
            'Downloading Ubuntu cloud image. This may take a few minutes depending on your internet speed.'
          ) : step === 'creating' ? (
            'Creating the virtual machine disk and configuration. This usually takes about 1-2 minutes.'
          ) : step === 'deploying' ? (
            'Installing packages and starting services. This may take 10-30 minutes on first boot.'
          ) : (
            'Please wait while we set up your AI Computer...'
          )}
        </p>
      </div>
    </div>
  );
}
