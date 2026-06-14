// Web Audio API Synthesizer for 8-bit Retro Minecraft-like Chimes

let audioCtx: AudioContext | null = null;

const getAudioContext = (): AudioContext => {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  return audioCtx;
};

// Play a quick retro note helper
const playNote = (
  ctx: AudioContext, 
  freq: number, 
  type: OscillatorType, 
  startTime: number, 
  duration: number, 
  startVolume = 0.1
) => {
  const osc = ctx.createOscillator();
  const gainNode = ctx.createGain();

  osc.type = type;
  osc.frequency.setValueAtTime(freq, startTime);

  gainNode.gain.setValueAtTime(startVolume, startTime);
  // Exponential decay
  gainNode.gain.exponentialRampToValueAtTime(0.00001, startTime + duration);

  osc.connect(gainNode);
  gainNode.connect(ctx.destination);

  osc.start(startTime);
  osc.stop(startTime + duration);
};

// 1. Server Started Chime (Ascending 8-bit Level-Up Arpeggio - Loudest)
export const playStartChime = () => {
  try {
    const ctx = getAudioContext();
    const now = ctx.currentTime;
    
    // Play 4 notes in a rapid ascending arpeggio (G4 -> C5 -> E5 -> G5)
    const notes = [392.00, 523.25, 659.25, 784.00];
    const type: OscillatorType = 'triangle'; // triangle wave gives a nice hollow woodwind/bell sound

    notes.forEach((freq, index) => {
      const time = now + index * 0.08; // 80ms spacing
      playNote(ctx, freq, type, time, 0.4, 0.45);
    });

    // Add a high square wave chirp at the very end for extra 8-bit pop!
    playNote(ctx, 1046.50, 'square', now + 0.32, 0.2, 0.12); // C6 note
  } catch (err) {
    console.warn('Audio chime failed to play:', err);
  }
};

// 2. Server Stopped Chime (Buzzy Descending Power Down + Low Piston Thud - Loudest)
export const playStopChime = () => {
  try {
    const ctx = getAudioContext();
    const now = ctx.currentTime;

    // Descending buzzer pitch (from 180Hz to 60Hz)
    const osc = ctx.createOscillator();
    const gainNode = ctx.createGain();

    osc.type = 'sawtooth'; // Sawtooth wave gives a nice buzzy machine stop sound
    osc.frequency.setValueAtTime(180.00, now);
    osc.frequency.linearRampToValueAtTime(60.00, now + 0.35);

    gainNode.gain.setValueAtTime(0.42, now);
    gainNode.gain.exponentialRampToValueAtTime(0.00001, now + 0.35);

    osc.connect(gainNode);
    gainNode.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + 0.35);

    // Low thud note for solid landing (E2 thud)
    playNote(ctx, 82.41, 'triangle', now + 0.1, 0.4, 0.5);

    // Low frequency noise puff for piston/steam release feel
    const bufferSize = ctx.sampleRate * 0.25;
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = Math.random() * 2 - 1;
    }

    const noiseNode = ctx.createBufferSource();
    noiseNode.buffer = buffer;

    const filter = ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(300, now);
    filter.frequency.exponentialRampToValueAtTime(30, now + 0.25);

    const noiseGain = ctx.createGain();
    noiseGain.gain.setValueAtTime(0.15, now);
    noiseGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.25);

    noiseNode.connect(filter);
    filter.connect(noiseGain);
    noiseGain.connect(ctx.destination);

    noiseNode.start(now);
    noiseNode.stop(now + 0.25);
  } catch (err) {
    console.warn('Audio chime failed to play:', err);
  }
};

// 3. Server Restarted Chime (Dual tone arpeggio + magical sweep - Loudest)
export const playRestartChime = () => {
  try {
    const ctx = getAudioContext();
    const now = ctx.currentTime;

    // Play a bright restart success chord (C5 -> G5 -> C6)
    playNote(ctx, 523.25, 'triangle', now, 0.3, 0.4);
    playNote(ctx, 784.00, 'triangle', now + 0.06, 0.3, 0.4);
    playNote(ctx, 1046.50, 'triangle', now + 0.12, 0.5, 0.4);

    // Add a high sine-wave whistle that sweeps upwards (523.25Hz to 1200Hz)
    const osc = ctx.createOscillator();
    const gainNode = ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(523.25, now + 0.12);
    osc.frequency.exponentialRampToValueAtTime(1200.00, now + 0.4);

    gainNode.gain.setValueAtTime(0.24, now + 0.12);
    gainNode.gain.exponentialRampToValueAtTime(0.00001, now + 0.4);

    osc.connect(gainNode);
    gainNode.connect(ctx.destination);

    osc.start(now + 0.12);
    osc.stop(now + 0.4);
  } catch (err) {
    console.warn('Audio chime failed to play:', err);
  }
};

// 4. Player Joined Chime (High-pitched double-ding)
export const playPlayerJoinChime = () => {
  try {
    const ctx = getAudioContext();
    const now = ctx.currentTime;

    // E5 -> A5 ascending quick ding-ding
    playNote(ctx, 659.25, 'triangle', now, 0.2, 0.25);
    playNote(ctx, 880.00, 'triangle', now + 0.08, 0.25, 0.25);
  } catch (err) {
    console.warn('Audio chime failed to play:', err);
  }
};

// 5. Player Disconnected Chime (Descending double-note)
export const playPlayerLeaveChime = () => {
  try {
    const ctx = getAudioContext();
    const now = ctx.currentTime;

    // A4 -> E4 descending quick double-note
    playNote(ctx, 440.00, 'triangle', now, 0.2, 0.22);
    playNote(ctx, 329.63, 'triangle', now + 0.08, 0.25, 0.22);
  } catch (err) {
    console.warn('Audio chime failed to play:', err);
  }
};
