import { Sparkles, Terminal, Globe, FileCode } from 'lucide-react';

export function WelcomeScreen() {
  return (
    <div className="h-full flex flex-col items-center justify-center px-8 py-12">
      {/* Logo */}
      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-violet-600 flex items-center justify-center mb-6 shadow-lg shadow-violet-500/20">
        <Sparkles size={24} className="text-white" />
      </div>
      
      <h2 className="text-lg font-semibold text-white mb-2">
        What can I help you with?
      </h2>
      <p className="text-sm text-white/50 text-center max-w-sm mb-8">
        I can execute code, automate tasks, and control the browser in a secure VM.
      </p>

      {/* Quick actions */}
      <div className="w-full max-w-md space-y-2">
        <QuickAction
          icon={<Terminal size={16} />}
          title="Run shell commands"
          description="Execute any shell command in the VM"
        />
        <QuickAction
          icon={<FileCode size={16} />}
          title="Write & run code"
          description="Create and execute Python scripts"
        />
        <QuickAction
          icon={<Globe size={16} />}
          title="Browser automation"
          description="Navigate, click, and extract data from websites"
        />
      </div>
    </div>
  );
}

function QuickAction({ icon, title, description }: { 
  icon: React.ReactNode; 
  title: string; 
  description: string; 
}) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.06] hover:bg-white/[0.04] transition-colors cursor-pointer group">
      <div className="w-8 h-8 rounded-lg bg-white/[0.06] flex items-center justify-center text-white/60 group-hover:text-violet-400 transition-colors">
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-white/90">{title}</div>
        <div className="text-xs text-white/40">{description}</div>
      </div>
    </div>
  );
}

