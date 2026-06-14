import React, { createContext, useContext, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, AlertTriangle, XCircle, Info, X } from 'lucide-react';

export type ToastType = 'success' | 'warning' | 'error' | 'info';

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextType {
  showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    // Auto dismiss after 5 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Icon selector based on type
  const getIcon = (type: ToastType) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-status-online shrink-0" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-status-warning shrink-0" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-status-error shrink-0" />;
      case 'info':
        return <Info className="w-5 h-5 text-[#45D9FF] shrink-0" />;
    }
  };

  // Border and accent selector based on type
  const getStyles = (type: ToastType) => {
    switch (type) {
      case 'success':
        return 'border-status-online bg-bg-surface/90 shadow-[0_4px_12px_rgba(46,204,113,0.1)]';
      case 'warning':
        return 'border-status-warning bg-bg-surface/90 shadow-[0_4px_12px_rgba(245,197,66,0.1)]';
      case 'error':
        return 'border-status-error bg-bg-surface/90 shadow-[0_4px_12px_rgba(255,93,93,0.1)]';
      case 'info':
        return 'border-[#45D9FF] bg-bg-surface/90 shadow-[0_4px_12px_rgba(69,217,255,0.1)]';
    }
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      
      {/* Toast Portal Container */}
      <div className="fixed bottom-4 right-4 z-[99999] flex flex-col gap-2 w-full max-w-sm pointer-events-none">
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, x: 100, y: 20 }}
              animate={{ opacity: 1, x: 0, y: 0 }}
              exit={{ opacity: 0, x: 120, scale: 0.9 }}
              transition={{ type: 'spring', stiffness: 300, damping: 25 }}
              className={`flex items-start gap-3 p-4 border-l-4 rounded-r-md backdrop-blur-md border-y border-r border-t-white/5 border-b-black/25 text-text-primary text-sm font-sans pointer-events-auto shadow-mc-md ${getStyles(toast.type)}`}
            >
              {getIcon(toast.type)}
              <div className="flex-1 font-medium leading-tight pt-0.5">{toast.message}</div>
              <button 
                onClick={() => removeToast(toast.id)}
                className="text-text-muted hover:text-text-primary transition-colors cursor-pointer shrink-0"
              >
                <X className="w-4 h-4" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
};
