import type { SessionState, DebateParticipantView, CaptionEntry, VerdictView } from './types';
import type { DebatePhase } from '../transport/protocol';

export interface SceneViewModel {
  phase: string;
  activeSpeakerId: string | null;
  participants: Array<{ participant_id: string; accent_color?: string; seat_index?: number }>;
  cameraPreset: string;
  table: { mode: string };
  seats: Record<string, { mode: string }>;
}

export interface OverlayViewModel {
  phase: DebatePhase;
  topic: string | null;
  participants: DebateParticipantView[];
  activeSpeaker: DebateParticipantView | null;
  currentRound: number;
  totalRounds: number | null;
  currentCaption: CaptionEntry | null;
  captions: CaptionEntry[];
  verdict: VerdictView | null;
  participantCount: number;
}

export function selectSceneView(state: SessionState): SceneViewModel {
  const seatMap: Record<string, { mode: string }> = {};
  for (const p of state.participants) {
    seatMap[p.participant_id] = {
      mode: p.participant_id === state.activeSpeakerId ? 'active' : 'idle',
    };
  }
  return {
    phase: state.phase,
    activeSpeakerId: state.activeSpeakerId,
    participants: state.participants,
    cameraPreset: state.phase === 'complete' ? 'verdict-center' : 'speaker-focus',
    table: { mode: state.phase === 'complete' ? 'converged' : 'focused' },
    seats: seatMap,
  };
}

export function selectOverlayView(state: SessionState): OverlayViewModel {
  const activeSpeaker = state.activeSpeakerId
    ? state.participants.find(p => p.participant_id === state.activeSpeakerId) ?? null
    : null;
  return {
    phase: state.phase,
    topic: state.topic,
    participants: state.participants,
    activeSpeaker,
    currentRound: state.currentRound,
    totalRounds: state.totalRounds,
    currentCaption: state.captions.at(-1) ?? null,
    captions: state.captions,
    verdict: state.verdict,
    participantCount: state.participants.length,
  };
}
