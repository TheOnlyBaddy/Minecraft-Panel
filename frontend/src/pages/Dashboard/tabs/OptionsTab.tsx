import React from 'react';

interface OptionsTabProps {
  config: Record<string, any>;
  isLoadingConfig: boolean;
  isSavingConfig: boolean;
  handleConfigChange: (key: string, value: any) => void;
  handleSaveConfig: (e: React.FormEvent) => void;
  isModerator: boolean;
}

const OptionsTab: React.FC<OptionsTabProps> = ({
  config,
  isLoadingConfig,
  isSavingConfig,
  handleConfigChange,
  handleSaveConfig,
  isModerator,
}) => {
  if (isLoadingConfig) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="w-8 h-8 border-2 border-white/20 border-t-mc-emerald rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <form onSubmit={handleSaveConfig} className="space-y-6">
      {/* server.properties */}
      <div className="bg-bg-secondary border border-white/5 p-6 shadow-mc-sm">
        <h3 className="font-pixel text-sm text-mc-emerald mb-4 tracking-wide">server.properties</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          
          {/* Slots */}
          <div className="bg-bg-surface border border-white/5 p-4 flex flex-col justify-between">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-mono uppercase tracking-wider text-text-secondary">Slots</span>
              <input
                type="number"
                min="1"
                max="1000"
                value={config['max-players'] ?? ''}
                onChange={(e) => handleConfigChange('max-players', parseInt(e.target.value) || 1)}
                disabled={isModerator}
                className="w-20 px-2 py-1 bg-bg-elevated border border-white/10 text-white font-mono text-center focus:outline-none focus:border-mc-emerald"
              />
            </div>
            <span className="text-[10px] font-mono text-text-muted">max-players={config['max-players']}</span>
          </div>

          {/* Gamemode */}
          <div className="bg-bg-surface border border-white/5 p-4 flex flex-col justify-between">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-mono uppercase tracking-wider text-text-secondary">Gamemode</span>
              <select
                value={config['gamemode'] || 'survival'}
                onChange={(e) => handleConfigChange('gamemode', e.target.value)}
                disabled={isModerator}
                className="w-32 px-2 py-1 bg-bg-elevated border border-white/10 text-white font-mono focus:outline-none focus:border-mc-emerald"
              >
                <option value="survival">Survival</option>
                <option value="creative">Creative</option>
                <option value="adventure">Adventure</option>
                <option value="spectator">Spectator</option>
              </select>
            </div>
            <span className="text-[10px] font-mono text-text-muted">gamemode={config['gamemode']}</span>
          </div>

          {/* Difficulty */}
          <div className="bg-bg-surface border border-white/5 p-4 flex flex-col justify-between">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-mono uppercase tracking-wider text-text-secondary">Difficulty</span>
              <select
                value={config['difficulty'] || 'normal'}
                onChange={(e) => handleConfigChange('difficulty', e.target.value)}
                disabled={isModerator}
                className="w-32 px-2 py-1 bg-bg-elevated border border-white/10 text-white font-mono focus:outline-none focus:border-mc-emerald"
              >
                <option value="peaceful">Peaceful</option>
                <option value="easy">Easy</option>
                <option value="normal">Normal</option>
                <option value="hard">Hard</option>
              </select>
            </div>
            <span className="text-[10px] font-mono text-text-muted">difficulty={config['difficulty']}</span>
          </div>

          {/* Whitelist */}
          <div className="bg-bg-surface border border-white/5 p-4 flex flex-col justify-between">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-mono uppercase tracking-wider text-text-secondary">Whitelist</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={!!config['white-list']}
                  onChange={(e) => handleConfigChange('white-list', e.target.checked)}
                  disabled={isModerator}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-bg-elevated peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-text-muted after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-mc-emerald peer-checked:after:bg-bg-primary"></div>
              </label>
            </div>
            <span className="text-[10px] font-mono text-text-muted">white-list={String(config['white-list'])}</span>
          </div>

          {/* Cracked (Online Mode Inverted) */}
          <div className="bg-bg-surface border border-white/5 p-4 flex flex-col justify-between">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-mono uppercase tracking-wider text-text-secondary">Cracked</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={!config['online-mode']}
                  onChange={(e) => handleConfigChange('online-mode', !e.target.checked)}
                  disabled={isModerator}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-bg-elevated peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-text-muted after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-mc-emerald peer-checked:after:bg-bg-primary"></div>
              </label>
            </div>
            <span className="text-[10px] font-mono text-text-muted">online-mode={String(config['online-mode'])}</span>
          </div>

          {/* Allow Flight */}
          <div className="bg-bg-surface border border-white/5 p-4 flex flex-col justify-between">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-mono uppercase tracking-wider text-text-secondary">Allow Flight</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={!!config['allow-flight']}
                  onChange={(e) => handleConfigChange('allow-flight', e.target.checked)}
                  disabled={isModerator}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-bg-elevated peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-text-muted after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-mc-emerald peer-checked:after:bg-bg-primary"></div>
              </label>
            </div>
            <span className="text-[10px] font-mono text-text-muted">allow-flight={String(config['allow-flight'])}</span>
          </div>

        </div>
      </div>

      {/* Additional Settings */}
      <div className="bg-bg-secondary border border-white/5 p-6 shadow-mc-sm">
        <h3 className="font-pixel text-sm text-mc-emerald mb-4 tracking-wide">Additional Settings & Rules</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          
          {/* PVP */}
          <div className="bg-bg-surface border border-white/5 p-4 flex flex-col justify-between">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-mono uppercase tracking-wider text-text-secondary">PVP Enabled</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={!!config['pvp']}
                  onChange={(e) => handleConfigChange('pvp', e.target.checked)}
                  disabled={isModerator}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-bg-elevated peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-text-muted after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-mc-emerald peer-checked:after:bg-bg-primary"></div>
              </label>
            </div>
            <span className="text-[10px] font-mono text-text-muted">pvp={String(config['pvp'])}</span>
          </div>

          {/* Spawn Monsters */}
          <div className="bg-bg-surface border border-white/5 p-4 flex flex-col justify-between">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-mono uppercase tracking-wider text-text-secondary">Spawn Monsters</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={!!config['spawn-monsters']}
                  onChange={(e) => handleConfigChange('spawn-monsters', e.target.checked)}
                  disabled={isModerator}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-bg-elevated peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-text-muted after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-mc-emerald peer-checked:after:bg-bg-primary"></div>
              </label>
            </div>
            <span className="text-[10px] font-mono text-text-muted">spawn-monsters={String(config['spawn-monsters'])}</span>
          </div>

          {/* Spawn Animals */}
          <div className="bg-bg-surface border border-white/5 p-4 flex flex-col justify-between">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-mono uppercase tracking-wider text-text-secondary">Spawn Animals</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={!!config['spawn-animals']}
                  onChange={(e) => handleConfigChange('spawn-animals', e.target.checked)}
                  disabled={isModerator}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-bg-elevated peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-text-muted after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-mc-emerald peer-checked:after:bg-bg-primary"></div>
              </label>
            </div>
            <span className="text-[10px] font-mono text-text-muted">spawn-animals={String(config['spawn-animals'])}</span>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end pt-4">
        <button
          type="submit"
          disabled={isSavingConfig || isModerator}
          className="px-6 py-2.5 bg-gradient-to-r from-mc-emerald to-emerald-700 hover:to-mc-emerald text-bg-primary font-pixel font-bold tracking-wider text-xs shadow-mc-sm border border-mc-emerald/30 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-[0_0_12px_rgba(46,204,113,0.3)] transition-all"
        >
          {isSavingConfig ? 'Saving Settings...' : 'Save Configuration'}
        </button>
      </div>
    </form>
  );
};

export default OptionsTab;
