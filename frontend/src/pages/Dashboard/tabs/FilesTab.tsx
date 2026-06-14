import React from 'react';
import { FolderOpen, File, CornerDownRight, ArrowLeft, Save, Trash2, Edit } from 'lucide-react';

interface FilesTabProps {
  currentFilePath: string;
  filesList: any[];
  isLoadingFiles: boolean;
  editingFilePath: string | null;
  setEditingFilePath: (val: string | null) => void;
  editingFileContent: string;
  setEditingFileContent: (val: string) => void;
  isSavingFile: boolean;
  handleNavigateFiles: (name: string) => void;
  handleReadFile: (path: string) => void;
  handleWriteFile: (e: React.FormEvent) => void;
  handleDeleteFile: (path: string) => void;
  formatMB: (bytes: number) => string;
}

const FilesTab: React.FC<FilesTabProps> = ({
  currentFilePath,
  filesList,
  isLoadingFiles,
  editingFilePath,
  setEditingFilePath,
  editingFileContent,
  setEditingFileContent,
  isSavingFile,
  handleNavigateFiles,
  handleReadFile,
  handleWriteFile,
  handleDeleteFile,
  formatMB,
}) => {
  return (
    <div className="bg-bg-secondary border border-white/5 p-6 shadow-mc-sm font-sans select-none">
      
      {editingFilePath ? (
        // File Editor Mode
        <form onSubmit={handleWriteFile} className="space-y-4">
          <div className="flex justify-between items-center border-b border-white/5 pb-3">
            <span className="text-xs font-semibold text-white flex items-center gap-1.5">
              <CornerDownRight className="w-4 h-4 text-mc-emerald" />
              Editing: <code className="font-mono text-mc-emerald bg-bg-surface px-2 py-0.5 border border-white/5">{editingFilePath}</code>
            </span>
            
            <button 
              type="button" 
              onClick={() => setEditingFilePath(null)}
              className="inline-flex items-center gap-1 px-3 py-1.5 bg-bg-surface border border-white/10 hover:border-white/20 text-text-secondary hover:text-white font-pixel text-[9px] uppercase cursor-pointer transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Close
            </button>
          </div>

          <textarea
            value={editingFileContent}
            onChange={(e) => setEditingFileContent(e.target.value)}
            className="w-full h-96 p-4 bg-[#08090c] border border-white/10 text-[#f8fafc] font-mono text-xs focus:outline-none focus:border-mc-emerald leading-relaxed resize-y"
          />

          <div className="flex justify-end pt-2">
            <button 
              type="submit" 
              disabled={isSavingFile} 
              className="px-5 py-2.5 bg-gradient-to-r from-mc-emerald to-emerald-700 hover:to-mc-emerald text-bg-primary font-pixel font-bold text-xs tracking-wider border border-mc-emerald/30 cursor-pointer disabled:opacity-50 hover:shadow-[0_0_10px_rgba(46,204,113,0.3)] transition-all flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              {isSavingFile ? 'Saving changes...' : 'Save File'}
            </button>
          </div>
        </form>
      ) : (
        // File Browser Mode
        <>
          <div className="flex items-center gap-2 px-4 py-2.5 bg-bg-surface border border-white/5 font-mono text-xs mb-5">
            <span className="text-text-muted">Current Directory:</span>
            <span className="text-mc-emerald font-bold font-pixel text-[10px] uppercase">
              / {currentFilePath || 'Root'}
            </span>
          </div>

          {isLoadingFiles ? (
            <div className="flex justify-center py-16">
              <div className="w-8 h-8 border-2 border-white/20 border-t-mc-emerald rounded-full animate-spin" />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left font-sans text-xs border-collapse">
                <thead>
                  <tr className="border-b border-white/10 text-text-muted font-mono uppercase tracking-wider text-[10px]">
                    <th className="pb-3 font-semibold">Name</th>
                    <th className="pb-3 font-semibold">Type</th>
                    <th className="pb-3 font-semibold">Size</th>
                    <th className="pb-3 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 font-mono text-xs">
                  {/* Up directory navigator */}
                  {currentFilePath && (
                    <tr className="hover:bg-white/[0.01] transition-all">
                      <td 
                        onClick={() => handleNavigateFiles('..')} 
                        className="py-3 font-semibold text-mc-emerald cursor-pointer hover:underline flex items-center gap-1.5"
                      >
                        <FolderOpen className="w-3.5 h-3.5 text-mc-emerald shrink-0" />
                        .. (Parent Directory)
                      </td>
                      <td className="py-3 text-text-muted">Directory</td>
                      <td className="py-3 text-text-muted">-</td>
                      <td className="py-3 text-right text-text-muted">-</td>
                    </tr>
                  )}

                  {filesList.map((file, idx) => (
                    <tr key={idx} className="hover:bg-white/[0.01] transition-all">
                      <td 
                        onClick={() => file.isDir ? handleNavigateFiles(file.name) : file.isEditable ? handleReadFile(currentFilePath ? `${currentFilePath}/${file.name}` : file.name) : undefined}
                        className={`py-3 font-semibold flex items-center gap-1.5 ${
                          (file.isDir || file.isEditable) ? 'cursor-pointer hover:underline' : 'cursor-default'
                        } ${file.isDir ? 'text-mc-emerald' : 'text-white'}`}
                      >
                        {file.isDir ? (
                          <FolderOpen className="w-3.5 h-3.5 text-mc-emerald shrink-0" />
                        ) : (
                          <File className="w-3.5 h-3.5 text-text-muted shrink-0" />
                        )}
                        {file.name}
                      </td>
                      <td className="py-3 text-text-secondary">{file.isDir ? 'Directory' : 'File'}</td>
                      <td className="py-3 text-text-secondary">{file.isDir ? '-' : formatMB(file.sizeBytes)}</td>
                      <td className="py-3 text-right">
                        <div className="inline-flex gap-2">
                          {file.isEditable && (
                            <button
                              onClick={() => handleReadFile(currentFilePath ? `${currentFilePath}/${file.name}` : file.name)}
                              className="inline-flex items-center gap-1 px-2.5 py-1 bg-mc-emerald/10 border border-mc-emerald/20 hover:bg-mc-emerald/20 text-mc-emerald font-pixel text-[9px] uppercase cursor-pointer transition-colors"
                            >
                              <Edit className="w-3 h-3" />
                              Edit
                            </button>
                          )}
                          <button
                            onClick={() => handleDeleteFile(currentFilePath ? `${currentFilePath}/${file.name}` : file.name)}
                            disabled={file.name === 'paper.jar'}
                            className="inline-flex items-center gap-1 px-2.5 py-1 bg-status-error/10 border border-status-error/20 hover:bg-status-error/20 text-status-error font-pixel text-[9px] uppercase cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                          >
                            <Trash2 className="w-3 h-3" />
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

    </div>
  );
};

export default FilesTab;
