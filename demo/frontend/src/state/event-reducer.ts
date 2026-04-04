import type { DebateEvent } from '../transport/protocol';
import type { SessionState, DebateParticipantView, VerdictView } from './types';

export function createInitialSessionState(): SessionState {
  return {
    sessionId: null,
    topic: null,
    phase: 'idle',
    participants: [],
    activeSpeakerId: null,
    currentRound: 0,
    totalRounds: null,
    captions: [],
    timeline: [],
    verdict: null,
  };
}

export function reduceEvent(state: SessionState, event: DebateEvent): SessionState {
  const beat = {
    sequence: event.sequence,
    type: event.type,
    phase: event.phase,
    label: event.type.replace(/_/g, ' '),
  };

  switch (event.type) {
    case 'debate_created':
      return {
        ...state,
        sessionId: event.session_id,
        topic: String(event.payload.topic ?? ''),
        phase: 'idle',
        timeline: [...state.timeline, beat],
      };

    case 'agent_summoned': {
      const p = event.payload as Partial<DebateParticipantView> & { participant_id: string };
      const participant: DebateParticipantView = {
        participant_id: p.participant_id,
        label: String(p.label ?? p.participant_id),
        role: String(p.role ?? ''),
        stance: p.stance,
        seat_index: p.seat_index,
        accent_color: p.accent_color,
        emblem: p.emblem,
      };
      return {
        ...state,
        phase: 'summoning',
        participants: [...state.participants, participant],
        timeline: [...state.timeline, beat],
      };
    }

    case 'speaker_activated':
      return {
        ...state,
        phase: 'debate',
        activeSpeakerId: String(event.payload.speaker_id ?? ''),
        timeline: [...state.timeline, beat],
      };

    case 'argument_started': {
      const roundIndex = Number(event.payload.round_index ?? state.currentRound);
      return {
        ...state,
        currentRound: roundIndex,
        timeline: [...state.timeline, beat],
      };
    }

    case 'argument_completed': {
      const text = String(event.payload.challenge_text ?? '');
      const speakerId = String(event.payload.challenger_id ?? state.activeSpeakerId ?? '');
      const speaker = state.participants.find(p => p.participant_id === speakerId);
      return {
        ...state,
        captions: text
          ? [
              ...state.captions,
              {
                speakerId,
                speakerLabel: speaker?.label ?? speakerId,
                text,
                round: state.currentRound,
              },
            ]
          : state.captions,
        timeline: [...state.timeline, beat],
      };
    }

    case 'round_closed':
      return {
        ...state,
        timeline: [...state.timeline, beat],
      };

    case 'judge_intervened':
      return { ...state, phase: 'verdict', timeline: [...state.timeline, beat] };

    case 'verdict_revealed': {
      const verdict: VerdictView = {
        summary: String(event.payload.summary ?? ''),
        verdicts: (event.payload.verdicts as unknown[]) ?? [],
        contested_topics: (event.payload.contested_topics as string[]) ?? [],
      };
      return {
        ...state,
        phase: 'complete',
        verdict,
        timeline: [...state.timeline, beat],
      };
    }

    case 'error_raised':
      return { ...state, phase: 'error', timeline: [...state.timeline, beat] };

    default:
      return { ...state, timeline: [...state.timeline, beat] };
  }
}
