/**
 * Create Agent Modal
 * 
 * Modal dialog for creating a new AIC agent with VM configuration.
 * Includes environment check step before showing configuration.
 * Only collects configuration - actual setup happens in SetupWorkspace.
 */

import { useState, useEffect } from 'react';
import { X, Loader2, HardDrive, Cpu, MemoryStick, ChevronRight, Bot } from 'lucide-react';
import { useAppStore } from '../../store';
import { api } from '../../services';
import { EnvironmentCheck } from '../Setup';
import type { AvailableImage, AICAgent, CandidateModel } from '../../services/api';

// Setup config returned when agent is created
export interface SetupConfig {
  agent: AICAgent;
  sourceImage: string;
  useCnMirrors: boolean;
}

interface CreateAgentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated?: (config: SetupConfig) => void;  // Called when agent is created with setup config
}

// Modal steps
type ModalStep = 'environment' | 'configure';

// OS options
const OS_OPTIONS = [
  { type: 'ubuntu', versions: ['24.04', '22.04', '20.04'] },
  { type: 'debian', versions: ['12', '11'] },
];

// Backend options
const BACKEND_OPTIONS = [
  { id: 'qemu', name: 'QEMU', description: 'Cross-platform virtualization' },
  // { id: 'virtualization_framework', name: 'Apple Virtualization', description: 'Native macOS (coming soon)' },
];

// Memory options (MB)
const MEMORY_OPTIONS = [
  { value: '2048', label: '2 GB' },
  { value: '4096', label: '4 GB' },
  { value: '8192', label: '8 GB' },
  { value: '16384', label: '16 GB' },
];

// CPU options
const CPU_OPTIONS = [2, 4, 6, 8];

