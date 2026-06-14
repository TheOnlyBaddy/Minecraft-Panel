import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { motion } from 'framer-motion';
import { Lock, User, Check } from 'lucide-react';
import Logo from '../../components/Logo';

const Login: React.FC = () => {
  const { login, panelName } = useAuth();
  const { showToast } = useToast();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [bgUrl, setBgUrl] = useState<string | null>(null);

  useEffect(() => {
    const imgPng = new Image();
    imgPng.src = '/background.png';
    imgPng.onload = () => setBgUrl('/background.png');
    imgPng.onerror = () => {
      const imgJpg = new Image();
      imgJpg.src = '/background.jpg';
      imgJpg.onload = () => setBgUrl('/background.jpg');
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      showToast('Username/Email and password are required.', 'error');
      return;
    }

    setIsSubmitting(true);

    try {
      const loggedInUser = await login(username, password);
      const displayName = loggedInUser?.username || username;
      showToast(`Welcome back, ${displayName}!`, 'success');
    } catch (err: any) {
      showToast(err.message || 'Authentication failed. Please verify credentials.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full flex items-center justify-center bg-[#090a0f] overflow-hidden select-none">
      {/* Dynamic custom background image or tiled deepslate fallback */}
      {bgUrl ? (
        <div 
          className="custom-bg-pan opacity-45 pointer-events-none transition-all duration-1000"
          style={{ backgroundImage: `url(${bgUrl})` }}
        />
      ) : (
        <div className="absolute inset-0 bg-deepslate opacity-20 pointer-events-none" />
      )}
      
      {/* Radial vignette overlay */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_20%,#090a0f_95%)] pointer-events-none" />

      {/* Login Card (Glassmorphism, 500px width limit) */}
      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: 'spring', duration: 0.8, bounce: 0.2 }}
        className="relative z-10 w-full max-w-[500px] mx-4 bg-bg-surface/75 backdrop-blur-md border border-white/10 shadow-mc-lg p-8 md:p-10"
      >
        {/* Logo and Header Area */}
        <div className="text-center mb-8">
          <Logo 
            className="w-10 h-10 object-contain"
            fallbackIconClassName="w-8 h-8"
            containerClassName="inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br from-mc-emerald to-emerald-700 shadow-mc-sm border border-mc-emerald/30 mb-4 text-white" 
          />
          <h1 className="font-pixel text-4xl md:text-5xl text-white tracking-wide drop-shadow-[0_3px_0_rgba(0,0,0,0.6)]">
            {panelName}
          </h1>
          <p className="text-text-muted text-xs font-mono mt-1 tracking-wider uppercase">
            Minecraft Server Panel
          </p>
        </div>

        {/* Credentials Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Username Input Group */}
          <div className="space-y-2">
            <label htmlFor="username" className="block text-xs font-mono uppercase tracking-wider text-text-secondary">
              Username or Email
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-text-muted">
                <User className="w-4 h-4" />
              </span>
              <input
                type="text"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                autoComplete="username"
                disabled={isSubmitting}
                className="w-full pl-10 pr-4 py-3 bg-[#11141a]/90 border border-white/10 rounded-none text-white text-sm placeholder:text-text-muted focus:outline-none focus:border-mc-emerald transition-all font-sans"
              />
            </div>
          </div>

          {/* Password Input Group */}
          <div className="space-y-2">
            <label htmlFor="password" className="block text-xs font-mono uppercase tracking-wider text-text-secondary">
              Password
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-text-muted">
                <Lock className="w-4 h-4" />
              </span>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                autoComplete="current-password"
                disabled={isSubmitting}
                className="w-full pl-10 pr-4 py-3 bg-[#11141a]/90 border border-white/10 rounded-none text-white text-sm placeholder:text-text-muted focus:outline-none focus:border-mc-emerald transition-all font-sans"
              />
            </div>
          </div>

          {/* Remember Me Checkbox */}
          <div className="flex items-center">
            <button
              type="button"
              id="remember"
              onClick={() => setRememberMe(!rememberMe)}
              disabled={isSubmitting}
              className="flex items-center text-xs font-mono text-text-secondary cursor-pointer hover:text-white transition-colors"
            >
              <div className={`w-4 h-4 border border-white/20 mr-2 flex items-center justify-center transition-colors ${rememberMe ? 'bg-mc-emerald border-mc-emerald' : 'bg-black/40'}`}>
                {rememberMe && <Check className="w-3 h-3 text-bg-primary stroke-[3]" />}
              </div>
              Remember Me
            </button>
          </div>

          {/* Login Button with Emerald Gradient & Soft Glow */}
          <motion.button
            whileHover={{ scale: isSubmitting ? 1 : 1.01 }}
            whileTap={{ scale: isSubmitting ? 1 : 0.99 }}
            type="submit"
            disabled={isSubmitting}
            className={`w-full py-2 bg-gradient-to-r from-mc-emerald to-[#27ae60] hover:to-mc-emerald text-bg-primary font-pixel font-bold tracking-wider text-xl transition-all duration-300 shadow-mc-sm border border-mc-emerald/30 relative overflow-hidden group cursor-pointer ${
              isSubmitting ? 'opacity-80 cursor-not-allowed' : 'hover:shadow-[0_0_15px_rgba(46,204,113,0.5)]'
            }`}
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-bg-primary/20 border-t-bg-primary rounded-full animate-spin" />
                Connecting...
              </span>
            ) : (
              'Connect to Server'
            )}
          </motion.button>
        </form>

        {/* Bottom Technical Note */}
        <p className="mt-8 text-center text-[10px] font-mono text-text-muted">
          v1.0.0 // Encrypted Session Mode
        </p>
      </motion.div>
    </div>
  );
};

export default Login;
