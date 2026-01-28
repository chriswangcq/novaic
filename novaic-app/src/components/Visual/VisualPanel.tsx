import { VNCView } from './VNCView';
import { useAppStore } from '../../store';

interface VisualPanelProps {
  isThumbnail?: boolean;
}

export function VisualPanel({ isThumbnail = false }: VisualPanelProps) {
  const { setLayoutMode } = useAppStore();

  // Thumbnail mode: just show VNC, click to expand
  if (isThumbnail) {
    return (
      <div 
        className="h-full w-full cursor-pointer"
        onClick={() => setLayoutMode('normal')}
      >
        <VNCView isThumbnail />
      </div>
    );
  }

  // Full mode or normal mode: just show VNC (no tabs)
  return (
    <div className="flex flex-col h-full">
      <VNCView />
    </div>
  );
}

