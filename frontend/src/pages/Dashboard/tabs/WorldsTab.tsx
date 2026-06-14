import React from 'react';
import { Globe, Download, ShieldAlert, Trash2 } from 'lucide-react';

interface WorldsTabProps {
  worldStats: any;
  isLoadingWorldStats: boolean;
  isResettingWorld: boolean;
  handleDownloadWorld: () => void;
  handleResetWorld: () => void;
  formatMB: (bytes: number) => string;
}

const WorldsTab: React.FC<WorldsTabProps> = ({
  worldStats,
  isLoadingWorldStats,
  isResettingWorld,
  handleDownloadWorld,
  handleResetWorld,
  formatMB,
}) => {
  if (isLoadingWorldStats) {
    return (
      <div className="flex items-center justify-center py-16 bg-bg-secondary border border-white/5 shadow-mc-sm">
        <div className="w-8 h-8 border-2 border-white/20 border-t-mc-emerald rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="bg-bg-secondary border border-white/5 p-6 shadow-mc-sm font-sans select-none space-y-6">
      <h3 className="font-pixel text-sm text-mc-emerald tracking-wide">Minecraft Worlds</h3>
      
      {worldStats ? (
        <div className="space-y-6 mt-4">
          {/* Dimension Grid Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            
            {/* Active World */}
            <div className="bg-bg-surface border border-white/5 p-5 shadow-mc-sm">
              <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">Active World Name</span>
              <div className="text-xl font-bold font-pixel text-mc-emerald mt-2 drop-shadow-[0_1px_0_rgba(0,0,0,0.5)]">
                {worldStats.level_name}
              </div>
            </div>

            {/* Overworld Size */}
            <div className="bg-bg-surface border border-white/5 p-5 shadow-mc-sm">
              <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">Overworld Size</span>
              <div className="text-xl font-bold font-mono text-white mt-2">
                {formatMB(worldStats.world_size)}
              </div>
            </div>

            {/* Nether Size */}
            <div className="bg-bg-surface border border-white/5 p-5 shadow-mc-sm">
              <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">Nether Size</span>
              <div className="text-xl font-bold font-mono text-white mt-2">
                {formatMB(worldStats.nether_size)}
              </div>
            </div>

            {/* End Size */}
            <div className="bg-bg-surface border border-white/5 p-5 shadow-mc-sm">
              <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">The End Size</span>
              <div className="text-xl font-bold font-mono text-white mt-2">
                {formatMB(worldStats.end_size)}
              </div>
            </div>

          </div>

          {/* Footprint total size & Download */}
          <div className="bg-bg-surface border border-white/5 p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 shadow-mc-sm">
            <div>
              <h4 className="text-xs font-pixel uppercase tracking-wider text-white">Total World Disk Footprint</h4>
              <p className="text-xs text-text-secondary mt-1">
                Combined storage size of all dimensions: <strong className="text-mc-emerald font-mono">{formatMB(worldStats.total_size)}</strong>
              </p>
            </div>
            
            <button 
              onClick={handleDownloadWorld} 
              className="px-5 py-2.5 bg-gradient-to-r from-mc-emerald to-emerald-700 hover:to-mc-emerald text-bg-primary font-pixel font-bold text-xs tracking-wider border border-mc-emerald/30 cursor-pointer shadow-mc-sm hover:shadow-[0_0_10px_rgba(46,204,113,0.3)] transition-all flex items-center gap-2 shrink-0 w-full sm:w-auto justify-center"
            >
              <Download className="w-4 h-4 fill-bg-primary" />
              Download World (ZIP)
            </button>
          </div>

          {/* Danger Zone: Reset Worlds */}
          <div className="border border-status-error/30 bg-status-error/5 p-6 shadow-mc-sm">
            <h4 className="text-xs font-pixel uppercase tracking-wide text-status-error flex items-center gap-2">
              <ShieldAlert className="w-4 h-4" />
              Danger Zone: Reset Worlds
            </h4>
            <p className="text-xs text-text-secondary mt-2 leading-relaxed font-sans">
              Resetting worlds deletes all world files recursively from the storage disk and stops the server if it is active. This action is irreversible and permanent. On next server boot, fresh world folders will be generated.
            </p>
            <button
              onClick={handleResetWorld}
              disabled={isResettingWorld}
              className="mt-4 px-5 py-2.5 bg-gradient-to-r from-status-error to-red-800 hover:to-status-error text-white font-pixel font-bold text-xs tracking-wider border border-status-error/30 cursor-pointer hover:shadow-[0_0_10px_rgba(255,93,93,0.2)] transition-all flex items-center gap-2"
            >
              <Trash2 className="w-4 h-4" />
              {isResettingWorld ? 'Resetting worlds...' : 'Reset Minecraft Worlds'}
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center p-12 bg-bg-surface/50 border border-white/5 text-center space-y-3">
          <Globe className="w-8 h-8 text-text-muted" />
          <span className="text-text-secondary text-xs font-mono">Failed to retrieve world storage metrics from API.</span>
        </div>
      )}
      
    </div>
  );
};

export default WorldsTab;
