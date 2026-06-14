import React from 'react';
import { Key, Trash2, Copy, UserCheck, ShieldAlert, FileText } from 'lucide-react';

interface AccessTabProps {
  user: any;
  usersList: any[];
  isLoadingUsers: boolean;
  isCreatingUser: boolean;
  newUsername: string;
  setNewUsername: (val: string) => void;
  newEmail: string;
  setNewEmail: (val: string) => void;
  newPassword: string;
  setNewPassword: (val: string) => void;
  handleCreateUser: (e: React.FormEvent) => void;
  handleDeleteUser: (id: number, username: string) => void;
  copiedUserId: number | null;
  handleCopyEmail: (email: string, id: number) => void;
  showChangePasswordModal: boolean;
  setShowChangePasswordModal: (val: boolean) => void;
  cpCurrentPassword: string;
  setCpCurrentPassword: (val: string) => void;
  cpNewPassword: string;
  setCpNewPassword: (val: string) => void;
  cpConfirmPassword: string;
  setCpConfirmPassword: (val: string) => void;
  isChangingPassword: boolean;
  cpSuccess: string;
  cpError: string;
  setCpError: (val: string) => void;
  setCpSuccess: (val: string) => void;
  handleChangePassword: (e: React.FormEvent) => void;
  
  // Audit Logs
  auditLogs: any[];
  auditTotal: number;
  auditPage: number;
  setAuditPage: (updater: number | ((prev: number) => number)) => void;
  auditLimit: number;
  auditActionFilter: string;
  setAuditActionFilter: (val: string) => void;
  auditUserFilter: string;
  setAuditUserFilter: (val: string) => void;
  auditSearchQuery: string;
  setAuditSearchQuery: (val: string) => void;
  isLoadingAudit: boolean;
  handleAuditSearchSubmit: (e: React.FormEvent) => void;
  expandedAuditId: number | null;
  setExpandedAuditId: (id: number | null) => void;
  fetchAuditLogs: () => void;
  formatDate: (dateStr: string | null) => string;
}