export function CreateAgentModal({ isOpen, onClose, onCreated }: CreateAgentModalProps) {
  const { createAgent, loadAgents } = useAppStore();
  
  // Step state
  const [step, setStep] = useState<ModalStep>('environment');
  
  // Form state
  const [name, setName] = useState('');
  const [backend, setBackend] = useState('qemu');
  const [osType, setOsType] = useState('ubuntu');
  const [osVersion, setOsVersion] = useState('24.04');
  const [memory, setMemory] = useState('4096');
  const [cpus, setCpus] = useState(4);
  const [sourceImage, setSourceImage] = useState('');
  const [useCnMirrors, setUseCnMirrors] = useState(false);
  
  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [availableImages, setAvailableImages] = useState<AvailableImage[]>([]);
  const [error, setError] = useState('');
  
  // Model selection state
  const [availableModels, setAvailableModels] = useState<CandidateModel[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>('');
  const [isLoadingModels, setIsLoadingModels] = useState(false);

  // Auto-detect locale for mirror selection
  useEffect(() => {
    const locale = navigator.language || '';
    if (locale.startsWith('zh')) {
      setUseCnMirrors(true);
    }
  }, []);

  // Load available images when entering configure step
  useEffect(() => {
    if (isOpen && step === 'configure') {
      loadImages();
    }
  }, [isOpen, step]);

  // Load available models when modal opens
  useEffect(() => {
    if (isOpen) {
      loadAvailableModels();
    }
  }, [isOpen]);

  const loadAvailableModels = async () => {
    setIsLoadingModels(true);
    try {
      const models = await api.listAvailableModels();
      setAvailableModels(models);
      // Auto-select first model if available
      if (models.length > 0 && !selectedModelId) {
        const firstModel = models[0];
        setSelectedModelId(`${firstModel.api_key_id}:${firstModel.id}`);
      }
    } catch (error) {
      console.error('Failed to load models:', error);
    } finally {
      setIsLoadingModels(false);
    }
  };

  const loadImages = async () => {
    try {
      const images = await api.getAvailableImages();
      setAvailableImages(images);
      // Auto-select first image if available
      if (images.length > 0 && !sourceImage) {
        setSourceImage(images[0].path);
      }
    } catch (error) {
      console.error('Failed to load images:', error);
    }
  };

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setStep('environment');  // Always start with environment check
      setName('');
      setBackend('qemu');
      setOsType('ubuntu');
      setOsVersion('24.04');
      setMemory('4096');
      setCpus(4);
      setError('');
      setSelectedModelId('');  // Reset model selection
    }
  }, [isOpen]);

  // Handle environment check passed
  const handleEnvironmentReady = () => {
    setStep('configure');
  };

  // Get available versions for selected OS
  const availableVersions = OS_OPTIONS.find(os => os.type === osType)?.versions || [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name.trim()) {
      setError('Agent name is required');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // Create agent with pending status
      const agent = await createAgent({
        name: name.trim(),
        backend,
        os_type: osType,
        os_version: osVersion,
        memory,
        cpus,
        source_image: sourceImage || undefined,
      });
      
      // Set model for the new agent
      if (selectedModelId) {
        try {
          await api.setAgentModel(agent.id, selectedModelId);
          console.log('[CreateAgentModal] Set model for agent:', agent.id, selectedModelId);
        } catch (modelError) {
          console.warn('[CreateAgentModal] Failed to set model, continuing:', modelError);
          // Don't fail the whole creation if model setting fails
        }
      }
      
      await loadAgents();
      
      // Call onCreated with setup config (triggers setup flow)
      if (onCreated) {
        onCreated({
          agent,
          sourceImage: sourceImage || '',
          useCnMirrors,
        });
      }
      
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create agent');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  // Get modal title based on step
  const getModalTitle = () => {
    switch (step) {
      case 'environment':
        return 'Create New Agent';
      case 'configure':
        return 'Configure Agent';
      default:
        return 'Create New Agent';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-nb-surface border border-nb-border rounded-xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-nb-border">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-nb-text">{getModalTitle()}</h2>
            {/* Step indicator */}
            <div className="flex items-center gap-1 ml-3">
              <div className={`w-2 h-2 rounded-full ${step === 'environment' ? 'bg-blue-500' : 'bg-green-500'}`} />
              <ChevronRight size={14} className="text-nb-text-secondary" />
              <div className={`w-2 h-2 rounded-full ${step === 'configure' ? 'bg-blue-500' : 'bg-nb-border'}`} />
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md hover:bg-nb-hover text-nb-text-secondary hover:text-nb-text transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Step: Environment Check */}
        {step === 'environment' && (
          <EnvironmentCheck 
            onReady={handleEnvironmentReady}
            onBack={onClose}
          />
        )}

        {/* Step: Configure */}
        {step === 'configure' && (
          <>
        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5 overflow-y-auto max-h-[calc(90vh-140px)]">
          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          {/* Agent Name */}
          <div>
            <label className="block text-sm font-medium text-nb-text mb-2">
              Agent Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My Agent"
              className="w-full px-3 py-2 bg-nb-bg border border-nb-border rounded-lg text-nb-text placeholder-nb-text-secondary focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Model Selection */}
          <div>
            <label className="block text-sm font-medium text-nb-text mb-2">
              <Bot size={14} className="inline mr-1" />
              Default Model
            </label>
            <select
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
              disabled={isLoadingModels}
              className="w-full px-3 py-2 bg-nb-bg border border-nb-border rounded-lg text-nb-text focus:outline-none focus:border-blue-500 disabled:opacity-50"
            >
              {isLoadingModels ? (
                <option value="">Loading models...</option>
              ) : availableModels.length === 0 ? (
                <option value="">No models available</option>
              ) : (
                <>
                  <option value="">Select a model...</option>
                  {availableModels.map(model => (
                    <option key={`${model.api_key_id}:${model.id}`} value={`${model.api_key_id}:${model.id}`}>
                      {model.name} ({model.api_key_name})
                    </option>
                  ))}
                </>
              )}
            </select>
            {availableModels.length === 0 && !isLoadingModels && (
              <p className="mt-1 text-xs text-amber-400">
                Configure API keys in Settings to enable models
              </p>
            )}
          </div>

          {/* Backend */}
          <div>
            <label className="block text-sm font-medium text-nb-text mb-2">
              Virtualization Backend
            </label>
            <div className="grid grid-cols-1 gap-2">
              {BACKEND_OPTIONS.map(opt => (
                <label
                  key={opt.id}
                  className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                    backend === opt.id 
                      ? 'border-blue-500 bg-blue-500/10' 
                      : 'border-nb-border hover:border-nb-border-light'
                  }`}
                >
                  <input
                    type="radio"
                    name="backend"
                    value={opt.id}
                    checked={backend === opt.id}
                    onChange={(e) => setBackend(e.target.value)}
                    className="sr-only"
                  />
                  <div>
                    <div className="text-sm font-medium text-nb-text">{opt.name}</div>
                    <div className="text-xs text-nb-text-secondary">{opt.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* OS Type & Version */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-nb-text mb-2">
                Operating System
              </label>
              <select
                value={osType}
                onChange={(e) => {
                  setOsType(e.target.value);
                  const versions = OS_OPTIONS.find(os => os.type === e.target.value)?.versions || [];
                  setOsVersion(versions[0] || '');
                }}
                className="w-full px-3 py-2 bg-nb-bg border border-nb-border rounded-lg text-nb-text focus:outline-none focus:border-blue-500"
              >
                {OS_OPTIONS.map(os => (
                  <option key={os.type} value={os.type}>
                    {os.type.charAt(0).toUpperCase() + os.type.slice(1)}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-nb-text mb-2">
                Version
              </label>
              <select
                value={osVersion}
                onChange={(e) => setOsVersion(e.target.value)}
                className="w-full px-3 py-2 bg-nb-bg border border-nb-border rounded-lg text-nb-text focus:outline-none focus:border-blue-500"
              >
                {availableVersions.map(ver => (
                  <option key={ver} value={ver}>{ver}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Source Image */}
          {availableImages.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-nb-text mb-2">
                <HardDrive size={14} className="inline mr-1" />
                Base Image
              </label>
              <select
                value={sourceImage}
                onChange={(e) => setSourceImage(e.target.value)}
                className="w-full px-3 py-2 bg-nb-bg border border-nb-border rounded-lg text-nb-text focus:outline-none focus:border-blue-500"
              >
                <option value="">Create new (requires ISO download)</option>
                {availableImages.map(img => (
                  <option key={img.path} value={img.path}>
                    {img.name} ({(img.size / 1024 / 1024 / 1024).toFixed(1)} GB)
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-nb-text-secondary">
                Clone from existing image for faster setup
              </p>
            </div>
          )}

          {/* Memory & CPU */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-nb-text mb-2">
                <MemoryStick size={14} className="inline mr-1" />
                Memory
              </label>
              <select
                value={memory}
                onChange={(e) => setMemory(e.target.value)}
                className="w-full px-3 py-2 bg-nb-bg border border-nb-border rounded-lg text-nb-text focus:outline-none focus:border-blue-500"
              >
                {MEMORY_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-nb-text mb-2">
                <Cpu size={14} className="inline mr-1" />
                CPU Cores
              </label>
              <select
                value={cpus}
                onChange={(e) => setCpus(Number(e.target.value))}
                className="w-full px-3 py-2 bg-nb-bg border border-nb-border rounded-lg text-nb-text focus:outline-none focus:border-blue-500"
              >
                {CPU_OPTIONS.map(n => (
                  <option key={n} value={n}>{n} cores</option>
                ))}
              </select>
            </div>
          </div>

          {/* Mirror Selection */}
          <div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={useCnMirrors}
                onChange={(e) => setUseCnMirrors(e.target.checked)}
                className="w-4 h-4 rounded border-nb-border"
              />
              <span className="text-sm text-nb-text">Use China mirrors (faster for users in China)</span>
            </label>
          </div>
        </form>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-nb-border">
          <button
            type="button"
            onClick={() => setStep('environment')}
            className="px-4 py-2 text-sm text-nb-text-secondary hover:text-nb-text transition-colors"
          >
            Back
          </button>
          <button
            onClick={handleSubmit}
            disabled={isLoading || !name.trim()}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50 text-white text-sm font-medium rounded-lg transition-colors"
          >
            {isLoading && <Loader2 size={16} className="animate-spin" />}
            Create Agent
          </button>
        </div>
          </>
        )}
      </div>
    </div>
  );
}
