import { describe, expect, it } from 'vitest';
import { resolveCuePlan } from './animation-orchestrator';

describe('resolveCuePlan', () => {
  it('chooses verdict-center preset during verdict reveal when user is reading', () => {
    const cue = resolveCuePlan(
      { session_id: 's', sequence: 1, type: 'verdict_revealed', phase: 'verdict', payload: {} },
      { reducedMotion: false, userReading: true }
    );

    expect(cue.cameraPreset).toBe('verdict-center');
    expect(cue.overlayMotion).toBe('minimal');
  });

  it('returns challenge-confrontation for challenge_issued', () => {
    const cue = resolveCuePlan(
      { session_id: 's', sequence: 2, type: 'challenge_issued', phase: 'clash', payload: {} },
      { reducedMotion: false, userReading: false }
    );

    expect(cue.cameraPreset).toBe('challenge-confrontation');
  });

  it('returns speaker-focus as default', () => {
    const cue = resolveCuePlan(
      { session_id: 's', sequence: 3, type: 'speaker_activated', phase: 'debate', payload: {} },
      { reducedMotion: false, userReading: false }
    );

    expect(cue.cameraPreset).toBe('speaker-focus');
  });
});
