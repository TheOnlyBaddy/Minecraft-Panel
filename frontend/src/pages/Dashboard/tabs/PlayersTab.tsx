import React from 'react';
import { Users, RefreshCw, Star, Ban, UserMinus } from 'lucide-react';

interface PlayersTabProps {
  activePlayerList: 'online' | 'whitelist' | 'ops' | 'banned-players' | 'banned-ips';
  setActivePlayerList: (list: 'online' | 'whitelist' | 'ops' | 'banned-players' | 'banned-ips') => void;
  playersData: any[];
  isLoadingPlayers: boolean;
  newPlayerNameOrIp: string;
  setNewPlayerNameOrIp: (val: string) => void;
  banReason: string;
  setBanReason: (val: string) => void;
  fetchPlayers: () => void;
  handleAddPlayer: (e: React.FormEvent) => void;
  handleRemovePlayer: (target: string) => void;
  runPlayerCommand: (command: 'op' | 'deop' | 'kick' | 'ban', username: string) => void;
  formatDate: (dateStr: string | null) => string;
}

const PlayersTab: React.FC<PlayersTabProps> = ({
  activePlayerList,
  setActivePlayerList,
  playersData,
  isLoadingPlayers,
  newPlayerNameOrIp,
  setNewPlayerNameOrIp,
  banReason,
  setBanReason,
  fetchPlayers,
  handleAddPlayer,
  handleRemovePlayer,
  runPlayerCommand,
  formatDate,
}) => {
  return (
    <div className="bg-bg-secondary border border-white/5 p-6 shadow-mc-sm select-none font-sans">
      
      {/* Navigation menu & reload */}
      <div className="flex flex-col md:flex-row justify-between items-stretch md:items-center gap-4 border-b border-white/5 pb-4 mb-6">
        <div className="flex flex-wrap gap-2">
          {(['online', 'whitelist', 'ops', 'banned-players', 'banned-ips'] as const).map((list) => (
            <button
              key={list}
              onClick={() => {
                setActivePlayerList(list);
              }}
              className={`px-3 py-1.5 border border-white/10 font-pixel text-[10px] uppercase cursor-pointer transition-all ${
                activePlayerList === list 
                  ? 'bg-mc-emerald border-mc-emerald text-bg-primary font-bold hover:shadow-[0_0_8px_rgba(46,204,113,0.3)]' 
                  : 'bg-bg-surface text-text-secondary hover:text-white hover:border-white/20'
              }`}
            >
              {list.replace('-', ' ')}
            </button>
          ))}
        </div>

        <button
          onClick={fetchPlayers}
          disabled={isLoadingPlayers}
          className="flex items-center justify-center gap-1.5 px-4 py-1.5 bg-bg-surface border border-white/10 text-text-secondary hover:text-white font-pixel text-[10px] uppercase cursor-pointer disabled:opacity-50 transition-all shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoadingPlayers ? 'animate-spin' : ''}`} />
          {isLoadingPlayers ? 'Reloading...' : 'Reload List'}
        </button>
      </div>

      {/* Input box to add player manually */}
      {activePlayerList !== 'online' && (
        <div className="mb-6 p-4 bg-bg-surface border border-white/5">
          <form onSubmit={handleAddPlayer} className="flex flex-col md:flex-row gap-3">
            <input
              type="text"
              placeholder={activePlayerList === 'banned-ips' ? 'Type an IP address (e.g., 192.168.1.100)...' : 'Type Minecraft username...'}
              value={newPlayerNameOrIp}
              onChange={(e) => setNewPlayerNameOrIp(e.target.value)}
              className="flex-grow px-3 py-2 bg-bg-secondary border border-white/10 text-white font-sans text-xs focus:outline-none focus:border-mc-emerald h-10"
            />
            {activePlayerList.startsWith('banned') && (
              <input
                type="text"
                placeholder="Ban reason..."
                value={banReason}
                onChange={(e) => setBanReason(e.target.value)}
                className="flex-grow px-3 py-2 bg-bg-secondary border border-white/10 text-white font-sans text-xs focus:outline-none focus:border-mc-emerald h-10"
              />
            )}
            <button 
              type="submit" 
              className="px-5 h-10 bg-gradient-to-r from-mc-emerald to-emerald-700 hover:to-mc-emerald text-bg-primary font-pixel font-bold text-xs tracking-wider border border-mc-emerald/30 cursor-pointer hover:shadow-[0_0_10px_rgba(46,204,113,0.3)] transition-all shrink-0"
            >
              Add to List
            </button>
          </form>
        </div>
      )}

      {/* Loading state or records */}
      {isLoadingPlayers ? (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-2 border-white/20 border-t-mc-emerald rounded-full animate-spin" />
        </div>
      ) : playersData.length > 0 ? (
        <>
          {/* ── Desktop table (hidden on mobile) ── */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-left font-sans text-xs border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-text-muted font-mono uppercase tracking-wider text-[10px]">
                  {activePlayerList === 'banned-ips' ? (
                    <>
                      <th className="pb-3 font-semibold">Banned IP Address</th>
                      <th className="pb-3 font-semibold">Ban Date</th>
                      <th className="pb-3 font-semibold">Source</th>
                      <th className="pb-3 font-semibold">Expires</th>
                      <th className="pb-3 font-semibold">Reason</th>
                    </>
                  ) : (
                    <>
                      <th className="pb-3 font-semibold">Player Name</th>
                      <th className="pb-3 font-semibold">UUID</th>
                      {activePlayerList === 'ops' && <th className="pb-3 font-semibold">OP Level</th>}
                      {activePlayerList === 'online' && <th className="pb-3 font-semibold">Status</th>}
                      {activePlayerList === 'banned-players' && (
                        <>
                          <th className="pb-3 font-semibold">Ban Date</th>
                          <th className="pb-3 font-semibold">Source</th>
                          <th className="pb-3 font-semibold">Reason</th>
                        </>
                      )}
                    </>
                  )}
                  <th className="pb-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {playersData.map((player, idx) => (
                  <tr key={idx} className="hover:bg-white/[0.01] transition-all">
                    {activePlayerList === 'banned-ips' ? (
                      <>
                        <td className="py-3 font-semibold text-white">{player.ip}</td>
                        <td className="py-3 text-text-secondary font-mono">{formatDate(player.created)}</td>
                        <td className="py-3 text-text-secondary">{player.source}</td>
                        <td className="py-3 text-text-secondary font-mono">{player.expires}</td>
                        <td className="py-3 text-text-secondary">{player.reason}</td>
                      </>
                    ) : (
                      <>
                        <td className="py-3 font-semibold text-white flex items-center gap-2">
                          <div className="w-4 h-4 bg-bg-surface border border-white/15 rounded-none flex items-center justify-center font-pixel text-[9px] text-mc-emerald font-bold">
                            {player.name.slice(0, 1).toUpperCase()}
                          </div>
                          {player.name}
                        </td>
                        <td className="py-3"><code className="font-mono text-[10px] text-text-secondary bg-[#1a1f26] px-1.5 py-0.5 border border-white/5">{player.uuid}</code></td>
                        {activePlayerList === 'ops' && <td className="py-3 text-text-secondary font-mono">Level {player.level}</td>}
                        {activePlayerList === 'online' && (
                          <td className="py-3">
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 text-[10px] font-pixel text-status-online bg-status-online/10 border border-status-online/25">
                              <span className="w-1.5 h-1.5 bg-status-online rounded-none animate-pulse" />
                              Online
                            </span>
                          </td>
                        )}
                        {activePlayerList === 'banned-players' && (
                          <>
                            <td className="py-3 text-text-secondary font-mono">{formatDate(player.created)}</td>
                            <td className="py-3 text-text-secondary">{player.source}</td>
                            <td className="py-3 text-text-secondary">{player.reason}</td>
                          </>
                        )}
                      </>
                    )}
                    
                    <td className="py-3 text-right">
                      {activePlayerList === 'online' ? (
                        <div className="inline-flex gap-2">
                          <button
                            onClick={() => runPlayerCommand('op', player.name)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 bg-mc-emerald/10 border border-mc-emerald/20 hover:bg-mc-emerald/20 text-mc-emerald font-pixel text-[9px] uppercase cursor-pointer transition-colors"
                          >
                            <Star className="w-3 h-3 fill-mc-emerald" />
                            OP
                          </button>
                          <button
                            onClick={() => runPlayerCommand('kick', player.name)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 bg-mc-gold/10 border border-mc-gold/20 hover:bg-mc-gold/20 text-mc-gold font-pixel text-[9px] uppercase cursor-pointer transition-colors"
                          >
                            <UserMinus className="w-3 h-3" />
                            Kick
                          </button>
                          <button
                            onClick={() => runPlayerCommand('ban', player.name)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 bg-status-error/10 border border-status-error/20 hover:bg-status-error/20 text-status-error font-pixel text-[9px] uppercase cursor-pointer transition-colors"
                          >
                            <Ban className="w-3 h-3" />
                            Ban
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => handleRemovePlayer(activePlayerList === 'banned-ips' ? player.ip : (player.uuid || player.name))}
                          className="inline-flex items-center gap-1 px-3 py-1 bg-status-error/10 border border-status-error/20 hover:bg-status-error/20 text-status-error font-pixel text-[9px] uppercase cursor-pointer transition-colors"
                        >
                          Remove
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* ── Mobile card layout (visible only on small screens) ── */}
          <div className="md:hidden flex flex-col gap-3">
            {playersData.map((player, idx) => (
              <div key={idx} className="bg-bg-surface border border-white/5 p-4 space-y-3">
                {/* Card header: Avatar + Name / IP */}
                <div className="flex items-center gap-3">
                  {activePlayerList === 'banned-ips' ? (
                    <div className="w-9 h-9 bg-status-error/15 border border-status-error/25 flex items-center justify-center font-pixel text-sm text-status-error font-bold shrink-0">
                      IP
                    </div>
                  ) : (
                    <div className="w-9 h-9 bg-bg-secondary border border-white/15 flex items-center justify-center font-pixel text-sm text-mc-emerald font-bold shrink-0">
                      {player.name.slice(0, 1).toUpperCase()}
                    </div>
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="text-white font-semibold text-sm truncate">
                      {activePlayerList === 'banned-ips' ? player.ip : player.name}
                    </p>
                    {activePlayerList !== 'banned-ips' && player.uuid && (
                      <p className="font-mono text-[10px] text-text-muted truncate">{player.uuid}</p>
                    )}
                  </div>
                  {/* Status badge */}
                  {activePlayerList === 'online' && (
                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 text-[10px] font-pixel text-status-online bg-status-online/10 border border-status-online/25 shrink-0">
                      <span className="w-1.5 h-1.5 bg-status-online animate-pulse" />
                      Online
                    </span>
                  )}
                  {activePlayerList === 'ops' && (
                    <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-pixel text-mc-gold bg-mc-gold/10 border border-mc-gold/25 shrink-0">
                      Level {player.level}
                    </span>
                  )}
                </div>

                {/* Extra details for ban lists */}
                {(activePlayerList === 'banned-players' || activePlayerList === 'banned-ips') && (
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[11px] border-t border-white/5 pt-3">
                    <div>
                      <span className="text-text-muted font-mono uppercase text-[9px]">Ban Date</span>
                      <p className="text-text-secondary font-mono">{formatDate(player.created)}</p>
                    </div>
                    <div>
                      <span className="text-text-muted font-mono uppercase text-[9px]">Source</span>
                      <p className="text-text-secondary">{player.source}</p>
                    </div>
                    {activePlayerList === 'banned-ips' && (
                      <div>
                        <span className="text-text-muted font-mono uppercase text-[9px]">Expires</span>
                        <p className="text-text-secondary font-mono">{player.expires}</p>
                      </div>
                    )}
                    <div className={activePlayerList === 'banned-ips' ? '' : 'col-span-2'}>
                      <span className="text-text-muted font-mono uppercase text-[9px]">Reason</span>
                      <p className="text-text-secondary">{player.reason}</p>
                    </div>
                  </div>
                )}

                {/* Action buttons */}
                <div className="flex flex-wrap gap-2 border-t border-white/5 pt-3">
                  {activePlayerList === 'online' ? (
                    <>
                      <button
                        onClick={() => runPlayerCommand('op', player.name)}
                        className="flex-1 inline-flex items-center justify-center gap-1 px-2.5 py-1.5 bg-mc-emerald/10 border border-mc-emerald/20 active:bg-mc-emerald/25 text-mc-emerald font-pixel text-[9px] uppercase cursor-pointer transition-colors"
                      >
                        <Star className="w-3 h-3 fill-mc-emerald" />
                        OP
                      </button>
                      <button
                        onClick={() => runPlayerCommand('kick', player.name)}
                        className="flex-1 inline-flex items-center justify-center gap-1 px-2.5 py-1.5 bg-mc-gold/10 border border-mc-gold/20 active:bg-mc-gold/25 text-mc-gold font-pixel text-[9px] uppercase cursor-pointer transition-colors"
                      >
                        <UserMinus className="w-3 h-3" />
                        Kick
                      </button>
                      <button
                        onClick={() => runPlayerCommand('ban', player.name)}
                        className="flex-1 inline-flex items-center justify-center gap-1 px-2.5 py-1.5 bg-status-error/10 border border-status-error/20 active:bg-status-error/25 text-status-error font-pixel text-[9px] uppercase cursor-pointer transition-colors"
                      >
                        <Ban className="w-3 h-3" />
                        Ban
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => handleRemovePlayer(activePlayerList === 'banned-ips' ? player.ip : (player.uuid || player.name))}
                      className="w-full inline-flex items-center justify-center gap-1 px-3 py-1.5 bg-status-error/10 border border-status-error/20 active:bg-status-error/25 text-status-error font-pixel text-[9px] uppercase cursor-pointer transition-colors"
                    >
                      Remove
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="flex flex-col items-center justify-center p-12 bg-bg-surface/50 border border-white/5 text-center space-y-3">
          <Users className="w-8 h-8 text-text-muted" />
          <span className="text-text-secondary text-xs font-mono">No players are currently listed in this category.</span>
        </div>
      )}
      
    </div>
  );
};

export default PlayersTab;
