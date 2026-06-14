import React, { useState } from 'react';
import { Terminal, Send, Trash2, ShieldAlert } from 'lucide-react';

interface ConsoleTabProps {
  consoleError: string | null;
  commandInput: string;
  setCommandInput: (val: string) => void;
  isExecutingCommand: boolean;
  handleSendCommand: (e: React.FormEvent) => void;
  searchQuery: string;
  setSearchQuery: (val: string) => void;
  filteredLogs: string[];
  getLogClass: (line: string) => string;
  terminalBodyRef: React.RefObject<HTMLDivElement>;
  isServerOffline: boolean;
  clearLogs: () => void;
  handleScroll: () => void;
}

const ConsoleTab: React.FC<ConsoleTabProps> = ({
  consoleError,
  commandInput,
  setCommandInput,
  isExecutingCommand,
  handleSendCommand,
  searchQuery,
  setSearchQuery,
  filteredLogs,
  getLogClass,
  terminalBodyRef,
  isServerOffline,
  clearLogs,
  handleScroll,
}) => {
  // Autocomplete internal states
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [activeSuggestionIndex, setActiveSuggestionIndex] = useState(0);

  const MC_COMMANDS = [
    'help', 'say ', 'list', 'op ', 'deop ', 'whitelist add ', 'whitelist remove ', 'whitelist list', 'whitelist on', 'whitelist off', 
    'ban ', 'pardon ', 'kick ', 'tp ', 'gamerule ', 'stop', 'restart', 'save-all', 'save-on', 'save-off', 'difficulty ', 'gamemode '
  ];

  const handleCommandChange = (value: string) => {
    setCommandInput(value);
    if (!value.startsWith('/')) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    const query = value.slice(1);
    if (!query.trim()) {
      setSuggestions(MC_COMMANDS.map(c => '/' + c));
      setShowSuggestions(true);
      return;
    }
    const filtered = MC_COMMANDS.filter(cmd => 
      cmd.toLowerCase().startsWith(query.toLowerCase())
    ).map(c => '/' + c);
    
    setSuggestions(filtered);
    setShowSuggestions(filtered.length > 0);
    setActiveSuggestionIndex(0);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (showSuggestions && suggestions.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setActiveSuggestionIndex(prev => (prev + 1) % suggestions.length);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActiveSuggestionIndex(prev => (prev - 1 + suggestions.length) % suggestions.length);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        setCommandInput(suggestions[activeSuggestionIndex]);
        setSuggestions([]);
        setShowSuggestions(false);
      } else if (e.key === 'Tab') {
        e.preventDefault();
        setCommandInput(suggestions[activeSuggestionIndex]);
        setSuggestions([]);
        setShowSuggestions(false);
      } else if (e.key === 'Escape') {
        setShowSuggestions(false);
      }
    }
  };

  return (
    <div className="bg-bg-secondary border border-white/5 flex flex-col h-[550px] shadow-mc-sm relative overflow-hidden">
      {/* Console Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 px-4 py-3 bg-[#0d0e12] border-b border-white/5 shrink-0">
        <div className="flex items-center gap-2 font-pixel text-sm text-text-secondary">
          <Terminal className="w-4 h-4 text-mc-emerald" />
          <span>Interactive Shell Stream</span>
        </div>
        
        <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
          {/* Search bar */}
          <input
            type="text"
            placeholder="Search logs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-grow sm:flex-grow-0 px-3 py-1 bg-bg-surface border border-white/10 font-mono text-xs sm:w-48 focus:outline-none focus:border-mc-emerald text-white placeholder:text-text-muted"
          />

          <button 
            onClick={clearLogs}
            className="flex items-center justify-center gap-1 px-3 py-1 bg-bg-surface border border-white/10 font-pixel text-xs text-status-error hover:bg-status-error hover:text-bg-primary transition-all cursor-pointer shrink-0 min-h-[26px]"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear screen</span>
          </button>
        </div>
      </div>

      {/* Connection error banner */}
      {consoleError && (
        <div className="px-4 py-2 bg-status-error/10 border-b border-status-error/20 text-status-error text-xs font-mono flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 shrink-0" />
          <span>Socket Connection Error: {consoleError}</span>
        </div>
      )}

      {/* Monospace Output */}
      <div 
        ref={terminalBodyRef}
        onScroll={handleScroll}
        className="flex-1 p-4 bg-[#08090c] overflow-y-auto font-mono text-xs space-y-1 select-text scrollbar-thin"
      >
        {filteredLogs.length > 0 ? (
          filteredLogs.map((line, idx) => (
            <p key={idx} className={`leading-relaxed whitespace-pre-wrap ${getLogClass(line)}`}>
              {line}
            </p>
          ))
        ) : (
          <div className="flex h-full items-center justify-center text-text-muted font-pixel text-sm select-none">
            {searchQuery ? 'No lines matching query found.' : 'Terminal logs are empty.'}
          </div>
        )}
      </div>

      {/* Terminal Input block */}
      <div className="relative border-t border-white/5 bg-[#0d0e12] p-4 shrink-0 flex items-center gap-3">
        {/* Autocomplete floating list */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute bottom-full left-4 mb-1 w-64 bg-bg-elevated border border-white/10 shadow-mc-lg z-50 max-h-40 overflow-y-auto font-mono text-xs select-none">
            {suggestions.map((sug, i) => (
              <div
                key={sug}
                onClick={() => {
                  setCommandInput(sug);
                  setSuggestions([]);
                  setShowSuggestions(false);
                }}
                className={`px-3 py-1.5 cursor-pointer transition-colors ${
                  i === activeSuggestionIndex 
                    ? 'bg-mc-emerald text-bg-primary font-bold' 
                    : 'text-text-secondary hover:bg-bg-surface hover:text-white'
                }`}
              >
                {sug}
              </div>
            ))}
          </div>
        )}

        <span className="font-mono text-mc-emerald font-bold select-none">&gt;</span>
        <form onSubmit={handleSendCommand} className="flex-1 flex gap-3">
          <input
            type="text"
            placeholder={
              isServerOffline
                ? 'Server is offline. Start the server to submit console commands.'
                : "Type a command (start with '/' to see suggestions, e.g. /say hello)..."
            }
            value={commandInput}
            onChange={(e) => handleCommandChange(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isServerOffline || isExecutingCommand}
            className="flex-1 px-3 py-2 bg-bg-surface border border-white/10 rounded-none text-white text-xs placeholder:text-text-muted focus:outline-none focus:border-mc-emerald font-mono disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isServerOffline || isExecutingCommand || !commandInput.trim()}
            className="flex items-center justify-center gap-2 px-5 bg-gradient-to-r from-mc-emerald to-emerald-700 hover:to-mc-emerald text-bg-primary font-pixel text-sm font-bold shadow-mc-sm border border-mc-emerald/30 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-[0_0_10px_rgba(46,204,113,0.3)] transition-all"
          >
            {isExecutingCommand ? (
              <div className="w-3.5 h-3.5 border border-bg-primary/20 border-t-bg-primary rounded-full animate-spin" />
            ) : (
              <Send className="w-3.5 h-3.5" />
            )}
            <span>Execute</span>
          </button>
        </form>
      </div>
    </div>
  );
};

export default ConsoleTab;
