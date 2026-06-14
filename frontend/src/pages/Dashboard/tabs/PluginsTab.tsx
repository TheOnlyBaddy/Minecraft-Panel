import React from 'react';
import { Layers, FolderOpen, Globe, HardDriveDownload } from 'lucide-react';

interface PluginsTabProps {
  installedPlugins: any[];
  isLoadingPlugins: boolean;
  isUninstallingPlugin: Record<string, boolean>;
  handleUninstallPlugin: (filename: string) => void;
  handleUploadPluginFile: (file: File) => void;
  isDragging: boolean;
  setIsDragging: (val: boolean) => void;
  isUploadingPluginFile: boolean;
  setActiveTab: (tab: any) => void;
  setCurrentFilePath: (path: string) => void;
}

const PluginsTab: React.FC<PluginsTabProps> = ({
  installedPlugins,
  isLoadingPlugins,
  isUninstallingPlugin,
  handleUninstallPlugin,
  handleUploadPluginFile,
  isDragging,
  setIsDragging,
  isUploadingPluginFile,
  setActiveTab,
  setCurrentFilePath,
}) => {
  return (
    <div className="bg-bg-secondary border border-white/5 p-6 shadow-mc-sm select-none font-sans">
      
      {/* Header and open folders btn */}
      <div className="flex justify-between items-center mb-6 border-b border-white/5 pb-4">
        <h3 className="font-pixel text-sm text-mc-emerald tracking-wide">Minecraft Plugins Database</h3>
        <button
          onClick={() => {
            setCurrentFilePath('plugins');
            setActiveTab('files');
          }}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-bg-surface border border-white/10 hover:border-mc-emerald text-text-secondary hover:text-white transition-all text-xs font-pixel uppercase cursor-pointer"
        >
          <FolderOpen className="w-3.5 h-3.5" />
          Open Plugins Folder
        </button>
      </div>

      {/* Restart Warning banner */}
      <div className="bg-status-error/10 border border-status-error/20 p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 shadow-mc-sm">
        <div>
          <strong className="block text-xs font-pixel uppercase tracking-wide text-status-error mb-1">
            ⚠️ Restart Required
          </strong>
          <span className="text-xs text-text-secondary">
            Installing, updating, or uninstalling plugins will only take effect after restarting the Minecraft server.
          </span>
        </div>
        
        <button 
          onClick={async () => {
            if (confirm("Are you sure you want to restart the Minecraft server?")) {
              try {
                await fetch('/api/server/stop', { method: 'POST' });
                setTimeout(() => fetch('/api/server/start', { method: 'POST' }), 2000);
              } catch (e) {
                console.error(e);
              }
            }
          }}
          className="px-4 py-2 bg-gradient-to-r from-status-error to-red-800 hover:to-status-error text-white font-pixel font-bold text-xs tracking-wider border border-status-error/30 cursor-pointer shadow-mc-sm hover:shadow-[0_0_10px_rgba(255,93,93,0.2)] transition-all shrink-0 w-full sm:w-auto text-center"
        >
          Restart Server
        </button>
      </div>

      {/* Drag & Drop uploader card */}
      <div className="mb-6">
        <input
          type="file"
          accept=".jar"
          style={{ display: 'none' }}
          id="plugin-file-upload-input"
          onChange={async (e) => {
            const files = e.target.files;
            if (files && files.length > 0) {
              await handleUploadPluginFile(files[0]);
            }
          }}
        />
        <div 
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={async (e) => {
            e.preventDefault();
            setIsDragging(false);
            const files = e.dataTransfer.files;
            if (files && files.length > 0) {
              const file = files[0];
              if (!file.name.endsWith('.jar')) {
                alert('Only .jar files can be uploaded as plugins.');
                return;
              }
              await handleUploadPluginFile(file);
            }
          }}
          onClick={() => document.getElementById('plugin-file-upload-input')?.click()}
          className={`flex flex-col items-center justify-center p-8 border-2 border-dashed text-center transition-all cursor-pointer ${
            isDragging 
              ? 'border-mc-emerald bg-mc-emerald/5 text-white' 
              : 'border-white/10 bg-bg-surface hover:border-white/20 text-text-muted hover:text-text-secondary'
          }`}
        >
          <HardDriveDownload className={`w-8 h-8 mb-3 ${isUploadingPluginFile ? 'animate-bounce text-mc-emerald' : 'text-text-muted'}`} />
          {isUploadingPluginFile ? (
            <div>
              <strong className="block text-xs font-pixel text-white uppercase tracking-wider mb-1">Uploading plugin...</strong>
              <span className="text-[10px] font-mono text-text-muted">Transferring JAR package payload to plugins directory</span>
            </div>
          ) : (
            <div>
              <strong className="block text-xs font-pixel uppercase tracking-wider mb-1">
                {isDragging ? 'Drop JAR to upload!' : 'Drag & drop plugin .jar file here'}
              </strong>
              <span className="text-[10px] font-mono text-text-muted">or click to browse local folders</span>
            </div>
          )}
        </div>
      </div>

      {/* Installed plugins lists */}
      <div className="space-y-4">
        <h4 className="font-pixel text-[11px] text-text-secondary tracking-wider uppercase mb-3">
          Currently Installed ({installedPlugins.length})
        </h4>

        {isLoadingPlugins ? (
          <div className="flex justify-center py-8">
            <div className="w-6 h-6 border border-white/25 border-t-mc-emerald rounded-full animate-spin" />
          </div>
        ) : installedPlugins.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 bg-bg-surface/50 border border-white/5 text-center space-y-2">
            <Layers className="w-8 h-8 text-text-muted" />
            <span className="text-text-secondary text-xs font-mono">No plugins currently installed on this server.</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3">
            {installedPlugins.map((plugin) => {
              const uninstalling = isUninstallingPlugin[plugin.file_name] || false;
              return (
                <div 
                  key={plugin.file_name} 
                  className="bg-bg-surface border border-white/5 hover:border-white/10 transition-all p-4 shadow-mc-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
                >
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <strong className="text-sm font-semibold text-white">{plugin.name}</strong>
                      <span className="px-1.5 py-0.5 bg-bg-secondary border border-white/10 text-mc-emerald font-mono text-[10px]">
                        {plugin.version}
                      </span>
                    </div>
                    <p className="text-xs text-text-secondary">{plugin.description}</p>
                    <div className="flex flex-wrap gap-4 text-[10px] font-mono text-text-muted pt-1">
                      {plugin.authors && plugin.authors.length > 0 && (
                        <span>👤 Author: {plugin.authors.join(', ')}</span>
                      )}
                      {plugin.website && (
                        <span className="inline-flex items-center gap-1">
                          <Globe className="w-3 h-3 text-text-muted shrink-0" />
                          <a 
                            href={plugin.website.startsWith('http') ? plugin.website : `http://${plugin.website}`} 
                            target="_blank" 
                            rel="noopener noreferrer" 
                            className="underline text-mc-emerald hover:text-white transition-colors"
                          >
                            Website
                          </a>
                        </span>
                      )}
                      <span className="bg-black/20 px-1 border border-white/5 text-[9px]">File: {plugin.file_name}</span>
                    </div>
                  </div>

                  <div className="flex gap-2 w-full md:w-auto shrink-0 justify-end">
                    <button
                      onClick={() => {
                        setCurrentFilePath(`plugins/${plugin.name}`);
                        setActiveTab('files');
                      }}
                      className="px-3 py-1.5 bg-bg-secondary border border-white/10 hover:border-white/20 text-white font-pixel text-[9px] uppercase cursor-pointer transition-colors"
                    >
                      📁 Configs
                    </button>
                    <button
                      disabled={uninstalling}
                      onClick={() => handleUninstallPlugin(plugin.file_name)}
                      className="px-3 py-1.5 bg-status-error/10 border border-status-error/20 hover:bg-status-error/20 text-status-error font-pixel text-[9px] uppercase cursor-pointer disabled:opacity-50 transition-colors"
                    >
                      {uninstalling ? 'Uninstalling...' : 'Uninstall'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

    </div>
  );
};

export default PluginsTab;
