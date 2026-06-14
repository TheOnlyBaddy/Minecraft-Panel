import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import Login from './pages/Login/Login';
import Dashboard from './pages/Dashboard/Dashboard';
import LoadingScreen from './components/LoadingScreen';

const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [isAppLoading, setIsAppLoading] = useState(true);

  const handleLoadingComplete = React.useCallback(() => {
    setIsAppLoading(false);
  }, []);

  // Show loading screen until auth state is loaded AND the XP progress bar finishes animation
  if (isLoading || isAppLoading) {
    return (
      <LoadingScreen 
        isComplete={!isLoading}
        onComplete={handleLoadingComplete} 
      />
    );
  }

  return (
    <Router>
      <Routes>
        <Route
          path="/login"
          element={!isAuthenticated ? <Login /> : <Navigate to="/" replace />}
        />
        <Route
          path="/"
          element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" replace />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
};

const App: React.FC = () => {
  return (
    <ToastProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ToastProvider>
  );
};

export default App;
