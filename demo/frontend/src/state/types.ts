import type { DebatePhase } from '../transport/protocol';

export interface DebateParticipantView {
  participant_id: string;
  label: string;
  role: string;
  stance?: string;
  seat_index?: number;
  accent_color?: string;
  emblem?: string;
}

export interface TimelineBeat {
  sequence: number;
  type: string;
  phase: DebatePhase;
  label: string;
}

export interface VerdictView {
  summary: string;
  verdicts: unknown[];
  contested_topics: string[];
}

export interface SessionState {
  sessionId: string | null;
  topic: string | null;
  phase: DebatePhase;
  participants: DebateParticipantView[];
  activeSpeakerId: string | null;
  currentRound: number;
  totalRounds: number | null;
  captions: CaptionEntry[];
  timeline: TimelineBeat[];
  verdict: VerdictView | null;
}

export interface CaptionEntry {
  speakerId: string;
  speakerLabel: string;
  text: string;
  round: number;
}
