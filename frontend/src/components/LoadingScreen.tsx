import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

const MESSAGES = [
  'Generating Chunks...',
  'Loading World...',
  'Preparing Redstone...',
  'Checking TPS...',
  'Initializing Console...',
  'Loading Plugins...',
  'Preparing Spawn Area...'
];

interface LoadingScreenProps {
  isComplete: boolean;
  onComplete?: () => void;
}

const LoadingScreen: React.FC<LoadingScreenProps> = ({ isComplete, onComplete }) => {
  const { panelName } = useAuth();
  const [messageIndex, setMessageIndex] = useState(0);
  const [progress, setProgress] = useState(0);
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

  // Message rotation
  useEffect(() => {
    const messageInterval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % MESSAGES.length);
    }, 1200);

    return () => clearInterval(messageInterval);
  }, []);

  // Progress bar simulation
  useEffect(() => {
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(progressInterval);
          if (onComplete) {
            setTimeout(onComplete, 400); // Small buffer before hiding
          }
          return 100;
        }

        // If authentication is not yet complete, hold progress at 95%
        if (!isComplete && prev >= 92) {
          if (prev < 95) {
            return prev + 1;
          }
          return prev;
        }

        // Smooth increments (2% to 6% every 120ms)
        const maxIncrement = isComplete ? 12 : 6;
        const increment = Math.floor(Math.random() * (maxIncrement - 2 + 1)) + 2;
        return Math.min(prev + increment, 100);
      });
    }, 120);

    return () => clearInterval(progressInterval);
  }, [isComplete, onComplete]);

  // Translate progress to standard MC level
  const currentLevel = Math.floor((progress / 100) * 30);

  return (
    <div className="fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-bg-primary select-none overflow-hidden">
      {/* Dynamic custom background image or tiled deepslate fallback */}
      {bgUrl ? (
        <div 
          className="custom-bg-pan opacity-15 pointer-events-none transition-all duration-1000"
          style={{ backgroundImage: `url(${bgUrl})` }}
        />
      ) : (
        <div className="absolute inset-0 bg-deepslate opacity-10 pointer-events-none" />
      )}
      
      {/* Radial vignette overlay */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_20%,#090a0f_95%)] pointer-events-none" />

      {/* Container card */}
      <div className="w-full max-w-[500px] px-8 text-center relative z-10">
        {/* Logo / Header in display font */}
        <h1 className="font-pixel text-5xl md:text-6xl text-mc-emerald mb-8 drop-shadow-[0_3px_0_rgba(0,0,0,0.8)] tracking-wider">
          {panelName}
        </h1>

        {/* Dynamic loading text */}
        <div className="h-8 mb-4 flex items-center justify-center">
          <AnimatePresence mode="wait">
            <motion.p
              key={messageIndex}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              transition={{ duration: 0.15 }}
              className="text-text-secondary text-lg md:text-xl font-pixel drop-shadow-[0_1px_0_rgba(0,0,0,0.5)]"
            >
              {MESSAGES[messageIndex]}
            </motion.p>
          </AnimatePresence>
        </div>

        {/* XP Level Number */}
        <div className="relative mb-2">
          <span 
            className="font-pixel text-3xl font-bold text-[#7cbf3f] select-none"
            style={{
              textShadow: '1px 1px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 0px 2px 3px rgba(0,0,0,0.8)'
            }}
          >
            {currentLevel}
          </span>
        </div>

        {/* Minecraft XP Bar Wrapper */}
        <div className="w-full h-3 bg-[#111111] border-2 border-[#555555] rounded-none overflow-hidden relative p-[1px] shadow-mc-md">
          {/* XP Bar Green Content */}
          <motion.div
            className="h-full bg-[#7cbf3f]"
            initial={{ width: '0%' }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            style={{
              boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.4), inset 0 -1px 0 rgba(0, 0, 0, 0.4)'
            }}
          />
        </div>

        {/* Technical progress tracker */}
        <p className="mt-4 font-mono text-xs text-text-muted">
          Chunk Loading: {progress}% (Level {currentLevel}/30)
        </p>
      </div>
    </div>
  );
};

export default LoadingScreen;
