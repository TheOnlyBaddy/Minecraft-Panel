import React from 'react';
import { Cpu, HardDrive, Users, Database, Play, Square, RotateCcw } from 'lucide-react';

interface ServerTabProps {
  telemetryData: any;
  currentStatus: string;
  isRestarting: boolean;
  actionPending: string | null;
  handleAction: (action: 'start' | 'stop' | 'restart') => void;
  cpuHistory: number[];
  memHistory: number[];
  sparkWidth: number;
  sparkHeight: number;
  cpuPaths: { path: string; areaPath: string };
  memPaths: { path: string; areaPath: string };
  memPercent: number;
  diskPercent: number;
  formatGB: (bytes: number) => string;
  getStatusText: (status: string) => string;
  isAgentOffline: boolean;
}

const ServerTab: React.FC<ServerTabProps> = ({
  telemetryData,
  currentStatus,
  isRestarting,
  actionPending,
  handleAction,
  cpuHistory,
  memHistory,
  sparkWidth,
  sparkHeight,
  cpuPaths,
  memPaths,
  memPercent,
  diskPercent,
  formatGB,
  getStatusText,
  isAgentOffline,
}) => {
  const isServerRunning = currentStatus === 'RUNNING';
  const isServerOffline = currentStatus === 'STOPPED' || currentStatus === 'CRASHED';
  const isServerTransitioning = currentStatus === 'STARTING' || currentStatus === 'STOPPING';

  return (
    <div className="space-y-6 select-none font-sans">
      
      {/* Control Bar (Lifecycle Panel) */}
      <section className="bg-bg-secondary border border-white/5 p-6 shadow-mc-sm flex flex-col md:flex-row justify-between items-center gap-6">
        <div className="flex flex-col gap-1 w-full md:w-auto">
          <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">Minecraft Server Status</span>
          <div className="relative flex items-center gap-3 mt-1.5">
            <span className={`inline-flex items-center px-3 py-1 text-xs font-pixel tracking-wide border border-black/30 shadow-mc-sm ${
              isRestarting ? 'bg-status-warning text-bg-primary animate-pulse' :
              currentStatus === 'RUNNING' ? 'bg-status-online text-bg-primary' :
              currentStatus === 'STARTING' ? 'bg-status-starting text-bg-primary animate-pulse' :
              currentStatus === 'STOPPING' ? 'bg-status-stopping text-bg-primary animate-pulse' :
              currentStatus === 'CRASHED' ? 'bg-status-error text-white font-bold' : 'bg-status-offline text-text-secondary'
            }`}>
              {getStatusText(currentStatus)}
            </span>
            {actionPending && (
              <div className="flex items-center gap-2 text-xs font-mono text-text-muted italic">
                <div className="w-3.5 h-3.5 border border-white/10 border-t-mc-emerald rounded-full animate-spin" />
                <span>Dispatching {actionPending}...</span>
              </div>
            )}
          </div>
        </div>

        <div className="flex gap-3 w-full md:w-auto">
          {/* Start Button */}
          <button
            onClick={() => handleAction('start')}
            disabled={!isServerOffline || !!actionPending || isAgentOffline}
            className="flex-1 md:flex-none flex items-center justify-center gap-2 px-5 py-2.5 bg-gradient-to-r from-mc-emerald to-emerald-700 hover:to-mc-emerald text-bg-primary font-pixel font-bold text-xs tracking-wider border border-mc-emerald/30 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed hover:shadow-[0_0_12px_rgba(46,204,113,0.3)] transition-all"
          >
            <Play className="w-4 h-4 fill-bg-primary" />
            Start
          </button>

          {/* Stop Button */}
          <button
            onClick={() => handleAction('stop')}
            disabled={isServerOffline || isServerTransitioning || !!actionPending || isAgentOffline}
            className="flex-1 md:flex-none flex items-center justify-center gap-2 px-5 py-2.5 bg-gradient-to-r from-status-error to-red-800 hover:to-status-error text-white font-pixel font-bold text-xs tracking-wider border border-status-error/30 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed hover:shadow-[0_0_12px_rgba(255,93,93,0.2)] transition-all"
          >
            <Square className="w-4 h-4 fill-white" />
            Stop
          </button>

          {/* Restart Button */}
          <button
            onClick={() => handleAction('restart')}
            disabled={!isServerRunning || !!actionPending || isAgentOffline}
            className="flex-1 md:flex-none flex items-center justify-center gap-2 px-5 py-2.5 bg-gradient-to-r from-mc-gold to-yellow-700 hover:to-mc-gold text-bg-primary font-pixel font-bold text-xs tracking-wider border border-mc-gold/30 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed hover:shadow-[0_0_12px_rgba(245,197,66,0.2)] transition-all"
          >
            <RotateCcw className="w-4 h-4" />
            Restart
          </button>
        </div>
      </section>

      {/* Hardware Performance Cards */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* CPU */}
        <div className="bg-bg-secondary border border-white/5 p-5 shadow-mc-sm flex flex-col justify-between hover:border-white/10 transition-all duration-200 group">
          <div className="flex justify-between items-center text-text-muted">
            <span className="text-[10px] font-mono uppercase tracking-wider">CPU Usage</span>
            <Cpu className="w-4 h-4 text-mc-emerald group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-3xl font-bold font-mono tracking-tight text-white mt-2">
            {telemetryData ? telemetryData.cpu_percent.toFixed(1) : '0.0'}%
          </div>
          <span className="text-[10px] font-mono text-text-muted mt-1.5">Host CPU Core Load</span>
        </div>

        {/* RAM */}
        <div className="bg-bg-secondary border border-white/5 p-5 shadow-mc-sm flex flex-col justify-between hover:border-white/10 transition-all duration-200 group">
          <div className="flex justify-between items-center text-text-muted">
            <span className="text-[10px] font-mono uppercase tracking-wider">Memory (RAM)</span>
            <Database className="w-4 h-4 text-[#45D9FF] group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-3xl font-bold font-mono tracking-tight text-white mt-2">
            {telemetryData ? memPercent.toFixed(1) : '0.0'}%
          </div>
          <span className="text-[10px] font-mono text-text-muted mt-1.5">
            {telemetryData ? `${formatGB(telemetryData.memory_used)} of ${formatGB(telemetryData.memory_total)}` : '0.0 GB / 0.0 GB'}
          </span>
        </div>

        {/* Online Players */}
        <div className="bg-bg-secondary border border-white/5 p-5 shadow-mc-sm flex flex-col justify-between hover:border-white/10 transition-all duration-200 group">
          <div className="flex justify-between items-center text-text-muted">
            <span className="text-[10px] font-mono uppercase tracking-wider">Players Online</span>
            <Users className="w-4 h-4 text-mc-gold group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-3xl font-bold font-mono tracking-tight text-white mt-2">
            {telemetryData ? telemetryData.active_players : 0}
          </div>
          <span className="text-[10px] font-mono text-text-muted mt-1.5">Active concurrent sessions</span>
        </div>

        {/* Disk Usage */}
        <div className="bg-bg-secondary border border-white/5 p-5 shadow-mc-sm flex flex-col justify-between hover:border-white/10 transition-all duration-200 group">
          <div className="flex justify-between items-center text-text-muted">
            <span className="text-[10px] font-mono uppercase tracking-wider">Disk Storage</span>
            <HardDrive className="w-4 h-4 text-[#B388FF] group-hover:scale-110 transition-transform" />
          </div>
          <div className="mt-2">
            <div className="text-3xl font-bold font-mono tracking-tight text-white">
              {telemetryData ? diskPercent.toFixed(1) : '0.0'}%
            </div>
            <div className="w-full h-1 bg-bg-surface mt-2.5 relative">
              <div 
                className="h-full bg-[#B388FF] transition-all duration-500"
                style={{ width: `${diskPercent}%` }}
              />
            </div>
          </div>
          <span className="text-[10px] font-mono text-text-muted mt-1.5">
            {telemetryData ? `${formatGB(telemetryData.disk_used)} of ${formatGB(telemetryData.disk_total)} used` : '0.0 GB / 0.0 GB'}
          </span>
        </div>
      </section>

      {/* SVG Historical Metrics Charts */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* CPU History Chart */}
        <div className="bg-bg-secondary border border-white/5 p-5 shadow-mc-sm flex flex-col">
          <div className="flex justify-between items-center mb-4">
            <span className="text-xs font-mono uppercase tracking-wider text-text-secondary">CPU Load Timeline</span>
            <span className="font-mono text-xs font-semibold text-mc-emerald">
              {telemetryData ? telemetryData.cpu_percent.toFixed(1) : '0.0'}% Current
            </span>
          </div>
          <div className="h-44 flex relative overflow-hidden bg-[#08090c] border border-white/5 p-1">
            {cpuHistory.length >= 2 ? (
              <svg className="w-full h-full" viewBox={`0 0 ${sparkWidth} ${sparkHeight}`} preserveAspectRatio="none">
                <defs>
                  <linearGradient id="cpuChartGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2ECC71" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#2ECC71" stopOpacity="0.0" />
                  </linearGradient>
                </defs>
                <g className="stroke-white/5 stroke-1">
                  <line x1="0" y1={sparkHeight * 0.25} x2={sparkWidth} y2={sparkHeight * 0.25} />
                  <line x1="0" y1={sparkHeight * 0.5} x2={sparkWidth} y2={sparkHeight * 0.5} />
                  <line x1="0" y1={sparkHeight * 0.75} x2={sparkWidth} y2={sparkHeight * 0.75} />
                </g>
                <path fill="url(#cpuChartGrad)" d={cpuPaths.areaPath} />
                <path fill="none" stroke="#2ECC71" strokeWidth="2.5" d={cpuPaths.path} />
              </svg>
            ) : (
              <div className="m-auto font-pixel text-[10px] text-text-muted uppercase">
                Collecting telemetry samples...
              </div>
            )}
          </div>
        </div>

        {/* RAM History Chart */}
        <div className="bg-bg-secondary border border-white/5 p-5 shadow-mc-sm flex flex-col">
          <div className="flex justify-between items-center mb-4">
            <span className="text-xs font-mono uppercase tracking-wider text-text-secondary">Memory Consumption Timeline</span>
            <span className="font-mono text-xs font-semibold text-[#45D9FF]">
              {memPercent.toFixed(1)}% Current
            </span>
          </div>
          <div className="h-44 flex relative overflow-hidden bg-[#08090c] border border-white/5 p-1">
            {memHistory.length >= 2 ? (
              <svg className="w-full h-full" viewBox={`0 0 ${sparkWidth} ${sparkHeight}`} preserveAspectRatio="none">
                <defs>
                  <linearGradient id="memChartGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#45D9FF" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#45D9FF" stopOpacity="0.0" />
                  </linearGradient>
                </defs>
                <g className="stroke-white/5 stroke-1">
                  <line x1="0" y1={sparkHeight * 0.25} x2={sparkWidth} y2={sparkHeight * 0.25} />
                  <line x1="0" y1={sparkHeight * 0.5} x2={sparkWidth} y2={sparkHeight * 0.5} />
                  <line x1="0" y1={sparkHeight * 0.75} x2={sparkWidth} y2={sparkHeight * 0.75} />
                </g>
                <path fill="url(#memChartGrad)" d={memPaths.areaPath} />
                <path fill="none" stroke="#45D9FF" strokeWidth="2.5" d={memPaths.path} />
              </svg>
            ) : (
              <div className="m-auto font-pixel text-[10px] text-text-muted uppercase">
                Collecting telemetry samples...
              </div>
            )}
          </div>
        </div>

      </section>

    </div>
  );
};

export default ServerTab;
