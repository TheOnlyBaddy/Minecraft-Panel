import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useConsoleWebSocket } from '../../hooks/useConsoleWebSocket';
import { useToast } from '../../context/ToastContext';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Terminal, Settings, FileText, Users, Layers, FolderOpen, Database, 
  Copy, LogOut, ChevronLeft, ChevronRight, ShieldAlert, Server, Globe,
  Menu, X
} from 'lucide-react';
import Logo from '../../components/Logo';


// Tab imports
import ServerTab from './tabs/ServerTab';
import ConsoleTab from './tabs/ConsoleTab';
import OptionsTab from './tabs/OptionsTab';
import PlayersTab from './tabs/PlayersTab';
import PluginsTab from './tabs/PluginsTab';
import FilesTab from './tabs/FilesTab';
import WorldsTab from './tabs/WorldsTab';
import BackupsTab from './tabs/BackupsTab';
import AccessTab from './tabs/AccessTab';

// Audio chime imports
import { 
  playStartChime, playStopChime, playRestartChime,
  playPlayerJoinChime, playPlayerLeaveChime
} from '../../utils/audio';

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

const DEFAULT_CONFIG = {
  'max-players': 20,
  'gamemode': 'survival',
  'difficulty': 'normal',
  'white-list': false,
  'online-mode': true,
  'allow-flight': false,
  'force-gamemode': false,
  'spawn-protection': 16,
  'require-resource-pack': false,
  'pvp': true,
  'spawn-monsters': true,
  'spawn-animals': true,
  'spawn-npcs': true,
};

