import type { DebateEvent } from '../transport/protocol';

export interface MotionContext {
  reducedMotion: boolean;
  userReading: boolean;
}

export interface SceneCuePlan {
  cameraPreset: 'verdict-center' | 'challenge-confrontation' | 'speaker-focus' | 'overview';
  tableMode: 'converged' | 'directional' | 'focused' | 'idle';
  seatMode: 'audience' | 'tension' | 'active-speaker' | 'idle';
  overlayMotion: 'minimal' | 'measured' | 'normal';
}

export function resolveCuePlan(event: DebateEvent, context: MotionContext): SceneCuePlan {
  if (event.type === 'verdict_revealed') {
    return {
      cameraPreset: 'verdict-center',
      tableMode: 'converged',
      seatMode: 'audience',
      overlayMotion: context.userReading ? 'minimal' : 'measured',
    };
  }

  if (event.type === 'challenge_issued') {
    return {
      cameraPreset: 'challenge-confrontation',
      tableMode: 'directional',
      seatMode: 'tension',
      overlayMotion: 'minimal',
    };
  }

  return {
    cameraPreset: 'speaker-focus',
    tableMode: 'focused',
    seatMode: 'active-speaker',
    overlayMotion: context.reducedMotion ? 'minimal' : 'normal',
  };
}
