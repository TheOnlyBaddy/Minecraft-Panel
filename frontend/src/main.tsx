import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// Global API fetch interceptor for Vercel/Render hosting split
const VITE_API_URL = import.meta.env.VITE_API_URL;
if (VITE_API_URL) {
  const originalFetch = window.fetch;
  window.fetch = async (input, init) => {
    if (typeof input === 'string' && input.startsWith('/api')) {
      input = `${VITE_API_URL.replace(/\/$/, '')}${input}`;
      init = {
        ...init,
        credentials: 'include'
      };
    }
    return originalFetch(input, init);
  };
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