const Dashboard: React.FC = () => {
  const { user, logout, panelName } = useAuth();
  const { showToast } = useToast();
  const { data: telemetryData, isConnected: isTelemetryConnected, error: wsError } = useWebSocket();
  const { logs, isConnected: isConsoleConnected, error: consoleError, clearLogs } = useConsoleWebSocket();

  // Sidebar Collapse state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Navigation tab state
  const [activeTab, setActiveTab] = useState<'server' | 'options' | 'console' | 'log' | 'players' | 'plugins' | 'files' | 'worlds' | 'backups' | 'access'>('server');

  // Logs states
  const [logText, setLogText] = useState('');
  const [isLoadingLog, setIsLoadingLog] = useState(false);

  // Players states
  const [activePlayerList, setActivePlayerList] = useState<'online' | 'whitelist' | 'ops' | 'banned-players' | 'banned-ips'>('online');
  const [playersData, setPlayersData] = useState<any[]>([]);
  const [isLoadingPlayers, setIsLoadingPlayers] = useState(false);
  const [newPlayerNameOrIp, setNewPlayerNameOrIp] = useState('');
  const [banReason, setBanReason] = useState('Banned by administrator');

  // Files states
  const [currentFilePath, setCurrentFilePath] = useState('');
  const [filesList, setFilesList] = useState<any[]>([]);
  const [isLoadingFiles, setIsLoadingFiles] = useState(false);
  const [editingFilePath, setEditingFilePath] = useState<string | null>(null);
  const [editingFileContent, setEditingFileContent] = useState('');
  const [isSavingFile, setIsSavingFile] = useState(false);

  // Worlds states
  const [worldStats, setWorldStats] = useState<any>(null);
  const [isLoadingWorldStats, setIsLoadingWorldStats] = useState(false);
  const [isResettingWorld, setIsResettingWorld] = useState(false);

  // Access (Users list) states
  const [usersList, setUsersList] = useState<any[]>([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [copiedUserId, setCopiedUserId] = useState<number | null>(null);
  const [isCreatingUser, setIsCreatingUser] = useState(false);

  // Change password states
  const [showChangePasswordModal, setShowChangePasswordModal] = useState(false);
  const [cpCurrentPassword, setCpCurrentPassword] = useState('');
  const [cpNewPassword, setCpNewPassword] = useState('');
  const [cpConfirmPassword, setCpConfirmPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [cpSuccess, setCpSuccess] = useState('');
  const [cpError, setCpError] = useState('');

  // Overview historical metrics data for SVG Sparklines
  const [cpuHistory, setCpuHistory] = useState<number[]>([]);
  const [memHistory, setMemHistory] = useState<number[]>([]);
  const [actionPending, setActionPending] = useState<string | null>(null);
  const [isRestarting, setIsRestarting] = useState(false);
  const prevStatusRef = useRef<string | null>(null);
  const prevPlayerCountRef = useRef<number | null>(null);
  const prevPlayersListRef = useRef<string[] | null>(null);

  // Console terminal states
  const [searchQuery, setSearchQuery] = useState('');
  const [commandInput, setCommandInput] = useState('');
  const [isExecutingCommand, setIsExecutingCommand] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const terminalBodyRef = useRef<HTMLDivElement | null>(null);

  // Backups states
  const [backups, setBackups] = useState<BackupData[]>([]);
  const [isLoadingBackups, setIsLoadingBackups] = useState(false);
  const [isCreatingBackup, setIsCreatingBackup] = useState(false);
  const [restoringBackupId, setRestoringBackupId] = useState<number | null>(null);
  const [deletingBackupId, setDeletingBackupId] = useState<number | null>(null);

  // Config states
  const [config, setConfig] = useState<Record<string, any>>({});
  const [isLoadingConfig, setIsLoadingConfig] = useState(false);
  const [isSavingConfig, setIsSavingConfig] = useState(false);

  // Audit logs states
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [auditTotal, setAuditTotal] = useState(0);
  const [auditPage, setAuditPage] = useState(1);
  const [auditLimit] = useState(20);
  const [auditActionFilter, setAuditActionFilter] = useState('');
  const [auditUserFilter, setAuditUserFilter] = useState('');
  const [auditSearchQuery, setAuditSearchQuery] = useState('');
  const [isLoadingAudit, setIsLoadingAudit] = useState(false);
  const [expandedAuditId, setExpandedAuditId] = useState<number | null>(null);

  // Plugins states
  const [installedPlugins, setInstalledPlugins] = useState<any[]>([]);
  const [isLoadingPlugins, setIsLoadingPlugins] = useState(false);
  const [isUninstallingPlugin, setIsUninstallingPlugin] = useState<Record<string, boolean>>({});
  const [isDragging, setIsDragging] = useState(false);
  const [isUploadingPluginFile, setIsUploadingPluginFile] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopyAddress = () => {
    const address = telemetryData?.server_address || '127.0.0.1:25565';
    navigator.clipboard.writeText(address);
    setCopied(true);
    showToast('Copied server IP address to clipboard!', 'success');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopyEmail = (email: string, id: number) => {
    navigator.clipboard.writeText(email);
    setCopiedUserId(id);
    showToast('Copied email to clipboard!', 'success');
    setTimeout(() => setCopiedUserId(null), 2000);
  };

  const isModerator = false;

  // Keep track of historical metrics data
  useEffect(() => {
    if (telemetryData) {
      setCpuHistory((prev) => {
        const next = [...prev, telemetryData.cpu_percent];
        return next.slice(-30);
      });
      setMemHistory((prev) => {
        const memPercent = telemetryData.memory_total > 0 ? (telemetryData.memory_used / telemetryData.memory_total) * 100 : 0;
        const next = [...prev, memPercent];
        return next.slice(-30);
      });
    }
  }, [telemetryData]);

  // Track server status transitions and notify the user
  useEffect(() => {
    if (telemetryData) {
      const status = telemetryData.server_status;
      if (prevStatusRef.current !== null && prevStatusRef.current !== status) {
        if (status === 'RUNNING') {
          if (isRestarting) {
            setIsRestarting(false);
            showToast('Server restarted successfully!', 'success');
            playRestartChime();
          } else {
            showToast('Server is now online!', 'success');
            playStartChime();
          }
        } else if (status === 'STOPPED') {
          if (!isRestarting) {
            showToast('Server has stopped.', 'error');
            playStopChime();
          }
        } else if (status === 'CRASHED') {
          setIsRestarting(false);
          showToast('Server crashed!', 'error');
          playStopChime();
        }
      }
      prevStatusRef.current = status;
    }
  }, [telemetryData?.server_status, isRestarting, showToast]);

  // Track player joins and leaves via telemetry data
  useEffect(() => {
    if (telemetryData && telemetryData.server_status === 'RUNNING') {
      const currentList = telemetryData.active_players_list;
      const currentCount = telemetryData.active_players;

      if (currentList) {
        if (prevPlayersListRef.current !== null) {
          // Find who joined
          const joined = currentList.filter(p => !prevPlayersListRef.current!.includes(p));
          // Find who left
          const left = prevPlayersListRef.current!.filter(p => !currentList.includes(p));

          if (joined.length > 0) {
            joined.forEach(player => {
              showToast(`${player} joined the game`, 'success');
            });
            playPlayerJoinChime();
          }
          if (left.length > 0) {
            left.forEach(player => {
              showToast(`${player} left the game`, 'info');
            });
            playPlayerLeaveChime();
          }
        }
        prevPlayersListRef.current = currentList;
        prevPlayerCountRef.current = currentCount;
      } else {
        // Fallback to count if list is not present
        if (prevPlayerCountRef.current !== null) {
          if (currentCount > prevPlayerCountRef.current) {
            showToast('A player joined the game', 'success');
            playPlayerJoinChime();
          } else if (currentCount < prevPlayerCountRef.current) {
            showToast('A player left the game', 'info');
            playPlayerLeaveChime();
          }
        }
        prevPlayerCountRef.current = currentCount;
        prevPlayersListRef.current = null;
      }
    } else {
      // If server is not running, reset the tracking refs
      prevPlayerCountRef.current = null;
      prevPlayersListRef.current = null;
    }
  }, [telemetryData?.active_players, telemetryData?.active_players_list, telemetryData?.server_status, showToast]);

  // Terminal Auto-scrolling to bottom
  useEffect(() => {
    if (autoScroll && terminalBodyRef.current) {
      terminalBodyRef.current.scrollTop = terminalBodyRef.current.scrollHeight;
    }
  }, [logs, autoScroll, activeTab]);

  // Tab switch effect to fetch data dynamically
  useEffect(() => {
    if (activeTab === 'backups') {
      fetchBackups();
    } else if (activeTab === 'options') {
      fetchConfig();
    } else if (activeTab === 'log') {
      fetchLatestLog();
    } else if (activeTab === 'players') {
      fetchPlayers();
    } else if (activeTab === 'plugins') {
      fetchInstalledPlugins();
    } else if (activeTab === 'files') {
      fetchFiles();
    } else if (activeTab === 'worlds') {
      fetchWorldStats();
    } else if (activeTab === 'access') {
      fetchUsers();
      fetchAuditLogs();
    }
  }, [activeTab, auditPage, auditActionFilter, auditUserFilter, currentFilePath, activePlayerList]);

  // Auto-refresh online players tab when telemetry active_players changes (joined/left)
  useEffect(() => {
    if (activeTab === 'players' && activePlayerList === 'online') {
      fetchPlayers();
    }
  }, [telemetryData?.active_players]);

  const fetchBackups = async () => {
    setIsLoadingBackups(true);
    try {
      const response = await fetch('/api/backups');
      if (response.ok) {
        const data = await response.json();
        setBackups(data);
      }
    } catch (err) {
      console.error('Failed to load backups data:', err);
      showToast('Failed to load backups list.', 'error');
    } finally {
      setIsLoadingBackups(false);
    }
  };

  const fetchLatestLog = async () => {
    setIsLoadingLog(true);
    try {
      const response = await fetch('/api/server/logs/latest');
      if (response.ok) {
        const data = await response.json();
        setLogText(data.content || '');
      } else {
        showToast('Failed to load latest.log.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Failed to fetch server logs.', 'error');
    } finally {
      setIsLoadingLog(false);
    }
  };

  const handleClearLog = async () => {
    if (!confirm('Are you sure you want to clear latest.log?')) return;
    try {
      const response = await fetch('/api/server/logs/clear', { method: 'POST' });
      if (response.ok) {
        showToast('Log file cleared successfully.', 'success');
        fetchLatestLog();
      } else {
        showToast('Failed to clear log file.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Failed to clear log file.', 'error');
    }
  };

  const handleCreateBackup = async () => {
    setIsCreatingBackup(true);
    showToast('Creating server backup, please wait...', 'info');
    try {
      const response = await fetch('/api/backups/create', { method: 'POST' });
      if (response.ok) {
        showToast('Backup archive created successfully!', 'success');
        fetchBackups();
      } else {
        const errDetails = await response.json();
        showToast(`Backup failed: ${errDetails.detail || 'Unknown error'}`, 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Failed to contact backup API.', 'error');
    } finally {
      setIsCreatingBackup(false);
    }
  };

  const handleRestoreBackup = async (id: number, filename: string) => {
    if (!confirm(`Warning: Restoring backup "${filename}" will overwrite current world files. Proceed?`)) return;
    setRestoringBackupId(id);
    showToast('Restoring backup in progress, please wait...', 'info');
    try {
      const response = await fetch(`/api/backups/restore/${id}`, { method: 'POST' });
      if (response.ok) {
        showToast('Backup restored successfully. Please restart server.', 'success');
        fetchBackups();
      } else {
        const errDetails = await response.json();
        showToast(`Restore failed: ${errDetails.detail || 'Unknown error'}`, 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Failed to restore backup.', 'error');
    } finally {
      setRestoringBackupId(null);
    }
  };

  const handleDeleteBackup = async (id: number, filename: string) => {
    if (!confirm(`Are you sure you want to delete backup "${filename}"?`)) return;
    setDeletingBackupId(id);
    try {
      const response = await fetch(`/api/backups/${id}`, { method: 'DELETE' });
      if (response.ok) {
        showToast('Backup deleted successfully.', 'success');
        fetchBackups();
      } else {
        showToast('Failed to delete backup.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Failed to delete backup.', 'error');
    } finally {
      setDeletingBackupId(null);
    }
  };

  const fetchUsers = async () => {
    setIsLoadingUsers(true);
    try {
      const response = await fetch('/api/users');
      if (response.ok) {
        const data = await response.json();
        setUsersList(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingUsers(false);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUsername.trim() || !newPassword.trim() || !newEmail.trim()) {
      showToast('All fields are required to create a user.', 'warning');
      return;
    }
    setIsCreatingUser(true);
    try {
      const response = await fetch('/api/users/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: newUsername.trim(),
          email: newEmail.trim(),
          password: newPassword.trim(),
          role: 'ROLE_ADMIN'
        })
      });
      if (response.ok) {
        showToast('Administrator user created successfully!', 'success');
        setNewUsername('');
        setNewEmail('');
        setNewPassword('');
        fetchUsers();
      } else {
        const errDetails = await response.json();
        showToast(`Failed to create user: ${errDetails.detail || 'Unknown error'}`, 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Failed to create user.', 'error');
    } finally {
      setIsCreatingUser(false);
    }
  };

  const handleDeleteUser = async (id: number, username: string) => {
    if (!confirm(`Are you sure you want to delete user account "${username}"?`)) return;
    try {
      const response = await fetch(`/api/users/${id}`, { method: 'DELETE' });
      if (response.ok) {
        showToast('User account deleted successfully.', 'success');
        fetchUsers();
      } else {
        showToast('Failed to delete user.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Failed to delete user.', 'error');
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cpCurrentPassword.trim() || !cpNewPassword.trim() || !cpConfirmPassword.trim()) {
      setCpError('All fields are required.');
      return;
    }
    if (cpNewPassword.length < 8) {
      setCpError('New password must be at least 8 characters long.');
      return;
    }
    if (cpNewPassword !== cpConfirmPassword) {
      setCpError('New password and confirmation do not match.');
      return;
    }

    setIsChangingPassword(true);
    setCpError('');
    setCpSuccess('');
    try {
      const response = await fetch('/api/auth/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_password: cpCurrentPassword,
          new_password: cpNewPassword
        })
      });
      if (response.ok) {
        showToast('Password updated successfully!', 'success');
        setCpSuccess('Password changed successfully.');
        setCpCurrentPassword('');
        setCpNewPassword('');
        setCpConfirmPassword('');
        setTimeout(() => setShowChangePasswordModal(false), 1200);
      } else {
        const errDetails = await response.json();
        setCpError(errDetails.detail || 'Failed to change password.');
      }
    } catch (err) {
      console.error(err);
      setCpError('Failed to change password due to network error.');
    } finally {
      setIsChangingPassword(false);
    }
  };

  const fetchInstalledPlugins = async () => {
    setIsLoadingPlugins(true);
    try {
      const response = await fetch('/api/server/plugins');
      if (response.ok) {
        const data = await response.json();
        setInstalledPlugins(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingPlugins(false);
    }
  };

  const handleUploadPluginFile = async (file: File) => {
    setIsUploadingPluginFile(true);
    showToast(`Uploading plugin "${file.name}"...`, 'info');
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await fetch('/api/server/plugins/upload', {
        method: 'POST',
        body: formData
      });
      if (response.ok) {
        showToast('Plugin uploaded successfully! Please restart the server.', 'success');
        fetchInstalledPlugins();
      } else {
        const errDetails = await response.json();
        showToast(`Upload failed: ${errDetails.detail || 'Unknown error'}`, 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Failed to upload plugin.', 'error');
    } finally {
      setIsUploadingPluginFile(false);
    }
  };

  const handleUninstallPlugin = async (filename: string) => {
    if (!confirm(`Are you sure you want to uninstall/delete "${filename}"?`)) return;
    setIsUninstallingPlugin(prev => ({ ...prev, [filename]: true }));
    try {
      const response = await fetch(`/api/server/plugins/uninstall?file_name=${filename}`, {
        method: 'POST'
      });
      if (response.ok) {
        showToast('Plugin uninstalled successfully. Please restart server.', 'success');
        fetchInstalledPlugins();
      } else {
        showToast('Failed to uninstall plugin.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Failed to uninstall plugin.', 'error');
    } finally {
      setIsUninstallingPlugin(prev => ({ ...prev, [filename]: false }));
    }
  };

  const fetchFiles = async () => {
    setIsLoadingFiles(true);
    try {
      const params = new URLSearchParams();
      if (currentFilePath) params.append('path', currentFilePath);
      const response = await fetch(`/api/server/files/list?${params.toString()}`);
      if (response.ok) {
        const data = await response.json();
        setFilesList(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingFiles(false);
    }
  };

  const handleNavigateFiles = (name: string) => {
    if (name === '..') {
      const parts = currentFilePath.split('/');
      parts.pop();
      setCurrentFilePath(parts.join('/'));
    } else {
      setCurrentFilePath(currentFilePath ? `${currentFilePath}/${name}` : name);
    }
  };

  const handleReadFile = async (path: string) => {
    setIsLoadingFiles(true);
    try {
      const params = new URLSearchParams({ path });
      const response = await fetch(`/api/server/files/read?${params.toString()}`);
      if (response.ok) {
        const data = await response.json();
        setEditingFilePath(path);
        setEditingFileContent(data.content || '');
      } else {
        showToast('Failed to read file.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Failed to read file.', 'error');
    } finally {
      setIsLoadingFiles(false);
    }
  };

  const handleWriteFile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingFilePath) return;
    setIsSavingFile(true);
    try {
      const response = await fetch('/api/server/files/write', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          path: editingFilePath,
          content: editingFileContent
        })
      });
      if (response.ok) {
        showToast('File saved successfully!', 'success');
        setEditingFilePath(null);
        fetchFiles();
      } else {
        showToast('Failed to save file changes.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Failed to save file.', 'error');
    } finally {
      setIsSavingFile(false);
    }
  };

  const handleDeleteFile = async (path: string) => {
    if (!confirm(`Are you sure you want to delete file "${path}"?`)) return;
    try {
      const params = new URLSearchParams({ path });
      const response = await fetch(`/api/server/files/delete?${params.toString()}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        showToast('File deleted successfully.', 'success');
        fetchFiles();
      } else {
        showToast('Failed to delete file.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Failed to delete file.', 'error');
    }
  };

  const fetchWorldStats = async () => {
    setIsLoadingWorldStats(true);
    try {
      const response = await fetch('/api/server/worlds/stats');
      if (response.ok) {
        const data = await response.json();
        setWorldStats(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingWorldStats(false);
    }
  };

  const handleDownloadWorld = () => {
    showToast('Preparing world download ZIP...', 'info');
    window.open('/api/server/worlds/download', '_blank');
  };

  const handleResetWorld = async () => {
    if (!confirm('CRITICAL WARNING: This will stop the server and recursively delete all world folders! Continue?')) return;
    const name = prompt('Type "RESET" to confirm:');
    if (name !== 'RESET') {
      showToast('Reset cancelled.', 'info');
      return;
    }
    setIsResettingWorld(true);
    try {
      const response = await fetch('/api/server/worlds/reset', { method: 'POST' });
      if (response.ok) {
        showToast('Minecraft worlds successfully reset!', 'success');
        fetchWorldStats();
      } else {
        showToast('Failed to reset worlds.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Failed to reset worlds due to API error.', 'error');
    } finally {
      setIsResettingWorld(false);
    }
  };

  const runPlayerCommand = async (command: 'op' | 'deop' | 'kick' | 'ban', username: string) => {
    let finalCommand = `${command} ${username}`;
    if (command === 'ban') {
      finalCommand = `ban ${username} Banned by administrator`;
    }
    try {
      const response = await fetch('/api/server/console/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: finalCommand })
      });
      if (response.ok) {
        showToast(`Command /${finalCommand} executed.`, 'success');
        setTimeout(fetchPlayers, 800);
      } else {
        showToast('Failed to run player command.', 'error');
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchPlayers = async () => {
    setIsLoadingPlayers(true);
    try {
      const endpoint = activePlayerList === 'online' 
        ? '/api/server/players/online' 
        : `/api/server/players?list_type=${activePlayerList}`;
      const response = await fetch(endpoint);
      if (response.ok) {
        const data = await response.json();
        setPlayersData(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingPlayers(false);
    }
  };

  const handleRemovePlayer = async (target: string) => {
    try {
      const response = await fetch('/api/server/players/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          list_type: activePlayerList,
          username_or_ip: target
        })
      });
      if (response.ok) {
        showToast('Removed entry from list successfully.', 'success');
        fetchPlayers();
      } else {
        const errDetails = await response.json();
        showToast(`Failed to remove entry: ${errDetails.detail || 'Unknown error'}`, 'error');
      }
    } catch (e) {
      console.error(e);
      showToast('Failed to remove entry due to network error.', 'error');
    }
  };

  const handleAddPlayer = async (e: React.FormEvent) => {
    e.preventDefault();
    const val = newPlayerNameOrIp.trim();
    if (!val) return;

    try {
      const response = await fetch('/api/server/players/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          list_type: activePlayerList,
          username_or_ip: val,
          reason: banReason
        })
      });
      if (response.ok) {
        showToast(`Added ${val} to list successfully.`, 'success');
        setNewPlayerNameOrIp('');
        fetchPlayers();
      } else {
        const errDetails = await response.json();
        showToast(`Failed to add entry: ${errDetails.detail || 'Unknown error'}`, 'error');
      }
    } catch (e) {
      console.error(e);
      showToast('Failed to add entry due to network error.', 'error');
    }
  };

  const fetchConfig = async () => {
    setIsLoadingConfig(true);
    try {
      const response = await fetch('/api/server/config');
      if (response.ok) {
        const data = await response.json();
        setConfig({ ...DEFAULT_CONFIG, ...data });
      } else {
        const errDetails = await response.json();
        showToast(`Failed to load config: ${errDetails.detail}`, 'error');
      }
    } catch (err) {
      console.error('Failed to load configuration:', err);
    } finally {
      setIsLoadingConfig(false);
    }
  };

  const handleConfigChange = (key: string, value: any) => {
    setConfig((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingConfig(true);
    try {
      const response = await fetch('/api/server/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        showToast('Settings saved! Restart the server to apply changes.', 'success');
        fetchConfig();
      } else {
        const errDetails = await response.json();
        showToast(`Failed to save config: ${errDetails.detail || 'Unknown error'}`, 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Network request failed. Verify that server API is running.', 'error');
    } finally {
      setIsSavingConfig(false);
    }
  };

  const fetchAuditLogs = async () => {
    setIsLoadingAudit(true);
    try {
      const params = new URLSearchParams({
        page: auditPage.toString(),
        limit: auditLimit.toString(),
      });
      if (auditActionFilter) params.append('action', auditActionFilter);
      if (auditUserFilter) params.append('username', auditUserFilter);
      if (auditSearchQuery) params.append('search', auditSearchQuery);

      const response = await fetch(`/api/audit?${params.toString()}`);
      if (response.ok) {
        const data = await response.json();
        setAuditLogs(data.records);
        setAuditTotal(data.total);
      } else {
        const errDetails = await response.json();
        showToast(`Failed to load audit logs: ${errDetails.detail || 'Unknown error'}`, 'error');
      }
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setIsLoadingAudit(false);
    }
  };

  const handleAuditSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setAuditPage(1);
    fetchAuditLogs();
  };

  const handleAction = async (action: 'start' | 'stop' | 'restart') => {
    setActionPending(action);
    if (action === 'restart') {
      setIsRestarting(true);
    } else {
      setIsRestarting(false);
    }
    
    // Custom toasts: start -> success (green), stop -> error (red), restart -> warning (yellow)
    const actionLabels = {
      start: 'Server starting...',
      stop: 'Server stopping...',
      restart: 'Server restarting...',
    };
    const actionTypes = {
      start: 'success' as const,
      stop: 'error' as const,
      restart: 'warning' as const,
    };
    showToast(actionLabels[action], actionTypes[action]);

    try {
      const response = await fetch('/api/server/lifecycle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action }),
      });
      
      if (!response.ok) {
        const errDetails = await response.json();
        setIsRestarting(false);
        showToast(`Action failed: ${errDetails.detail || 'Unknown error'}`, 'error');
      }
    } catch (err) {
      console.error('Lifecycle action request failed:', err);
      setIsRestarting(false);
      showToast('Network request failed. Please check that server API is running.', 'error');
    } finally {
      setTimeout(() => {
        setActionPending(null);
      }, 1500);
    }
  };

  const handleSendCommand = async (e: React.FormEvent) => {
    e.preventDefault();
    const cmd = commandInput.trim();
    if (!cmd || isExecutingCommand) return;

    setIsExecutingCommand(true);
    try {
      const response = await fetch('/api/server/console/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: cmd }),
      });

      if (response.ok) {
        setCommandInput('');
        showToast(`Command "/${cmd}" sent.`, 'success');
      } else {
        const errData = await response.json();
        showToast(`Failed to execute command: ${errData.detail || 'Unknown error'}`, 'error');
      }
    } catch (err) {
      console.error('Command dispatch error:', err);
      showToast('Network request failed. Ensure server API is reachable.', 'error');
    } finally {
      setIsExecutingCommand(false);
    }
  };

  const formatGB = (bytes: number) => {
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
  };

  const formatMB = (bytes: number) => {
    if (bytes === 0) return '0.0 MB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Unknown';
    return new Date(dateStr).toLocaleString();
  };

  const getStatusText = (status: string) => {
    if (isRestarting) return 'Restarting...';
    switch (status) {
      case 'RUNNING': return 'Online';
      case 'STARTING': return 'Starting...';
      case 'STOPPING': return 'Stopping...';
      case 'CRASHED': return 'Crashed';
      case 'STOPPED': return 'Offline';
      default: return status;
    }
  };

  const getSparklinePaths = (values: number[], width: number, height: number) => {
    if (values.length < 2) {
      return { path: '', areaPath: '' };
    }
    const points = values.map((val, i) => {
      const x = (i / (values.length - 1)) * width;
      const clampedVal = Math.max(0, Math.min(100, val));
      const y = height - (clampedVal / 100) * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });

    const path = `M ${points.join(' L ')}`;
    const areaPath = `${path} L ${width.toFixed(1)},${height.toFixed(1)} L 0,${height.toFixed(1)} Z`;
    return { path, areaPath };
  };

  const getLogClass = (line: string) => {
    const upper = line.toUpperCase();
    if (upper.includes('[WARN]') || upper.includes('[WARNING]')) {
      return 'text-status-warning font-semibold';
    }
    if (upper.includes('[ERROR]') || upper.includes('[SEVERE]') || upper.includes('[PANEL ERROR]')) {
      return 'text-status-error font-bold';
    }
    if (upper.includes('[PANEL]')) {
      if (upper.includes('ERROR')) return 'text-status-error border-l-2 border-status-error pl-1 font-bold';
      if (upper.includes('SUCCESS') || upper.includes('BOOT DETECTED')) return 'text-mc-emerald font-semibold';
      return 'text-mc-diamond font-medium';
    }
    return 'text-text-secondary';
  };

  const handleScroll = () => {
    if (!terminalBodyRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = terminalBodyRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 30;
    setAutoScroll(isAtBottom);
  };

  const currentStatus = telemetryData?.server_status || 'STOPPED';
  const isServerOffline = currentStatus === 'STOPPED' || currentStatus === 'CRASHED';

  const sparkWidth = 500;
  const sparkHeight = 180;
  const cpuPaths = getSparklinePaths(cpuHistory, sparkWidth, sparkHeight);
  const memPaths = getSparklinePaths(memHistory, sparkWidth, sparkHeight);

  const memPercent = telemetryData?.memory_total ? (telemetryData.memory_used / telemetryData.memory_total) * 100 : 0;
  const diskPercent = telemetryData?.disk_total ? (telemetryData.disk_used / telemetryData.disk_total) * 100 : 0;

  const filteredLogs = logs.filter((line) =>
    line.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex h-screen w-full bg-bg-primary overflow-hidden text-text-primary">
      {/* Mobile Drawer Backdrop Overlay */}
      {mobileMenuOpen && (
        <div 
          onClick={() => setMobileMenuOpen(false)}
          className="fixed inset-0 bg-black/60 z-40 md:hidden transition-all duration-300"
        />
      )}

      {/* Sidebar Navigation */}
      <aside className={`bg-bg-secondary border-r border-white/5 flex flex-col h-screen transition-all duration-300 z-50 shrink-0 fixed md:relative top-0 bottom-0 left-0 ${
        mobileMenuOpen 
          ? 'translate-x-0 w-[280px]' 
          : '-translate-x-full md:translate-x-0 ' + (sidebarCollapsed ? 'md:w-16' : 'md:w-[280px]')
      }`}>
        
        {/* Logo area */}
        <div className="flex items-center justify-between p-4 border-b border-white/5 h-16 shrink-0">
          {(!sidebarCollapsed || mobileMenuOpen) && (
            <div className="flex items-center gap-2 text-white font-pixel text-base tracking-wider">
              <Logo 
                className="w-5 h-5 object-contain animate-pulse"
                fallbackIconClassName="w-5 h-5 text-mc-emerald animate-pulse"
              />
              <span>{panelName}</span>
            </div>
          )}
          {sidebarCollapsed && !mobileMenuOpen && (
            <Logo 
              className="w-5 h-5 object-contain mx-auto animate-pulse"
              fallbackIconClassName="w-5 h-5 text-mc-emerald mx-auto animate-pulse"
            />
          )}
          <button 
            onClick={() => {
              if (window.innerWidth < 768) {
                setMobileMenuOpen(false);
              } else {
                setSidebarCollapsed(!sidebarCollapsed);
              }
            }}
            className="text-text-muted hover:text-white transition-colors cursor-pointer"
          >
            <span className="md:hidden">
              <X className="w-5 h-5" />
            </span>
            <span className="hidden md:inline">
              {sidebarCollapsed ? <ChevronRight className="w-5 h-5 mx-auto" /> : <ChevronLeft className="w-5 h-5" />}
            </span>
          </button>
        </div>

        {/* Navigation links */}
        <nav className="flex-1 py-4 space-y-1 overflow-y-auto">
          {([
            { id: 'server', label: 'Server', icon: Server },
            { id: 'console', label: 'Console', icon: Terminal },
            { id: 'options', label: 'Properties', icon: Settings },
            { id: 'log', label: 'Logs', icon: FileText },
            { id: 'players', label: 'Players', icon: Users },
            { id: 'plugins', label: 'Plugins', icon: Layers },
            { id: 'files', label: 'Files', icon: FolderOpen },
            { id: 'worlds', label: 'Worlds', icon: Globe },
            { id: 'backups', label: 'Backups', icon: Database },
            { id: 'access', label: 'Access', icon: ShieldAlert },
          ] as const).map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  setMobileMenuOpen(false);
                }}
                className={`w-full flex items-center px-4 py-3 text-xs border-l-4 transition-all duration-150 cursor-pointer ${
                  isActive 
                    ? 'border-mc-emerald bg-bg-surface text-white shadow-[inset_4px_0_0_0_rgba(46,204,113,0.1)] font-medium' 
                    : 'border-transparent text-text-secondary hover:text-white hover:bg-bg-surface/30 hover:border-white/10'
                }`}
              >
                <Icon className={`w-4 h-4 shrink-0 ${(sidebarCollapsed && !mobileMenuOpen) ? 'mx-auto' : 'mr-3'}`} />
                {(!sidebarCollapsed || mobileMenuOpen) && <span>{item.label}</span>}
              </button>
            );
          })}
        </nav>

        {/* Server Status & Address Widget */}
        {!sidebarCollapsed ? (
          <div className="mx-3 mb-2 p-3 bg-bg-surface/40 border border-white/5 space-y-2.5">
            {/* Status */}
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">Server Status</span>
              <div className="flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-none ${
                  isRestarting ? 'bg-status-warning animate-pulse' :
                  currentStatus === 'RUNNING' ? 'bg-status-online shadow-[0_0_8px_rgba(46,204,113,0.5)]' :
                  currentStatus === 'STARTING' ? 'bg-status-starting animate-pulse' :
                  currentStatus === 'STOPPING' ? 'bg-status-stopping animate-pulse' : 'bg-status-offline'
                }`} />
                <span className="text-xs font-pixel text-white uppercase">{getStatusText(currentStatus)}</span>
              </div>
            </div>
            {/* Version */}
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">Minecraft Version</span>
              <span className="text-xs font-mono text-white">{telemetryData?.minecraft_version || '26.1.2'}</span>
            </div>
            {/* Address */}
            <div className="flex flex-col gap-1">
              <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">Server IP Address</span>
              <button 
                onClick={handleCopyAddress}
                className="w-full flex items-center justify-between px-2 py-1.5 bg-bg-primary/50 border border-white/5 hover:border-white/10 text-text-secondary hover:text-white transition-all text-xs font-mono cursor-pointer"
                title="Click to copy IP"
              >
                <span className="truncate">{copied ? 'Copied IP!' : (telemetryData?.server_address || '127.0.0.1:25565')}</span>
                <Copy className="w-3 h-3 text-text-muted shrink-0 ml-1.5" />
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3 py-3 border-t border-white/5 bg-bg-secondary/40 shrink-0">
            {/* Mini Status Dot */}
            <div 
              className={`w-3 h-3 rounded-none ${
                isRestarting ? 'bg-status-warning animate-pulse' :
                currentStatus === 'RUNNING' ? 'bg-status-online shadow-[0_0_8px_rgba(46,204,113,0.5)]' :
                currentStatus === 'STARTING' ? 'bg-status-starting animate-pulse' :
                currentStatus === 'STOPPING' ? 'bg-status-stopping animate-pulse' : 'bg-status-offline'
              }`}
              title={`Server: ${getStatusText(currentStatus)} (${telemetryData?.minecraft_version || '26.1.2'})`}
            />
            {/* Mini Copy Address Button */}
            <button 
              onClick={handleCopyAddress}
              className={`transition-colors cursor-pointer ${copied ? 'text-mc-emerald' : 'text-text-muted hover:text-white'}`}
              title={copied ? 'Copied!' : 'Copy Server IP Address'}
            >
              <Copy className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Profile / Bottom Details */}
        <div className="p-4 border-t border-white/5 bg-[#0e1116] shrink-0 space-y-3">
          {user && !sidebarCollapsed && (
            <div className="space-y-2">
              <div className="flex justify-between items-center bg-bg-surface/50 p-2 border border-white/5">
                <span className="text-xs font-semibold text-white truncate max-w-[120px]">{user.username}</span>
                <span className="text-[9px] font-mono uppercase px-1.5 py-0.5 bg-mc-emerald/10 text-mc-emerald border border-mc-emerald/20">
                  {user.role.replace('ROLE_', '')}
                </span>
              </div>
              <button 
                onClick={logout} 
                className="w-full flex items-center justify-center gap-2 py-2 bg-status-error/10 border border-status-error/20 hover:bg-status-error hover:text-bg-primary text-status-error font-pixel text-sm uppercase tracking-wider transition-all cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
                Sign Out
              </button>
            </div>
          )}
          {sidebarCollapsed && (
            <button 
              onClick={logout}
              title="Sign Out"
              className="w-10 h-10 flex items-center justify-center bg-status-error/10 border border-status-error/20 hover:bg-status-error hover:text-bg-primary text-status-error transition-all cursor-pointer mx-auto"
            >
              <LogOut className="w-4 h-4" />
            </button>
          )}
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden min-w-0">
        
        {/* Header */}
        <header className="flex justify-between items-center px-4 md:px-8 h-16 border-b border-white/5 bg-bg-secondary shrink-0 z-10">
          <div className="flex items-center min-w-0">
            <button 
              onClick={() => setMobileMenuOpen(true)}
              className="md:hidden mr-3 text-text-muted hover:text-white transition-colors cursor-pointer shrink-0"
              title="Open menu"
            >
              <Menu className="w-5 h-5" />
            </button>
            <h2 className="font-pixel text-base md:text-lg text-text-secondary tracking-wider truncate">
              {activeTab === 'server' && 'Server Diagnostics'}
              {activeTab === 'options' && 'Server Properties'}
              {activeTab === 'console' && 'Terminal Stream'}
              {activeTab === 'log' && 'Diagnostics Log'}
              {activeTab === 'players' && 'Permissions & Bans'}
              {activeTab === 'plugins' && 'Plugins Database'}
              {activeTab === 'files' && 'File Explorer'}
              {activeTab === 'worlds' && 'Active World Storage'}
              {activeTab === 'backups' && 'Backup Archives'}
              {activeTab === 'access' && 'Compliance & Access Logs'}
            </h2>
          </div>

          {/* Uptime indicators and address badge */}
          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-wider text-text-secondary">
              <span className={`w-2 h-2 rounded-none ${isTelemetryConnected ? 'bg-mc-emerald shadow-[0_0_8px_rgba(46,204,113,0.5)]' : 'bg-status-offline'}`} />
              <span>Telemetry</span>
            </div>
            
            {activeTab === 'console' && (
              <div className="hidden sm:flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-wider text-text-secondary">
                <span className={`w-2 h-2 rounded-none ${isConsoleConnected ? 'bg-mc-emerald shadow-[0_0_8px_rgba(46,204,113,0.5)]' : 'bg-status-error animate-pulse'}`} />
                <span>Console Live</span>
              </div>
            )}
          </div>
        </header>

        {/* Content Body Container */}
        <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6">
          {wsError && (
            <div className="p-4 bg-status-error/10 border border-status-error/20 text-status-error text-xs font-mono flex items-center gap-2">
              <ShieldAlert className="w-4.5 h-4.5 shrink-0" />
              <span>Telemetry WebSocket Connection Lost: {wsError}</span>
            </div>
          )}
          
          {/* Render Tab Components Dynamically */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.15 }}
              className="h-full"
            >
              {activeTab === 'server' && (
                <ServerTab
                  telemetryData={telemetryData}
                  currentStatus={currentStatus}
                  isRestarting={isRestarting}
                  actionPending={actionPending}
                  handleAction={handleAction}
                  cpuHistory={cpuHistory}
                  memHistory={memHistory}
                  sparkWidth={sparkWidth}
                  sparkHeight={sparkHeight}
                  cpuPaths={cpuPaths}
                  memPaths={memPaths}
                  memPercent={memPercent}
                  diskPercent={diskPercent}
                  formatGB={formatGB}
                  getStatusText={getStatusText}
                />
              )}

              {activeTab === 'console' && (
                <ConsoleTab
                  consoleError={consoleError}
                  commandInput={commandInput}
                  setCommandInput={setCommandInput}
                  isExecutingCommand={isExecutingCommand}
                  handleSendCommand={handleSendCommand}
                  searchQuery={searchQuery}
                  setSearchQuery={setSearchQuery}
                  filteredLogs={filteredLogs}
                  getLogClass={getLogClass}
                  terminalBodyRef={terminalBodyRef}
                  isServerOffline={isServerOffline}
                  clearLogs={clearLogs}
                  handleScroll={handleScroll}
                />
              )}

              {activeTab === 'options' && (
                <OptionsTab
                  config={config}
                  isLoadingConfig={isLoadingConfig}
                  isSavingConfig={isSavingConfig}
                  handleConfigChange={handleConfigChange}
                  handleSaveConfig={handleSaveConfig}
                  isModerator={isModerator}
                />
              )}

              {activeTab === 'log' && (
                <div className="bg-bg-secondary border border-white/5 flex flex-col h-[550px] shadow-mc-sm">
                  <div className="flex justify-between items-center px-4 py-3 bg-[#0d0e12] border-b border-white/5 shrink-0">
                    <span className="font-pixel text-sm text-text-secondary">latest.log</span>
                    <div className="flex gap-2">
                      <button onClick={fetchLatestLog} className="px-3 py-1 bg-bg-surface border border-white/10 hover:border-white/20 text-text-secondary hover:text-white transition-colors cursor-pointer text-xs font-pixel uppercase">
                        Refresh
                      </button>
                      <button onClick={() => window.open('/api/server/logs/latest', '_blank')} className="px-3 py-1 bg-bg-surface border border-white/10 hover:border-white/20 text-text-secondary hover:text-white transition-colors cursor-pointer text-xs font-pixel uppercase">
                        Raw
                      </button>
                      <button onClick={handleClearLog} className="px-3 py-1 bg-bg-surface border border-status-error/20 hover:bg-status-error/10 hover:text-status-error text-status-error transition-colors cursor-pointer text-xs font-pixel uppercase">
                        Clear File
                      </button>
                    </div>
                  </div>
                  <div className="flex-1 p-4 bg-[#08090c] overflow-y-auto font-mono text-xs space-y-1 select-text">
                    {isLoadingLog ? (
                      <div className="flex h-full items-center justify-center">
                        <div className="w-6 h-6 border border-white/20 border-t-mc-emerald rounded-full animate-spin" />
                      </div>
                    ) : logText ? (
                      logText.split('\n').map((line, idx) => (
                        <p key={idx} className={getLogClass(line)}>
                          {line}
                        </p>
                      ))
                    ) : (
                      <div className="flex h-full items-center justify-center text-text-muted font-pixel text-sm uppercase">
                        Log file is empty.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {activeTab === 'players' && (
                <PlayersTab
                  activePlayerList={activePlayerList}
                  setActivePlayerList={setActivePlayerList}
                  playersData={playersData}
                  isLoadingPlayers={isLoadingPlayers}
                  newPlayerNameOrIp={newPlayerNameOrIp}
                  setNewPlayerNameOrIp={setNewPlayerNameOrIp}
                  banReason={banReason}
                  setBanReason={setBanReason}
                  fetchPlayers={fetchPlayers}
                  handleAddPlayer={handleAddPlayer}
                  handleRemovePlayer={handleRemovePlayer}
                  runPlayerCommand={runPlayerCommand}
                  formatDate={formatDate}
                />
              )}

              {activeTab === 'plugins' && (
                <PluginsTab
                  installedPlugins={installedPlugins}
                  isLoadingPlugins={isLoadingPlugins}
                  isUninstallingPlugin={isUninstallingPlugin}
                  handleUninstallPlugin={handleUninstallPlugin}
                  handleUploadPluginFile={handleUploadPluginFile}
                  isDragging={isDragging}
                  setIsDragging={setIsDragging}
                  isUploadingPluginFile={isUploadingPluginFile}
                  setActiveTab={setActiveTab}
                  setCurrentFilePath={setCurrentFilePath}
                />
              )}

              {activeTab === 'files' && (
                <FilesTab
                  currentFilePath={currentFilePath}
                  filesList={filesList}
                  isLoadingFiles={isLoadingFiles}
                  editingFilePath={editingFilePath}
                  setEditingFilePath={setEditingFilePath}
                  editingFileContent={editingFileContent}
                  setEditingFileContent={setEditingFileContent}
                  isSavingFile={isSavingFile}
                  handleNavigateFiles={handleNavigateFiles}
                  handleReadFile={handleReadFile}
                  handleWriteFile={handleWriteFile}
                  handleDeleteFile={handleDeleteFile}
                  formatMB={formatMB}
                />
              )}

              {activeTab === 'worlds' && (
                <WorldsTab
                  worldStats={worldStats}
                  isLoadingWorldStats={isLoadingWorldStats}
                  isResettingWorld={isResettingWorld}
                  handleDownloadWorld={handleDownloadWorld}
                  handleResetWorld={handleResetWorld}
                  formatMB={formatMB}
                />
              )}

              {activeTab === 'backups' && (
                <BackupsTab
                  backups={backups}
                  isLoadingBackups={isLoadingBackups}
                  isCreatingBackup={isCreatingBackup}
                  restoringBackupId={restoringBackupId}
                  deletingBackupId={deletingBackupId}
                  handleCreateBackup={handleCreateBackup}
                  handleRestoreBackup={handleRestoreBackup}
                  handleDeleteBackup={handleDeleteBackup}
                  formatMB={formatMB}
                  formatDate={formatDate}
                  isModerator={isModerator}
                />
              )}

              {activeTab === 'access' && (
                <AccessTab
                  user={user}
                  usersList={usersList}
                  isLoadingUsers={isLoadingUsers}
                  isCreatingUser={isCreatingUser}
                  newUsername={newUsername}
                  setNewUsername={setNewUsername}
                  newEmail={newEmail}
                  setNewEmail={setNewEmail}
                  newPassword={newPassword}
                  setNewPassword={setNewPassword}
                  handleCreateUser={handleCreateUser}
                  handleDeleteUser={handleDeleteUser}
                  copiedUserId={copiedUserId}
                  handleCopyEmail={handleCopyEmail}
                  showChangePasswordModal={showChangePasswordModal}
                  setShowChangePasswordModal={setShowChangePasswordModal}
                  cpCurrentPassword={cpCurrentPassword}
                  setCpCurrentPassword={setCpCurrentPassword}
                  cpNewPassword={cpNewPassword}
                  setCpNewPassword={setCpNewPassword}
                  cpConfirmPassword={cpConfirmPassword}
                  setCpConfirmPassword={setCpConfirmPassword}
                  isChangingPassword={isChangingPassword}
                  cpSuccess={cpSuccess}
                  cpError={cpError}
                  setCpError={setCpError}
                  setCpSuccess={setCpSuccess}
                  handleChangePassword={handleChangePassword}
                  auditLogs={auditLogs}
                  auditTotal={auditTotal}
                  auditPage={auditPage}
                  setAuditPage={setAuditPage}
                  auditLimit={auditLimit}
                  auditActionFilter={auditActionFilter}
                  setAuditActionFilter={setAuditActionFilter}
                  auditUserFilter={auditUserFilter}
                  setAuditUserFilter={setAuditUserFilter}
                  auditSearchQuery={auditSearchQuery}
                  setAuditSearchQuery={setAuditSearchQuery}
                  isLoadingAudit={isLoadingAudit}
                  handleAuditSearchSubmit={handleAuditSearchSubmit}
                  expandedAuditId={expandedAuditId}
                  setExpandedAuditId={setExpandedAuditId}
                  fetchAuditLogs={fetchAuditLogs}
                  formatDate={formatDate}
                />
              )}
            </motion.div>
          </AnimatePresence>

        </div>
      </main>
    </div>
  );
};

export default Dashboard;
