import React from 'react';
import { Database, Plus, RefreshCw, Trash2 } from 'lucide-react';

interface BackupData {
  id: number;
  filename: string;
  filepath: string;
  file_size: number;
  checksum: string;
  status: 'PENDING' | 'SUCCESSFUL' | 'FAILED';
  created_by: number | null;
  created_at: string | null;
}

interface BackupsTabProps {
  backups: BackupData[];
  isLoadingBackups: boolean;
  isCreatingBackup: boolean;
  restoringBackupId: number | null;
  deletingBackupId: number | null;
  handleCreateBackup: () => void;
  handleRestoreBackup: (id: number, filename: string) => void;
  handleDeleteBackup: (id: number, filename: string) => void;
  formatMB: (bytes: number) => string;
  formatDate: (dateStr: string | null) => string;
  isModerator: boolean;
}

const BackupsTab: React.FC<BackupsTabProps> = ({
  backups,
  isLoadingBackups,
  isCreatingBackup,
  restoringBackupId,
  deletingBackupId,
  handleCreateBackup,
  handleRestoreBackup,
  handleDeleteBackup,
  formatMB,
  formatDate,
  isModerator,
}) => {
  return (
    <div className="bg-bg-secondary border border-white/5 p-6 shadow-mc-sm font-sans select-none space-y-6">
      
      {/* Backups Header */}
      <div className="flex justify-between items-center border-b border-white/5 pb-4">
        <div className="flex flex-col">
          <span className="font-pixel text-sm text-mc-emerald tracking-wide">Backup Storage Index</span>
          <span className="text-[10px] font-mono text-text-muted mt-1 uppercase">
            Total Archives: {backups.length}
          </span>
        </div>

        <button
          onClick={handleCreateBackup}
          disabled={isModerator || isCreatingBackup || restoringBackupId !== null}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-mc-emerald to-emerald-700 hover:to-mc-emerald text-bg-primary font-pixel font-bold text-xs tracking-wider border border-mc-emerald/30 cursor-pointer shadow-mc-sm hover:shadow-[0_0_10px_rgba(46,204,113,0.3)] transition-all disabled:opacity-40"
        >
          {isCreatingBackup ? (
            <>
              <div className="w-3.5 h-3.5 border border-bg-primary/20 border-t-bg-primary rounded-full animate-spin" />
              <span>Compressing...</span>
            </>
          ) : (
            <>
              <Plus className="w-4 h-4 fill-bg-primary stroke-[3]" />
              <span>Create Backup</span>
            </>
          )}
        </button>
      </div>

      {/* Backups Table */}
      {isLoadingBackups ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-2 border-white/20 border-t-mc-emerald rounded-full animate-spin" />
        </div>
      ) : backups.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-left font-sans text-xs border-collapse">
            <thead>
              <tr className="border-b border-white/10 text-text-muted font-mono uppercase tracking-wider text-[10px]">
                <th className="pb-3 font-semibold">Filename</th>
                <th className="pb-3 font-semibold">Creation Date</th>
                <th className="pb-3 font-semibold">Size</th>
                <th className="pb-3 font-semibold">Checksum</th>
                <th className="pb-3 font-semibold">Status</th>
                <th className="pb-3 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-mono text-xs">
              {backups.map((backup) => (
                <tr key={backup.id} className="hover:bg-white/[0.01] transition-all">
                  <td className="py-3.5 font-semibold text-white">{backup.filename}</td>
                  <td className="py-3.5 text-text-secondary">{formatDate(backup.created_at)}</td>
                  <td className="py-3.5 text-text-secondary">{formatMB(backup.file_size)}</td>
                  <td className="py-3.5 text-text-muted" title={backup.checksum}>
                    {backup.checksum.slice(0, 8)}...
                  </td>
                  <td className="py-3.5">
                    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-[10px] font-pixel border ${
                      backup.status === 'SUCCESSFUL' 
                        ? 'border-status-online/25 bg-status-online/10 text-status-online' 
                        : backup.status === 'PENDING'
                        ? 'border-status-warning/25 bg-status-warning/10 text-status-warning animate-pulse'
                        : 'border-status-error/25 bg-status-error/10 text-status-error'
                    }`}>
                      {backup.status}
                    </span>
                  </td>
                  
                  <td className="py-3.5 text-right">
                    <div className="inline-flex gap-2">
                      <button
                        onClick={() => handleRestoreBackup(backup.id, backup.filename)}
                        disabled={
                          isModerator ||
                          backup.status !== 'SUCCESSFUL' ||
                          restoringBackupId !== null ||
                          deletingBackupId !== null
                        }
                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-[#45D9FF]/10 border border-[#45D9FF]/20 hover:bg-[#45D9FF]/20 text-[#45D9FF] font-pixel text-[9px] uppercase cursor-pointer disabled:opacity-40 transition-all"
                      >
                        {restoringBackupId === backup.id ? (
                          <>
                            <div className="w-3.5 h-3.5 border border-[#45D9FF]/20 border-t-[#45D9FF] rounded-full animate-spin" />
                            <span>Restoring...</span>
                          </>
                        ) : (
                          <>
                            <RefreshCw className="w-3.5 h-3.5" />
                            <span>Restore</span>
                          </>
                        )}
                      </button>
                      <button
                        onClick={() => handleDeleteBackup(backup.id, backup.filename)}
                        disabled={
                          isModerator ||
                          restoringBackupId !== null ||
                          deletingBackupId !== null
                        }
                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-status-error/10 border border-status-error/20 hover:bg-status-error/20 text-status-error font-pixel text-[9px] uppercase cursor-pointer disabled:opacity-40 transition-all"
                      >
                        {deletingBackupId === backup.id ? (
                          <>
                            <div className="w-3.5 h-3.5 border border-status-error/20 border-t-status-error rounded-full animate-spin" />
                            <span>Deleting...</span>
                          </>
                        ) : (
                          <>
                            <Trash2 className="w-3.5 h-3.5" />
                            <span>Delete</span>
                          </>
                        )}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center p-12 bg-bg-surface/50 border border-white/5 text-center space-y-3">
          <Database className="w-8 h-8 text-text-muted" />
          <span className="text-text-secondary text-xs font-mono">No backup archives are currently stored.</span>
        </div>
      )}
      
    </div>
  );
};

export default BackupsTab;
