export type DebateEventType =
  | 'debate_created'
  | 'agent_summoned'
  | 'speaker_activated'
  | 'argument_started'
  | 'argument_completed'
  | 'challenge_issued'
  | 'rebuttal_started'
  | 'consensus_shifted'
  | 'judge_intervened'
  | 'round_closed'
  | 'verdict_requested'
  | 'verdict_revealed'
  | 'debate_paused'
  | 'debate_resumed'
  | 'error_raised'
  | 'action_acknowledged';

export type DebatePhase =
  | 'idle'
  | 'summoning'
  | 'debate'
  | 'clash'
  | 'verdict'
  | 'complete'
  | 'error';

export type SessionActionType =
  | 'pause_debate'
  | 'resume_debate'
  | 'focus_agent'
  | 'inject_challenge'
  | 'redirect_debate'
  | 'advance_round'
  | 'request_verdict'
  | 'move_camera';

const VALID_EVENT_TYPES = new Set<string>([
  'debate_created',
  'agent_summoned',
  'speaker_activated',
  'argument_started',
  'argument_completed',
  'challenge_issued',
  'rebuttal_started',
  'consensus_shifted',
  'judge_intervened',
  'round_closed',
  'verdict_requested',
  'verdict_revealed',
  'debate_paused',
  'debate_resumed',
  'error_raised',
  'action_acknowledged',
]);

export interface DebateEvent {
  session_id: string;
  sequence: number;
  type: DebateEventType;
  phase: DebatePhase;
  payload: Record<string, unknown>;
}

export interface SessionActionRequest {
  action: SessionActionType;
  payload: Record<string, unknown>;
}

export function parseDebateEvent(raw: unknown): DebateEvent {
  if (!raw || typeof raw !== 'object') {
    throw new Error('Invalid event: not an object');
  }
  const obj = raw as Record<string, unknown>;
  if (!VALID_EVENT_TYPES.has(String(obj.type))) {
    throw new Error(`Unknown event type: ${obj.type}`);
  }
  return {
    session_id: String(obj.session_id ?? ''),
    sequence: Number(obj.sequence ?? 0),
    type: obj.type as DebateEventType,
    phase: (obj.phase ?? 'idle') as DebatePhase,
    payload: (obj.payload as Record<string, unknown>) ?? {},
  };
}
