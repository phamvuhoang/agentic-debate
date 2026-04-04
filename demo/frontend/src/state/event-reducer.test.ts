import { describe, expect, it } from 'vitest';
import { reduceEvent, createInitialSessionState } from './event-reducer';

describe('reduceEvent', () => {
  it('tracks summoned agents, active speaker, and verdict state', () => {
    let state = createInitialSessionState();

    state = reduceEvent(state, {
      session_id: 'session-1',
      sequence: 1,
      type: 'agent_summoned',
      phase: 'summoning',
      payload: { participant_id: 'economist', label: 'Economist' },
    });
    state = reduceEvent(state, {
      session_id: 'session-1',
      sequence: 2,
      type: 'speaker_activated',
      phase: 'debate',
      payload: { speaker_id: 'economist' },
    });

    expect(state.participants).toHaveLength(1);
    expect(state.activeSpeakerId).toBe('economist');
  });

  it('transitions to complete phase on verdict_revealed', () => {
    let state = createInitialSessionState();
    state = reduceEvent(state, {
      session_id: 'session-1',
      sequence: 1,
      type: 'verdict_revealed',
      phase: 'complete',
      payload: { summary: 'Alice won.', verdicts: [], contested_topics: [] },
    });

    expect(state.phase).toBe('complete');
    expect(state.verdict).not.toBeNull();
  });
});
