import { useCallback } from 'react';

// Simple sound synthesis using Web Audio API to avoid external assets
const playTone = (freq: number, type: OscillatorType, duration: number, vol: number = 0.1) => {
  try {
    const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioContext) return;
    
    const ctx = new AudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc.type = type;
    osc.frequency.setValueAtTime(freq, ctx.currentTime);
    
    gain.gain.setValueAtTime(vol, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration);
    
    osc.connect(gain);
    gain.connect(ctx.destination);
    
    osc.start();
    osc.stop(ctx.currentTime + duration);
  } catch (e) {
    console.error("Audio playback failed", e);
  }
};

export const useSoundEffects = () => {
  const playClick = useCallback(() => {
    // Mechanical click sound
    playTone(800, 'square', 0.05, 0.05);
  }, []);

  const playSuccess = useCallback(() => {
    // Success chime
    playTone(600, 'sine', 0.1, 0.1);
    setTimeout(() => playTone(1200, 'sine', 0.2, 0.1), 100);
  }, []);

  const playError = useCallback(() => {
    // Error buzz
    playTone(150, 'sawtooth', 0.3, 0.1);
  }, []);

  const playTyping = useCallback(() => {
    // Subtle typing sound
    playTone(400 + Math.random() * 200, 'triangle', 0.03, 0.02);
  }, []);

  return { playClick, playSuccess, playError, playTyping };
};