const AccessTab: React.FC<AccessTabProps> = ({
  user,
  usersList,
  isLoadingUsers,
  isCreatingUser,
  newUsername,
  setNewUsername,
  newEmail,
  setNewEmail,
  newPassword,
  setNewPassword,
  handleCreateUser,
  handleDeleteUser,
  copiedUserId,
  handleCopyEmail,
  showChangePasswordModal,
  setShowChangePasswordModal,
  cpCurrentPassword,
  setCpCurrentPassword,
  cpNewPassword,
  setCpNewPassword,
  cpConfirmPassword,
  setCpConfirmPassword,
  isChangingPassword,
  cpSuccess,
  cpError,
  setCpError,
  setCpSuccess,
  handleChangePassword,
  
  auditLogs,
  auditTotal,
  auditPage,
  setAuditPage,
  auditLimit,
  auditActionFilter,
  setAuditActionFilter,
  auditUserFilter,
  setAuditUserFilter,
  auditSearchQuery,
  setAuditSearchQuery,
  isLoadingAudit,
  handleAuditSearchSubmit,
  expandedAuditId,
  setExpandedAuditId,
  fetchAuditLogs,
  formatDate,
}) => {
  return (
    <div className="space-y-8 select-none">
      
      {/* Panel Users Management section */}
      <div className="bg-bg-secondary border border-white/5 p-6 shadow-mc-sm">
        <h3 className="font-pixel text-sm text-mc-emerald mb-4 tracking-wide">Panel Users Management</h3>
        
        {user?.username === 'admin' ? (
          <form onSubmit={handleCreateUser} className="flex flex-col sm:flex-row flex-wrap gap-3 mb-6 items-stretch sm:items-center">
            <input
              type="text"
              placeholder="Username"
              value={newUsername}
              onChange={(e) => setNewUsername(e.target.value)}
              className="px-4 py-2 bg-bg-surface border border-white/10 text-white font-sans text-xs focus:outline-none focus:border-mc-emerald h-10 w-full sm:w-40"
            />
            <input
              type="email"
              placeholder="Email Address"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              className="px-4 py-2 bg-bg-surface border border-white/10 text-white font-sans text-xs focus:outline-none focus:border-mc-emerald h-10 w-full sm:w-52"
            />
            <input
              type="password"
              placeholder="Password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="px-4 py-2 bg-bg-surface border border-white/10 text-white font-sans text-xs focus:outline-none focus:border-mc-emerald h-10 w-full sm:w-40"
            />
            <button
              type="submit"
              disabled={isCreatingUser}
              className="px-5 h-10 bg-gradient-to-r from-mc-emerald to-emerald-700 hover:to-mc-emerald text-bg-primary font-pixel font-bold text-xs tracking-wider border border-mc-emerald/30 cursor-pointer disabled:opacity-50 hover:shadow-[0_0_10px_rgba(46,204,113,0.3)] transition-all w-full sm:w-auto shrink-0 flex items-center justify-center"
            >
              {isCreatingUser ? 'Creating...' : 'Add Administrator'}
            </button>
          </form>
        ) : (
          <div className="bg-bg-surface/50 border border-white/5 px-4 py-3 text-text-secondary text-xs font-mono mb-6 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-mc-gold shrink-0" />
            <span>Only the primary "admin" account is authorized to manage panel users.</span>
          </div>
        )}

        {isLoadingUsers ? (
          <div className="flex justify-center py-6">
            <div className="w-6 h-6 border border-white/25 border-t-mc-emerald rounded-full animate-spin" />
          </div>
        ) : (
          <div>
            {/* Desktop Table View */}
            <div className="hidden sm:block overflow-x-auto">
              <table className="w-full text-left font-sans text-xs border-collapse">
                <thead>
                  <tr className="border-b border-white/10 text-text-muted font-mono uppercase tracking-wider text-[10px]">
                    <th className="pb-3 font-semibold">Username</th>
                    <th className="pb-3 font-semibold">Mail ID</th>
                    <th className="pb-3 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {usersList.map((usr) => (
                    <tr key={usr.id} className="hover:bg-white/[0.01] transition-all">
                      <td className="py-3.5 font-semibold text-white flex items-center gap-1.5">
                        <UserCheck className="w-3.5 h-3.5 text-mc-emerald/70" />
                        {usr.username}
                      </td>
                      <td className="py-3.5">
                        <button 
                          onClick={() => handleCopyEmail(usr.email, usr.id)}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-bg-surface border border-white/5 hover:border-white/10 text-text-secondary hover:text-white transition-all text-xs font-mono cursor-pointer"
                          title="Click to copy email"
                        >
                          <Copy className="w-3 h-3 text-text-muted shrink-0" />
                          <span>{copiedUserId === usr.id ? 'Copied!' : usr.email}</span>
                        </button>
                      </td>
                      <td className="py-3.5 text-right">
                        <div className="inline-flex gap-2 justify-end">
                          {usr.id === user?.id && (
                            <button
                              onClick={() => {
                                setCpCurrentPassword('');
                                setCpNewPassword('');
                                setCpConfirmPassword('');
                                setCpError('');
                                setCpSuccess('');
                                setShowChangePasswordModal(true);
                              }}
                              className="inline-flex items-center justify-center gap-1 px-3 py-1.5 bg-[#45D9FF]/10 border border-[#45D9FF]/20 hover:bg-[#45D9FF]/20 text-[#45D9FF] font-pixel text-[10px] uppercase cursor-pointer transition-all"
                            >
                              <Key className="w-3.5 h-3.5" />
                              Change Password
                            </button>
                          )}
                          {user?.username === 'admin' && (
                            <button
                              onClick={() => handleDeleteUser(usr.id, usr.username)}
                              disabled={usr.id === user?.id}
                              className="inline-flex items-center justify-center gap-1 px-3 py-1.5 bg-status-error/10 border border-status-error/20 hover:bg-status-error/20 text-status-error font-pixel text-[10px] uppercase cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                              Delete Account
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile Card View */}
            <div className="sm:hidden space-y-4">
              {usersList.map((usr) => (
                <div key={usr.id} className="bg-bg-surface border border-white/5 p-4 space-y-3 shadow-mc-sm">
                  {/* Card Header (Username & Icon) */}
                  <div className="flex justify-between items-center border-b border-white/5 pb-2">
                    <div className="flex items-center gap-1.5 font-semibold text-white">
                      <UserCheck className="w-3.5 h-3.5 text-mc-emerald animate-pulse" />
                      <span>{usr.username}</span>
                    </div>
                    {usr.id === user?.id && (
                      <span className="text-[9px] font-mono uppercase px-1.5 py-0.5 bg-mc-emerald/10 text-mc-emerald border border-mc-emerald/20">
                        You
                      </span>
                    )}
                  </div>
                  
                  {/* Card Body (Email copy button) */}
                  <div className="flex flex-col gap-1.5">
                    <span className="text-[9px] font-mono uppercase text-text-muted">Email Address</span>
                    <button 
                      onClick={() => handleCopyEmail(usr.email, usr.id)}
                      className="w-full flex items-center justify-between px-3 py-2 bg-bg-primary/50 border border-white/5 hover:border-white/10 text-text-secondary hover:text-white transition-all text-xs font-mono cursor-pointer"
                      title="Click to copy email"
                    >
                      <span className="truncate mr-2">{copiedUserId === usr.id ? 'Copied to clipboard!' : usr.email}</span>
                      <Copy className="w-3.5 h-3.5 text-text-muted shrink-0" />
                    </button>
                  </div>

                  {/* Card Actions */}
                  <div className="flex flex-col gap-2 pt-2 border-t border-white/5">
                    {usr.id === user?.id && (
                      <button
                        onClick={() => {
                          setCpCurrentPassword('');
                          setCpNewPassword('');
                          setCpConfirmPassword('');
                          setCpError('');
                          setCpSuccess('');
                          setShowChangePasswordModal(true);
                        }}
                        className="w-full flex items-center justify-center gap-1.5 py-2 bg-[#45D9FF]/10 border border-[#45D9FF]/20 hover:bg-[#45D9FF]/20 text-[#45D9FF] font-pixel text-xs uppercase cursor-pointer transition-all"
                      >
                        <Key className="w-3.5 h-3.5" />
                        Change Password
                      </button>
                    )}
                    {user?.username === 'admin' && (
                      <button
                        onClick={() => handleDeleteUser(usr.id, usr.username)}
                        disabled={usr.id === user?.id}
                        className="w-full flex items-center justify-center gap-1.5 py-2 bg-status-error/10 border border-status-error/20 hover:bg-status-error/20 text-status-error font-pixel text-xs uppercase cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        Delete Account
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Compliance Logs Section */}
      <div className="bg-bg-secondary border border-white/5 p-6 shadow-mc-sm">
        <div className="flex justify-between items-center mb-4 border-b border-white/5 pb-3">
          <div className="flex flex-col">
            <h3 className="font-pixel text-sm text-mc-emerald tracking-wide">Compliance Audit Trails</h3>
            <span className="text-[10px] font-mono text-text-muted mt-1 uppercase">Total Events Logged: {auditTotal}</span>
          </div>
        </div>

        {/* Audit Search Filters */}
        <form onSubmit={handleAuditSearchSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="space-y-1.5">
            <span className="block text-[10px] font-mono uppercase tracking-wider text-text-muted">Filter Action</span>
            <select
              value={auditActionFilter}
              onChange={(e) => { setAuditPage(1); setAuditActionFilter(e.target.value); }}
              className="w-full px-3 py-2 bg-bg-surface border border-white/10 text-white font-mono text-xs focus:outline-none focus:border-mc-emerald h-10"
            >
              <option value="">All Actions</option>
              <option value="LOGIN">LOGIN</option>
              <option value="LOGOUT">LOGOUT</option>
              <option value="SERVER_LIFECYCLE">SERVER_LIFECYCLE</option>
              <option value="EXECUTE_COMMAND">EXECUTE_COMMAND</option>
              <option value="UPDATE_CONFIG">UPDATE_CONFIG</option>
              <option value="CREATE_BACKUP">CREATE_BACKUP</option>
              <option value="RESTORE_BACKUP">RESTORE_BACKUP</option>
              <option value="DELETE_BACKUP">DELETE_BACKUP</option>
            </select>
          </div>

          <div className="space-y-1.5">
            <span className="block text-[10px] font-mono uppercase tracking-wider text-text-muted">Actor Username</span>
            <input
              type="text"
              placeholder="e.g. admin"
              value={auditUserFilter}
              onChange={(e) => { setAuditPage(1); setAuditUserFilter(e.target.value); }}
              className="w-full px-3 py-2 bg-bg-surface border border-white/10 text-white font-mono text-xs focus:outline-none focus:border-mc-emerald h-10"
            />
          </div>

          <div className="space-y-1.5">
            <span className="block text-[10px] font-mono uppercase tracking-wider text-text-muted">Search Target / Details</span>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Search details metadata..."
                value={auditSearchQuery}
                onChange={(e) => setAuditSearchQuery(e.target.value)}
                className="flex-grow px-3 py-2 bg-bg-surface border border-white/10 text-white font-mono text-xs focus:outline-none focus:border-mc-emerald h-10"
              />
              <button
                type="submit"
                className="px-4 bg-bg-surface border border-white/10 hover:border-mc-emerald hover:text-white text-text-secondary text-xs font-pixel uppercase cursor-pointer h-10 transition-all shrink-0"
              >
                Search
              </button>
              {(auditSearchQuery || auditActionFilter || auditUserFilter) && (
                <button
                  type="button"
                  onClick={() => {
                    setAuditPage(1);
                    setAuditActionFilter('');
                    setAuditUserFilter('');
                    setAuditSearchQuery('');
                    setTimeout(fetchAuditLogs, 0);
                  }}
                  className="px-3 bg-bg-surface border border-status-error/30 hover:bg-status-error/10 hover:text-status-error text-status-error text-xs font-pixel uppercase cursor-pointer h-10 transition-all shrink-0"
                >
                  Clear
                </button>
              )}
            </div>
          </div>
        </form>

        {isLoadingAudit ? (
          <div className="flex justify-center py-12">
            <div className="w-8 h-8 border-2 border-white/20 border-t-mc-emerald rounded-full animate-spin" />
          </div>
        ) : auditLogs.length > 0 ? (
          <div className="space-y-4">
            <div className="overflow-x-auto">
              <table className="w-full text-left font-sans text-xs border-collapse">
                <thead>
                  <tr className="border-b border-white/10 text-text-muted font-mono uppercase tracking-wider text-[10px]">
                    <th className="pb-3 font-semibold hidden sm:table-cell">Timestamp</th>
                    <th className="pb-3 font-semibold">Actor</th>
                    <th className="pb-3 font-semibold">Action</th>
                    <th className="pb-3 font-semibold hidden sm:table-cell">Target</th>
                    <th className="pb-3 font-semibold hidden md:table-cell">IP Address</th>
                    <th className="pb-3 font-semibold text-right">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {auditLogs.map((log) => {
                    const isExpanded = expandedAuditId === log.id;
                    return (
                      <React.Fragment key={log.id}>
                        <tr className="hover:bg-white/[0.01] transition-all">
                          <td className="py-3 text-text-secondary font-mono hidden sm:table-cell">{formatDate(log.timestamp)}</td>
                          <td className="py-3 font-semibold text-white">{log.username}</td>
                          <td className="py-3">
                            <span className={`px-2 py-0.5 font-mono text-[9px] uppercase border ${
                              log.action.includes('ERROR') || log.action.includes('FAILED')
                                ? 'border-status-error/35 bg-status-error/10 text-status-error'
                                : 'border-mc-emerald/35 bg-mc-emerald/10 text-mc-emerald'
                            }`}>
                              {log.action.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="py-3 hidden sm:table-cell"><code className="font-mono text-[10px] text-text-secondary bg-[#1a1f26] px-1.5 py-0.5 border border-white/5">{log.target}</code></td>
                          <td className="py-3 font-mono text-text-muted hidden md:table-cell">{log.ip_address}</td>
                          <td className="py-3 text-right">
                            <button
                              type="button"
                              onClick={() => setExpandedAuditId(isExpanded ? null : log.id)}
                              className="px-2.5 py-1 bg-bg-surface border border-white/10 hover:text-white transition-colors cursor-pointer text-[10px] font-pixel uppercase"
                            >
                              {isExpanded ? 'Hide Info' : 'Show Info'}
                            </button>
                          </td>
                        </tr>
                        {isExpanded && (
                          <tr>
                            <td colSpan={6} className="bg-[#0b0c10] border border-white/5 p-4 text-text-primary">
                              <div className="flex flex-col gap-2">
                                <div className="flex flex-col gap-2 font-mono text-[10px] text-text-muted mb-2 border-b border-white/5 pb-2">
                                  <span className="sm:hidden">
                                    Timestamp: <span className="text-text-secondary">{formatDate(log.timestamp)}</span>
                                  </span>
                                  <span className="sm:hidden">
                                    Target: <span className="text-text-secondary">{log.target}</span>
                                  </span>
                                  <span className="md:hidden">
                                    IP Address: <span className="text-text-secondary">{log.ip_address}</span>
                                  </span>
                                  <span>
                                    User Agent: <span className="text-text-secondary">{log.user_agent}</span>
                                  </span>
                                </div>
                                {log.details ? (
                                  <pre className="font-mono text-[10px] text-[#f8fafc] leading-relaxed max-h-48 overflow-y-auto bg-[#07080a] p-3 border border-white/5 whitespace-pre">
                                    {JSON.stringify(JSON.parse(log.details), null, 2)}
                                  </pre>
                                ) : (
                                  <span className="text-xs font-mono text-text-muted italic">No metadata payload logged.</span>
                                )}
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="flex justify-between items-center pt-4 border-t border-white/5 text-[10px] font-mono text-text-muted">
              <span>
                Showing { (auditPage - 1) * auditLimit + 1 } - { Math.min(auditPage * auditLimit, auditTotal) } of { auditTotal } compliance events
              </span>
              
              <div className="inline-flex gap-2">
                <button
                  type="button"
                  onClick={() => setAuditPage(p => Math.max(1, p - 1))}
                  disabled={auditPage === 1}
                  className="px-3 py-1.5 bg-bg-surface border border-white/10 hover:border-mc-emerald hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer uppercase font-pixel"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => setAuditPage(p => p + 1)}
                  disabled={auditPage * auditLimit >= auditTotal}
                  className="px-3 py-1.5 bg-bg-surface border border-white/10 hover:border-mc-emerald hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer uppercase font-pixel"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center p-16 bg-[#08090c] border border-white/5 text-center space-y-3">
            <FileText className="w-10 h-10 text-text-muted" />
            <span className="text-text-secondary text-xs font-mono">No compliance events match your search or filter configuration.</span>
          </div>
        )}
      </div>

      {/* Change Password Modal Popup */}
      {showChangePasswordModal && (
        <div 
          className="fixed inset-0 z-[9999] bg-black/60 backdrop-blur-sm flex items-center justify-center animate-in fade-in duration-200"
          onClick={() => setShowChangePasswordModal(false)}
        >
          <div 
            className="relative bg-bg-secondary border border-white/10 p-6 md:p-8 w-full max-w-md shadow-mc-lg animate-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            <button 
              className="absolute top-4 right-4 text-text-muted hover:text-white transition-colors cursor-pointer text-sm font-sans" 
              onClick={() => setShowChangePasswordModal(false)} 
              title="Close"
            >
              ✕
            </button>
            
            <h3 className="font-pixel text-sm text-mc-emerald mb-1">🔒 Change Password</h3>
            <p className="text-text-secondary text-xs font-sans mb-6">
              Logged in as <strong className="text-white">{user?.username}</strong>. Enter credentials to update console password.
            </p>

            <form onSubmit={handleChangePassword} className="space-y-4 font-sans text-xs">
              <div className="space-y-1.5">
                <label className="block font-mono uppercase tracking-wider text-text-muted text-[10px]">Current Password</label>
                <input
                  type="password"
                  placeholder="Enter current password"
                  value={cpCurrentPassword}
                  onChange={(e) => { setCpCurrentPassword(e.target.value); setCpError(''); setCpSuccess(''); }}
                  className="w-full px-3 py-2 bg-bg-surface border border-white/10 text-white focus:outline-none focus:border-mc-emerald"
                  autoComplete="current-password"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block font-mono uppercase tracking-wider text-text-muted text-[10px]">New Password</label>
                <input
                  type="password"
                  placeholder="Min. 8 characters"
                  value={cpNewPassword}
                  onChange={(e) => { setCpNewPassword(e.target.value); setCpError(''); setCpSuccess(''); }}
                  className="w-full px-3 py-2 bg-bg-surface border border-white/10 text-white focus:outline-none focus:border-mc-emerald"
                  autoComplete="new-password"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block font-mono uppercase tracking-wider text-text-muted text-[10px]">Confirm New Password</label>
                <input
                  type="password"
                  placeholder="Re-enter new password"
                  value={cpConfirmPassword}
                  onChange={(e) => { setCpConfirmPassword(e.target.value); setCpError(''); setCpSuccess(''); }}
                  className="w-full px-3 py-2 bg-bg-surface border border-white/10 text-white focus:outline-none focus:border-mc-emerald"
                  autoComplete="new-password"
                />
              </div>

              {cpError && (
                <div className="p-3 bg-status-error/10 border border-status-error/20 text-status-error font-mono text-[11px] leading-tight">
                  {cpError}
                </div>
              )}
              {cpSuccess && (
                <div className="p-3 bg-mc-emerald/10 border border-mc-emerald/20 text-mc-emerald font-mono text-[11px] leading-tight">
                  {cpSuccess}
                </div>
              )}

              <div className="flex gap-2 pt-2">
                <button
                  type="submit"
                  disabled={isChangingPassword}
                  className="px-5 py-2 bg-gradient-to-r from-mc-emerald to-emerald-700 hover:to-mc-emerald text-bg-primary font-pixel font-bold text-xs tracking-wider border border-mc-emerald/30 cursor-pointer disabled:opacity-50 hover:shadow-[0_0_10px_rgba(46,204,113,0.3)] transition-all flex-1"
                >
                  {isChangingPassword ? 'Updating...' : 'Update Password'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowChangePasswordModal(false)}
                  className="px-4 py-2 bg-bg-surface border border-white/10 hover:border-white/20 text-text-secondary hover:text-white transition-colors cursor-pointer text-xs font-pixel"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};

export default AccessTab;
